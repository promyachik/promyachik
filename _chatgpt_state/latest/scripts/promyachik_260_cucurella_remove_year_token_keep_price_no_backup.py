from pathlib import Path
import re
import subprocess
import sys
import datetime

PACKAGE = "PROMYACHIK 260 - CUCURELLA REMOVE YEAR TOKEN KEEP PRICE - NO BACKUP"
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_DIR = SCRIPT_PATH.parents[1]
REPORT_PATH = PROJECT_DIR / "var" / "promyachik_260_cucurella_remove_year_token_keep_price_no_backup_report.txt"
PARTIAL_PATH = PROJECT_DIR / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE_PATH = PROJECT_DIR / "static" / "css" / "style.css"
CHART_CSS_PATH = PROJECT_DIR / "static" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_CUC_PATH = PROJECT_DIR / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

DATE_TOKEN_PATTERNS = [
    r"\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}",
    r"\{\{\s*default\s+\$promyachikCucPoint249\.date_label\s+\$promyachikCucPoint249\.date\s*\}\}",
    r"\{\{\s*\$promyachikCucPoint249\.date\s*\}\}",
    r"\{\{\s*\$promyachikCucPoint249\.date_label\s*\}\}",
]
VALUE_TOKEN_RE = re.compile(r"\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\}")
CUC_START = '{{ if in $.RelPermalink "/transfers/marc-cucurella-real-madrid/" }}'
CUC_ELSE = '{{ else }}'

log = []
changed_files = []

def add(msg: str):
    print(msg)
    log.append(msg)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8", newline="")

def remove_date_from_cucurella_branch(text: str):
    start = text.find(CUC_START)
    if start < 0:
        return text, 0, "CUCURELLA_BRANCH_NOT_FOUND"
    else_pos = text.find(CUC_ELSE, start)
    if else_pos < 0:
        return text, 0, "CUCURELLA_ELSE_NOT_FOUND"

    before = text[:start]
    branch = text[start:else_pos]
    after = text[else_pos:]
    replacements = 0

    # 1) Remove a whole HTML element if it is the dedicated date element.
    whole_date_element = re.compile(
        r"<([a-zA-Z0-9]+)([^>]*class=[\"'][^\"']*promyachik-cucurella-price-label-249__date[^\"']*[\"'][^>]*)>\s*"
        r"(?:" + "|".join(DATE_TOKEN_PATTERNS) + r")\s*</\1>",
        flags=re.S,
    )
    branch, n = whole_date_element.subn("", branch)
    replacements += n
    add(f"remove dedicated date html element: replacements={n}")

    # 2) If the date is plain text before the price token, remove only the date token.
    for pat in DATE_TOKEN_PATTERNS:
        branch, n = re.subn(pat, "", branch)
        replacements += n
        add(f"remove date token {pat}: replacements={n}")

    # 3) Remove now-empty date spans if any are left.
    empty_date_element = re.compile(
        r"<([a-zA-Z0-9]+)([^>]*class=[\"'][^\"']*promyachik-cucurella-price-label-249__date[^\"']*[\"'][^>]*)>\s*</\1>",
        flags=re.S,
    )
    branch, n = empty_date_element.subn("", branch)
    replacements += n
    add(f"remove empty date html element: replacements={n}")

    # 4) Add marker only once.
    marker = "{{/* PROMYACHIK 260: Cucurella year/date token removed; price value_label kept. */}}"
    if marker not in branch:
        branch = branch.replace(CUC_START, CUC_START + " " + marker, 1)
        replacements += 1
        add("added 260 marker to cucurella branch")
    else:
        add("260 marker already present")

    # Safety: if value token disappeared, stop and do not write.
    if not VALUE_TOKEN_RE.search(branch):
        return text, replacements, "PRICE_VALUE_TOKEN_NOT_FOUND_AFTER_EDIT"

    return before + branch + after, replacements, "OK"

