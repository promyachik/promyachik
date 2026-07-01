from pathlib import Path
import datetime
import re
import subprocess
import sys

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_305_konate_hide_bottom_white_45_page_class_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 305 - KONATE HIDE BOTTOM WHITE 45 VIA PAGE CLASS - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Target only the Konate transfer page.")
log.append("- Hide only the legacy bottom value-row last label inside .player-market-chart__points.")
log.append("- Do not hide any overlay or gold labels.")
log.append("- Do not touch Ramos.")
log.append("- Do not create backup.")
log.append("- Do not push.")
log.append("- Do not open site.")
log.append("")

if not ROOT.exists():
    log.append(f"ERROR: project dir not found: {ROOT}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

partial = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
css = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"

if not partial.exists():
    log.append(f"ERROR: partial not found: {partial}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

if not css.exists():
    log.append(f"ERROR: css not found: {css}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

changed_files = []

# 1) Add a page-specific Hugo variable to the chart partial.
partial_text = partial.read_text(encoding="utf-8")
partial_old = partial_text

var_line = '{{- $promyachik305KonateHideBottom45 := or (in (lower (default "" .RelPermalink)) "ibrahima-konate-real-madrid") (in (lower (default "" .Title)) "konate") (in (lower (default "" .Title)) "konaté") -}}'

if "promyachik305KonateHideBottom45" not in partial_text:
    chart_line_re = re.compile(r'(\{\{\-\s*\$chart\s*:=\s*\.Params\.market_value_chart\s*\-\}\}\s*)')
    partial_text, inserted_var = chart_line_re.subn(r"\1" + var_line + "\n", partial_text, count=1)
    if inserted_var == 0:
        partial_text = var_line + "\n" + partial_text
        inserted_var = 1
    log.append(f"inserted Konate page variable: {inserted_var}")
else:
    log.append("Konate page variable already present")

# 2) Add a class only to the player chart section on the Konate page.
class_snippet = '{{ if $promyachik305KonateHideBottom45 }} player-market-chart--konate-hide-bottom-white-45{{ end }}'

if "player-market-chart--konate-hide-bottom-white-45" not in partial_text:
    section_class_re = re.compile(r'(class\s*=\s*")([^"]*\bplayer-market-chart\b[^"]*)(")', re.S)
    def add_konate_class(match):
        return match.group(1) + match.group(2) + class_snippet + match.group(3)
    partial_text, class_added = section_class_re.subn(add_konate_class, partial_text, count=1)
    log.append(f"added Konate class to first player chart class attribute: {class_added}")
else:
    log.append("Konate class already present in partial")
    class_added = 1

if "player-market-chart--konate-hide-bottom-white-45" not in partial_text:
    log.append("ERROR: could not add or find Konate-specific chart class")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

if partial_text != partial_old:
    partial.write_text(partial_text, encoding="utf-8")
    changed_files.append(str(partial.relative_to(ROOT)))
    log.append(f"CHANGED: {partial}")
else:
    log.append("UNCHANGED: partial already had required Konate marker")

# 3) Add a narrow CSS rule that hides only the bottom legacy row last value on that page.
css_text = css.read_text(encoding="utf-8")
css_old = css_text
marker_start = "/* PROMYACHIK 305 KONATE HIDE BOTTOM WHITE 45 START */"
marker_end = "/* PROMYACHIK 305 KONATE HIDE BOTTOM WHITE 45 END */"
marker_re = re.compile(re.escape(marker_start) + r".*?" + re.escape(marker_end), re.S)
css_text, removed_old = marker_re.subn("", css_text)
log.append(f"removed old 305 css blocks: {removed_old}")

rule = f"""
{marker_start}
/* Konate only: hide the legacy bottom-row duplicate last price.
   The gold overlay labels are intentionally not targeted here. */
body.transfer-page .player-market-chart--konate-hide-bottom-white-45 .player-market-chart__points .player-market-chart__point:last-child > strong {{
    display: none !important;
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
    log.append("UNCHANGED: css already had required rule")

# 4) Build Hugo output to update public.
log.append("")
log.append("HUGO")
proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-3000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-3000:])

# 5) Verify generated Konate page has class and CSS has rule.
public_konate = ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"
public_ramos = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
public_css = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"

log.append("")
log.append("VERIFY")
log.append(f"public_konate_exists: {public_konate.exists()}")
log.append(f"public_ramos_exists: {public_ramos.exists()}")
log.append(f"public_css_exists: {public_css.exists()}")

ok = proc.returncode == 0 and public_konate.exists() and public_css.exists()

if public_konate.exists():
    konate_html = public_konate.read_text(encoding="utf-8", errors="ignore")
    konate_has_class = "player-market-chart--konate-hide-bottom-white-45" in konate_html
    konate_has_chart = "player-market-chart" in konate_html
    log.append(f"konate_has_player_chart: {konate_has_chart}")
    log.append(f"konate_has_305_class: {konate_has_class}")
    ok = ok and konate_has_class and konate_has_chart

if public_ramos.exists():
    ramos_html = public_ramos.read_text(encoding="utf-8", errors="ignore")
    ramos_has_class = "player-market-chart--konate-hide-bottom-white-45" in ramos_html
    log.append(f"ramos_has_305_class_should_be_false: {ramos_has_class}")
    ok = ok and not ramos_has_class

if public_css.exists():
    public_css_text = public_css.read_text(encoding="utf-8", errors="ignore")
    public_has_marker = marker_start in public_css_text and marker_end in public_css_text
    public_has_selector = ".player-market-chart--konate-hide-bottom-white-45 .player-market-chart__points .player-market-chart__point:last-child > strong" in public_css_text
    log.append(f"public_css_has_305_marker: {public_has_marker}")
    log.append(f"public_css_has_narrow_selector: {public_has_selector}")
    ok = ok and public_has_marker and public_has_selector

log.append("")
log.append("CHANGED FILES")
for item in changed_files:
    log.append(f"- {item}")
log.append(f"EFFECTIVE_CHANGED_FILES: {len(changed_files)}")
log.append("")
log.append("CHECKS")
log.append("backup_created: False")
log.append("push_made: False")
log.append("ramos_touched: False")
log.append("konate_only_class: True")
log.append(f"VERIFIED_OK: {ok}")
log.append("")
log.append("DONE" if ok else "FAILED")

REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
