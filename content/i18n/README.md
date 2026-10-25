# Static directory translations

Korean remains the default at `/`. The eight additional languages are English
(`/en/`), Japanese (`/ja/`), Simplified Chinese (`/zh/`), Spanish (`/es/`), German
(`/de/`), French (`/fr/`), Portuguese (`/pt/`) and Russian (`/ru/`). Each language
has a homepage and apps, lectures, research, papers, patents, projects and feeds
pages. No visitor is automatically redirected away from Korean.

Each language JSON contains translated interface text, page metadata, count
formats and app names/descriptions keyed by the stable app ID. Add translated
app copy in all eight catalogs whenever `content/apps.json` changes. The build
fails if an app translation is absent. Do not copy generated HTML into these
sources. Builds do not require a network, a translation service or sibling apps.

The language menu links to the same route in each language. JavaScript preserves
the current section/record fragment when switching. Ordinary HTML links work
without JavaScript. Every page has its own canonical and a reciprocal nine-language
`hreflang` set; `x-default` points to the corresponding Korean page. All 72 page
URLs belong to `sitemap-main.xml`, referenced by the unchanged root sitemap index.

Business copy, directory copy, app names/descriptions, navigation, filters,
search states, contact labels and feed documentation are translated. Original
lecture and research titles, institution names, dates, publication/preprint
labels and document links are preserved as source records. The localized pages
explain this. Their record identifiers and anchors match the Korean archives.
RSS/JSON Feed and public JSON retain the Korean catalog and stable identities.

App cards use the matching app language only when verified in the app's
`languages` list. Otherwise they retain the original launch URL; no speculative
app language paths are generated. Korean cards remain one per app, newest first.

## Sources and attribution

NaNa Lab authored the directory translations. Engineering app names and purpose
summaries in English, Japanese, Chinese, Spanish and German were adapted from
NaNaCompany's own `localization/<language>.json`. The checked-in `sources.json`
records source repositories, commits, source paths and license links. French,
Portuguese and Russian engineering copy was newly translated for this directory;
formulas are preserved. Original app preview images remain hosted by their apps.

Engineering locale source license: MIT. Copyright (c) 2026 NaNaCompany.
Changes: shortened the source purpose into directory descriptions and added
translations for the additional directory languages.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Verification

Run the existing site, sitemap, syndication and interaction checks, plus
`python scripts/check_localization.py`. This verifies translated app coverage,
language routes, reciprocal alternates, canonical URLs, matching archive identities,
local assets, category controls, language navigation and sitemap coverage.
