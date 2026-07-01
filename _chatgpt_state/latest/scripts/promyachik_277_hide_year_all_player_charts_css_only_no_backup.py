from pathlib import Path
import subprocess
import datetime
import sys

PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "var" / "promyachik_277_hide_year_all_player_charts_css_only_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

STATIC_CSS = PROJECT / "static" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_CSS = PROJECT / "public" / "css" / "transfer-player-market-value-chart.css"

MARKER_START = "/* PROMYACHIK 277 HIDE YEAR ALL PLAYER CHARTS CSS ONLY START */"
MARKER_END = "/* PROMYACHIK 277 HIDE YEAR ALL PLAYER CHARTS CSS ONLY END */"

CSS_BLOCK = f"""
{MARKER_START}
/*
   Global safe mode for all current and future player market charts.
   Do not remove DOM nodes, do not change layout, do not touch JS.
   The year/date <small> stays in the DOM for old positioning scripts,
   but becomes visually invisible. The price <strong> remains visible.
*/
body.transfer-page .player-market-chart .player-market-chart__point small {{
    color: transparent !important;
    text-shadow: none !important;
    -webkit-text-fill-color: transparent !important;
}}

body.transfer-page .player-market-chart .player-market-chart__point strong {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}}

.player-market-chart-modal .player-market-chart--enlarged .player-market-chart__point small {{
    color: transparent !important;
    text-shadow: none !important;
    -webkit-text-fill-color: transparent !important;
}}

.player-market-chart-modal .player-market-chart--enlarged .player-market-chart__point strong {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}}
{MARKER_END}
""".strip() + "\n"


def remove_marker_block(text: str) -> tuple[str, int]:
    removed = 0
    while MARKER_START in text and MARKER_END in text:
        start = text.index(MARKER_START)
        end = text.index(MARKER_END, start) + len(MARKER_END)
        while end < len(text) and text[end] in " \t\r\n":
            end += 1
        text = text[:start].rstrip() + "\n\n" + text[end:].lstrip()
        removed += 1
    return text, removed

log = []
log.append("PROMYACHIK 277 - HIDE YEAR ALL PLAYER CHARTS CSS ONLY - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {PROJECT}")
log.append("")
log.append("RULE")
log.append("- Do not create backup.")
log.append("- Do not push.")
log.append("- Do not open site.")
log.append("- Do not touch JS.")
log.append("- Do not touch partials/templates.")
log.append("- Do not remove year DOM nodes; hide year visually only.")
log.append("- Apply to all current and future player market charts.")
log.append("- Keep price strong visible.")
log.append("")

try:
    if not STATIC_CSS.exists():
        log.append(f"ERROR: CSS file not found: {STATIC_CSS}")
        REPORT.write_text("\n".join(log), encoding="utf-8")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        sys.exit(1)

    before = STATIC_CSS.read_text(encoding="utf-8", errors="ignore")
    after, removed_277 = remove_marker_block(before)
    after = after.rstrip() + "\n\n" + CSS_BLOCK
    STATIC_CSS.write_text(after, encoding="utf-8")
    log.append(f"CHANGED: {STATIC_CSS} | removed_old_277_blocks={removed_277} | appended_global_css_only_hide")

    log.append("")
    log.append("HUGO")
    proc = subprocess.run(["hugo", "-D"], cwd=PROJECT, text=True, capture_output=True)
    log.append(f"exit_code: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2000:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2000:])

    if proc.returncode == 0:
        try:
            PUBLIC_CSS.parent.mkdir(parents=True, exist_ok=True)
            PUBLIC_CSS.write_text(STATIC_CSS.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            log.append(f"PUBLIC CSS SYNCED: {PUBLIC_CSS}")
        except Exception as e:
            log.append(f"PUBLIC CSS SYNC ERROR: {e!r}")

    static_text = STATIC_CSS.read_text(encoding="utf-8", errors="ignore")
    public_text = PUBLIC_CSS.read_text(encoding="utf-8", errors="ignore") if PUBLIC_CSS.exists() else ""

    log.append("")
    log.append("CHECKS")
    log.append("changed_files:")
    log.append("- static/css/transfer-player-market-value-chart.css")
    log.append(f"backup_created: False")
    log.append(f"js_touched: False")
    log.append(f"partial_touched: False")
    log.append(f"static_css_has_277_marker: {MARKER_START in static_text}")
    log.append(f"public_css_has_277_marker: {MARKER_START in public_text}")
    log.append(f"static_css_has_global_point_small_rule: {'body.transfer-page .player-market-chart .player-market-chart__point small' in static_text}")
    log.append(f"static_css_has_global_point_strong_rule: {'body.transfer-page .player-market-chart .player-market-chart__point strong' in static_text}")
    log.append(f"public_css_exists: {PUBLIC_CSS.exists()}")

    ok = (
        proc.returncode == 0
        and MARKER_START in static_text
        and MARKER_START in public_text
        and 'body.transfer-page .player-market-chart .player-market-chart__point small' in static_text
        and 'body.transfer-page .player-market-chart .player-market-chart__point strong' in static_text
    )
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
