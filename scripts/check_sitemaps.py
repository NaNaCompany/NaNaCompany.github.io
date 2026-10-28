"""Validate the root sitemap index, every leaf map, and robots discovery."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import URLError
import argparse
import json
import time
import xml.etree.ElementTree as ET

from build_site import build
from site_urls import canonical_url
from repository_groups import grouped_landing_urls, grouped_repositories, sitemap_repositories
from sitemap_sources import (discover_leaf_urls, flattened_sources, local_sitemap_path,
                             parse_leaf, sitemap_entry, source_urls, validate_location)

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://nanalab.kr/'
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


def leaf(raw, location, *, directory=False, base=SITE):
    urls = parse_leaf(raw, location, base)
    for url in urls:
        parts = urlsplit(url)
        assert parts.scheme == 'https' and parts.netloc == 'nanalab.kr' and not parts.fragment, url
        # Directory link preferences do not change independently published app
        # routes. App leaf maps retain their own valid /ko/ pages.
        assert url == canonical_url(url, korean_aliases=directory), 'Noncanonical sitemap URL: ' + url
    return set(urls)


def fetch(location):
    for attempt in range(3):
        request = Request(location + '?verify=' + str(time.time_ns()), headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urlopen(request, timeout=40) as response:
                assert response.status == 200, location
                return response.read()
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(0.5 * (attempt + 1))


def check(live=False, remote_leaves=False):
    outputs, _ = build()
    manifest = json.loads((ROOT / 'content/sitemap-sources.json').read_text(encoding='utf-8'))
    index_url, main_url = SITE + 'sitemap.xml', SITE + 'sitemap-main.xml'
    registered_urls = flattened_sources(manifest['sources'])
    expected = {main_url} | set(registered_urls)
    extras = {url for row in manifest.get('supplemental', []) for url in row['urls']}
    if extras:
        expected.add(SITE + 'sitemap-details.xml')
    raw = fetch(index_url) if live else (ROOT / 'sitemap.xml').read_bytes()
    assert raw.decode() == outputs['sitemap.xml'], 'Published root sitemap is stale'
    assert len(raw) <= 50 * 1024 * 1024, 'Sitemap index exceeds 50 MiB'
    index = ET.fromstring(raw)
    assert index.tag == NS + 'sitemapindex', 'Expected sitemap index at root'
    assert all(node.tag == NS + 'sitemap' for node in index), 'Page entries in sitemap index'
    locations = [node.findtext(NS + 'loc') for node in index]
    assert locations and len(locations) == len(set(locations)) <= 50000, 'Invalid index locations'
    assert index_url not in locations, 'Sitemap index references itself'
    assert set(locations) == expected, 'Sitemap index differs from registered leaf maps'
    robots = fetch(SITE + 'robots.txt').decode() if live else (ROOT / 'robots.txt').read_text(encoding='utf-8')
    assert robots == outputs['robots.txt'], 'Published robots.txt is stale'
    assert 'User-agent: *' in robots and 'Allow: /' in robots
    advertised = [line.split(':', 1)[1].strip() for line in robots.splitlines() if line.startswith('Sitemap:')]
    assert len(advertised) == len(set(advertised)), 'Duplicate robots sitemap directive'
    assert set(advertised) == expected | {index_url}, 'Robots must advertise index and every leaf map'
    apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf-8'))
    repositories = sitemap_repositories(apps)
    repository_ids = {row['id'] for row in repositories}
    repository_by_id = {row['id']: row for row in repositories}
    assert {row['app_id'] for row in manifest['sources']} <= repository_ids
    children = {row['id']: row for row in grouped_repositories(apps)}
    for source in manifest['sources']:
        if source['app_id'] in children:
            child = children[source['app_id']]
            assert child['status'] == 'published'
            assert source.get('directory_app_id') == child['directory_app_id'], 'Child sitemap lost parent association'
            for location in source_urls(source):
                validate_location(location, child['url'])
    # A newly added app must not silently lose discovery of its detailed map.
    registered = {row['app_id'] for row in manifest['sources']}
    assert len(registered) == len(manifest['sources']), 'Duplicate app sitemap registration'
    for app in repositories:
        if app.get('external') or app.get('kind') == 'template':
            continue
        repository = ROOT.parent / app['id']
        entry = sitemap_entry(repository)
        if entry:
            assert app['id'] in registered, 'Run scripts/sync_sitemaps.py for: ' + app['id']
            if not live:
                row = next(row for row in manifest['sources'] if row['app_id'] == app['id'])
                base = app.get('url') or SITE + app['id'] + '/'
                assert source_urls(row) == discover_leaf_urls(entry, base), 'Run scripts/sync_sitemaps.py for: ' + app['id']
    source_by_url = {url: row for row in manifest['sources'] for url in source_urls(row)}
    bases = {row['app_id']: repository_by_id[row['app_id']].get('url') or SITE + row['app_id'] + '/'
             for row in manifest['sources']}
    for location, source in source_by_url.items():
        validate_location(location, bases[source['app_id']])

    def read(location):
        assert location.startswith(SITE), location
        name = location.removeprefix(SITE)
        if live or (remote_leaves and location in source_by_url):
            body = fetch(location)
        elif name in outputs:
            body = (ROOT / name).read_bytes()
        else:
            source = source_by_url[location]
            path = local_sitemap_path(ROOT.parent / source['app_id'], bases[source['app_id']], location)
            body = path.read_bytes()
        if name in outputs:
            assert body.decode() == outputs[name], 'Generated sitemap is stale: ' + location
        base = bases[source_by_url[location]['app_id']] if location in source_by_url else SITE
        return location, leaf(body, location, directory=location == main_url, base=base)

    if live or remote_leaves:
        with ThreadPoolExecutor(max_workers=8) as pool:
            maps = dict(pool.map(read, locations))
    else:
        maps = dict(map(read, locations))
    assert maps[main_url] == leaf(outputs['sitemap-main.xml'].encode(), 'generated main', directory=True)
    assert grouped_landing_urls(apps) <= maps[main_url], 'Published child language landings missing'
    app_pages = {}
    for source in manifest['sources']:
        leaves = [maps[url] for url in source_urls(source)]
        combined = set().union(*leaves)
        assert len(combined) == sum(map(len, leaves)), 'Duplicate page URLs across app leaves: ' + source['app_id']
        app_pages[source['app_id']] = combined
    for child in children.values():
        if child['status'] == 'published':
            required = {child['url']} | {child['url'] + child.get('language_paths', {}).get(language, language + '/') for language in child['languages']}
            assert required <= app_pages[child['id']], 'Child sitemap misses language landings: ' + child['id']
    if extras:
        assert maps[SITE + 'sitemap-details.xml'] == extras
    # Preserve every existing page URL and its metadata.
    baseline = ET.parse(ROOT / 'content/sitemap-base.xml').getroot()
    current = ET.fromstring(outputs['sitemap-main.xml'])
    def metadata(node):
        # Ignore indentation after </url>, which changes when another URL is appended.
        return ET.tostring(ET.fromstring(ET.tostring(node)))
    entries = {node.findtext(NS + 'loc'): metadata(node) for node in current.findall(NS + 'url')}
    for node in baseline.findall(NS + 'url'):
        assert metadata(node) == entries[node.findtext(NS + 'loc')], 'Original metadata changed'
    all_urls = set().union(*maps.values())
    mode = 'live' if live else 'local-with-remote-leaves' if remote_leaves else 'local'
    result = {'status': 'passed', 'mode': mode, 'sitemaps': len(maps),
              'index_entries': len(locations), 'registered_apps': len(manifest['sources']),
              'app_sitemaps': len(registered_urls), 'main_urls': len(maps[main_url]),
              'supplemental_urls': len(extras), 'unique_page_urls': len(all_urls),
              'additional_detail_urls': len(all_urls - maps[main_url])}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--remote-leaves', action='store_true',
                        help='Check local generated files and fetch every app leaf from its public URL')
    args = parser.parse_args()
    check(args.live, args.remote_leaves)
