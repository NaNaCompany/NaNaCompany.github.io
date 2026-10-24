"""Build the static app directory and locally imported portfolio pages.

Usage: python scripts/build_site.py [--check]
Requires only the Python standard library. No network access during builds.
"""
from pathlib import Path
from datetime import date, datetime
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import urljoin
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


class Cards(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source, self.stack, self.cards = source, [], []
        self.lines = [0] + [m.end() for m in re.finditer('\n', source)]
        self.feed(source)

    def source_offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        classes = dict(attrs).get('class', '').split()
        is_card = bool(set(classes) & {'singleLectureContainer', 'singleProjectContainer', 'singleCodeContainer'})
        self.stack.append((tag, self.source_offset(), is_card))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                matched, self.stack = self.stack[i:], self.stack[:i]
                for _, start, card in matched:
                    if card:
                        self.cards.append(self.source[start:self.source.index('>', self.source_offset()) + 1])
                break


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def imported(key):
    source = read(f'content/portfolio/{key}.html')
    if key == 'lectures':
        # Match the source site's cross-listing of all offline courses into Lectures.
        source += '\n' + read('content/portfolio/courses-offline.html')
    # Relative resources belong to the source portfolio, not this domain.
    source = re.sub(r'\b(href|src)="([^"]+)"', lambda m: f'{m[1]}="{escape(urljoin("https://bhban.kr/", unescape(m[2])), quote=True)}"', source)
    source = re.sub(r'<a\b([^>]*)>(\s*<i\b[^>]*class="([^"]*)"[^>]*></i>\s*)</a>',
                    lambda m: '<a' + m[1] + '>' + ('PDF' if 'pdf' in m[3] else '링크 열기') + '</a>', source)
    cards = Cards(source).cards
    if key == 'lectures':
        unique = {}
        for card in cards:
            identity = re.search(r'data-record-id="([^"]+)"', card)
            assert identity, 'Lecture record needs an identity'
            unique.setdefault(identity[1], card)
        cards = sorted(unique.values(), key=lecture_latest_date, reverse=True)
    return cards


def lecture_latest_date(card):
    match = re.search(r'class="firstCommitDate"[^>]*>(.*?)</', card, re.S)
    text = match[1].strip() if match else ''
    if re.fullmatch(r'\d{4}년?', text):
        return int(re.search(r'\d{4}', text)[0]) * 10000
    year, latest = 0, 0
    for explicit, month, day in re.findall(r'(?:(\d{4})\s*\.\s*)?(\d{1,2})\s*\.\s*(\d{1,2})\.?', text):
        year = int(explicit) if explicit else year
        if year:
            try:
                latest = max(latest, int(date(year, int(month), int(day)).strftime('%Y%m%d')))
            except ValueError:
                continue
    return latest


def lecture_archive(cards):
    categories = ['전체', '기업', '공공기관', '교육기관', '연구기관', '컨퍼런스']
    buttons = []
    for category in categories:
        count = len(cards) if category == '전체' else sum(f'data-category="{category}"' in card for card in cards)
        buttons.append(f'<button type="button" class="lecture-filter{ " active" if category == "전체" else ""}" data-lecture-category="{category}" aria-pressed="{str(category == "전체").lower()}" aria-controls="lecture-list">{category} <span>{count}</span></button>')
    return '<section id="lectures" class="knowledge-addition"><div class="container"><h2 class="section-title">Lectures</h2><p class="section-description">강의·출강 이력 전체 · 최신 강의순</p><div class="archive-controls"><label for="archive-search">강연 제목·기관·연도 검색</label><input type="search" id="archive-search" placeholder="기관명 또는 주제 검색"></div><nav class="lecture-category-nav" aria-label="강의 기관 분류">' + ''.join(buttons) + f'</nav><p id="archive-count" role="status" aria-live="polite">전체 {len(cards)}건 · 최신 강의순</p><div id="lecture-list" class="portfolio-grid">' + ''.join(cards) + '</div><p id="lecture-empty" hidden>일치하는 강연이 없습니다. 검색어나 기관 분류를 바꿔 보세요.</p></div></section>'


def research_archive(sections):
    navigation = '<nav class="research-category-nav container" aria-label="R&D 분류">' + ''.join(f'<a href="#{key}">{label} <span>{len(sections[key])}</span></a>' for key, label in [('papers','논문·연구'),('patents','특허·실용신안'),('websites','개발 프로젝트')]) + '</nav>'
    return '<section id="research" class="knowledge-addition"><div class="container"><h2 class="section-title">R&amp;D</h2><p class="section-description">논문·특허·개발 프로젝트 전체</p></div>' + navigation + ''.join(portfolio_section(k,h,sections[k]) for k,h in [('papers','논문·연구'),('patents','특허·실용신안'),('websites','개발 프로젝트')]) + '</section>'


def app_card(app, index):
    app_id, name = escape(app['id']), escape(app['name'])
    category = escape(app['category'])
    url = escape(app.get('url', 'https://nanalab.kr/' + app['id'] + '/'), quote=True)
    symbol = escape(app['symbol'])
    image = f'<img src="/apps/img/{escape(app["image"])}" alt="" loading="lazy" width="480" height="300">' if app.get('image') else ''
    if app.get('image_url'):
        image = f'<img src="{escape(app["image_url"], quote=True)}" alt="" loading="lazy" width="480" height="300">'
    action = '템플릿 보기' if app.get('kind') == 'template' else '앱 열기'
    return f'''<article class="directory-card" data-category="{category}" data-name="{name}" data-app-id="{app_id}">
      <a class="card-visual tone-{index % 5}" href="{url}" target="_blank" rel="noopener noreferrer" tabindex="-1" aria-hidden="true"><span class="visual-symbol">{symbol}</span>{image}</a>
      <div class="card-copy"><span class="card-category">{category}</span><h3><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h3><p>{escape(app['description'])}</p>
      <div class="card-bottom"><span>{'개발 템플릿' if app.get('kind') == 'template' else 'Web app'}</span><a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="{name} {action}">{action} <span aria-hidden="true">↗</span></a></div></div></article>'''


def directory(apps):
    categories = list(dict.fromkeys(app['category'] for app in apps))
    filters = '<button type="button" class="filter-chip active" data-filter="all" aria-pressed="true">전체 <span>' + str(len(apps)) + '</span></button>'
    filters += ''.join(f'<button type="button" class="filter-chip" data-filter="{escape(c)}" aria-pressed="false">{escape(c)}</button>' for c in categories)
    return f'''<section id="apps" class="directory-section container" aria-labelledby="apps-heading">
      <div class="section-top"><div><p class="eyebrow">THE APP COLLECTION</p><h2 id="apps-heading">어떤 일이든, 더 가볍게.</h2><p>작업에 꼭 맞는 작은 도구를 찾아보세요.</p></div><p class="collection-total"><strong>{len(apps):02d}</strong> apps &amp; tools</p></div>
      <div class="directory-controls"><label class="search-box"><span aria-hidden="true">⌕</span><span class="sr-only">앱 이름 또는 기능 검색</span><input id="app-search" type="search" placeholder="어떤 도구를 찾으세요?" autocomplete="off"><kbd aria-hidden="true">/</kbd></label><div class="filter-list" aria-label="앱 분류">{filters}</div></div>
      <p id="result-count" class="result-count" role="status" aria-live="polite">전체 {len(apps)}개</p><div class="directory-grid">{''.join(app_card(a, i) for i, a in enumerate(apps))}</div>
      <div id="empty-results" class="empty-results" hidden><h3>일치하는 도구가 없습니다.</h3><p>다른 검색어를 입력하거나 분류를 바꿔 보세요.</p><button type="button" id="reset-filters" class="text-link">전체 도구 보기</button></div></section>'''


def portfolio_section(key, heading, cards, preview=False):
    route = 'lectures' if key == 'lectures' else 'research'
    visible = cards[:3] if preview else cards
    label = '강연' if key == 'lectures' else {'papers':'논문', 'patents':'특허', 'codes':'오픈소스', 'websites':'프로젝트'}[key]
    more = f'<a class="text-link" href="/{route}/">{label} 전체 {len(cards)}건 보기 <span aria-hidden="true">↗</span></a>' if preview else f'<span class="section-count">{len(cards)}건</span>'
    return f'<section id="{key}" class="portfolio-section container"><div class="section-top"><div><p class="eyebrow">{key.upper()}</p><h2>{heading}</h2></div>{more}</div><div class="portfolio-grid">{"".join(visible)}</div></section>'


def build():
    apps = json.loads(read('content/apps.json'))
    apps = sorted(apps, key=lambda app: datetime.fromisoformat(app['published_at'].replace('Z', '+00:00')), reverse=True)
    assert len({a['id'] for a in apps}) == len(apps)
    shell = read('content/home-shell.html')
    sections = {key: imported(key) for key in ['lectures','papers','patents','websites']}
    assert all(sections.values())
    shell = shell.replace('</head>', '<link rel="stylesheet" href="/additions.css">\n</head>')
    shell = shell.replace('src="script.js"', 'src="/script.js?v=archives-20261024"')
    shell = shell.replace('href="/additions.css"', 'href="/additions.css?v=app-list-20261024"')
    shell = shell.replace('<a href="#apps">Recent</a>', '<a href="#apps">Apps</a>')
    shell = shell.replace('<a href="https://nanalab.kr/apps">APPs</a>', '<a href="#lectures">Lectures</a><a href="#research">Research</a>')
    app_section = directory(apps).replace('class="directory-section container"', 'class="app-section catalog-addition container"')
    app_section = app_section.replace('어떤 일이든, 더 가볍게.', 'NaNa Apps').replace('THE APP COLLECTION', 'APPS').replace('작업에 꼭 맞는 작은 도구를 찾아보세요.', '최신 앱부터 만나보세요. 작업에 꼭 맞는 도구를 찾아보세요.')
    # Only replace the old RSS section; the existing page sections and order stay intact.
    shell = re.sub(r'<section id="apps".*?</section>', lambda _: app_section, shell, flags=re.S)
    previews = lecture_archive(sections['lectures']) + research_archive(sections)
    shell = shell.replace('<section id="contact"', previews + '\n<section id="contact"', 1)
    shell = shell.replace('저서 31건','저서 36건').replace('특허출원 34건','특허·실용신안 출원 34건').replace('논문 15건 (SCI 포함)',f'논문·연구 {len(sections["papers"])}건 (프리프린트 포함)')
    head, rest = shell.split('</head>',1)
    prefix, main = rest.split('<main>',1)
    _, suffix = main.split('</main>',1)
    # The archive routes use the original header, logo, typography and footer.
    head = head.replace('href="style.css"','href="/style.css"').replace('href="favicon.ico/','href="/favicon.ico/')
    prefix = prefix.replace('src="logo.png"','src="/logo.png"').replace('href="#','href="/#')
    suffix = suffix.replace('src="script.js"','src="/script.js"')
    def subpage(content, title, route):
        page_head = re.sub(r'<title>.*?</title>',f'<title>{title} | NaNa Lab</title>',head)
        page_head = re.sub(r'<meta property="og:title"[^>]*>',f'<meta property="og:title" content="{title} | NaNa Lab">',page_head)
        page_head = re.sub(r'<meta property="og:url"[^>]*>',f'<meta property="og:url" content="https://nanalab.kr/{route}/">',page_head)
        return page_head + f'<link rel="canonical" href="https://nanalab.kr/{route}/"></head>' + prefix + '<main>' + content + '</main>' + suffix
    def intro(title, text):
        return f'<section class="page-hero"><div class="container"><h1 class="page-title">{title}</h1><p class="page-subtitle">{text}</p></div></section>'
    source_note = '<p class="container source-note">출처: <a href="https://bhban.kr" target="_blank" rel="noopener noreferrer">반병현 공식 홈페이지 bhban.kr</a> · 원본 섹션의 정적 스냅샷이며, 원문 자료는 출처 사이트로 연결됩니다.</p>'
    controls = '<div class="container archive-controls"><label for="archive-search">강연 제목·기관·연도 검색</label><input type="search" id="archive-search" placeholder="기관명 또는 주제 검색"><p id="archive-count" role="status" aria-live="polite"></p></div>'
    outputs = {'index.html':shell}
    outputs['apps/index.html'] = subpage(intro('NaNa Apps','필요한 웹앱과 도구를 한곳에서 만나보세요.') + app_section,'Apps','apps')
    outputs['lectures/index.html'] = subpage(intro('Lectures','강의·출강 이력') + lecture_archive(sections['lectures']) + source_note,'Lectures','lectures')
    outputs['research/index.html'] = subpage(intro('R&D','논문·특허·개발 프로젝트') + research_archive(sections) + source_note,'Research','research')
    for route, key, label in [('papers','papers','논문·연구'), ('patents','patents','특허·실용신안'), ('projects','websites','개발 프로젝트')]:
        outputs[f'{route}/index.html'] = subpage(intro(label, 'R&D') + '<nav class="research-category-nav container"><a href="/papers/">논문·연구</a><a href="/patents/">특허·실용신안</a><a href="/projects/">개발 프로젝트</a></nav>' + portfolio_section(key,label,sections[key]) + source_note,label,route)
    # Preserve every original sitemap URL and its existing metadata.
    sitemap = read('content/sitemap-base.xml')
    additions = ['/lectures/','/research/','/papers/','/patents/','/projects/'] + ['/' + a['id'] + '/' for a in apps if a.get('kind') != 'template' and not a.get('external')]
    for route in additions:
        url = 'https://nanalab.kr' + route
        if f'<loc>{url}</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>',f'  <url><loc>{url}</loc><lastmod>2026-10-24</lastmod></url>\n</urlset>')
    outputs['sitemap.xml'] = sitemap
    return outputs, {'apps':len(apps), **{k:len(v) for k,v in sections.items()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs, counts = build()
    stale = []
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    if stale:
        raise SystemExit('Stale outputs: ' + ', '.join(stale))
    print(json.dumps({'status':'checked' if args.check else 'built', **counts}, ensure_ascii=False))
