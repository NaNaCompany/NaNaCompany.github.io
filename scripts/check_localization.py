"""Validate static language routes, navigation, translated copy and SEO links."""
from html.parser import HTMLParser
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import xml.etree.ElementTree as ET
from localization import LANGUAGES, ROUTES, SITE, path_for

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.lang, self.canonical, self.alternates = None, [], {}
        self.links, self.assets, self.apps, self.record_ids = [], [], [], []
        self.language_links, self.filters, self.lecture_filters = [], {}, {}
        self.in_language_nav = False
        self.in_footer = False
        self.footer_menus = 0
        self.preference_scripts = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'footer':
            self.in_footer = True
        if tag == 'details' and 'language-menu' in a.get('class', '').split():
            assert self.in_footer, 'Language menu must be in the footer'
            self.footer_menus += 1
        if tag == 'script' and urlsplit(a.get('src', '')).path == '/language-preference.js':
            assert 'defer' in a, 'Language detection must not block HTML parsing'
            self.preference_scripts.append(a['src'])
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a['href'])
        if tag == 'link' and a.get('hreflang'):
            assert a['hreflang'] not in self.alternates, 'Duplicate alternate language'
            self.alternates[a['hreflang']] = a['href']
        if tag == 'nav' and a.get('aria-label') == 'Language':
            self.in_language_nav = True
        if tag == 'a':
            self.links.append(a.get('href', ''))
            if self.in_language_nav:
                self.language_links.append(a['href'])
        if tag in {'script','img','source'} and a.get('src'):
            self.assets.append(a['src'])
        if tag == 'link' and a.get('rel') in {'stylesheet','icon','manifest','apple-touch-icon'}:
            self.assets.append(a['href'])
        if a.get('data-app-id'):
            self.apps.append(a['data-app-id'])
        if a.get('data-record-id'):
            self.record_ids.append(a['data-record-id'])
        if a.get('data-filter'):
            self.filters[a['data-filter']] = a.get('data-label')
        if a.get('data-lecture-category'):
            self.lecture_filters[a['data-lecture-category']] = a.get('data-label')

    def handle_endtag(self, tag):
        if tag == 'footer':
            self.in_footer = False
        if tag == 'nav':
            self.in_language_nav = False


def check():
    apps = json.loads((ROOT / 'content/apps.json').read_text(encoding='utf8'))
    primary = Page((ROOT / 'index.html').read_text(encoding='utf8'))
    assert primary.lang == 'ko'
    main_urls = {node.text for node in ET.parse(ROOT / 'sitemap-main.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    for language in LANGUAGES:
        catalog = None if language == 'ko' else json.loads((ROOT / f'content/i18n/{language}.json').read_text(encoding='utf8'))
        if catalog:
            assert catalog['language'] == language
            for app in apps:
                translated = catalog['apps'].get(app['id'])
                assert translated and translated['name'] and translated['description'], f'Missing {language} app: {app["id"]}'
                assert not re.search('[가-힣]', translated['name'] + translated['description']), f'Untranslated {language} app: {app["id"]}'
        for route in ROUTES:
            path = path_for(language, route)
            source = (ROOT / path.strip('/') / 'index.html').read_text(encoding='utf8')
            page = Page(source)
            assert page.lang == language, path
            assert page.footer_menus == 1, f'Missing or repeated footer menu: {path}'
            assert len(page.preference_scripts) == 1, f'Missing or repeated language detection: {path}'
            assert page.canonical == [SITE + path], path
            expected = {code: SITE + path_for(code, route) for code in LANGUAGES}
            expected['x-default'] = SITE + path_for('ko', route)
            assert page.alternates == expected, f'Nonreciprocal hreflang: {path}'
            assert page.language_links == [path_for(code, route) for code in LANGUAGES], f'Language route lost: {path}'
            assert source.count('data-google-vignette="false"') == len(LANGUAGES), f'Language switch may trigger interstitial: {path}'
            assert SITE + path in main_urls, f'Missing localized sitemap URL: {path}'
            for asset in page.assets:
                if language != 'ko':
                    assert asset.startswith('/') or urlsplit(asset).scheme == 'https', f'Relative asset {path}: {asset}'
            original = Page((ROOT / route / 'index.html').read_text(encoding='utf8'))
            assert page.record_ids == original.record_ids, f'Archive identities changed: {path}'
            if route in {'','apps'}:
                assert page.apps == primary.apps, f'Localized catalog missing or reordered: {path}'
                if catalog:
                    assert all(label for label in page.filters.values()), path
                    assert catalog['ui']['어떤 도구를 찾으세요?'] in source, path
                    assert 'data-template="' in source, path
            if catalog and route in {'','lectures'}:
                assert set(page.lecture_filters) == {'전체','기업','공공기관','교육기관','연구기관','컨퍼런스'}, path
                assert all(page.lecture_filters.values()), path
            if catalog and not route:
                assert escape(catalog['ui']['R&D과제의 성공적인 수행과 지표달성, 특허출원을 지원합니다.'], quote=False) in source, f'Business copy not translated: {path}'
            if catalog:
                for href in page.links:
                    if href in page.language_links:
                        continue
                    parts = urlsplit(href)
                    assert not (not parts.scheme and parts.path.strip('/') in ROUTES and parts.path.startswith('/')), f'Language navigation escaped to Korean: {path}: {href}'
    print(json.dumps({'status':'passed','languages':len(LANGUAGES),'localized_pages':len(ROUTES)*(len(LANGUAGES)-1),
                      'checks':['Korean default','translated app catalog','reciprocal hreflang','self canonicals',
                                'equivalent-route footer switcher','language detection script','archive identity','localized filters','assets','sitemap coverage']}))


if __name__ == '__main__':
    check()
