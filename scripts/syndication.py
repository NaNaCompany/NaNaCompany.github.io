"""Build public read-only JSON catalogs, RSS 2.0 and JSON Feed 1.1 offline."""
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json
import re
import xml.etree.ElementTree as ET

SITE = 'https://nanalab.kr'
SOURCE = 'https://bhban.kr/'
SECTIONS = {'apps': '앱', 'lectures': '강의', 'papers': '논문·연구',
            'patents': '특허·실용신안', 'projects': '개발 프로젝트'}
ROUTES = {'websites': 'projects'}
ATOM = 'http://www.w3.org/2005/Atom'
ET.register_namespace('atom', ATOM)
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


def plain(value):
    return re.sub(r'\s+', ' ', value).strip()


class Record(HTMLParser):
    """Extract semantic text without exporting executable source HTML."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.attrs, self.stack, self.fields, self.links, self.images = {}, [], {}, [], []
        self.text = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.attrs:
            self.attrs = attrs
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs['src'])
        if tag == 'a' and urlsplit(attrs.get('href', '')).scheme in {'http', 'https'}:
            self.links.append(attrs['href'])
        if attrs.get('data-citation'):
            self.fields.setdefault('citation', attrs['data-citation'])
        if tag in VOID:
            self.handle_data(' ')
            return
        fields = set(attrs.get('class', '').split()) & {
            'abstract', 'bookDescription', 'firstCommitDate', 'lec_inst'}
        if re.fullmatch(r'h[3-6]', tag):
            fields.add('title')
        self.stack.append((tag, fields, []))

    def handle_data(self, data):
        self.text.append(data)
        for _, _, chunks in self.stack:
            chunks.append(data)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                matched, self.stack = self.stack[i:], self.stack[:i]
                for _, fields, chunks in matched:
                    for key in fields:
                        self.fields.setdefault(key, plain(''.join(chunks)))
                self.handle_data(' ')
                break


def record_identity(key, parsed):
    if parsed.attrs.get('data-record-id'):
        return parsed.attrs['data-record-id']
    text = plain(''.join(parsed.text))
    application = re.search(r'\b\d{2}-\d{4}-\d{7}\b', text)
    # Prefer persistent source identifiers to descriptions, images or list position.
    basis = application[0] if application else next(
        (url for url in parsed.links if not urlsplit(url).path.lower().endswith('.pdf')),
        parsed.fields.get('title', ''))
    assert basis, f'Missing record identity: {key}'
    return key + '-' + sha256(basis.encode()).hexdigest()[:20]


def anchor_for(key, identity):
    safe = re.sub(r'[^a-zA-Z0-9_-]', '-', identity)
    return 'record-' + ROUTES.get(key, key) + '-' + safe


def anchor_cards(key, cards):
    result = []
    for card in cards:
        parsed = Record(card)
        anchor = anchor_for(key, record_identity(key, parsed))
        if 'id' not in parsed.attrs:
            card = re.sub(r'^(<\w+)', lambda m: m[0] + f' id="{anchor}"', card, count=1)
        result.append(card)
    return result


def dated(record, text, year=None):
    """Use source calendar days, never turn a year-only value into January 1."""
    record['date_precision'] = 'unknown'
    if text:
        record['date_text'] = text
    explicit = re.search(r'\b(\d{4})\s*[.년/-]\s*(\d{1,2})\s*[.월/-]\s*(\d{1,2})', text)
    if explicit:
        try:
            value = datetime(*map(int, explicit.groups()), tzinfo=timezone(timedelta(hours=9)))
            record.update(date_published=value.isoformat(), date_precision='day')
            return
        except ValueError:
            pass
    match = re.search(r'(?<!\d)(?:19|20)\d{2}(?!\d)', str(year or text))
    if match:
        record.update(year=int(match[0]), date_precision='year')


def archive_record(key, card):
    parsed = Record(card)
    identity = record_identity(key, parsed)
    section = ROUTES.get(key, key)
    title = parsed.fields.get('title', '')
    assert title, f'Missing title: {key}/{identity}'
    row = {'id': identity, 'section': section, 'title': title,
           'url': SITE + '/' + section + '/#' + parsed.attrs.get('id', anchor_for(key, identity)),
           'summary': parsed.fields.get('abstract') or parsed.fields.get('bookDescription') or title,
           'source_url': SOURCE}
    for source, target in [('data-category', 'category'), ('data-publication-type', 'publication_type')]:
        if parsed.attrs.get(source):
            row[target] = parsed.attrs[source]
    for source, target in [('lec_inst', 'institution'), ('citation', 'citation')]:
        if parsed.fields.get(source):
            row[target] = parsed.fields[source]
    if parsed.images:
        row['image'] = parsed.images[0]
    if parsed.links:
        row['links'] = list(dict.fromkeys(parsed.links))
        row['external_url'] = next((u for u in row['links'] if not urlsplit(u).path.lower().endswith('.pdf')), row['links'][0])
    date_text = parsed.fields.get('firstCommitDate', '')
    if key == 'patents':
        match = re.search(r'출원일\s*(\d{4}\.\d{1,2}\.\d{1,2})', plain(''.join(parsed.text)))
        date_text = match[1] if match else ''
        row['date_kind'] = 'application_date'
    elif key == 'lectures':
        row['date_kind'] = 'lecture_date'
    year = parsed.attrs.get('data-publication-year')
    if key == 'papers' and not year:
        year = parsed.fields.get('bookDescription', '')
    dated(row, date_text, year)
    return row


def app_record(app):
    row = {'id': app['id'], 'section': 'apps', 'title': app['name'],
           'url': app.get('url', SITE + '/' + app['id'] + '/'), 'summary': app['description'],
           'category': app['category'], 'date_published': app['published_at'],
           'date_precision': 'second', 'date_kind': app['date_source'], 'source_url': SITE + '/apps/'}
    image = app.get('image_url') or (SITE + '/apps/img/' + app['image'] if app.get('image') else None)
    if image:
        row['image'] = image
    for key in ['repository', 'languages', 'kind']:
        if key in app:
            row[key] = app[key]
    if app.get('languages'):
        row['language_urls'] = {language: row['url'] + app.get('language_paths', {}).get(language, language + '/')
                                for language in app['languages']}
    return row


def order(row):
    if row.get('date_published'):
        value = datetime.fromisoformat(row['date_published'].replace('Z', '+00:00')).astimezone(timezone.utc)
        return value.year, value.month, value.day, value.hour, value.minute, value.second
    return row.get('year', 0), 0, 0, 0, 0, 0


def item_id(row):
    return 'urn:nanalab:' + row['section'] + ':' + row['id']


def feed_text(row):
    summary = row['summary']
    if len(summary) > 360:
        summary = summary[:357].rstrip() + '…'
    lines = [summary]
    for key, label in [('institution', '기관'), ('date_text', '원본 날짜'), ('citation', '인용')]:
        if row.get(key):
            lines.append(label + ': ' + row[key])
    if row.get('publication_type'):
        lines.append('자료 유형: ' + row['publication_type'])
    lines.append('출처: ' + row['source_url'])
    return '\n\n'.join(lines)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def feeds(rows, title, path, home):
    description = 'NaNa Lab의 앱·강의·논문·특허·개발 프로젝트 소식. 원본 날짜 기준 최신순.'
    feed = {'version': 'https://jsonfeed.org/version/1.1', 'title': title,
            'home_page_url': SITE + home, 'feed_url': SITE + path + '.json',
            'description': description, 'language': 'ko',
            'favicon': SITE + '/favicon.ico/android-icon-192x192.png', 'items': []}
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for tag, value in [('title', title), ('link', SITE + home), ('description', description), ('language', 'ko')]:
        ET.SubElement(channel, tag).text = value
    ET.SubElement(channel, '{' + ATOM + '}link', href=SITE + path + '.xml', rel='self', type='application/rss+xml')
    for row in rows:
        label = SECTIONS[row['section']]
        if row.get('publication_type') == 'preprint':
            label += ' / 프리프린트'
        item_title = '[' + label + '] ' + row['title']
        text = feed_text(row)
        item = {'id': item_id(row), 'url': row['url'], 'title': item_title,
                'content_text': text, 'tags': list(dict.fromkeys([label] + ([row['category']] if row.get('category') else [])))}
        for key in ['date_published', 'image', 'external_url']:
            if row.get(key):
                item[key] = row[key]
        feed['items'].append(item)
        entry = ET.SubElement(channel, 'item')
        for tag, value in [('title', item_title), ('link', row['url']), ('description', text)]:
            ET.SubElement(entry, tag).text = value
        ET.SubElement(entry, 'guid', isPermaLink='false').text = item_id(row)
        for tag in item['tags']:
            ET.SubElement(entry, 'category').text = tag
        if row.get('date_published'):
            value = datetime.fromisoformat(row['date_published'].replace('Z', '+00:00'))
            ET.SubElement(entry, 'pubDate').text = format_datetime(value)
    ET.indent(rss, space='  ')
    xml = ET.tostring(rss, encoding='unicode', xml_declaration=False)
    return {path.lstrip('/') + '.xml': '<?xml version="1.0" encoding="UTF-8"?>\n' + xml + '\n',
            path.lstrip('/') + '.json': json_text(feed)}


def build_syndication(apps, sections, provenance):
    catalogs = {'apps': [app_record(app) for app in apps]}
    for key, cards in sections.items():
        catalogs[ROUTES.get(key, key)] = [archive_record(key, card) for card in cards]
    for key, rows in catalogs.items():
        assert len({item_id(row) for row in rows}) == len(rows), 'Duplicate public IDs: ' + key
        catalogs[key] = sorted(rows, key=order, reverse=True)
    all_rows = sorted([row for rows in catalogs.values() for row in rows], key=order, reverse=True)
    research = sorted([row for key in ['papers', 'patents', 'projects'] for row in catalogs[key]], key=order, reverse=True)
    outputs = {}
    for key, rows in {**catalogs, 'research': research}.items():
        outputs['api/' + key + '.json'] = json_text({
            'schema_version': '1.0', 'type': key, 'count': len(rows), 'items': rows,
            'source': {'url': SITE + '/apps/'} if key == 'apps' else {
                'url': SOURCE, 'repository': provenance['repository'], 'commit': provenance['commit']}})
    outputs.update(feeds(all_rows[:200], 'NaNa Lab 업데이트', '/feed', '/'))
    for key, rows in [('apps', catalogs['apps']), ('lectures', catalogs['lectures']), ('research', research)]:
        title = 'NaNa Lab ' + {'apps': '앱', 'lectures': '강의', 'research': '연구'}[key]
        outputs.update(feeds(rows[:100], title, '/feeds/' + key, '/' + key + '/'))
    outputs['api/index.json'] = json_text({
        'schema_version': '1.0', 'title': 'NaNa Lab 공개 데이터', 'home_page_url': SITE,
        'documentation_url': SITE + '/feeds/', 'total_count': len(all_rows),
        'catalogs': {key: {'url': SITE + '/api/' + key + '.json', 'count': len(rows)}
                     for key, rows in {**catalogs, 'research': research}.items()},
        'feeds': {key: {'rss': SITE + path + '.xml', 'json_feed': SITE + path + '.json'}
                  for key, path in [('all', '/feed'), ('apps', '/feeds/apps'),
                                    ('lectures', '/feeds/lectures'), ('research', '/feeds/research')]}})
    return outputs


def documentation():
    links = ''.join(f'<li>{label}: <a href="{path}.xml">RSS</a> · <a href="{path}.json">JSON Feed</a></li>'
                    for label, path in [('통합 업데이트', '/feed'), ('앱', '/feeds/apps'),
                                        ('강의', '/feeds/lectures'), ('연구', '/feeds/research')])
    catalogs = ''.join(f'<li><a href="/api/{key}.json">{label} JSON</a></li>' for key, label in
                       [('apps', '앱'), ('lectures', '강의'), ('papers', '논문'),
                        ('patents', '특허'), ('projects', '프로젝트'), ('research', '연구 통합')])
    return ('<section class="container syndication-doc"><h2>구독 피드</h2><p>아래 주소를 RSS 리더에 등록하세요. '
            'RSS 2.0과 JSON Feed 1.1을 제공합니다. 통합 피드는 최근 200건, 분야별 피드는 최근 100건입니다.</p>'
            '<ul>' + links + '</ul><h2>조회용 JSON</h2><p>전체 목록을 정적 JSON으로 제공합니다. '
            '별도 로그인이나 API 키 없이 GET 요청으로 읽을 수 있습니다. 응답의 <code>items</code>가 목록이며 '
            '<code>count</code>가 항목 수입니다.</p><ul>' + catalogs + '</ul>'
            '<p><a href="/api/index.json">전체 엔드포인트·개수·스키마 버전</a></p>'
            '<pre><code>const response = await fetch("https://nanalab.kr/api/apps.json");\n'
            'const { items } = await response.json();</code></pre>'
            '<h2>날짜와 출처</h2><p>앱은 등록 원본의 공개 시각, 강의·특허는 원문에 적힌 일정을 사용합니다. '
            '일자만 있는 자료는 한국 시간 00:00으로 표현합니다. 연도만 확인되는 자료에는 정확한 게시 일시를 넣지 않습니다. '
            '날짜를 모르는 항목은 뒤에 정렬합니다. 재빌드만으로 ID나 게시 시각이 바뀌지 않습니다.</p>'
            '<p>강의·연구 자료의 원본 출처는 <a href="https://bhban.kr/">bhban.kr</a>입니다. '
            '논문·프리프린트 구분과 인용·원문 링크를 확인하세요. 공개 API 제공은 원문 자료의 이용 조건을 변경하지 않습니다.</p>'
            '<p>모든 파일은 사이트 빌드 때 함께 갱신됩니다. JSON Feed는 호스팅 환경에 따라 '
            '<code>application/json</code>으로 응답할 수 있으며 JSON Feed 1.1에서 허용하는 방식입니다.</p></section>')
