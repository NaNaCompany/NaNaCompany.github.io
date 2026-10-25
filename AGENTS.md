# Site maintenance

Preserve the original NaNa Lab design, header, hero video, typography, colors, business sections, and contact form. Changes must be additive unless the user explicitly asks otherwise. The original stylesheet `style.css` must not be replaced by a new visual system. New app and knowledge section styles belong in `additions.css` and must be scoped to those sections.

Edit `content/apps.json`, `content/home-shell.html`, `additions.css`, and `script.js`; rebuild generated HTML with `python scripts/build_site.py`. The app grid replaces only the former RSS section. Keep Services, About, Customers, Process, and Contact in their original order and structure. Preserve existing sitemap URLs and metadata when appending routes.

## App update queue

Before adding or updating app cards, read `../updateque.md` if present. It is the workspace-level queue for new apps and app changes. Inspect the named repository and confirm its purpose, launch URL, and assets. Add or update records in `content/apps.json`, deduplicating by app ID and URL. Preserve the queue and do not mark work complete until generated cards pass validation. If the queue is absent, do not invent entries.

Check the queue only when requested. Do not create recurring monitoring. An explicit queue request may add apps previously excluded from the initial catalog, including `rebirth_country`.

Run `python scripts/build_site.py --check`, `python scripts/check_site.py`, `node --check script.js`, and `node scripts/check_interactions.cjs` after relevant changes. The catalog coverage check expects sibling app repositories in the parent workspace. Never overwrite unrelated local work. Commit and push only within the user's authorized scope.

Imported portfolio snapshots belong in `content/portfolio/`. Use `scripts/sync_portfolio.py` to refresh them from a verified source checkout. Preserve publication/preprint labels and original document links.

Display full Lectures and R&D archives on the homepage, not three-card previews. Match the source site's lecture cross-listing: combine `lectures` with `courses-offline`, deduplicate by record ID, sort by latest date, and retain the institution filters (기업, 공공기관, 교육기관, 연구기관, 컨퍼런스). Do not add an online-courses button or section. R&D contains all papers, patents, and projects, with their respective routes and navigation.

Keep app cards in one column at every viewport width. Order apps newest first by `published_at`: use verified GitHub repository creation timestamps for repository apps, and the first directory registration timestamp for external apps. Set `date_source` accordingly. Do not reorder based on maintenance commits. Require dates for newly added apps so later builds remain deterministic.

For language variants of one app, publish only one Korean app card. Include each verified language URL in the sitemap using the app's `languages` list; do not create duplicate `_en`, `_es`, or other language-only cards. Apps kept under the workspace's `sites/` directory may declare their workspace-relative `repository_path` for coverage checks.

When Korean is served at the app root instead of `/ko/`, set `language_paths` to `{"ko":""}`. Keep every language in `languages` and preserve verified alternate-language sitemap links. Workspace coverage applies to repositories with a NaNaCompany GitHub origin; unpublished local drafts do not create speculative app entries.

The same build generates RSS 2.0, JSON Feed 1.1 and public JSON catalogs using `scripts/syndication.py`. Keep stable IDs independent of build time and preserve original dates, institution categories, publication/preprint labels and attribution. Do not include local repository paths in public JSON. Run `python scripts/check_syndication.py` after feed or archive changes. `/feed.xml` and `/feed.json` include apps, lectures and research; section feeds live under `/feeds/` and full catalogs under `/api/`.
