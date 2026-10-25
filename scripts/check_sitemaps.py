"""Validate the root sitemap index and all leaf maps; --live checks deployment."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse
import json
import xml.etree.ElementTree as ET

from build_site import build

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
    return set(urls)


def fetch(location):
    request = Request(location + '?verify=sitemap-index', headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(request, timeout=40) as response:
        assert response.status == 200, location
        return response.read()


def check(live=False):
    outputs, _ = build()
    manifest = json.loads((ROOT / 'content/sitemap-sources.json').read_text(encoding='utf-8'))
    expected = {SITE + 'sitemap-main.xml'} | {row['url'] for row in manifest['sources']}
    extras = {url for row in manifest.get('supplemental', []) for url in row['urls']}
    if extras:
        expected.add(SITE + 'sitemap-details.xml')
    raw = fetch(SITE + 'sitemap.xml') if live else outputs['sitemap.xml'].encode()
    assert raw.decode() == outputs['sitemap.xml'], 'Published index is stale'
    index = ET.fromstring(raw)
    assert index.tag == NS + 'sitemapindex'
    locations = [node.text for node in index.findall(NS + 'sitemap/' + NS + 'loc')]
    assert len(locations) == len(set(locations)) <= 50000 and set(locations) == expected
    apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf-8'))
    app_ids = {row['id'] for row in apps}
    assert {row['app_id'] for row in manifest['sources']} <= app_ids
    # A newly added app must not silently lose its detailed map from the index.
    registered = {row['app_id'] for row in manifest['sources']}
    for app in apps:
        if app.get('external') or app.get('kind') == 'template':
            continue
        repository = ROOT.parent / app['id']
        if any(path.is_file() for path in [repository / 'docs/sitemap.xml', repository / 'sitemap.xml']):
            assert app['id'] in registered, 'Run scripts/sync_sitemaps.py for: ' + app['id']
    source_by_url = {row['url']: row for row in manifest['sources']}

    def read(location):
        assert location.startswith(SITE) and location != SITE + 'sitemap.xml', location
        name = location.removeprefix(SITE)
        if live:
            body = fetch(location)
        elif name in outputs:
            body = outputs[name].encode()
        else:
            source = ROOT.parent / source_by_url[location]['app_id']
            path = next((p for p in [source / 'docs/sitemap.xml', source / 'sitemap.xml'] if p.is_file()), None)
            assert path, 'Source checkout unavailable: ' + location
            body = path.read_bytes()
        return location, leaf(body, location)

    if live:
        with ThreadPoolExecutor(max_workers=8) as pool:
            maps = dict(pool.map(read, locations))
    else:
        maps = dict(map(read, locations))
    assert maps[SITE + 'sitemap-main.xml'] == leaf(outputs['sitemap-main.xml'].encode(), 'generated main')
    if extras:
        assert maps[SITE + 'sitemap-details.xml'] == extras
    # Existing URL metadata belongs in the page sitemap, never in the index.
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
              'app_sitemaps': len(manifest['sources']), 'main_urls': len(maps[SITE + 'sitemap-main.xml']),
              'supplemental_urls': len(extras), 'unique_page_urls': len(all_urls),
              'additional_detail_urls': len(all_urls - maps[SITE + 'sitemap-main.xml'])}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    check(parser.parse_args().live)
