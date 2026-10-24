"""Refresh portfolio snapshots from a separately checked-out source repository."""
import argparse
from datetime import date
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ['lectures', 'papers', 'patents', 'websites', 'about']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Path to a needleworm.github.io checkout')
    args = parser.parse_args()
    source = args.source.resolve()
    snapshots = {key: (source / 'content' / 'sections' / f'{key}.html').read_text(encoding='utf-8') for key in SECTIONS}
    commit = subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'], text=True).strip()
    for key, text in snapshots.items():
        (ROOT / 'content/portfolio' / f'{key}.html').write_text(text, encoding='utf-8')
    manifest_path = ROOT / 'content/portfolio/provenance.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest.update(commit=commit, imported_on=date.today().isoformat(), sections=SECTIONS)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Portfolio snapshots refreshed. Run scripts/build_site.py next.')
