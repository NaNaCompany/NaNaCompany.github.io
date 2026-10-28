"""Validate generated pages, catalog coverage, assets, and imported records."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter
import json
import re
import runpy
from datetime import datetime
import xml.etree.ElementTree as ET
from repository_groups import grouped_repositories
from sitemap_sources import flattened_sources

ROOT = Path(__file__).resolve().parents[1]


def has_initial_commit(repository):
    """An unborn repository is still a draft, even if its origin is configured."""
    directory = repository / '.git'
    head = (directory / 'HEAD').read_text(encoding='utf-8').strip()
    if not head.startswith('ref: '):
        return bool(re.fullmatch(r'[0-9a-f]{40,64}', head))
    reference = head.removeprefix('ref: ')
    packed = directory / 'packed-refs'
    return (directory / reference).is_file() or (packed.is_file() and
        any(line.endswith(' ' + reference) for line in packed.read_text(encoding='utf-8').splitlines()))


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.images, self.app_ids, self.headings = [], [], [], [], 0
        self.canonicals = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'img':
            self.images.append(attrs.get('src', ''))
        if tag == 'link' and 'canonical' in attrs.get('rel', '').split():
            self.canonicals.append(attrs.get('href'))
        if attrs.get('data-app-id'):
            self.app_ids.append(attrs['data-app-id'])
        if tag == 'h1':
            self.headings += 1


def check():
    builder = runpy.run_path(str(ROOT / 'scripts/build_site.py'))
    outputs, counts = builder['build']()
    apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf-8'))
    app_ids = {a['id'] for a in apps}
    original = (ROOT / 'content/home-shell.html').read_text(encoding='utf-8')
    home = outputs['index.html']
    for section in ['services', 'partners', 'process', 'contact']:
        pattern = rf'<section id="{section}".*?</section>'
        assert builder['canonical_links'](re.search(pattern, original, re.S)[0]) == re.search(pattern, home, re.S)[0], f'Original section changed: {section}'
    hero = r'<section class="hero">.*?</section>'
    assert builder['canonical_links'](re.search(hero, original, re.S)[0]) == re.search(hero, home, re.S)[0], 'Original hero changed'
    for key, route in [('lectures','lectures'),('papers','papers'),('patents','patents'),('websites','projects')]:
        imported_cards = builder['imported'](key)
        for card in imported_cards:
            card = builder['canonical_links'](card)
            assert card in home, f'Missing {key} card on home'
            assert card in outputs[f'{route}/index.html'], f'Missing {key} card on {route}'
            if key != 'lectures':
                assert card in outputs['research/index.html'], f'Missing {key} card on R&D'
    for category in ['전체','기업','공공기관','교육기관','연구기관','컨퍼런스']:
        for page in [home, outputs['lectures/index.html']]:
            assert f'data-lecture-category="{category}"' in page, f'Missing lecture category {category}'
    assert len(builder['Cards'](home).cards) == sum(counts[key] for key in ['lectures','papers','patents','websites']), 'Home archive truncated or duplicated'
    # Only published NaNaCompany source repositories belong to this directory.
    # Local drafts without an origin may share the workspace while being built.
    expected = {p.name for p in ROOT.parent.iterdir() if p.is_dir() and not p.name.startswith('.')
                and (p / '.git/config').is_file() and p.name not in {ROOT.name, 'src_cdn'}
                # Another task may be creating/cloning a repository concurrently.
                # A .git-only placeholder has no app checkout to register yet.
                and any(child.name != '.git' for child in p.iterdir())
                and has_initial_commit(p)
                and re.search(r'url\s*=\s*(?:https://github\.com/|git@github\.com:)NaNaCompany/',
                              (p / '.git/config').read_text(encoding='utf-8'), re.I)}
    local_app_ids = {a['id'] for a in apps if not a.get('external')}
    # A verified split belongs to its existing card; preparing children expose no URLs.
    grouped_ids = {row['id'] for row in grouped_repositories(apps)}
    assert grouped_ids <= expected, f'Grouped repository checkout unavailable: {grouped_ids - expected}'
    expected -= grouped_ids
    # Language-only sibling repositories do not create additional app cards.
    expected = {name for name in expected if not any(name == base + '_' + language for base in local_app_ids for language in ['ko','en','es','zh','ja','fr','de','pt','ru','ar','it'])}
    for app in apps:
        if app.get('repository_path'):
            repository = (ROOT.parent / app['repository_path']).resolve()
            assert repository.is_relative_to(ROOT.parent.resolve()) and (repository / '.git').exists(), f'Missing app repository: {app["id"]}'
            expected.add(app['id'])
    assert local_app_ids == expected, f'Catalog differs from workspace: {local_app_ids ^ expected}'
    for app in apps:
        if app.get('external'):
            assert urlsplit(app.get('url', '')).scheme == 'https', f'Invalid external app URL: {app["id"]}'
    for name, expected_text in outputs.items():
        text = (ROOT / name).read_text(encoding='utf-8')
        assert text == expected_text, f'Stale: {name}'
        if not name.endswith('.html'):
            continue
        page = Page(text)
        route = name.removesuffix('index.html')
        assert page.canonicals == ['https://nanalab.kr/' + route], f'Invalid canonical in {name}'
        duplicates = [key for key, n in Counter(page.ids).items() if n > 1]
        assert not duplicates, f'Duplicate IDs in {name}: {duplicates}'
        assert page.headings == 1, f'Expected one h1 in {name}'
        assert 'api.nanalab.kr/rss' not in text and 'blog-list' not in text, name
        for link in page.links + page.images:
            parts = urlsplit(link)
            if link in page.links:
                assert link == builder['canonical_url'](link), f'Noncanonical local link {name}: {link}'
            if parts.scheme or parts.netloc:
                assert parts.scheme in {'https','http','mailto','tel'}, link
                continue
            if not parts.path:
                assert not parts.fragment or parts.fragment in page.ids, f'Broken anchor {name}: {link}'
                continue
            target = ROOT / parts.path.lstrip('/')
            assert target.exists(), f'Missing resource {name}: {link}'
        if name in {'index.html','apps/index.html'}:
            assert set(page.app_ids) == app_ids and len(page.app_ids) == len(apps), name
            expected_order = [app['id'] for app in sorted(apps, key=lambda app: datetime.fromisoformat(app['published_at'].replace('Z', '+00:00')), reverse=True)]
            assert page.app_ids == expected_order, f'Apps not newest first: {name}'
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    index = ET.fromstring(outputs['sitemap.xml'])
    assert index.tag == namespace + 'sitemapindex', 'Expected sitemap index at root'
    assert all(entry.tag == namespace + 'sitemap' for entry in index), 'Page entries in sitemap index'
    index_urls = [entry.findtext(namespace + 'loc') for entry in index]
    assert len(index_urls) == len(set(index_urls)), 'Duplicate sitemap references'
    assert 'https://nanalab.kr/sitemap.xml' not in index_urls, 'Self-referencing sitemap index'
    manifest = json.loads((ROOT / 'content/sitemap-sources.json').read_text(encoding='utf-8'))
    expected_maps = {'https://nanalab.kr/sitemap-main.xml'} | set(flattened_sources(manifest['sources']))
    if any(row['urls'] for row in manifest.get('supplemental', [])):
        expected_maps.add('https://nanalab.kr/sitemap-details.xml')
    assert set(index_urls) == expected_maps, 'Sitemap index missing or adding unregistered maps'
    sitemap = ET.fromstring(outputs['sitemap-main.xml'])
    assert sitemap.tag == namespace + 'urlset', 'Expected page URLs in sitemap-main.xml'
    sitemap_urls = [entry.text for entry in sitemap.iter(namespace + 'loc')]
    assert len(sitemap_urls) == len(set(sitemap_urls)), 'Duplicate sitemap URLs'
    assert all(url == builder['canonical_url'](url) for url in sitemap_urls), 'Noncanonical sitemap URL'
    assert builder['homepage_sitemap_urls'](home) <= set(sitemap_urls), 'Homepage links missing from main sitemap'
    for app in apps:
        launch_url = app.get('url') or f'https://nanalab.kr/{app["id"]}/'
        assert builder['homepage_sitemap_urls'](f'<a href="{launch_url}"></a>') <= set(sitemap_urls), 'App landing URL missing from main sitemap'
        for language in app.get('languages', []):
            language_path = app.get('language_paths', {}).get(language, language + '/')
            assert f'https://nanalab.kr/{app["id"]}/{language_path}' in sitemap_urls, 'Missing language URL'
    print(json.dumps({'status':'passed', 'checks':['catalog coverage','build freshness','unique IDs','local links and assets','heading structure','RSS removal','sitemap XML'], **counts}, ensure_ascii=False))


if __name__ == '__main__':
    check()
