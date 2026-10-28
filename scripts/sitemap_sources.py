"""Shared manifest flattening and safe, local app sitemap discovery.

Schema 1.0 keeps ``url`` as the first leaf and optionally stores further leaves
in ``additional_urls``. One source row continues to identify one repository.
"""
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

SITE = 'https://nanalab.kr/'
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
MAX_BYTES = 50 * 1024 * 1024
RESERVED = {SITE + name for name in ('sitemap.xml', 'sitemap-main.xml', 'sitemap-details.xml')}


def validate_location(location, base=SITE):
    assert isinstance(location, str), 'Invalid sitemap location'
    parts, prefix = urlsplit(location), urlsplit(base)
    assert prefix.scheme == 'https' and prefix.netloc == 'nanalab.kr' and prefix.path.endswith('/'), base
    assert not prefix.query and not prefix.fragment, base
    assert parts.scheme == 'https' and parts.netloc == prefix.netloc, location
    assert not parts.query and not parts.fragment, location
    assert parts.path.startswith(prefix.path) and parts.path.endswith('.xml'), location
    assert not any(token in parts.path for token in ('\\', '%', '//')), 'Unsafe sitemap path: ' + location
    assert not any(part in {'.', '..'} for part in parts.path.split('/')), 'Unsafe sitemap path: ' + location
    return location


def source_urls(row):
    additional = row.get('additional_urls', [])
    assert isinstance(additional, list), 'additional_urls must be a list'
    urls = [row['url'], *additional]
    assert len(urls) == len(set(urls)), 'Duplicate sitemap source: ' + row['app_id']
    for url in urls:
        validate_location(url)
        assert url not in RESERVED, 'App source uses a reserved sitemap URL: ' + url
    return urls


def flattened_sources(rows):
    assert len({row['app_id'] for row in rows}) == len(rows), 'Duplicate app sitemap registration'
    urls = [url for row in rows for url in source_urls(row)]
    assert len(urls) == len(set(urls)), 'Duplicate sitemap source'
    return urls


def sitemap_entry(repository):
    return next((path for path in (repository / 'docs/sitemap.xml', repository / 'sitemap.xml', repository / 'dist/sitemap.xml')
                 if path.is_file()), None)


def local_sitemap_path(repository, base, location):
    """Resolve a public leaf against the actual publishing root, never another repo."""
    validate_location(location, base)
    entry = sitemap_entry(repository)
    assert entry, 'Source checkout unavailable: ' + location
    root = entry.parent.resolve()
    assert root.is_relative_to(repository.resolve()), 'Sitemap publishing root escapes repository'
    relative = urlsplit(location).path.removeprefix(urlsplit(base).path)
    path = (root / relative).resolve()
    assert path.is_relative_to(root), 'Sitemap path escapes publishing root: ' + location
    assert path.is_file(), 'Source sitemap unavailable: ' + location
    return path


def parse_leaf(raw, location, base=SITE):
    assert len(raw) <= MAX_BYTES, 'Sitemap exceeds 50 MiB: ' + location
    tree = ET.fromstring(raw)
    assert tree.tag == NS + 'urlset', 'Nested index or invalid leaf: ' + location
    assert all(node.tag == NS + 'url' for node in tree), 'Invalid leaf entry: ' + location
    urls = [node.findtext(NS + 'loc') for node in tree]
    assert urls and len(urls) == len(set(urls)) <= 50000, 'Empty, oversized or duplicate URLs: ' + location
    prefix = urlsplit(base)
    for url in urls:
        assert isinstance(url, str), 'Missing page URL: ' + location
        parts = urlsplit(url)
        assert parts.scheme == 'https' and parts.netloc == prefix.netloc and not parts.fragment, url
        assert parts.path.startswith(prefix.path), 'Page outside app base: ' + url
        assert not any(token in parts.path for token in ('\\', '%2e', '%2E', '%2f', '%2F', '%5c', '%5C')), url
        assert not any(part in {'.', '..'} for part in parts.path.split('/')), url
    return urls


def discover_leaf_urls(source, base):
    """Accept a leaf or one local index; reject a second index level and cycles."""
    entry_url = validate_location(base.rstrip('/') + '/sitemap.xml', base)
    repository_root = source.parent.resolve()
    raw = source.read_bytes()
    assert len(raw) <= MAX_BYTES, 'Sitemap exceeds 50 MiB: ' + entry_url
    tree = ET.fromstring(raw)
    if tree.tag == NS + 'urlset':
        parse_leaf(raw, entry_url, base)
        return [entry_url]
    assert tree.tag == NS + 'sitemapindex', 'Invalid sitemap: ' + entry_url
    assert all(node.tag == NS + 'sitemap' for node in tree), 'Invalid sitemap index entry: ' + entry_url
    locations = [node.findtext(NS + 'loc') for node in tree]
    assert locations and len(locations) == len(set(locations)) <= 50000, 'Invalid index locations: ' + entry_url
    seen_pages = set()
    for location in locations:
        validate_location(location, base)
        assert location != entry_url, 'Sitemap index references itself: ' + location
        relative = urlsplit(location).path.removeprefix(urlsplit(base).path)
        path = (repository_root / relative).resolve()
        assert path.is_relative_to(repository_root), 'Sitemap path escapes publishing root: ' + location
        assert path.is_file(), 'Source sitemap unavailable: ' + location
        pages = set(parse_leaf(path.read_bytes(), location, base))
        assert not pages & seen_pages, 'Duplicate page URLs across app leaves: ' + location
        seen_pages.update(pages)
    return locations
