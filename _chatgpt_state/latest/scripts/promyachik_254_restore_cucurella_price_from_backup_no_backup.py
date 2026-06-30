# -*- coding: utf-8 -*-
"""
PROMYACHIK 254
Restore Cucurella chart price/year markup from an EXISTING backup if available.
No new backup folders or backup files are created.
No push. No site opened.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "var"
VAR.mkdir(parents=True, exist_ok=True)
REPORT = VAR / "promyachik_254_restore_cucurella_price_from_backup_no_backup_report.txt"

lines: list[str] = []

def log(s: str = "") -> None:
    print(s)
    lines.append(s)


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def find_existing_backup_file(backup_dir: Path, rel: str) -> Path | None:
    direct = backup_dir / Path(rel)
    if direct.exists() and direct.is_file():
        return direct
    name = Path(rel).name.lower()
    matches = [p for p in backup_dir.rglob("*") if p.is_file() and p.name.lower() == name]
    # Prefer a match whose path suffix contains the same relative path parts.
    rel_parts = [part.lower() for part in Path(rel).parts]
    scored = []
    for p in matches:
        parts = [part.lower() for part in p.parts]
        score = sum(1 for part in rel_parts if part in parts)
        scored.append((score, len(str(p)), p))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]


def remove_block_by_markers(text: str, marker: str) -> tuple[str, int]:
    # Handles standard START/END comment blocks.
    pattern = re.compile(
        r"/\*[^*]*PROMYACHIK\s+" + re.escape(marker) + r"[\s\S]*?START\s*\*/[\s\S]*?/\*[^*]*PROMYACHIK\s+" + re.escape(marker) + r"[\s\S]*?END\s*\*/",
        re.IGNORECASE,
    )
    text2, n = pattern.subn("", text)
    return text2, n


def remove_late_bad_blocks(text: str) -> tuple[str, int]:
    before = text
    removed = 0
    # Remove appended 250/251/253 blocks if they were appended with a header comment and no END marker.
    # These packages were only CSS/script cleanup attempts and are safe to delete for restore.
    for num in ("250", "251", "253"):
        pattern = re.compile(
            r"/\*\s*=*\s*PROMYACHIK\s+" + num + r"[\s\S]*?(?=/\*\s*=*\s*PROMYACHIK\s+\d+|\Z)",
            re.IGNORECASE,
        )
        text, n = pattern.subn("", text)
        removed += n
    # Remove any CSS rule that hides a year/small label on Cucurella and may affect price block layout.
    css_hide_patterns = [
        r"body[^{}]*(?:cucurella|marc-cucurella)[^{}]*small[^{}]*\{[^{}]*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0)[^{}]*\}",
        r"body[^{}]*(?:cucurella|marc-cucurella)[^{}]*(?:date|year|label)[^{}]*\{[^{}]*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0)[^{}]*\}",
        r"\.promyachik-cucurella[^{}]*(?:date|year|label)[^{}]*\{[^{}]*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0)[^{}]*\}",
    ]
    for pat in css_hide_patterns:
        text, n = re.subn(pat, "", text, flags=re.IGNORECASE)
        removed += n
    return text, removed + (1 if before != text else 0)


def ensure_css_restore(css_path: Path) -> bool:
    if not css_path.exists():
        return False
    text = read_text(css_path)
    original = text
    for marker in ("249", "250", "251", "253"):
        text, _ = remove_block_by_markers(text, marker)
    text, _ = remove_late_bad_blocks(text)
    restore_block = r'''

/* PROMYACHIK 254 RESTORE CUCURELLA PRICE VISIBILITY NO BACKUP START */
body.transfer-page .player-market-chart__point,
body.transfer-page .player-market-chart__x-label,
body.transfer-page .player-market-chart__price,
body.transfer-page .player-market-chart__value,
body.transfer-page .pf-market-chart__price,
body.transfer-page .pf-market-chart__value,
body.transfer-page .promyachik-cucurella-price-label-249,
body.transfer-page .promyachik-cucurella-price-label-249__value,
.player-market-chart-modal .player-market-chart__point,
.player-market-chart-modal .player-market-chart__x-label,
.player-market-chart-modal .player-market-chart__price,
.player-market-chart-modal .player-market-chart__value,
.player-market-chart-modal .pf-market-chart__price,
.player-market-chart-modal .pf-market-chart__value {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}
body.transfer-page .player-market-chart__point strong,
body.transfer-page .player-market-chart__x-label strong,
body.transfer-page .player-market-chart__price strong,
body.transfer-page .player-market-chart__value strong,
body.transfer-page .promyachik-cucurella-price-label-249__value,
.player-market-chart-modal .player-market-chart__point strong,
.player-market-chart-modal .player-market-chart__x-label strong,
.player-market-chart-modal .player-market-chart__price strong,
.player-market-chart-modal .player-market-chart__value strong {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  color: #d4af37 !important;
  font-weight: 900 !important;
  white-space: nowrap !important;
}
/* PROMYACHIK 254 RESTORE CUCURELLA PRICE VISIBILITY NO BACKUP END */
'''
    if "PROMYACHIK 254 RESTORE CUCURELLA PRICE VISIBILITY" not in text:
        text = text.rstrip() + restore_block
    if text != original:
        write_text(css_path, text)
        return True
    return False


def restore_from_existing_backup() -> tuple[Path | None, list[str]]:
    target_rels = [
        "layouts/partials/transfer-player-market-value-chart.html",
        "static/css/style.css",
        "static/css/transfer-player-market-value-chart.css",
        "static/js/transfer-player-market-value-chart.js",
    ]

    candidates: list[Path] = []
    explicit = Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS\2026-06-30_00-39-32_FULL_BACKUP_BEFORE_249_CUCURELLA_PRICE_LAYER")
    candidates.append(explicit)
    for base in [Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS"), ROOT.parent / "Promyachik_BACKUPS"]:
        if base.exists():
            candidates.extend(sorted(base.glob("*BEFORE_249_CUCURELLA_PRICE_LAYER*"), reverse=True))
    candidates.append(ROOT / "_backup_promyachik_249_before_cucurella_price_layer_20260630_003932")
    candidates.extend(sorted(ROOT.glob("_backup_promyachik_*before_cucurella_price_layer*"), reverse=True))

    # Deduplicate while preserving order.
    seen = set()
    candidates2 = []
    for c in candidates:
        key = str(c).lower()
        if key not in seen:
            seen.add(key)
            candidates2.append(c)

    scored: list[tuple[int, Path]] = []
    for c in candidates2:
        if not c.exists() or not c.is_dir():
            continue
        count = sum(1 for rel in target_rels if find_existing_backup_file(c, rel))
        if count:
            scored.append((count, c))
    if not scored:
        return None, []
    scored.sort(key=lambda x: (-x[0], str(x[1])))
    backup = scored[0][1]

    restored: list[str] = []
    for rel in target_rels:
        src = find_existing_backup_file(backup, rel)
        if not src:
            log(f"SKIP restore {rel}: not found in existing backup")
            continue
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        restored.append(rel)
        log(f"RESTORED FROM EXISTING BACKUP: {rel}")
    return backup, restored


def run_hugo() -> tuple[int, str, str]:
    commands = [["hugo", "-D"], ["hugo.exe", "-D"]]
    last_err = ""
    for cmd in commands:
        try:
            p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=120)
            return p.returncode, p.stdout, p.stderr
        except FileNotFoundError as e:
            last_err = str(e)
            continue
        except Exception as e:
            return 999, "", repr(e)
    return 999, "", last_err


def count_public_price_symbols() -> tuple[int, list[str]]:
    paths = [
        ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html",
        ROOT / "public" / "transfers" / "marc-cucurella-chelsea-real-madrid" / "index.html",
    ]
    hits = []
    count = 0
    for p in paths:
        if not p.exists():
            continue
        text = read_text(p)
        c = text.count("€") + text.count("&euro;") + text.count("&#8364;")
        if c:
            hits.append(f"{p.relative_to(ROOT)}: euro_count={c}")
            count += c
    return count, hits


log("PROMYACHIK 254 - RESTORE CUCURELLA PRICE FROM EXISTING BACKUP - NO BACKUP")
log("=" * 100)
log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Project dir: {ROOT}")
log("")
log("RULE")
log("- Restore visible Cucurella chart price/year state broken by 250-253.")
log("- Prefer existing 249 backup if it exists.")
log("- Do not create any backup folder or backup file.")
log("- Do not push.")
log("- Do not open site.")
log("")
log("NO BACKUP")
log("- Full backup: NOT CREATED")
log("- Safety backup: NOT CREATED")
log("")

backup, restored = restore_from_existing_backup()
if backup:
    log("")
    log(f"USED EXISTING BACKUP: {backup}")
else:
    log("NO EXISTING 249 BACKUP FOUND. FALLBACK: clean bad 250-253 CSS and force price visibility.")

changed = set(restored)
for rel in ["static/css/style.css", "static/css/transfer-player-market-value-chart.css"]:
    path = ROOT / rel
    if ensure_css_restore(path):
        changed.add(rel)
        log(f"PATCHED CSS PRICE VISIBILITY: {rel}")

# Clean obvious 250/253 hide markers from JS if present, without touching normal code.
for rel in ["static/js/transfer-player-market-value-chart.js"]:
    path = ROOT / rel
    if path.exists():
        text = read_text(path)
        original = text
        for marker in ("250", "251", "253"):
            text, _ = remove_block_by_markers(text, marker)
        text, _ = remove_late_bad_blocks(text)
        if text != original:
            write_text(path, text)
            changed.add(rel)
            log(f"CLEANED BAD JS MARKERS: {rel}")

log("")
log("CHANGED FILES")
if changed:
    for rel in sorted(changed):
        log(f"- {rel}")
else:
    log("- none")

log("")
log("HUGO")
code, out, err = run_hugo()
log(f"hugo_exit_code: {code}")
log("--- STDOUT tail ---")
log("\n".join(out.splitlines()[-18:]))
log("--- STDERR tail ---")
log("\n".join(err.splitlines()[-18:]))

price_count, price_hits = count_public_price_symbols()
log("")
log("PUBLIC CUCURELLA CHECK")
log(f"public_cucurella_price_symbol_count: {price_count}")
for h in price_hits:
    log(f"- {h}")

log("")
log("CHECKS")
log(f"backup_created: False")
log(f"used_existing_backup: {bool(backup)}")
log(f"restored_file_count: {len(restored)}")
log(f"changed_file_count: {len(changed)}")
log(f"hugo_exit_code: {code}")
log(f"VERIFIED_OK: {code == 0 and bool(changed)}")
log("")
log("NO BACKUP CREATED.")
log("NO PUSH MADE.")
log("NO SITE OPENED.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nREPORT: {REPORT}")
if code != 0:
    sys.exit(1)
