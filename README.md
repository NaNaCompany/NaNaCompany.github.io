# NaNa Lab

**AI for Every Business**

이 저장소는 [NaNa Lab 공식 웹사이트📍nanalab.kr](https://nanalab.kr/?utm_source=chatgpt.com) 의 호스팅을 위한 레포지토리입니다.

---

## 🌐 소개

**NaNa Lab**은 (주)나나컴퍼니가 운영하는 AI 및 기술 컨설팅 전문 서비스입니다.
기업과 공공기관이 AI 기반 성과를 달성할 수 있도록 사업 기획, R&D 과제 협력, PoC 수행, 기술 자문 등 다양한 서비스를 제공합니다. :contentReference[oaicite:1]{index=1}

---

## 🚀 주요 서비스

- **R&D 과제 협력** – 과제 수행 및 지표 달성, 특허출원 지원 :contentReference[oaicite:2]{index=2}
- **AI 기술 자문 & 사업 기획** – AI 도입 관련 전략 자문 :contentReference[oaicite:3]{index=3}
- **PoC (Proof of Concept) 수행** – 아이디어 검증 중심의 프로젝트 수행 :contentReference[oaicite:4]{index=4}
- **AI 시제품 개발** – 업무 효율화를 위한 AI 시제품 구현 :contentReference[oaicite:5]{index=5}
- **평가 보고서 작성** – 사업계획서 타당성 검토 및 의견 보고서 작성 :contentReference[oaicite:6]{index=6}
- **교육 서비스** – 생성형 AI 활용 교육 제공 :contentReference[oaicite:7]{index=7}

---

## 👤 대표

**반병현** – AI 엔지니어 및 Co-founder
- 상상텃밭(주) 前 CTO
- 다수 저서 및 특허 보유
- KAIST 바이오 및 뇌공학과 학사/석사 조기졸업 :contentReference[oaicite:8]{index=8}

---

## 🤝 협업/자문/교육 사례

공공기관, 기업, 교육기관 등 다양한 고객과 협업한 이력이 있으며,
실제 사례로는 **KOTRA, LG 그룹, 삼성전자, 교육청, 대학교**, 그리고 여러 공공기관 등을 포함하고 있습니다. :contentReference[oaicite:9]{index=9}

---

## 📌 웹사이트

🔗 https://nanalab.kr/ — NaNa Lab 공식 홈페이지 :contentReference[oaicite:10]{index=10}

---

## 📄 라이선스

이 저장소의 수정을 불허합니다.




## 사이트 유지보수

앱 카드는 모든 화면에서 1컬럼으로 표시합니다. `content/apps.json`의 `published_at`에는 시간대가 포함된 ISO 8601 시각을 기록합니다. 저장소 앱은 GitHub 저장소 생성일(`date_source: github_repository_created_at`), 외부 앱은 최초 디렉터리 등록 시각(`date_source: directory_registration`)을 사용하며 최신순으로 자동 정렬됩니다. 유지보수 커밋은 노출 순서를 바꾸지 않습니다.

원래 디자인과 히어로 영상, Services·About·Customers·Process·Contact 섹션을 유지합니다. RSS 영역만 앱 카드 격자로 교체하고 Lectures·Research 섹션을 추가했습니다. 새로운 스타일은 `additions.css`의 추가 섹션에만 적용합니다.

- 앱 원본: `content/apps.json` — 항목 추가 후 빌드하면 메인과 `/apps/`에 함께 반영됩니다. 이미지가 없으면 `symbol`을 표시합니다. 외부 썸네일은 `image_url`로 지정합니다.
- 메인 원본: `content/home-shell.html` — 원래 홈페이지를 보존한 템플릿입니다.
- 강연·연구: `content/portfolio/` — bhban.kr의 원본 섹션 스냅샷과 출처 커밋을 저장합니다. `/lectures/`와 `/research/`에 전체 자료를 생성합니다.
- 업데이트 큐: 사용자 요청이 있을 때 상위 작업 폴더의 `updateque.md`를 읽습니다. 자동 감시하지 않습니다. 실제 저장소와 실행 주소를 확인하고 중복 없이 추가합니다. 큐 원문은 보존합니다.
- 사이트맵: 제출 주소 `/sitemap.xml`은 `/sitemap-main.xml`과 각 앱의 세부 사이트맵을 연결하는 `sitemapindex`입니다. `/sitemap-main.xml`에는 메인에서 클릭 가능한 같은 도메인의 URL과 모든 내부 앱 대표 URL을 담고, 기존 URL과 메타데이터를 보존합니다. 각 하위 파일은 페이지 목록인 `urlset`이며, 색인끼리 중첩하지 않습니다. 루트 `/robots.txt`의 `Sitemap:` 항목에도 색인과 모든 하위 사이트맵을 알립니다. `content/sitemap-base.xml`은 메인 URL 목록의 원본, `content/sitemap-sources.json`은 앱별 사이트맵 연결 원본입니다.
- 대표 주소: 디렉터리 페이지는 `https://nanalab.kr/경로/`로 통일합니다. `scripts/site_urls.py`는 렌더링된 내부 링크와 공개 데이터의 링크에 같은 규칙을 적용하며, 기존 강의·연구 레코드 ID와 구독 피드 ID는 유지합니다. 사이트맵의 슬래시 중복은 최신 확인된 수정일과 메타데이터를 합쳐 한 건만 남깁니다. 2026-10-25 실응답 확인에서 404였던 루트 `/service`, `/privacy`는 제거했으며, 실제 페이지 `/invest/service/`, `/invest/privacy/`는 유지합니다.

```text
python scripts/build_site.py
python scripts/build_site.py --check
python scripts/check_site.py
python scripts/check_sitemaps.py
python scripts/check_syndication.py
node --check script.js
node scripts/check_interactions.cjs
```

`check_site.py`는 원본 히어로·서비스·고객사·협업 과정·문의 폼의 보존, 카드 목록과 작업 폴더의 일치, 내부 링크와 이미지, 생성 결과, RSS 제거, XML을 검사합니다. 목록 검사에는 상위 작업 폴더의 앱 저장소들이 필요합니다. 이벤트 검사는 DOM 모형을 사용하므로 실제 화면 확인과 구별합니다.

원본 강연·연구 자료를 갱신하려면 `python scripts/sync_portfolio.py <원본-저장소-경로>` 후 다시 빌드합니다. 논문·프리프린트 표기와 원문 링크를 유지합니다.

앱을 추가·갱신할 때 `python scripts/sync_sitemaps.py`로 각 저장소의 공개용 `sitemap.xml`을 찾아 연결 원본을 갱신한 뒤 빌드합니다. 외부 사이트와 개발 템플릿은 제외합니다. 이미 연결한 저장소가 로컬에 없더라도 연결은 보존합니다. 일반 빌드는 저장된 원본만 읽으므로 네트워크 없이 재현할 수 있습니다. 앱의 세부 페이지가 늘어나면 앱 자체 사이트맵을 갱신합니다. 루트 `robots.txt`는 `content/robots-base.txt`의 정책·소유권 확인 정보를 보존하고 색인과 메인·앱 사이트맵 주소를 자동 추가합니다. 출처 파일의 실제 수정일을 알 수 없는 URL에는 가짜 `lastmod`를 넣지 않습니다.

한 서비스가 여러 저장소로 분리된 경우 `content/repository-groups.json`에서 대표 앱과 하위 저장소를 연결합니다. 앱 카드는 대표 1개를 유지합니다. 실제 Pages 배포 커밋·공개 언어 페이지·사이트맵을 확인한 하위 저장소만 `published`로 기록하고, 메인 페이지 목록과 루트 sitemapindex·robots에 연결합니다. 준비 중인 `preparing` 저장소에는 주소를 등록하지 않습니다. 세계 법령 자료실의 한국 법률(`world-law-kr-acts`)과 명령·규칙(`world-law-kr-orders`)은 공개 지도에 연결하며, 독일 저장소(`world-law-de`)는 준비 상태입니다. `python scripts/check_repository_groups.py`가 중복 카드·잘못된 연결·미공개 주소 등록을 검사합니다.

개별 사이트맵이 없는 앱은 공개 HTML 페이지를 확인해 `/sitemap-details.xml`에 보완하고 루트 색인과 `robots.txt`에서 알립니다. 메인 목록에 이미 있는 URL, 개발 소스·테스트·템플릿과 `noindex` 페이지는 보완 목록에서 제외합니다. 전용 사이트맵이 있는 앱은 해당 파일을 직접 연결합니다. Astra는 `/astra/sitemap.xml`에서 공개 페이지 전체를 관리합니다.

배포 후 `python scripts/check_sitemaps.py --live`는 루트 색인·메인 목록·robots.txt의 배포 최신 상태와 모든 앱 XML의 HTTP 응답·구조·중복·동일 도메인·기존 URL·메타데이터 보존·발견 경로를 확인하고, 중복을 제외한 전체 URL 수를 출력합니다. Search Console 제출 주소는 `https://nanalab.kr/sitemap.xml`이며, 이 색인 하나에서 메인 목록과 모든 앱의 하위 사이트맵으로 연결됩니다. 색인과 하위 사이트맵을 읽는 시점은 다를 수 있으며, 발견된 페이지 수는 실제 검색 색인 완료 수와 다릅니다. 하위 경로의 robots.txt와 별개로 같은 호스트 전체에 실제 적용되는 정책은 루트 `/robots.txt`입니다. 구성 기준은 [Google의 사이트맵 색인 안내](https://developers.google.com/search/docs/crawling-indexing/sitemaps/large-sitemaps)를 따릅니다.

## 구독 피드와 공개 JSON

사이트 빌드에서 RSS 2.0, JSON Feed 1.1, 조회용 JSON을 함께 생성합니다. 별도 백엔드·인증 키·번역 API가 필요하지 않습니다. 사용 안내는 [구독·데이터](https://nanalab.kr/feeds/)에서 확인할 수 있습니다.

| 용도 | RSS | JSON Feed |
|---|---|---|
| 앱·강의·연구 통합, 최근 200건 | `/feed.xml` | `/feed.json` |
| 앱, 최근 100건 | `/feeds/apps.xml` | `/feeds/apps.json` |
| 강의, 최근 100건 | `/feeds/lectures.xml` | `/feeds/lectures.json` |
| 논문·특허·프로젝트, 최근 100건 | `/feeds/research.xml` | `/feeds/research.json` |

전체 목록은 `/api/apps.json`, `/api/lectures.json`, `/api/papers.json`, `/api/patents.json`, `/api/projects.json`에서 제공합니다. `/api/research.json`은 논문·특허·프로젝트 통합 목록이며, `/api/index.json`은 엔드포인트·개수·스키마 버전을 안내합니다. 모든 주소는 `https://nanalab.kr` 기준입니다. 응답은 `schema_version`, `type`, `count`, `items`, `source`로 구성됩니다. `items`에 안정적인 `id`, 제목, 요약, 이동 주소, 원본 출처, 확인 가능한 날짜·분류·기관·논문 유형·인용·원문 링크를 담습니다. 로컬 경로는 공개하지 않습니다.

통합 피드는 날짜 기준 최신순이며, 전체 목록은 API에서 조회합니다. 앱은 `published_at`을 사용합니다. 강의 일정·특허 출원일처럼 일자만 확인되면 한국 시간 00:00으로 표현하고 `date_precision: day`로 표시합니다. 연도만 확인되는 자료에는 `year`만 제공하고 정확한 게시 시각을 만들지 않습니다. 날짜가 없는 프로젝트는 뒤로 정렬합니다. 기존 원본 ID를 우선 사용하며, ID가 없는 과거 기록은 원본의 식별용 주석을 사용하므로 목록 순서를 바꿔도 ID가 유지됩니다. 수정 시각을 빌드 시각으로 덮어쓰지 않습니다.

강의·연구 API의 `source`에는 bhban.kr과 가져온 원본 저장소·커밋을 기록합니다. 공개 목록 제공은 원문 논문·이미지·문서의 이용 조건을 변경하지 않습니다. 저서·언론보도는 현재 원본 목록에 없어 제공하지 않습니다.

피드 자동 발견용 `<link rel="alternate">`와 작은 하단 구독 링크를 생성합니다. GitHub Pages가 JSON Feed에 `application/json`을 사용해도 JSON Feed 1.1에서 허용하는 응답입니다. 파일 변경과 HTTP 캐시는 호스팅 서버가 관리합니다.

```javascript
const response = await fetch('https://nanalab.kr/api/lectures.json');
const { items } = await response.json();
const corporateLectures = items.filter(item => item.category === '기업');
```

`python scripts/build_site.py` 후 `python scripts/check_syndication.py`를 실행하면 생성 최신성, RSS/JSON Feed 일치, XML 이스케이프, 안정적인 ID, 날짜 정밀도, 출처, 실제 항목 앵커를 검사합니다. 규격 참고: [RSS 2.0](https://www.rssboard.org/rss-specification), [JSON Feed 1.1](https://www.jsonfeed.org/version/1.1/).

강연·R&D는 메인에서도 전체 자료를 표시합니다. 강연은 원본 사이트와 같이 `lectures`와 `courses-offline`을 합쳐 ID 중복을 제거하고 최신 강의순으로 정렬합니다. 기업·공공기관·교육기관·연구기관·컨퍼런스 분류와 검색을 함께 사용할 수 있습니다. 온라인 강좌 버튼은 추가하지 않습니다. R&D의 전체 논문·특허·개발 프로젝트는 `/research/`와 각각 `/papers/`, `/patents/`, `/projects/`에서도 제공합니다.

## 디렉터리 다국어

한국어 메인(`/`)과 영어·일본어·중국어 간체·스페인어·독일어·프랑스어·포르투갈어·러시아어 서브 페이지를 제공합니다. 각 언어에서 홈·앱·강의·연구·논문·특허·프로젝트·구독 안내를 볼 수 있습니다. 최하단 푸터의 언어 메뉴는 같은 경로와 유효한 섹션 앵커를 유지합니다. 한국어 기본 경로로 접속하면 직접 저장한 선택, IP 국가, 브라우저 언어, 영어 순으로 언어를 정합니다. `/en/`처럼 언어가 지정된 주소는 자동 변경하지 않습니다. 앱 카드의 이름·설명과 공통 UI를 번역하고, 원문 강의·논문 제목 및 기관명·날짜·자료 링크는 보존합니다. RSS와 공개 JSON은 기존 한국어 데이터를 유지합니다.

IP 국가는 같은 도메인의 Cloudflare `/cdn-cgi/trace`에서 확인하며 외부 위치 조회 서비스로 추가 전송하지 않습니다. 국가 코드만 세션에 1시간 보관하고 조회가 2.2초 내 완료되지 않으면 브라우저 언어로 처리합니다. IP 원문은 저장하지 않습니다. `node scripts/check_language_preference.cjs`로 국가별 이동, 수동 선택, 저장소 차단, 조회 실패와 시간 초과를 검사합니다.

번역 원본·출처와 유지보수 방법은 [content/i18n/README.md](content/i18n/README.md)를 확인하세요. 새 앱을 추가할 때 8개 언어의 `apps` 항목도 추가하고, 기존 검사에 더해 `python scripts/check_localization.py`를 실행하세요. 모든 언어 페이지는 고유 canonical, 상호 hreflang, 사이트맵 URL을 빌드에서 함께 생성합니다.
