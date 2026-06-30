# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess
import datetime
import re

PROJECT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT / "var"
REPORT_DIR.mkdir(exist_ok=True)
REPORT = REPORT_DIR / "promyachik_253_cucurella_hide_year_only_restore_price_no_backup_report.txt"

PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
PUBLIC_CUC = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

MARKER_ID = "pfb-253-cucurella-hide-point-years"
STYLE_BLOCK = '''
{{- if eq .RelPermalink "/transfers/marc-cucurella-real-madrid/" -}}
<style id="pfb-253-cucurella-hide-point-years">
/* 253: Cucurella chart — hide only the year/date above price, keep price visible */
body.transfer-page .player-market-chart__point small {
  display: none !important;
}
body.transfer-page .player-market-chart__point strong {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}
</style>
{{- end -}}
'''.strip()

lines = []
def log(msg=""):
    lines.append(str(msg))

log("PROMYACHIK 253 - CUCURELLA HIDE YEAR ONLY RESTORE PRICE NO BACKUP")
log("=" * 100)
log(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Project dir: {PROJECT}")
log("")
log("RULE")
log("- Continue Cucurella chart task after failed 250/251 attempts.")
log("- Hide only the year/date that appears above the price in the chart points.")
log("- Keep price labels visible.")
log("- Do not move prices in this package.")
log("- Do not touch Ramos content markdown.")
log("- Do not touch Cucurella content markdown.")
log("- Do not create any backup folder or backup file.")
log("- No push.")
log("- No site opened.")
log("")
log("NO BACKUP")
log("- Full backup: NOT CREATED")
log("- Safety backup: NOT CREATED")
log("- User explicitly forbade backups without command.")
log("")

changed = []
try:
    text = PARTIAL.read_text(encoding="utf-8")
except Exception as e:
    log(f"ERROR: cannot read partial: {PARTIAL} | {e}")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    raise SystemExit(1)

original = text

# Remove duplicate/older 253 style block if this package is rerun.
text, removed_old = re.subn(
    r"\n?\{\{-\s*if\s+eq\s+\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*-\}\}\s*"
    r"<style\s+id=\"pfb-253-cucurella-hide-point-years\">.*?</style>\s*"
    r"\{\{-\s*end\s*-\}\}\n?",
    "\n",
    text,
    flags=re.S,
)
log(f"STEP 1 - remove old 253 style block if rerun: replacements={removed_old}")

# Insert style immediately after the chart if-condition so it renders only on Cucurella page.
inserted = False
patterns = [
    r"(\{\{-\s*if\s+\$chart\s*-\}\})",
    r"(\{\{\s*if\s+\$chart\s*\}\})",
]
for pat in patterns:
    new_text, n = re.subn(pat, r"\1\n" + STYLE_BLOCK + "\n", text, count=1)
    if n:
        text = new_text
        inserted = True
        log(f"STEP 2 - insert Cucurella-only inline CSS after chart if: pattern={pat} replacements={n}")
        break

if not inserted:
    # Fallback: append to the end of partial. Still wrapped by page permalink condition.
    text = text.rstrip() + "\n" + STYLE_BLOCK + "\n"
    log("STEP 2 - chart if not found; appended Cucurella-only inline CSS to partial end")

if text != original:
    PARTIAL.write_text(text, encoding="utf-8", newline="")
    changed.append(str(PARTIAL.relative_to(PROJECT)).replace('\\', '/'))
    log(f"CHANGED: {PARTIAL} | added Cucurella-only year-hide CSS")
else:
    log(f"UNCHANGED: {PARTIAL} | marker already present")

log("")
log("CHANGED FILES")
for f in changed:
    log(f"- {f}")
log(f"EFFECTIVE_CHANGED_FILES: {len(changed)}")
log("")

# Run Hugo build.
log("HUGO")
cmd = ["hugo", "-D"]
try:
    p = subprocess.run(cmd, cwd=str(PROJECT), text=True, capture_output=True, timeout=90)
    log(f"COMMAND: {' '.join(cmd)}")
    log(f"EXIT_CODE: {p.returncode}")
    log("--- STDOUT tail ---")
    log("\n".join((p.stdout or "").splitlines()[-18:]))
    log("--- STDERR tail ---")
    log("\n".join((p.stderr or "").splitlines()[-18:]))
    hugo_ok = (p.returncode == 0)
except Exception as e:
    log(f"ERROR running hugo: {e}")
    hugo_ok = False

log("")
log("PUBLIC CUCURELLA CHECK")
public_exists = PUBLIC_CUC.exists()
public_has_marker = False
public_has_hide_small = False
public_has_strong_visible = False
public_has_price = False
public_has_cucurella = False
if public_exists:
    html = PUBLIC_CUC.read_text(encoding="utf-8", errors="replace")
    public_has_marker = MARKER_ID in html
    public_has_hide_small = "player-market-chart__point small" in html and "display: none" in html
    public_has_strong_visible = "player-market-chart__point strong" in html and "visibility: visible" in html
    public_has_price = any(x in html for x in ["€", "&euro;", "млн", "m", "M"])
    public_has_cucurella = any(x in html for x in ["Cucurella", "Кукурелья", "cucurella"])
log(f"public_cucurella_exists: {public_exists}")
log(f"public_has_253_marker: {public_has_marker}")
log(f"public_has_hide_small_rule: {public_has_hide_small}")
log(f"public_has_strong_visible_rule: {public_has_strong_visible}")
log(f"public_has_price_text_or_symbol: {public_has_price}")
log(f"public_has_cucurella_text: {public_has_cucurella}")

verified_ok = hugo_ok and public_exists and public_has_marker and public_has_hide_small and public_has_strong_visible and public_has_price
log("")
log("CHECKS")
log(f"hugo_exit_code_ok: {hugo_ok}")
log("backup_created: False")
log(f"partial_has_253_marker: {MARKER_ID in text}")
log(f"VERIFIED_OK: {verified_ok}")
log("")
log("NO BACKUP CREATED.")
log("NO PUSH MADE.")
log("NO SITE OPENED.")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print()
print(f"REPORT: {REPORT}")

raise SystemExit(0 if verified_ok else 2)
