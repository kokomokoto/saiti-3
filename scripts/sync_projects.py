#!/usr/bin/env python3
"""Simple sync: copy app/data/projects.json -> site/data/objects.json

Usage (PowerShell):
  python .\scripts\sync_projects.py

This normalizes 'category' to a list, ensures a 'description' field exists,
and rewrites image paths to 'static/img/...' when the source is a bare filename.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / 'app' / 'data' / 'projects.json'
SITE_DATA = ROOT / 'site' / 'data' / 'objects.json'


def normalize_project(p):
    # ensure categories is a list
    cat = p.get('category', [])
    if isinstance(cat, str):
        cat = [cat]
    elif not isinstance(cat, list):
        cat = list(cat) if cat else []
    out = dict(p)
    out['category'] = cat
    # ensure description exists
    if 'description' not in out:
        out['description'] = ''
    # normalize image: keep absolute or http(s), otherwise prefix with static/img/
    img = out.get('image', '') or ''
    if isinstance(img, str) and img and not (img.startswith('/') or img.startswith('http')):
        img = 'static/img/' + Path(img).name
    out['image'] = img
    return out


def main():
    if not APP_DATA.exists():
        print(f"Source data not found: {APP_DATA}")
        return 1
    SITE_DATA.parent.mkdir(parents=True, exist_ok=True)
    # backup existing site file
    if SITE_DATA.exists():
        bak = SITE_DATA.with_suffix('.json.bak')
        shutil.copy2(SITE_DATA, bak)
        print(f"Backed up existing site file to: {bak}")

    with APP_DATA.open('r', encoding='utf-8') as f:
        projects = json.load(f)

    normalized = [normalize_project(p) for p in projects]

    with SITE_DATA.open('w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(normalized)} items to {SITE_DATA}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
