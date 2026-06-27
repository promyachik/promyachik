# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import argparse, re, subprocess, json, shutil
from datetime import datetime
from typing import List, Tuple, Optional

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def split_frontmatter(text: str):
    if not text.startswith("---"): return "", text
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i+1:])
    return "", text

def front_keys(front: str) -> List[str]:
    return [m.group(1) for m in re.finditer(r"^([A-Za-z0-9_\-]+):", front, re.M)]

def has_key(front: str, key: str) -> bool:
    return re.search(rf"^{re.escape(key)}\s*:", front, re.M) is not None

def score_page(path: Path, front: str, target_slug: str, require_value: bool, require_stats: bool) -> int:
    if target_slug and target_slug.lower() in str(path).lower():
        return -999999
    keys = set(front_keys(front))
    score = len(keys)
    value_ok = any(has_key(front, k) for k in ["value_history","market_value_history","dynamic_value","price_points","market_history"])
    stats_ok = any(has_key(front, k) for k in ["previous_club_stats","career_stats","stats_rows","stats","statistics","season_stats"])
    if value_ok: score += 1000
    if stats_ok: score += 500
    if require_value and not value_ok: score -= 100000
    if require_stats and not stats_ok: score -= 100000
    if "draft: true" in front.lower(): score -= 1000
    return score

def inspect(root: Path, target_slug: str = ""):
    rows = []
    for p in (root / "content" / "transfers").rglob("index.md"):
        text = read_text(p); front, body = split_frontmatter(text)
        if not front: continue
        value_ok = any(has_key(front, k) for k in ["value_history","market_value_history","dynamic_value","price_points","market_history"])
        stats_ok = any(has_key(front, k) for k in ["previous_club_stats","career_stats","stats_rows","stats","statistics","season_stats"])
        rows.append((score_page(p, front, target_slug, False, False), p, front_keys(front), value_ok, stats_ok))
    rows.sort(key=lambda x: x[0], reverse=True)
    print("TRANSFER PAGE STRUCTURE SOURCES")
    print("="*80)
    for i, (score, p, keys, value_ok, stats_ok) in enumerate(rows[:30], 1):
        print(f"{i}. score={score} | value_block={value_ok} | stats_block={stats_ok} | {p}")
        print("   keys=" + ", ".join(keys[:140]))

def choose_source(root: Path, target_slug: str, source_slug: str, require_value: bool, require_stats: bool):
    rows = []
    for p in (root / "content" / "transfers").rglob("index.md"):
        if source_slug and source_slug.lower() not in str(p).lower():
            continue
        text = read_text(p); front, body = split_frontmatter(text)
        if not front: continue
        rows.append((score_page(p, front, target_slug, require_value, require_stats), p, front, body))
    rows.sort(key=lambda x: x[0], reverse=True)
    if not rows or rows[0][0] < 0:
        raise SystemExit("No valid source found with required blocks. Run inspect first.")
    return rows[0]

def run_hugo(root: Path):
    res = subprocess.run(["hugo"], cwd=root, capture_output=True, text=True, timeout=120)
    print("HUGO_EXIT_CODE:", res.returncode)
    print(res.stdout[-3000:])
    print(res.stderr[-6000:])
    if res.returncode != 0:
        raise SystemExit(res.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--mode", choices=["inspect"], default="inspect")
    ap.add_argument("--target-slug", default="")
    ap.add_argument("--source-slug", default="")
    ap.add_argument("--require-value", action="store_true")
    ap.add_argument("--require-stats", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    inspect(root, args.target_slug)

if __name__ == "__main__":
    main()
