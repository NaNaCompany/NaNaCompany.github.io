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

원래 디자인과 히어로 영상, Services·About·Customers·Process·Contact 섹션을 유지합니다. RSS 영역만 앱 카드 격자로 교체하고 Lectures·Research 섹션을 추가했습니다. 새로운 스타일은 `additions.css`의 추가 섹션에만 적용합니다.

- 앱 원본: `content/apps.json` — 항목 추가 후 빌드하면 메인과 `/apps/`에 함께 반영됩니다. 이미지가 없으면 `symbol`을 표시합니다. 외부 썸네일은 `image_url`로 지정합니다.
- 메인 원본: `content/home-shell.html` — 원래 홈페이지를 보존한 템플릿입니다.
- 강연·연구: `content/portfolio/` — bhban.kr의 원본 섹션 스냅샷과 출처 커밋을 저장합니다. `/lectures/`와 `/research/`에 전체 자료를 생성합니다.
- 업데이트 큐: 사용자 요청이 있을 때 상위 작업 폴더의 `updateque.md`를 읽습니다. 자동 감시하지 않습니다. 실제 저장소와 실행 주소를 확인하고 중복 없이 추가합니다. 큐 원문은 보존합니다.
- 사이트맵: `content/sitemap-base.xml`의 기존 URL과 메타데이터를 유지하고 추가 경로만 넣습니다.

```text
python scripts/build_site.py
python scripts/build_site.py --check
python scripts/check_site.py
node --check script.js
node scripts/check_interactions.cjs
```

`check_site.py`는 원본 히어로·서비스·고객사·협업 과정·문의 폼의 보존, 카드 목록과 작업 폴더의 일치, 내부 링크와 이미지, 생성 결과, RSS 제거, XML을 검사합니다. 목록 검사에는 상위 작업 폴더의 앱 저장소들이 필요합니다. 이벤트 검사는 DOM 모형을 사용하므로 실제 화면 확인과 구별합니다.

원본 강연·연구 자료를 갱신하려면 `python scripts/sync_portfolio.py <원본-저장소-경로>` 후 다시 빌드합니다. 논문·프리프린트 표기와 원문 링크를 유지합니다.

강연·R&D는 메인에서도 전체 자료를 표시합니다. 강연은 원본 사이트와 같이 `lectures`와 `courses-offline`을 합쳐 ID 중복을 제거하고 최신 강의순으로 정렬합니다. 기업·공공기관·교육기관·연구기관·컨퍼런스 분류와 검색을 함께 사용할 수 있습니다. 온라인 강좌 버튼은 추가하지 않습니다. R&D의 전체 논문·특허·개발 프로젝트는 `/research/`와 각각 `/papers/`, `/patents/`, `/projects/`에서도 제공합니다.
