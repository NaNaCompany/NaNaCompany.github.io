"""Validate generated pages, catalog coverage, assets, and imported records."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter
import json
import re
import runpy
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.images, self.app_ids, self.headings = [], [], [], [], 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'img':
            self.images.append(attrs.get('src', ''))
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
        assert re.search(pattern, original, re.S)[0] == re.search(pattern, home, re.S)[0], f'Original section changed: {section}'
    hero = r'<section class="hero">.*?</section>'
    assert re.search(hero, original, re.S)[0] == re.search(hero, home, re.S)[0], 'Original hero changed'
    for key, route in [('lectures','lectures'),('papers','papers'),('patents','patents'),('websites','projects')]:
        imported_cards = builder['imported'](key)
        for card in imported_cards:
            assert card in home, f'Missing {key} card on home'
            assert card in outputs[f'{route}/index.html'], f'Missing {key} card on {route}'
            if key != 'lectures':
                assert card in outputs['research/index.html'], f'Missing {key} card on R&D'
    for category in ['전체','기업','공공기관','교육기관','연구기관','컨퍼런스']:
        for page in [home, outputs['lectures/index.html']]:
            assert f'data-lecture-category="{category}"' in page, f'Missing lecture category {category}'
    assert len(builder['Cards'](home).cards) == sum(counts[key] for key in ['lectures','papers','patents','websites']), 'Home archive truncated or duplicated'
    expected = {p.name for p in ROOT.parent.iterdir() if p.is_dir() and not p.name.startswith('.')
                and (p / '.git').exists() and p.name not in {ROOT.name, 'src_cdn'}}
    local_app_ids = {a['id'] for a in apps if not a.get('external')}
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
        duplicates = [key for key, n in Counter(page.ids).items() if n > 1]
        assert not duplicates, f'Duplicate IDs in {name}: {duplicates}'
        assert page.headings == 1, f'Expected one h1 in {name}'
        assert 'api.nanalab.kr/rss' not in text and 'blog-list' not in text, name
        for link in page.links + page.images:
            parts = urlsplit(link)
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
    ET.fromstring(outputs['sitemap.xml'])
    print(json.dumps({'status':'passed', 'checks':['catalog coverage','build freshness','unique IDs','local links and assets','heading structure','RSS removal','sitemap XML'], **counts}, ensure_ascii=False))


if __name__ == '__main__':
    check()
