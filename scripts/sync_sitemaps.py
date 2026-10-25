"""Discover catalog apps' canonical sitemap files without changing app repositories.

Run when adding/updating apps, then rebuild. Existing sources are retained if a
source checkout is temporarily unavailable. Normal builds read the saved manifest.
"""
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
MANIFEST = ROOT / 'content/sitemap-sources.json'


def discover():
    previous = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    sources = {row['app_id']: row for row in previous.get('sources', [])}
    supplemental = {row['app_id']: row for row in previous.get('supplemental', [])}
    primary_path = ROOT / 'sitemap-main.xml'
    primary = {node.text for node in ET.parse(primary_path).iter(NS + 'loc')} if primary_path.exists() else set()
    apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf-8'))
    scanned = 0
    for app in apps:
        if app.get('external') or app.get('kind') == 'template':
            continue
        base = app.get('url', 'https://nanalab.kr/' + app['id'] + '/')
        parts = urlsplit(base)
        if parts.scheme != 'https' or parts.netloc != 'nanalab.kr':
            continue
        repository = ROOT.parent / app['id']
        source = next((path for path in [repository / 'docs/sitemap.xml', repository / 'sitemap.xml']
                       if path.is_file()), None)
        if source is None:
            if not (repository / 'index.html').is_file():
                continue
            pages = []
            excluded = {'src', 'content', 'templates', 'tests', 'locales', 'scripts', 'node_modules', 'previews', 'artifacts'}
            for file in sorted(repository.rglob('*.html')):
                relative = file.relative_to(repository)
                if any(part.startswith(('.', '_')) or part in excluded for part in relative.parts[:-1]):
                    continue
                if file.name.lower().startswith('test'):
                    continue
                text = file.read_text(encoding='utf-8-sig')
                if '<html' not in text.lower() or re.search(r'<meta\b[^>]*\bcontent=["\'][^"\']*noindex', text, re.I):
                    continue
                url = base + relative.as_posix().removesuffix('index.html')
                if url not in primary:
                    pages.append(url)
            supplemental[app['id']] = {'app_id': app['id'], 'urls': pages}
            continue
        tree = ET.parse(source).getroot()
        assert tree.tag == NS + 'urlset', f'Expected leaf sitemap: {app["id"]}'
        urls = [node.text for node in tree.findall(NS + 'url/' + NS + 'loc')]
        assert urls and len(urls) == len(set(urls)) <= 50000, app['id']
        assert all(url and url.startswith(base) for url in urls), app['id']
        sources[app['id']] = {'app_id': app['id'], 'url': base.rstrip('/') + '/sitemap.xml'}
        supplemental.pop(app['id'], None)
        scanned += 1
    rows = sorted(sources.values(), key=lambda row: row['url'])
    assert len({row['url'] for row in rows}) == len(rows), 'Duplicate sitemap source'
    extras = [row for _, row in sorted(supplemental.items()) if row['urls']]
    MANIFEST.write_text(json.dumps({'schema_version': '1.0', 'sources': rows, 'supplemental': extras}, ensure_ascii=False, indent=2) + '\n',
                        encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'synced', 'app_sitemaps': len(rows), 'local_sitemaps_checked': scanned,
                      'supplemental_pages': sum(len(row['urls']) for row in extras)}))


if __name__ == '__main__':
    discover()
