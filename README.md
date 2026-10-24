# NaNa Lab 웹앱 디렉터리

나나랩의 웹앱과 도구를 검색하고 바로 열 수 있는 정적 사이트입니다. GitHub Pages에서 `nanalab.kr`로 제공합니다.

## 구성

- `/`: 앱 카드 디렉터리, 강연·연구 미리보기, 대표 소개와 문의
- `/apps/`: 메인과 같은 목록을 사용하는 앱 전용 디렉터리
- `/lectures/`: 기관·제목·연도로 검색할 수 있는 전체 강연 이력
- `/research/`: 논문, 프리프린트, 특허, 개발 프로젝트

RSS와 외부 목록 API를 사용하지 않습니다. 카드와 가져온 자료는 빌드 시 HTML에 포함되어 JavaScript가 없어도 읽고 링크를 열 수 있습니다. 검색과 분류는 브라우저에서 동작합니다.

## 앱 추가

`content/apps.json`에 항목을 추가합니다. 기존 항목과 다른 `id`, `name`, `category`, `description`, `symbol`이 필요합니다.

```json
{
  "id": "new_tool",
  "name": "새 도구",
  "category": "생활·업무",
  "description": "이 도구로 할 수 있는 일을 간단하게 설명합니다.",
  "symbol": "+"
}
```

기본 링크는 `https://nanalab.kr/<id>/`입니다. 다른 주소는 `url`로 지정합니다. `image`는 `apps/img/` 안의 파일 이름이며 생략할 수 있습니다. 실행 가능한 웹앱 대신 개발 템플릿이면 `kind`를 `template`으로 지정하고 저장소 URL을 넣습니다. 분류 버튼, 개수, 메인과 `/apps/` 카드가 함께 생성됩니다.

현재 목록은 작업 공간의 앱 저장소를 기준으로 합니다. 사이트 자체, `src_cdn`, `rebirth_country`, 숨김 도구 폴더는 제외합니다. 앱 추가·제외 후 목록 검증도 같은 기준을 사용합니다.

## 빌드와 확인

### 앱 업데이트 큐

상위 작업 폴더에 `updateque.md`가 있으면 앱 추가·수정 전에 최신 내용을 확인합니다. 큐에 적힌 저장소의 실제 기능, 실행 주소, 이미지 자료를 확인한 뒤 `content/apps.json`에 반영합니다. 기존 항목은 ID와 URL로 중복을 확인하며, 큐 원문은 보존합니다. 반영 후 아래 검증을 실행합니다. 큐 파일을 읽는 작업 지침과 별개로, 주기적인 자동 확인은 예약 작업이 설정되어 있을 때만 실행됩니다.

Python 3와 Node.js가 필요합니다. 별도 Python 패키지는 필요하지 않습니다.

```text
python scripts/build_site.py
python scripts/build_site.py --check
python scripts/check_site.py
node --check script.js
node scripts/check_interactions.cjs
```

`check_site.py`는 작업 공간의 저장소와 앱 목록 일치, 로컬 리소스, 중복 ID, 앵커, 생성 결과, RSS 제거와 사이트맵을 검증합니다. 상위 폴더에 앱 저장소들이 함께 있어야 목록 검증이 가능합니다. `check_interactions.cjs`는 검색·분류·초기화 이벤트를 DOM 모형에서 확인합니다. 실제 브라우저의 시각 검증과 구별해야 합니다.

생성된 `index.html`, `apps/index.html`, `lectures/index.html`, `research/index.html`, `sitemap.xml`은 직접 고치지 않습니다. 앱은 `content/apps.json`, 메인 기본 섹션은 `content/home-shell.html`, 디자인은 `directory.css`에서 수정합니다. 기존 문의 전송 설정은 유지합니다.

## 강연·연구 자료 갱신

출처는 [반병현 공식 홈페이지](https://bhban.kr)와 [원본 저장소](https://github.com/needleworm/needleworm.github.io)입니다. `content/portfolio/`에 원본 섹션 스냅샷을 보관하고 커밋과 가져온 날짜를 `provenance.json`에 기록합니다. 원문의 상대 이미지·PDF 링크는 빌드 과정에서 `https://bhban.kr/` 주소로 변환합니다. 논문 출판 상태와 프리프린트 표기를 유지합니다.

원본 저장소를 최신으로 준비한 뒤 실행합니다.

```text
python scripts/sync_portfolio.py <원본-저장소-경로>
python scripts/build_site.py
python scripts/check_site.py
```

홈의 강연·논문 미리보기는 각 스냅샷의 앞쪽 자료를 보여줍니다. 대표 소개의 논문 수는 프리프린트를 포함한 가져온 논문 카드 수로 계산합니다. 저서·특허 등 소개 문구는 원본과 대조하여 별도로 갱신합니다. 동기화는 명시적으로 실행하며 방문 때 원격 데이터를 가져오지 않습니다.

## 미리보기

```text
python -m http.server 4180 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:4180/`을 엽니다. 루트 기준 리소스 경로를 사용하므로 파일을 직접 여는 방식 대신 HTTP 서버를 사용합니다.
