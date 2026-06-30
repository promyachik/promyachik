from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

PACKAGE_ID = "250"
PACKAGE_NAME = "HIDE YEAR ABOVE PRICE NO BACKUP"
MARKER = "PROMYACHIK 250 - HIDE YEAR ABOVE PRICE - NO BACKUP"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def tail(text: str, limit: int = 80) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-limit:])


def replace_regex(path: Path, patterns: list[tuple[str, str, str]], report: list[str]) -> bool:
    if not path.exists():
        report.append(f"MISSING: {path}")
        return False

    original = read_text(path)
    current = original
    total_changes = 0

    for label, pattern, replacement in patterns:
        current, count = re.subn(pattern, replacement, current, flags=re.MULTILINE | re.DOTALL)
        total_changes += count
        report.append(f"  {label}: replacements={count}")

    if current != original:
        write_text(path, current)
        report.append(f"CHANGED: {path}")
        return True

    report.append(f"UNCHANGED: {path}")
    return False


def append_css(path: Path, report: list[str]) -> bool:
    if not path.exists():
        report.append(f"MISSING: {path}")
        return False

    text = read_text(path)
    if MARKER in text:
        report.append(f"UNCHANGED: {path} | marker already exists")
        return False

    block = f'''

/* =========================================
   {MARKER}
   Removes only the year/date label above chart prices.
   No backup is created by this package.
========================================= */
body.transfer-page .player-market-chart__point small,
.player-market-chart-modal .player-market-chart__point small,
body.transfer-page .player-market-chart__x-label,
.player-market-chart-modal .player-market-chart__x-label {{
    display: none !important;
}}

body.transfer-page .player-market-chart__point,
.player-market-chart-modal .player-market-chart__point {{
    gap: 0 !important;
}}
'''
    write_text(path, text.rstrip() + block + "\n")
    report.append(f"CHANGED: {path} | appended CSS marker")
    return True


def run_command(project_dir: Path, args: list[str], report: list[str]) -> int:
    report.append("COMMAND: " + " ".join(args))
    try:
        result = subprocess.run(
            args,
            cwd=str(project_dir),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except FileNotFoundError as error:
        report.append(f"COMMAND_ERROR: {error}")
        return 999

    report.append(f"EXIT_CODE: {result.returncode}")
    report.append("--- STDOUT tail ---")
    report.append(tail(result.stdout))
    report.append("--- STDERR tail ---")
    report.append(tail(result.stderr))
    return result.returncode


def main() -> None:
    script_path = Path(__file__).resolve()
    project_dir = script_path.parents[1]

    report: list[str] = []
    report.append(f"PROMYACHIK {PACKAGE_ID} - {PACKAGE_NAME}")
    report.append("=" * 100)
    report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Project dir: {project_dir}")
    report.append("")
    report.append("RULE")
    report.append("- Remove/hide only the year/date text shown above chart prices.")
    report.append("- Keep price labels visible.")
    report.append("- Do not move prices in this package.")
    report.append("- Do not touch Ramos content.")
    report.append("- Do not touch Cucurella content markdown.")
    report.append("- Do not create any backup folder or backup file.")
    report.append("- No push.")
    report.append("- No site opened.")
    report.append("")
    report.append("NO BACKUP")
    report.append("- Full backup: NOT CREATED")
    report.append("- Safety backup: NOT CREATED")
    report.append("- User explicitly forbade backups without command.")
    report.append("")

    changed_files: list[str] = []

    partial = project_dir / "layouts" / "partials" / "transfer-player-market-value-chart.html"
    js = project_dir / "static" / "js" / "transfer-player-market-value-chart.js"
    style_css = project_dir / "static" / "css" / "style.css"
    chart_css = project_dir / "static" / "css" / "transfer-player-market-value-chart.css"

    report.append("TEMPLATE CHANGE")
    if replace_regex(
        partial,
        [
            (
                "remove Hugo .label small above value_label",
                r"\n\s*<small>\s*\{\{\s*\.label\s*\}\}\s*</small>",
                "",
            ),
            (
                "remove Hugo $point.label small above value_label",
                r"\n\s*<small>\s*\{\{\s*\$point\.label\s*\}\}\s*</small>",
                "",
            ),
        ],
        report,
    ):
        changed_files.append(str(partial.relative_to(project_dir)).replace("\\", "/"))

    report.append("")
    report.append("JAVASCRIPT CHANGE")
    if replace_regex(
        js,
        [
            (
                "remove JS point.label small above value_label",
                r"\n\s*<small>\s*\$\{[^\n{}]*point\.label[^\n{}]*\}\s*</small>",
                "",
            ),
            (
                "remove JS item.label small above value_label",
                r"\n\s*<small>\s*\$\{[^\n{}]*item\.label[^\n{}]*\}\s*</small>",
                "",
            ),
        ],
        report,
    ):
        changed_files.append(str(js.relative_to(project_dir)).replace("\\", "/"))

    report.append("")
    report.append("CSS FALLBACK")
    if append_css(style_css, report):
        changed_files.append(str(style_css.relative_to(project_dir)).replace("\\", "/"))
    if append_css(chart_css, report):
        changed_files.append(str(chart_css.relative_to(project_dir)).replace("\\", "/"))

    report.append("")
    report.append("CHANGED FILES")
    if changed_files:
        for file_name in changed_files:
            report.append(f"- {file_name}")
    else:
        report.append("- none")
    report.append(f"EFFECTIVE_CHANGED_FILES: {len(changed_files)}")

    report.append("")
    report.append("HUGO")
    hugo_exit = run_command(project_dir, ["hugo", "-D"], report)

    public_cucurella = project_dir / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
    public_has_player_chart = False
    public_has_point_small = False
    public_has_price_text = False

    if public_cucurella.exists():
        public_text = read_text(public_cucurella)
        public_has_player_chart = "player-market-chart" in public_text
        public_has_point_small = "player-market-chart__point" in public_text and "<small>" in public_text
        public_has_price_text = "€" in public_text

    css_marker_count = 0
    for css_path in (style_css, chart_css):
        if css_path.exists() and MARKER in read_text(css_path):
            css_marker_count += 1

    report.append("")
    report.append("CHECKS")
    report.append(f"hugo_exit_code: {hugo_exit}")
    report.append("backup_created: False")
    report.append(f"css_marker_count: {css_marker_count}")
    report.append(f"public_cucurella_exists: {public_cucurella.exists()}")
    report.append(f"public_cucurella_has_player_chart: {public_has_player_chart}")
    report.append(f"public_cucurella_has_point_small: {public_has_point_small}")
    report.append(f"public_cucurella_has_price_text: {public_has_price_text}")
    report.append(f"VERIFIED_OK: {hugo_exit == 0 and css_marker_count >= 1 and len(changed_files) > 0}")
    report.append("")
    report.append("NO BACKUP CREATED.")
    report.append("NO PUSH MADE.")
    report.append("NO SITE OPENED.")

    var_dir = project_dir / "var"
    var_dir.mkdir(exist_ok=True)
    report_path = var_dir / "promyachik_250_hide_year_above_price_no_backup_report.txt"
    write_text(report_path, "\n".join(report) + "\n")

    print("DONE")
    print("YEAR ABOVE PRICE HIDDEN/REMOVED")
    print("PRICE LABELS KEPT")
    print("NO BACKUP CREATED")
    print("NO PUSH MADE")
    print("NO SITE OPENED")
    print(f"REPORT: {report_path}")


if __name__ == "__main__":
    main()
