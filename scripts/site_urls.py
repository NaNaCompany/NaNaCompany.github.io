"""Canonical public URLs shared by HTML, catalogs, and sitemap checks."""
from html import escape, unescape
from urllib.parse import urlsplit, urlunsplit
import re

# Verified Korean copies remain accessible, while the root owns search identity.
KOREAN_ROOT_ALIASES = {
    'rebirth_country', 'rebirth_biology', 'line-copy', 'level-frame',
    'cat-naps', 'table-memory', 'color-drop',
}


def canonical_url(url):
    parts = urlsplit(url)
    if parts.scheme not in {'http', 'https'} or parts.netloc not in {'nanalab.kr', 'www.nanalab.kr'}:
        return url
    path = parts.path or '/'
    segments = path.split('/')
    if len(segments) >= 4 and segments[1] in KOREAN_ROOT_ALIASES and segments[2] == 'ko':
        path = '/' + '/'.join([segments[1], *segments[3:]])
    if path.endswith('/index.html'):
        path = path[:-len('index.html')]
    if path in {'/app', '/app/'}:
        path = '/apps/'
    elif not path.endswith('/') and '.' not in path.rsplit('/', 1)[-1]:
        path += '/'
    return urlunsplit(('https', 'nanalab.kr', path, parts.query, parts.fragment))


def canonical_links(source):
    """Normalize local absolute hyperlinks without altering source record IDs."""
    def replace(match):
        url = unescape(match[2])
        target = canonical_url(url)
        if target == url:
            return match[0]
        return 'href=' + match[1] + escape(target, quote=True) + match[1]
    return re.sub(r'\bhref=([\"\'])(.*?)\1', replace, source)
