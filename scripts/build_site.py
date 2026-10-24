"""Build the static app directory and locally imported portfolio pages.

Usage: python scripts/build_site.py [--check]
Requires only the Python standard library. No network access during builds.
"""
from pathlib import Path
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
    # Relative resources belong to the source portfolio, not this domain.
    source = re.sub(r'\b(href|src)="([^"]+)"', lambda m: f'{m[1]}="{escape(urljoin("https://bhban.kr/", unescape(m[2])), quote=True)}"', source)
    source = re.sub(r'<a\b([^>]*)>(\s*<i\b[^>]*class="([^"]*)"[^>]*></i>\s*)</a>',
                    lambda m: '<a' + m[1] + '>' + ('PDF' if 'pdf' in m[3] else '링크 열기') + '</a>', source)
    return Cards(source).cards


def app_card(app, index):
    app_id, name = escape(app['id']), escape(app['name'])
    category = escape(app['category'])
    url = escape(app.get('url', 'https://nanalab.kr/' + app['id'] + '/'), quote=True)
    symbol = escape(app['symbol'])
    image = f'<img src="/apps/img/{escape(app["image"])}" alt="" loading="lazy" width="480" height="300">' if app.get('image') else ''
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
    assert len({a['id'] for a in apps}) == len(apps), 'Duplicate app IDs'
    shell = read('content/home-shell.html')
    head = shell[:shell.index('</head>')]
    head = re.sub(r'<title>.*?</title>', '<title>NaNa Lab — 일상을 가볍게 만드는 웹앱</title>', head)
    head = head.replace('We help your AI Experience', '문서, 이미지, AI와 일상에 필요한 웹앱을 한곳에서. 나나랩의 도구를 검색하고 바로 사용하세요.')
    head = head.replace('NaNa Lab - AI for your Business', 'NaNa Lab — 웹앱 디렉터리')
    head = head.replace('당신의 AI 활용을 도와드립니다.', '문서부터 이미지까지, 일상을 가볍게 만드는 웹앱과 도구 모음.')
    head = head.replace('href="style.css"', 'href="/style.css"')
    head = head.replace('href="favicon.ico/', 'href="/favicon.ico/')
    head += '\n<link rel="stylesheet" href="/directory.css">\n'
    nav = '''<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="directory-header"><div class="container"><a class="wordmark" href="/" aria-label="NaNa Lab 홈"><img src="/logo.png" alt="" width="40" height="40"><span>NaNa<span class="wordmark-light"> Lab</span><small>SMALL TOOLS. BIG POSSIBILITIES.</small></span></a><button type="button" class="directory-menu" aria-controls="main-nav" aria-expanded="false" aria-label="메뉴 열기">메뉴</button><nav id="main-nav" aria-label="주 메뉴"><a href="/#apps">Apps</a><a href="/lectures/">Lectures</a><a href="/research/">Research</a><a href="/#about">About</a><a class="nav-contact" href="/#contact">함께 만들기 ↗</a></nav></div></header>'''
    footer = shell[shell.index('<footer'):shell.index('<script src="script.js">')].replace('&copy; 2025', '&copy; 2026')
    footer = '<div class="container footer-top"><a class="wordmark" href="/">NaNa Lab</a><p>작은 도구로 만드는, 더 큰 가능성.</p><a href="https://github.com/NaNaCompany" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div>' + footer
    scripts = '<script src="/script.js" defer></script></body></html>'
    def page(content, title=None, path='/'):
        page_head = head
        if title:
            page_head = re.sub(r'<title>.*?</title>', f'<title>{title} | NaNa Lab</title>', page_head)
            page_head = re.sub(r'<meta\s+(?:name="description"|property="og:description")\s+content="[^"]*"\s*/?>', f'<meta name="description" content="{title}. 반병현의 강연과 연구 활동을 나나랩에서 만나보세요.">', page_head, count=1)
            page_head = re.sub(r'<meta property="og:title"[^>]*>', f'<meta property="og:title" content="{title} | NaNa Lab">', page_head)
        page_head = re.sub(r'<meta property="og:url"[^>]*>', f'<meta property="og:url" content="https://nanalab.kr{path}">', page_head)
        return page_head + f'<link rel="canonical" href="https://nanalab.kr{path}"></head><body class="directory-page">' + nav + '<main id="main">' + content + '</main>' + footer + scripts
    sections = {key: imported(key) for key in ['lectures','papers','patents','websites']}
    assert all(sections.values()), 'Missing imported cards'
    hero = f'''<section class="directory-hero container"><div class="hero-main"><p class="eyebrow"><span class="status-dot"></span> MADE BY NANA LAB</p><h1>작은 도구,<br>무한한 <span>가능성.</span></h1><p class="hero-lead">복잡한 일은 간단하게. 번거로운 일은 가볍게.<br>지금 필요한 웹앱을 찾아, 바로 시작하세요.</p><a class="hero-cta" href="#apps">나에게 맞는 도구 찾기 <span aria-hidden="true">↘</span></a></div><div class="hero-art" aria-hidden="true"><span class="art-note">YOUR EVERYDAY TOOLKIT</span><div class="art-tile tile-one">Aa<span>TEXT</span></div><div class="art-tile tile-two">✳<span>CREATE</span></div><div class="art-tile tile-three">▦<span>CONNECT</span></div><div class="art-tile tile-four">±<span>CALCULATE</span></div><span class="art-caption">Less friction. More possibilities.</span></div></section>'''
    strip = '<div class="collection-strip"><div class="container"><span>하나의 공간, 다양한 도구.</span><span>문서와 텍스트</span><span>이미지와 미디어</span><span>생활과 업무</span><span>AI와 개발</span></div></div>'
    previews = '<div class="knowledge-band"><div class="container knowledge-intro"><p class="eyebrow">BEYOND THE TOOLS</p><h2>만드는 경험을, 나누는 지식으로.</h2><p>나나랩 대표 반병현의 강연과 연구를 만나보세요.</p></div>' + portfolio_section('lectures', '현장에서 만나는 AI', sections['lectures'], True) + portfolio_section('papers', '질문에서 시작되는 연구', sections['papers'], True) + '</div>'
    about = re.search(r'<section id="about".*?</section>', shell, re.S)[0]
    source_points = re.search(r'<ul class="about-points">.*?</ul>', read('content/portfolio/about.html'), re.S)[0]
    source_points = re.sub(r'논문\s*\d+건\s*\(SCI 포함\)', f'논문·연구 {len(sections["papers"])}건 (프리프린트 포함)', source_points)
    about = re.sub(r'<ul class="about-points">.*?</ul>', lambda _: source_points, about, flags=re.S)
    about = about.replace('src="profile.png"', 'src="/profile.png"')
    services = re.search(r'<section id="services".*?</section>', shell, re.S)[0]
    contact = re.search(r'<section id="contact".*?</section>', shell, re.S)[0].replace('src="email-sender.js"', 'src="/email-sender.js"')
    contact = contact.replace('form-group form-reveal', 'form-group')
    contact = re.sub(r'<div class="custom-select-wrapper">.*?<input type="hidden"[^>]*>\s*</div>', '<label class="sr-only" for="country_code">국가 번호</label><select id="country_code" name="country_code" aria-label="국가 번호"><option value="+82">KR (+82)</option><option value="+1">US (+1)</option><option value="+81">JP (+81)</option><option value="+86">CN (+86)</option><option value="">기타</option></select>', contact, flags=re.S)
    # The new directory retains the existing business contact flow.
    home = hero + strip + directory(apps) + previews + about + '<details class="services-details container"><summary>나나랩과 함께할 수 있는 일</summary>' + services + '</details>' + contact
    outputs = {'index.html':page(home), 'apps/index.html':page('<section class="subpage-hero container"><p class="eyebrow">NANA LAB / APPS</p><h1>필요한 도구를, 한곳에서.</h1><p>검색하고, 골라서, 바로 사용하세요.</p></section>' + directory(apps), path='/apps/')}
    intro = lambda label, desc: f'<section class="subpage-hero container"><p class="eyebrow">NANA LAB / KNOWLEDGE</p><h1>{label}</h1><p>{desc}</p><a class="text-link" href="/#contact">강연·연구 협업 문의 ↗</a></section>'
    source_note = '<p class="source-note container">출처: <a href="https://bhban.kr" target="_blank" rel="noopener noreferrer">반병현 공식 홈페이지 bhban.kr</a> · 원본 자료를 가져온 정적 스냅샷입니다. 논문 원문과 관련 자료는 출처 사이트로 연결됩니다.</p>'
    lecture_controls = '<div class="container archive-controls"><label for="archive-search">강연 제목·기관 검색</label><input type="search" id="archive-search" placeholder="기관명, 주제, 연도 검색"><p id="archive-count" role="status" aria-live="polite"></p></div>'
    outputs['lectures/index.html'] = page(intro('강연과 교육', '기업·공공기관·교육 현장에서 나눈 AI와 업무 자동화 이야기.') + lecture_controls + portfolio_section('lectures','강의·출강 이력', sections['lectures']) + source_note, '강연과 교육', '/lectures/')
    research_nav = '<nav class="container research-nav" aria-label="연구 분류"><a href="#papers">논문</a><a href="#patents">특허</a><a href="#websites">프로젝트</a></nav>'
    outputs['research/index.html'] = page(intro('연구와 개발', 'AI, 데이터, 기술을 탐구하며 쌓아 온 논문과 특허, 공개 프로젝트.') + research_nav + ''.join(portfolio_section(k,h,sections[k]) for k,h in [('papers','논문·연구'),('patents','특허·실용신안'),('websites','개발 프로젝트')]) + source_note, '연구와 개발', '/research/')
    outputs['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://nanalab.kr{p}</loc></url>' for p in ['/','/apps/','/lectures/','/research/'] + ['/' + a['id'] + '/' for a in apps if a.get('kind') != 'template']) + '</urlset>\n'
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
