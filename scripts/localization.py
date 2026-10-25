"""Static translations for the directory; Korean remains the default route.

Archive record titles, institutions, dates, identifiers and source links are
preserved. Translated app copy is stored separately from the Korean feed data.
"""
from html import escape, unescape
from html.entities import html5
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {'ko': '한국어', 'en': 'English', 'ja': '日本語', 'zh': '简体中文',
             'es': 'Español', 'de': 'Deutsch', 'fr': 'Français',
             'pt': 'Português', 'ru': 'Русский'}
ROUTES = ('', 'apps', 'lectures', 'research', 'papers', 'patents', 'projects', 'feeds')
SITE = 'https://nanalab.kr'
OG_LOCALES = {'ko':'ko_KR', 'en':'en_US', 'ja':'ja_JP', 'zh':'zh_CN',
              'es':'es_ES', 'de':'de_DE', 'fr':'fr_FR', 'pt':'pt_PT', 'ru':'ru_RU'}


def path_for(language, route=''):
    return '/' + '/'.join(part for part in [language if language != 'ko' else '', route] if part) + ('/' if language != 'ko' or route else '')


def language_navigation(language, route):
    links = ''.join(f'<a href="{path_for(code, route)}" lang="{code}" hreflang="{code}"'
                    + (' aria-current="page"' if code == language else '')
                    + f'>{label}</a>' for code, label in LANGUAGES.items())
    return (f'<details class="language-menu"><summary aria-label="Language">'
            f'<span aria-hidden="true">◎</span> {LANGUAGES[language]}</summary>'
            f'<nav aria-label="Language">{links}</nav></details>')


def alternate_links(route):
    return '\n'.join(f'<link rel="alternate" hreflang="{code}" href="{SITE}{path_for("ko" if code == "x-default" else code, route)}">'
                     for code in [*LANGUAGES, 'x-default'])


def normalize(text):
    return re.sub(r'\s+', ' ', unescape(text).strip())


class LocalizedHTML(HTMLParser):
    """Translate visible copy while keeping original markup and record keys."""
    def __init__(self, source, language, catalog, route):
        super().__init__(convert_charrefs=False)
        self.language, self.catalog, self.route = language, catalog, route
        self.ui, self.parts, self.skip, self.pending = catalog['ui'], [], 0, []
        self.feed(source)
        self.flush_text()

    def flush_text(self):
        if self.pending:
            self.parts.append(escape(self.translated(unescape(''.join(self.pending))), quote=False))
            self.pending.clear()

    def translated(self, value):
        key = normalize(value)
        target = self.ui.get(key)
        if target is None:
            if match := re.fullmatch(r'전체 (\d+)개', key):
                target = self.catalog['app_count'].format(label=self.ui['전체'], count=match[1])
            elif match := re.fullmatch(r'전체 (\d+)건 · 최신 강의순', key):
                target = self.catalog['lecture_count'].format(label=self.ui['전체'], count=match[1])
            elif match := re.fullmatch(r'(\d+)건', key):
                target = self.catalog['record_count'].format(count=match[1])
            elif key.endswith(':') and key[:-1] in self.ui:
                target = self.ui[key[:-1]] + ':'
            elif key.endswith(' JSON') and key[:-5] in self.ui:
                target = self.ui[key[:-5]] + ' JSON'
        if target is None:
            return value
        return re.match(r'^\s*', value)[0] + target + re.search(r'\s*$', value)[0]

    def local_link(self, href):
        parts = urlsplit(href)
        # Only directory navigation is localized. Apps keep verified launch URLs.
        if not parts.scheme and not parts.netloc and parts.path.startswith('/'):
            route = parts.path.strip('/')
            if route in ROUTES:
                return urlunsplit(('', '', path_for(self.language, route), parts.query, parts.fragment))
        return href

    def handle_starttag(self, tag, attrs):
        self.flush_text()
        raw = self.get_starttag_text()
        data = dict(attrs)
        if tag in {'script', 'style'}:
            self.skip += 1
        if tag == 'html':
            raw = re.sub(r'\blang="[^"]*"', f'lang="{self.language}"', raw)
        for key, value in attrs:
            if value is None:
                continue
            target = value
            if key in {'placeholder', 'aria-label', 'alt', 'title'}:
                target = self.translated(value)
                for ending in ['앱 열기', '템플릿 보기']:
                    if target.endswith(' ' + ending):
                        target = target[:-len(ending)] + self.ui[ending]
            elif tag == 'a' and key == 'href':
                target = self.local_link(value)
            elif key in {'src', 'href'} and not value.startswith(('/', '#')) and not urlsplit(value).scheme:
                # Original homepage assets must also work from /en/, /ja/, etc.
                target = '/' + value
            if target != value:
                raw = re.sub(r'(\b' + re.escape(key) + r'\s*=\s*)(["\'])(.*?)\2',
                             lambda m: m[1] + m[2] + escape(target, quote=True) + m[2], raw, count=1, flags=re.S)
        label = data.get('data-filter') or data.get('data-lecture-category')
        additions = ''
        if label:
            additions += f' data-label="{escape(self.ui.get("전체" if label == "all" else label, label), quote=True)}"'
        if data.get('id') in {'result-count', 'archive-count'}:
            key = 'app_count' if data['id'] == 'result-count' else 'lecture_count'
            additions += f' data-template="{escape(self.catalog[key], quote=True)}"'
        if data.get('id') == 'contact-form':
            for field, original in [('sending', '전송 중... (Sending...)'), ('success', '문의가 성공적으로 전송되었습니다! (Email sent successfully!)'), ('failure', '메일 전송에 실패했습니다:')]:
                additions += f' data-{field}="{escape(self.ui[original], quote=True)}"'
        if additions:
            raw = raw[:-1] + additions + '>'
        self.parts.append(raw)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in {'script', 'style'}:
            self.skip -= 1

    def handle_endtag(self, tag):
        self.flush_text()
        if tag in {'script', 'style'}:
            self.skip -= 1
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        if self.skip:
            self.parts.append(data)
        else:
            self.pending.append(data)

    def handle_entityref(self, name):
        self.pending.append('&' + name + (';' if name + ';' in html5 else ''))

    def handle_charref(self, name):
        self.pending.append('&#' + name + ';')

    def handle_comment(self, data):
        self.flush_text()
        self.parts.append('<!--' + data + '-->')

    def handle_decl(self, decl):
        self.flush_text()
        self.parts.append('<!' + decl + '>')


