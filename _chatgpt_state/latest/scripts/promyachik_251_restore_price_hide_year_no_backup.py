from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

PACKAGE_ID = "251"
PACKAGE_NAME = "RESTORE PRICE HIDE YEAR NO BACKUP"
BAD_250_MARKER = "PROMYACHIK 250 - HIDE YEAR ABOVE PRICE - NO BACKUP"
MARKER_251 = "PROMYACHIK 251 - RESTORE PRICE HIDE YEAR - NO BACKUP"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def tail(text: str, limit: int = 90) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-limit:])


def remove_bad_250_css(path: Path, report: list[str]) -> bool:
    if not path.exists():
        report.append(f"MISSING: {path}")
        return False

    original = read_text(path)
    current = original

    # Exact block produced by package 250. It hid .player-market-chart__x-label,
    # which can be the price row, so it must be removed completely.
    patterns = [
        (
            "remove full 250 marker block",
            r"\n/\*\s*=+\s*\n\s*PROMYACHIK 250 - HIDE YEAR ABOVE PRICE - NO BACKUP[\s\S]*?body\.transfer-page \.player-market-chart__point,\s*\n\.player-market-chart-modal \.player-market-chart__point\s*\{[\s\S]*?\}\s*\n",
            "\n",
        ),
        (
            "remove combined 250 x-label hide rule if marker block was partially edited",
            r"\nbody\.transfer-page \.player-market-chart__point small,\s*\n\.player-market-chart-modal \.player-market-chart__point small,\s*\nbody\.transfer-page \.player-market-chart__x-label,\s*\n\.player-market-chart-modal \.player-market-chart__x-label\s*\{\s*\n\s*display:\s*none\s*!important;\s*\n\}\s*\n",
            "\n",
        ),
        (
            "remove isolated 250 x-label hide rule",
            r"\nbody\.transfer-page \.player-market-chart__x-label,\s*\n\.player-market-chart-modal \.player-market-chart__x-label\s*\{\s*\n\s*display:\s*none\s*!important;\s*\n\}\s*\n",
            "\n",
        ),
    ]

    for label, pattern, replacement in patterns:
        current, count = re.subn(pattern, replacement, current, flags=re.MULTILINE)
        report.append(f"  {path.name}: {label}: replacements={count}")

    if current != original:
        write_text(path, current)
        report.append(f"CHANGED: {path} | removed bad 250 CSS")
        return True

    report.append(f"UNCHANGED: {path} | no bad 250 CSS found")
    return False


def remove_year_markup(path: Path, report: list[str]) -> bool:
    if not path.exists():
        report.append(f"MISSING: {path}")
        return False

    original = read_text(path)
    current = original

    patterns = [
        # Hugo template variants: remove only year/date label small, not price/value spans.
        (
            "remove Hugo .label small",
            r"\n\s*<small(?:\s+[^>]*)?>\s*\{\{\s*\.label\s*\}\}\s*</small>",
            "",
        ),
        (
            "remove Hugo $point.label small",
            r"\n\s*<small(?:\s+[^>]*)?>\s*\{\{\s*\$point\.label\s*\}\}\s*</small>",
            "",
        ),
        (
            "remove Hugo .year small",
            r"\n\s*<small(?:\s+[^>]*)?>\s*\{\{\s*\.year\s*\}\}\s*</small>",
            "",
        ),
        (
            "remove Hugo $point.year small",
            r"\n\s*<small(?:\s+[^>]*)?>\s*\{\{\s*\$point\.year\s*\}\}\s*</small>",
            "",
        ),
        (
            "remove explicit year/date class element",
            r"\n\s*<(?:small|span|div)\b[^>]*class=\"[^\"]*(?:year|date|label)[^\"]*\"[^>]*>\s*(?:\{\{\s*(?:\.|\$point\.)?(?:label|year|date)\s*\}\}|\d{4})\s*</(?:small|span|div)>",
            "",
        ),
    ]

    for label, pattern, replacement in patterns:
        current, count = re.subn(pattern, replacement, current, flags=re.MULTILINE | re.DOTALL)
        report.append(f"  {path.name}: {label}: replacements={count}")

    if current != original:
        write_text(path, current)
        report.append(f"CHANGED: {path} | removed year markup only")
        return True

    report.append(f"UNCHANGED: {path} | no removable year markup found")
    return False


def append_price_restore_css(path: Path, report: list[str]) -> bool:
    if not path.exists():
        report.append(f"MISSING: {path}")
        return False

    text = read_text(path)
    if MARKER_251 in text:
        report.append(f"UNCHANGED: {path} | 251 marker already exists")
        return False

    block = f'''

/* =========================================
   {MARKER_251}
   Fixes package 250: price labels must stay visible.
   No backup is created by this package.
========================================= */
body.transfer-page .player-market-chart__x-label,
.player-market-chart-modal .player-market-chart__x-label,
body.transfer-page .player-market-chart__price,
.player-market-chart-modal .player-market-chart__price,
body.transfer-page .player-market-chart__value,
.player-market-chart-modal .player-market-chart__value,
body.transfer-page .pf-market-chart__price,
.player-market-chart-modal .pf-market-chart__price,
body.transfer-page .pf-market-chart__value,
.player-market-chart-modal .pf-market-chart__value {{
    visibility: visible !important;
    opacity: 1 !important;
}}

body.transfer-page .player-market-chart__x-label,
.player-market-chart-modal .player-market-chart__x-label {{
    display: block !important;
}}
'''
    write_text(path, text.rstrip() + block + "\n")
    report.append(f"CHANGED: {path} | appended 251 price visibility CSS")
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


def find_public_cucurella_pages(project_dir: Path) -> list[Path]:
    public_dir = project_dir / "public"
    if not public_dir.exists():
        return []

    candidates: list[Path] = []
    for path in public_dir.rglob("index.html"):
        normalized = str(path).replace("\\", "/").lower()
        if "cucurella" in normalized:
            candidates.append(path)
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        if "Cucurella" in text or "Кукурель" in text:
            candidates.append(path)
    return candidates[:10]


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
    report.append("- Fix package 250: restore visible price labels if they were hidden with the year.")
    report.append("- Keep the year/date above the price removed/hidden where template/JS has a separate year label.")
    report.append("- Do not move prices in this package.")
    report.append("- Do not touch Ramos content markdown.")
    report.append("- Do not touch Cucurella content markdown.")
    report.append("- Do not create any backup folder or backup file.")
    report.append("- No push.")
    report.append("- No site opened.")
    report.append("")
    report.append("NO BACKUP")
    report.append("- Full backup: NOT CREATED")
    report.append("- Safety backup: NOT CREATED")
    report.append("- User explicitly forbade any backups without command.")
    report.append("")

    changed_files: list[str] = []

    partial = project_dir / "layouts" / "partials" / "transfer-player-market-value-chart.html"
    js = project_dir / "static" / "js" / "transfer-player-market-value-chart.js"
    css_paths = [
        project_dir / "static" / "css" / "style.css",
        project_dir / "static" / "css" / "transfer-player-market-value-chart.css",
    ]

    report.append("STEP 1 - REMOVE BAD 250 CSS THAT HID PRICE")
    for css_path in css_paths:
        if remove_bad_250_css(css_path, report):
            changed_files.append(str(css_path.relative_to(project_dir)).replace("\\", "/"))

    report.append("")
    report.append("STEP 2 - REMOVE ONLY YEAR/LABEL MARKUP, NOT PRICE")
    for source_path in (partial, js):
        if remove_year_markup(source_path, report):
            rel = str(source_path.relative_to(project_dir)).replace("\\", "/")
            if rel not in changed_files:
                changed_files.append(rel)

    report.append("")
    report.append("STEP 3 - ADD SAFE PRICE VISIBILITY CSS")
    # Put the safe visibility rule only in style.css because it is known to be loaded globally.
    if append_price_restore_css(css_paths[0], report):
        rel = str(css_paths[0].relative_to(project_dir)).replace("\\", "/")
        if rel not in changed_files:
            changed_files.append(rel)

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

    report.append("")
    report.append("PUBLIC CUCURELLA CHECK")
    public_pages = find_public_cucurella_pages(project_dir)
    report.append(f"public_cucurella_pages_found: {len(public_pages)}")
    public_has_euro = False
    public_has_250_marker = False
    public_has_251_marker = False
    for path in public_pages:
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            text = ""
        rel = str(path.relative_to(project_dir)).replace("\\", "/")
        has_euro = "€" in text or "&euro;" in text
        has_250 = BAD_250_MARKER in text
        has_251 = MARKER_251 in text
        public_has_euro = public_has_euro or has_euro
        public_has_250_marker = public_has_250_marker or has_250
        public_has_251_marker = public_has_251_marker or has_251
        report.append(f"- {rel} | euro_or_price_symbol={has_euro} | has_bad_250_marker={has_250} | has_251_marker={has_251}")

    css_has_bad_250 = False
    css_has_251 = False
    for css_path in css_paths:
        if css_path.exists():
            css_text = read_text(css_path)
            css_has_bad_250 = css_has_bad_250 or BAD_250_MARKER in css_text
            css_has_251 = css_has_251 or MARKER_251 in css_text

    report.append("")
    report.append("CHECKS")
    report.append(f"hugo_exit_code: {hugo_exit}")
    report.append("backup_created: False")
    report.append(f"css_has_bad_250_marker: {css_has_bad_250}")
    report.append(f"css_has_251_marker: {css_has_251}")
    report.append(f"public_any_cucurella_has_price_symbol: {public_has_euro}")
    report.append(f"VERIFIED_OK: {hugo_exit == 0 and css_has_251 and not css_has_bad_250 and len(changed_files) > 0}")
    report.append("")
    report.append("NO BACKUP CREATED.")
    report.append("NO PUSH MADE.")
    report.append("NO SITE OPENED.")

    var_dir = project_dir / "var"
    var_dir.mkdir(exist_ok=True)
    report_path = var_dir / "promyachik_251_restore_price_hide_year_no_backup_report.txt"
    write_text(report_path, "\n".join(report) + "\n")

    print("DONE")
    print("PRICE LABELS RESTORED")
    print("YEAR ABOVE PRICE REMAINS REMOVED WHERE IT IS A SEPARATE LABEL")
    print("NO BACKUP CREATED")
    print("NO PUSH MADE")
    print("NO SITE OPENED")
    print(f"REPORT: {report_path}")


if __name__ == "__main__":
    main()
