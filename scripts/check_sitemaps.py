"""Validate the root sitemap index, every leaf map, and robots discovery."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse
import json
import time
import xml.etree.ElementTree as ET

from build_site import build
from site_urls import canonical_url
from repository_groups import grouped_landing_urls, grouped_repositories, sitemap_repositories

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://nanalab.kr/'
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


def leaf(raw, location):
    assert len(raw) <= 50 * 1024 * 1024, 'Sitemap exceeds 50 MiB: ' + location
    tree = ET.fromstring(raw)
    assert tree.tag == NS + 'urlset', 'Nested index or invalid leaf: ' + location
    urls = [node.text for node in tree.findall(NS + 'url/' + NS + 'loc')]
    assert urls and len(urls) == len(set(urls)) <= 50000, 'Empty, oversized or duplicate URLs: ' + location
    for url in urls:
        parts = urlsplit(url)
        assert parts.scheme == 'https' and parts.netloc == 'nanalab.kr' and not parts.fragment, url
        assert url == canonical_url(url), 'Noncanonical sitemap URL: ' + url
    return set(urls)


def fetch(location):
    request = Request(location + '?verify=' + str(time.time_ns()), headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(request, timeout=40) as response:
        assert response.status == 200, location
        return response.read()


def check(live=False):
    outputs, _ = build()
    manifest = json.loads((ROOT / 'content/sitemap-sources.json').read_text(encoding='utf-8'))
    index_url, main_url = SITE + 'sitemap.xml', SITE + 'sitemap-main.xml'
    source_urls = [row['url'] for row in manifest['sources']]
    assert len(source_urls) == len(set(source_urls)), 'Duplicate sitemap source'
    assert not set(source_urls) & {index_url, main_url, SITE + 'sitemap-details.xml'}, 'App source uses a reserved sitemap URL'
    expected = {main_url} | set(source_urls)
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
    assert {row['app_id'] for row in manifest['sources']} <= repository_ids
    children = {row['id']: row for row in grouped_repositories(apps)}
    for source in manifest['sources']:
        if source['app_id'] in children:
            child = children[source['app_id']]
            assert child['status'] == 'published'
            assert source.get('directory_app_id') == child['directory_app_id'], 'Child sitemap lost parent association'
            assert source['url'] == child['url'] + 'sitemap.xml', 'Wrong child sitemap location'
    # A newly added app must not silently lose discovery of its detailed map.
    registered = {row['app_id'] for row in manifest['sources']}
    assert len(registered) == len(manifest['sources']), 'Duplicate app sitemap registration'
    for app in repositories:
        if app.get('external') or app.get('kind') == 'template':
            continue
        repository = ROOT.parent / app['id']
        if any(path.is_file() for path in [repository / 'docs/sitemap.xml', repository / 'sitemap.xml', repository / 'dist/sitemap.xml']):
            assert app['id'] in registered, 'Run scripts/sync_sitemaps.py for: ' + app['id']
    source_by_url = {row['url']: row for row in manifest['sources']}

    def read(location):
        assert location.startswith(SITE), location
        name = location.removeprefix(SITE)
        if live:
            body = fetch(location)
        elif name in outputs:
            body = (ROOT / name).read_bytes()
        else:
            source = ROOT.parent / source_by_url[location]['app_id']
            path = next((p for p in [source / 'docs/sitemap.xml', source / 'sitemap.xml', source / 'dist/sitemap.xml'] if p.is_file()), None)
            assert path, 'Source checkout unavailable: ' + location
            body = path.read_bytes()
        if name in outputs:
            assert body.decode() == outputs[name], 'Generated sitemap is stale: ' + location
        return location, leaf(body, location)

    if live:
        with ThreadPoolExecutor(max_workers=8) as pool:
            maps = dict(pool.map(read, locations))
    else:
        maps = dict(map(read, locations))
    assert maps[main_url] == leaf(outputs['sitemap-main.xml'].encode(), 'generated main')
    assert grouped_landing_urls(apps) <= maps[main_url], 'Published child language landings missing'
    for child in children.values():
        if child['status'] == 'published':
            required = {child['url']} | {child['url'] + child.get('language_paths', {}).get(language, language + '/') for language in child['languages']}
            assert required <= maps[child['url'] + 'sitemap.xml'], 'Child sitemap misses language landings: ' + child['id']
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
    result = {'status': 'passed', 'mode': 'live' if live else 'local', 'sitemaps': len(maps),
              'index_entries': len(locations), 'app_sitemaps': len(manifest['sources']), 'main_urls': len(maps[main_url]),
              'supplemental_urls': len(extras), 'unique_page_urls': len(all_urls),
              'additional_detail_urls': len(all_urls - maps[main_url])}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    check(parser.parse_args().live)
