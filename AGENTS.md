# Site maintenance

This repository is a static app directory. Edit `content/apps.json`, `content/home-shell.html`, `directory.css`, and `script.js`; rebuild generated HTML with `python scripts/build_site.py`.

## App update queue

Before adding or updating app cards, read `../updateque.md` if present. It is the workspace-level queue for new apps and app changes. Inspect the named repository and confirm its purpose, launch URL, and assets. Add or update records in `content/apps.json`, deduplicating by app ID and URL. Preserve the queue and do not mark work complete until generated cards pass validation. If the queue is absent, do not invent entries.

Run `python scripts/build_site.py --check`, `python scripts/check_site.py`, `node --check script.js`, and `node scripts/check_interactions.cjs` after relevant changes. The catalog coverage check expects sibling app repositories in the parent workspace. Never overwrite unrelated local work. Commit and push only within the user's authorized scope.

Imported portfolio snapshots belong in `content/portfolio/`. Use `scripts/sync_portfolio.py` to refresh them from a verified source checkout. Preserve publication/preprint labels and original document links.