def build_localized_pages(outputs, apps, card_renderer):
    originals = {name: source for name, source in outputs.items() if name.endswith('.html')}
    for name, source in originals.items():
        route = name.removesuffix('index.html').strip('/')
        assert route in ROUTES
        alternates = alternate_links(route)
        for language in LANGUAGES:
            page = source
            if language != 'ko':
                catalog = json.loads((ROOT / f'content/i18n/{language}.json').read_text(encoding='utf-8'))
                for index, app in enumerate(apps):
                    translated = catalog['apps'][app['id']]
                    target = app.get('url', SITE + '/' + app['id'] + '/')
                    if language in app.get('languages', []):
                        target = target.rstrip('/') + '/' + app.get('language_paths', {}).get(language, language + '/')
                    page = page.replace(card_renderer(app, index), card_renderer({**app, **translated, 'url': target}, index))
                page = ''.join(LocalizedHTML(page, language, catalog, route).parts)
                page = re.sub(r'<title>.*?</title>', f'<title>{escape(catalog["titles"][route])} | NaNa Lab</title>', page, count=1, flags=re.S)
                for attribute, key in [('name="description"', 'description'), ('property="og:description"', 'description'),
                                       ('property="og:title"', None), ('property="og:url"', None)]:
                    value = catalog[key] if key else (catalog['titles'][route] + ' | NaNa Lab' if 'title' in attribute else SITE + path_for(language, route))
                    page = re.sub(r'<meta ' + re.escape(attribute) + r'[^>]*>',
                                  f'<meta {attribute} content="{escape(value, quote=True)}">', page, count=1)
                page = re.sub(r'<link rel="canonical"[^>]*>', f'<link rel="canonical" href="{SITE}{path_for(language, route)}">', page, count=1)
                if route not in {'apps', 'feeds'}:
                    note = '<p class="container translation-note">' + escape(catalog['archive_note']) + '</p>'
                    page = page.replace('<section id="lectures"', note + '<section id="lectures"', 1) if not route else page.replace('</main>', note + '</main>', 1)
            locales = f'<meta property="og:locale" content="{OG_LOCALES[language]}">\n'
            locales += '\n'.join(f'<meta property="og:locale:alternate" content="{value}">'
                                  for code, value in OG_LOCALES.items() if code != language)
            page = page.replace('</head>', alternates + '\n' + locales + '\n</head>', 1)
            page = page.replace('<button class="menu-toggle"', language_navigation(language, route) + '\n<button class="menu-toggle"', 1)
            target = (language + '/' if language != 'ko' else '') + name
            outputs[target] = page
    return [SITE + path_for(language, route) for language in LANGUAGES for route in ROUTES]
