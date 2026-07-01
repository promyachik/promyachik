from pathlib import Path
import subprocess
import datetime
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "var" / "promyachik_282_apply_price_row_up_all_players_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 282 - APPLY PRICE ROW UP TO ALL PLAYER CHARTS - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Apply the successful Konate price-row-up spacing to all current and future player charts.")
log.append("- Remove the old Konate-only test style block from layout if present.")
log.append("- Keep hidden years unchanged.")
log.append("- Keep prices unchanged.")
log.append("- Do not touch JS.")
log.append("- Do not touch content markdown.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

changed_files = []

# 1) Remove Konate-only inline style test from layout so the rule is not duplicated.
layout = ROOT / "layouts" / "transfers" / "single.html"
if not layout.exists():
    log.append(f"ERROR: layout not found: {layout}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

layout_text = layout.read_text(encoding="utf-8")
layout_old = layout_text
start = "{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST START */}}"
end = "{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST END */}}"
block_re = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
layout_text, removed_281 = block_re.subn("", layout_text)
log.append(f"removed 281 Konate-only style blocks from layout: {removed_281}")

if layout_text != layout_old:
    layout.write_text(layout_text, encoding="utf-8")
    changed_files.append(str(layout.relative_to(ROOT)))
    log.append(f"CHANGED: {layout}")
else:
    log.append("UNCHANGED: layout had no 281 marker block")

# 2) Add/update global CSS rule in chart CSS.
css = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
if not css.exists():
    log.append(f"ERROR: css not found: {css}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

css_text = css.read_text(encoding="utf-8")
css_old = css_text
marker_start = "/* PROMYACHIK 282 PRICE ROW UP ALL PLAYER CHARTS START */"
marker_end = "/* PROMYACHIK 282 PRICE ROW UP ALL PLAYER CHARTS END */"
marker_re = re.compile(re.escape(marker_start) + r".*?" + re.escape(marker_end), re.S)
css_text, removed_old_282 = marker_re.subn("", css_text)
log.append(f"removed old 282 marker blocks from css: {removed_old_282}")

rule = f"""
{marker_start}
/* Same vertical position tested successfully on Konate in package 281.
   CSS-only: preserve DOM and JS positioning, just move the already aligned price row closer to the chart. */
body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points {{
  margin-top: 1px !important;
  transform: translateY(-6px) !important;
}}
{marker_end}
"""

if css_text and not css_text.endswith("\n"):
    css_text += "\n"
css_text += rule

if css_text != css_old:
    css.write_text(css_text, encoding="utf-8")
    changed_files.append(str(css.relative_to(ROOT)))
    log.append(f"CHANGED: {css}")
else:
    log.append("UNCHANGED: css text unchanged")

# 3) Run Hugo to sync public.
proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2500:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2500:])

public_css = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"
log.append("")
log.append("PUBLIC CSS CHECK")
log.append(f"public_css_exists: {public_css.exists()}")

ok = proc.returncode == 0 and public_css.exists()
if public_css.exists():
    public_text = public_css.read_text(encoding="utf-8", errors="ignore")
    has_marker = marker_start in public_text and marker_end in public_text
    has_transform = "translateY(-6px)" in public_text
    has_rule = ".player-market-chart__points" in public_text
    log.append(f"public_has_282_marker: {has_marker}")
    log.append(f"public_has_translateY_minus_6: {has_transform}")
    log.append(f"public_has_points_rule: {has_rule}")
    ok = ok and has_marker and has_transform and has_rule

# 4) Confirm layout no longer contains Konate-only style.
layout_after = layout.read_text(encoding="utf-8", errors="ignore")
layout_has_281 = "promyachik-281-konate-price-row-up-test" in layout_after or start in layout_after
log.append("")
log.append("LAYOUT CHECK")
log.append(f"layout_has_281_konate_only_style: {layout_has_281}")
ok = ok and not layout_has_281

# 5) Check current public transfer pages include linked CSS; CSS applies to all and future pages through shared stylesheet.
transfers_dir = ROOT / "public" / "transfers"
checked = []
if transfers_dir.exists():
    for p in sorted(transfers_dir.glob("*/index.html"))[:20]:
        html = p.read_text(encoding="utf-8", errors="ignore")
        if "transfer-player-market-value-chart.css" in html:
            checked.append(str(p.relative_to(ROOT)))
log.append("")
log.append("TRANSFER PAGE CHECK")
log.append(f"public_transfer_pages_linking_chart_css_count_sample: {len(checked)}")
for item in checked[:12]:
    log.append(f"- {item}")

log.append("")
log.append("CHANGED FILES")
for f in changed_files:
    log.append(f"- {f}")
log.append(f"EFFECTIVE_CHANGED_FILES: {len(changed_files)}")

log.append("")
log.append("CHECKS")
log.append("backup_created: False")
log.append("js_touched: False")
log.append("content_touched: False")
log.append(f"VERIFIED_OK: {ok}")
log.append("")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
