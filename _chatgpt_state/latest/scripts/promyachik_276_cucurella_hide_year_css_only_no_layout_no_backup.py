from pathlib import Path
import subprocess
import datetime
import sys

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "var" / "promyachik_276_cucurella_hide_year_css_only_no_layout_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

CSS_FILES = [
    PROJECT / "static" / "css" / "transfer-player-market-value-chart.css",
]

PUBLIC_CSS = PROJECT / "public" / "css" / "transfer-player-market-value-chart.css"

MARKER_START = "/* PROMYACHIK 276 CUCURELLA HIDE YEAR CSS ONLY NO LAYOUT START */"
MARKER_END = "/* PROMYACHIK 276 CUCURELLA HIDE YEAR CSS ONLY NO LAYOUT END */"

CSS_BLOCK = f"""
{MARKER_START}
/*
   Safe mode: do not remove DOM nodes and do not change element height/position.
   The old 244 alignment script still sees the same text and geometry, so prices
   should not jump to the footer. Only the year line becomes invisible visually.
*/
body.transfer-page
.player-market-chart[data-market-chart-key="cucurella"]
.player-market-chart__point small {{
    color: transparent !important;
    text-shadow: none !important;
    -webkit-text-fill-color: transparent !important;
}}

body.transfer-page
.player-market-chart[data-market-chart-key="cucurella"]
.player-market-chart__point strong {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}}

.player-market-chart-modal
.player-market-chart--enlarged[data-market-chart-key="cucurella"]
.player-market-chart__point small {{
    color: transparent !important;
    text-shadow: none !important;
    -webkit-text-fill-color: transparent !important;
}}
{MARKER_END}
""".strip() + "\n"


def remove_marker_block(text: str) -> tuple[str, int]:
    count = 0
    while MARKER_START in text and MARKER_END in text:
        start = text.index(MARKER_START)
        end = text.index(MARKER_END, start) + len(MARKER_END)
        # remove trailing whitespace/newline after marker block
        while end < len(text) and text[end] in " \t\r\n":
            end += 1
        text = text[:start].rstrip() + "\n\n" + text[end:].lstrip()
        count += 1
    return text, count

log = []
log.append("PROMYACHIK 276 - CUCURELLA HIDE YEAR CSS ONLY NO LAYOUT - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {PROJECT}")
log.append("")
log.append("RULE")
log.append("- Do not create backup.")
log.append("- Do not push.")
log.append("- Do not open site.")
log.append("- Do not touch JS.")
log.append("- Do not touch partials.")
log.append("- Do not remove year DOM node; hide it visually only to preserve price geometry.")
log.append("- Keep price strong visible.")
log.append("")

changed_files = []
try:
    for css_path in CSS_FILES:
        if not css_path.exists():
            log.append(f"ERROR: CSS file not found: {css_path}")
            REPORT.write_text("\n".join(log), encoding="utf-8")
            print("FAILED")
            print(f"REPORT: {REPORT}")
            sys.exit(1)

        text = css_path.read_text(encoding="utf-8", errors="ignore")
        text2, removed = remove_marker_block(text)
        text2 = text2.rstrip() + "\n\n" + CSS_BLOCK
        css_path.write_text(text2, encoding="utf-8")
        changed_files.append(str(css_path.relative_to(PROJECT)))
        log.append(f"CHANGED: {css_path} | removed_old_276_blocks={removed} | appended_css_only_hide")

    log.append("")
    log.append("HUGO")
    proc = subprocess.run(["hugo", "-D"], cwd=PROJECT, text=True, capture_output=True)
    log.append(f"exit_code: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2000:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2000:])

    # If Hugo did not copy the static CSS for any reason, copy the changed CSS directly too.
    if proc.returncode == 0:
        try:
            PUBLIC_CSS.parent.mkdir(parents=True, exist_ok=True)
            PUBLIC_CSS.write_text(CSS_FILES[0].read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            log.append(f"PUBLIC CSS SYNCED: {PUBLIC_CSS}")
        except Exception as e:
            log.append(f"PUBLIC CSS SYNC ERROR: {e!r}")

    static_text = CSS_FILES[0].read_text(encoding="utf-8", errors="ignore")
    public_text = PUBLIC_CSS.read_text(encoding="utf-8", errors="ignore") if PUBLIC_CSS.exists() else ""

    log.append("")
    log.append("CHECKS")
    log.append("changed_files:")
    for f in changed_files:
        log.append(f"- {f}")
    log.append(f"backup_created: False")
    log.append(f"js_touched: False")
    log.append(f"partial_touched: False")
    log.append(f"static_css_has_276_marker: {MARKER_START in static_text}")
    log.append(f"public_css_has_276_marker: {MARKER_START in public_text}")
    log.append(f"public_css_exists: {PUBLIC_CSS.exists()}")

    ok = proc.returncode == 0 and MARKER_START in static_text and MARKER_START in public_text
    log.append("")
    log.append("DONE" if ok else "FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(0 if ok else 1)

except Exception as e:
    log.append(f"FATAL ERROR: {e!r}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise
