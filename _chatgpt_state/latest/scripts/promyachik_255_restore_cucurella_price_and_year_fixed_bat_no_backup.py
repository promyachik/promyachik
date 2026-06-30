# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "var"
VAR.mkdir(parents=True, exist_ok=True)
REPORT = VAR / "promyachik_255_restore_cucurella_price_and_year_fixed_bat_no_backup_report.txt"

lines: list[str] = []
changed: set[str] = set()

def log(s: str = "") -> None:
    print(s)
    lines.append(s)

def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            pass
    return path.read_text(errors="replace")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")

def file_in_backup(backup_dir: Path, rel: str) -> Path | None:
    direct = backup_dir / Path(rel)
    if direct.exists() and direct.is_file():
        return direct
    name = Path(rel).name.lower()
    matches = [p for p in backup_dir.rglob("*") if p.is_file() and p.name.lower() == name]
    if not matches:
        return None
    rel_parts = [x.lower() for x in Path(rel).parts]
    scored = []
    for p in matches:
        parts = [x.lower() for x in p.parts]
        score = sum(1 for x in rel_parts if x in parts)
        scored.append((score, len(str(p)), p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]

def find_backup() -> Path | None:
    candidates: list[Path] = []
    candidates.append(Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS\2026-06-30_00-39-32_FULL_BACKUP_BEFORE_249_CUCURELLA_PRICE_LAYER"))
    candidates.append(ROOT / "_backup_promyachik_249_before_cucurella_price_layer_20260630_003932")
    for base in [Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS"), ROOT.parent / "Promyachik_BACKUPS", ROOT]:
        if base.exists():
            candidates.extend(sorted(base.glob("*249*Cucurella*"), reverse=True))
            candidates.extend(sorted(base.glob("*249*cucurella*"), reverse=True))
            candidates.extend(sorted(base.glob("*_backup_promyachik_249_before_cucurella_price_layer*"), reverse=True))
            candidates.extend(sorted(base.glob("*BEFORE_249_CUCURELLA_PRICE_LAYER*"), reverse=True))
    seen = set()
    unique: list[Path] = []
    for c in candidates:
        key = str(c).lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    target_rels = [
        "layouts/partials/transfer-player-market-value-chart.html",
        "static/css/style.css",
        "static/css/transfer-player-market-value-chart.css",
        "static/js/transfer-player-market-value-chart.js",
    ]
    scored: list[tuple[int, str, Path]] = []
    for c in unique:
        if not c.exists() or not c.is_dir():
            continue
        count = sum(1 for rel in target_rels if file_in_backup(c, rel))
        if count:
            scored.append((count, str(c), c))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]

def restore_from_backup(backup: Path) -> list[str]:
    restored: list[str] = []
    target_rels = [
        "layouts/partials/transfer-player-market-value-chart.html",
        "static/css/style.css",
        "static/css/transfer-player-market-value-chart.css",
        "static/js/transfer-player-market-value-chart.js",
    ]
    for rel in target_rels:
        src = file_in_backup(backup, rel)
        if not src:
            log(f"SKIP: {rel} not found in backup")
            continue
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        restored.append(rel)
        changed.add(rel)
        log(f"RESTORED: {rel}")
    return restored

def remove_bad_css_blocks(text: str) -> tuple[str, int]:
    original = text
    removed = 0
    # Remove generated comment blocks from failed packages.
    for n in ("250", "251", "253", "254"):
        patterns = [
            r"/\*\s*=*\s*PROMYACHIK\s+" + n + r"[\s\S]*?(?=/\*\s*=*\s*PROMYACHIK\s+\d+|\Z)",
            r"/\*\s*PROMYACHIK\s+" + n + r"[\s\S]*?END\s*\*/",
        ]
        for pat in patterns:
            text, c = re.subn(pat, "", text, flags=re.IGNORECASE)
            removed += c
    # Remove direct bad hide rules for year/price row.
    bad_rules = [
        r"body\.transfer-page\s+\.player-market-chart__point\s+small\s*\{\s*display\s*:\s*none\s*!important\s*;?\s*\}",
        r"\.player-market-chart-modal\s+\.player-market-chart__point\s+small\s*\{\s*display\s*:\s*none\s*!important\s*;?\s*\}",
        r"body\.transfer-page\s+\.player-market-chart__x-label[^{}]*\{[^{}]*display\s*:\s*none[^{}]*\}",
        r"\.player-market-chart-modal\s+\.player-market-chart__x-label[^{}]*\{[^{}]*display\s*:\s*none[^{}]*\}",
        r"body\.transfer-page\s+\.player-market-chart__point\s+small\s*,\s*\.player-market-chart-modal\s+\.player-market-chart__point\s+small\s*,\s*body\.transfer-page\s+\.player-market-chart__x-label\s*,\s*\.player-market-chart-modal\s+\.player-market-chart__x-label\s*\{[^{}]*display\s*:\s*none[^{}]*\}",
    ]
    for pat in bad_rules:
        text, c = re.subn(pat, "", text, flags=re.IGNORECASE)
        removed += c
    if text != original and removed == 0:
        removed = 1
    return text, removed

def clean_partial(path: Path) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    original = text
    # Remove the 253 inline style that hid small/year above price.
    text, n1 = re.subn(
        r"\s*<style\s+id=[\"']pfb-253-cucurella-hide-point-years[\"'][^>]*>[\s\S]*?</style>\s*",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    # Remove any inline style that clearly belongs to failed 253 marker.
    text, n2 = re.subn(
        r"\s*<style[^>]*>[\s\S]*?253[\s\S]*?player-market-chart__point\s+small[\s\S]*?display\s*:\s*none[\s\S]*?</style>\s*",
        "\n",
        text,
        flags=re.IGNORECASE,
    )
    if text != original:
        write_text(path, text)
        log(f"CLEANED PARTIAL BAD INLINE STYLE: {path.relative_to(ROOT)} replacements={n1+n2}")
        changed.add(str(path.relative_to(ROOT)).replace("\\", "/"))
        return True
    log(f"PARTIAL OK: {path.relative_to(ROOT)}")
    return False

def clean_css(path: Path) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    original = text
    text, removed = remove_bad_css_blocks(text)
    restore = """

/* PROMYACHIK 255 RESTORE CUCURELLA CHART PRICE AND YEAR VISIBILITY NO BACKUP START */
body.transfer-page .player-market-chart__point small,
body.transfer-page .player-market-chart__point strong,
body.transfer-page .player-market-chart__x-label,
body.transfer-page .player-market-chart__x-label small,
body.transfer-page .player-market-chart__x-label strong,
body.transfer-page .player-market-chart__price,
body.transfer-page .player-market-chart__price small,
body.transfer-page .player-market-chart__price strong,
body.transfer-page .player-market-chart__value,
body.transfer-page .player-market-chart__value small,
body.transfer-page .player-market-chart__value strong,
body.transfer-page .promyachik-cucurella-price-label-249,
body.transfer-page .promyachik-cucurella-price-label-249__value,
.player-market-chart-modal .player-market-chart__point small,
.player-market-chart-modal .player-market-chart__point strong,
.player-market-chart-modal .player-market-chart__x-label,
.player-market-chart-modal .player-market-chart__x-label small,
.player-market-chart-modal .player-market-chart__x-label strong,
.player-market-chart-modal .player-market-chart__price,
.player-market-chart-modal .player-market-chart__price small,
.player-market-chart-modal .player-market-chart__price strong,
.player-market-chart-modal .player-market-chart__value,
.player-market-chart-modal .player-market-chart__value small,
.player-market-chart-modal .player-market-chart__value strong {
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
  color: #d4af37 !important;
  font-weight: 900 !important;
  white-space: nowrap !important;
}
/* PROMYACHIK 255 RESTORE CUCURELLA CHART PRICE AND YEAR VISIBILITY NO BACKUP END */
"""
    if "PROMYACHIK 255 RESTORE CUCURELLA CHART PRICE AND YEAR VISIBILITY" not in text:
        text = text.rstrip() + restore
    if text != original:
        write_text(path, text)
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        log(f"PATCHED CSS: {rel} removed_bad_blocks={removed}")
        changed.add(rel)
        return True
    log(f"CSS OK: {path.relative_to(ROOT)}")
    return False

def run_hugo() -> tuple[int, str, str]:
    for cmd in (["hugo", "-D"], ["hugo.exe", "-D"]):
        try:
            p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=180)
            return p.returncode, p.stdout, p.stderr
        except FileNotFoundError:
            continue
        except Exception as e:
            return 999, "", repr(e)
    return 999, "", "hugo not found"

def find_public_cucurella_pages() -> list[Path]:
    pub = ROOT / "public" / "transfers"
    if not pub.exists():
        return []
    result = []
    for p in pub.rglob("index.html"):
        s = str(p).lower().replace("\\", "/")
        if "cucurella" in s:
            result.append(p)
    return sorted(result)

def count_price_tokens() -> tuple[int, list[str]]:
    hits = []
    total = 0
    for p in find_public_cucurella_pages():
        text = read_text(p)
        cnt = text.count("€") + text.count("&euro;") + text.count("&#8364;")
        total += cnt
        hits.append(f"{p.relative_to(ROOT)} euro_tokens={cnt}")
    return total, hits

log("PROMYACHIK 255 - RESTORE CUCURELLA PRICE/YEAR - FIXED BAT - NO BACKUP")
log("=" * 100)
log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Project dir: {ROOT}")
log("")
log("RULE")
log("- Fix broken package 254 BAT by using ASCII-only BAT.")
log("- Restore visible price/year area broken by 250-253.")
log("- Use existing backup only if already present; create no backup.")
log("- Do not push.")
log("- Do not open site.")
log("")
log("NO BACKUP")
log("- Full backup: NOT CREATED")
log("- Safety backup: NOT CREATED")
log("")

backup = find_backup()
restored: list[str] = []
if backup:
    log(f"EXISTING BACKUP FOUND: {backup}")
    restored = restore_from_backup(backup)
else:
    log("NO EXISTING 249 BACKUP FOUND. USING CLEANUP/FORCE-VISIBLE FALLBACK.")

clean_partial(ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html")
for css_rel in ["static/css/style.css", "static/css/transfer-player-market-value-chart.css"]:
    clean_css(ROOT / css_rel)

log("")
log("HUGO")
code, out, err = run_hugo()
log(f"hugo_exit_code: {code}")
log("--- STDOUT tail ---")
log("\n".join(out.splitlines()[-20:]))
log("--- STDERR tail ---")
log("\n".join(err.splitlines()[-20:]))

price_count, price_hits = count_price_tokens()
log("")
log("PUBLIC CUCURELLA CHECK")
log(f"public_cucurella_price_token_count: {price_count}")
for h in price_hits:
    log(f"- {h}")

log("")
log("CHANGED FILES")
if changed:
    for rel in sorted(changed):
        log(f"- {rel}")
else:
    log("- none")

log("")
log("CHECKS")
log("backup_created: False")
log(f"used_existing_backup: {bool(backup)}")
log(f"restored_file_count: {len(restored)}")
log(f"changed_file_count: {len(changed)}")
log(f"hugo_exit_code: {code}")
log(f"verified_price_tokens_present: {price_count > 0}")
log(f"VERIFIED_OK: {code == 0 and (len(changed) > 0) and price_count > 0}")
log("")
log("NO BACKUP CREATED.")
log("NO PUSH MADE.")
log("NO SITE OPENED.")

REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nREPORT: {REPORT}")
if code != 0:
    sys.exit(1)
