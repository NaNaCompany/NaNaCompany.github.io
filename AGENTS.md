# Site maintenance

Preserve the original NaNa Lab design, header, hero video, typography, colors, business sections, and contact form. Changes must be additive unless the user explicitly asks otherwise. The original stylesheet `style.css` must not be replaced by a new visual system. New app and knowledge section styles belong in `additions.css` and must be scoped to those sections.

Edit `content/apps.json`, `content/home-shell.html`, `additions.css`, and `script.js`; rebuild generated HTML with `python scripts/build_site.py`. The app grid replaces only the former RSS section. Keep Services, About, Customers, Process, and Contact in their original order and structure. Preserve existing sitemap URLs and metadata when appending routes.

## App update queue

Before adding or updating app cards, read `../updateque.md` if present. It is the workspace-level queue for new apps and app changes. Inspect the named repository and confirm its purpose, launch URL, and assets. Add or update records in `content/apps.json`, deduplicating by app ID and URL. Preserve the queue and do not mark work complete until generated cards pass validation. If the queue is absent, do not invent entries.

Check the queue only when requested. Do not create recurring monitoring. An explicit queue request may add apps previously excluded from the initial catalog, including `rebirth_country`.

Run `python scripts/build_site.py --check`, `python scripts/check_site.py`, `node --check script.js`, and `node scripts/check_interactions.cjs` after relevant changes. The catalog coverage check expects sibling app repositories in the parent workspace. Never overwrite unrelated local work. Commit and push only within the user's authorized scope.

Imported portfolio snapshots belong in `content/portfolio/`. Use `scripts/sync_portfolio.py` to refresh them from a verified source checkout. Preserve publication/preprint labels and original document links.