def append_force_css(path: Path):
    if not path.exists():
        add(f"css missing, skipped: {path}")
        return False
    css = read_text(path)
    marker_start = "/* PROMYACHIK 260 CUCURELLA HIDE YEAR KEEP PRICE START */"
    marker_end = "/* PROMYACHIK 260 CUCURELLA HIDE YEAR KEEP PRICE END */"
    block = f"""
{marker_start}
body.transfer-page .promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249__date {{
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}}
body.transfer-page .promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249__value {{
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}}
{marker_end}
"""
    pattern = re.compile(re.escape(marker_start) + r".*?" + re.escape(marker_end), flags=re.S)
    if marker_start in css and marker_end in css:
        new_css, n = pattern.subn(block.strip(), css)
        action = f"updated existing 260 CSS block replacements={n}"
    else:
        new_css = css.rstrip() + "\n" + block
        action = "appended 260 CSS block"
    if new_css != css:
        write_text(path, new_css)
        changed_files.append(str(path.relative_to(PROJECT_DIR)))
        add(f"CHANGED: {path} | {action}")
        return True
    add(f"UNCHANGED: {path}")
    return False

def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    add(PACKAGE)
    add("=" * 100)
    add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    add(f"Project dir: {PROJECT_DIR}")
    add("")
    add("RULE")
    add("- Remove only the year/date token above Cucurella price labels.")
    add("- Keep the price value_label visible.")
    add("- Do not move prices in this package.")
    add("- Do not create any backup folder or backup file.")
    add("- No push.")
    add("- No site opened.")
    add("")

    if not PARTIAL_PATH.exists():
        add(f"ERROR: partial not found: {PARTIAL_PATH}")
        REPORT_PATH.write_text("\n".join(log), encoding="utf-8")
        return 2

    old = read_text(PARTIAL_PATH)
    new, replacements, status = remove_date_from_cucurella_branch(old)
    add(f"partial edit status: {status}")
    add(f"partial replacements_total: {replacements}")

    if status != "OK":
        add("ERROR: partial edit stopped before writing.")
        REPORT_PATH.write_text("\n".join(log), encoding="utf-8")
        return 3

    if new != old:
        write_text(PARTIAL_PATH, new)
        changed_files.append(str(PARTIAL_PATH.relative_to(PROJECT_DIR)))
        add(f"CHANGED: {PARTIAL_PATH}")
    else:
        add(f"UNCHANGED: {PARTIAL_PATH}")

    # CSS fallback: harmless if date element was already removed; useful if old public/style cache exists.
    append_force_css(STYLE_PATH)
    append_force_css(CHART_CSS_PATH)

    add("")
    add("HUGO")
    try:
        proc = subprocess.run(["hugo", "-D"], cwd=str(PROJECT_DIR), text=True, capture_output=True, timeout=90)
        add(f"hugo_exit_code: {proc.returncode}")
        add("--- STDOUT tail ---")
        add("\n".join(proc.stdout.splitlines()[-18:]))
        add("--- STDERR tail ---")
        add("\n".join(proc.stderr.splitlines()[-18:]))
    except Exception as e:
        add(f"hugo_error: {e!r}")
        proc = None

    public_exists = PUBLIC_CUC_PATH.exists()
    public_text = read_text(PUBLIC_CUC_PATH) if public_exists else ""
    add("")
    add("CHECKS")
    add("backup_created: False")
    add(f"changed_files_count: {len(changed_files)}")
    for f in changed_files:
        add(f"changed: {f}")
    add(f"public_cucurella_exists: {public_exists}")
    add(f"public_has_price_layer_249: {'promyachik-cucurella-price-layer-249' in public_text}")
    add(f"public_has_date_class: {'promyachik-cucurella-price-label-249__date' in public_text}")
    add(f"public_has_value_class: {'promyachik-cucurella-price-label-249__value' in public_text}")
    add(f"public_has_euro_symbol: {'€' in public_text or '&euro;' in public_text}")
    add(f"partial_has_value_token: {bool(VALUE_TOKEN_RE.search(read_text(PARTIAL_PATH)))}")
    add("NO BACKUP CREATED.")
    add("NO PUSH MADE.")
    add("NO SITE OPENED.")

    ok = (proc is not None and proc.returncode == 0 and bool(changed_files) and public_exists)
    add(f"VERIFIED_OK: {ok}")
    REPORT_PATH.write_text("\n".join(log), encoding="utf-8")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
