from pathlib import Path
import datetime
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
TARGET_REL = "/promyachik/transfers/marc-cucurella-real-madrid/"
TARGET_REL_SHORT = "/transfers/marc-cucurella-real-madrid/"
TARGET_PUBLIC = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
REPORT = ROOT / "var" / "promyachik_263_cucurella_remove_year_relpermalink_branch_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []

def add(s=""):
    log.append(str(s))

def finish(code: int):
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if code == 0 else "FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(code)

add("PROMYACHIK 263 - CUCURELLA REMOVE YEAR BY RELPERMALINK BRANCH - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {ROOT}")
add("")
add("RULE")
add("- Work only with Cucurella target URL/RelPermalink branch.")
add("- Remove only year/date token from Cucurella price labels.")
add("- Keep price value_label visible.")
add("- Do not move prices in this package.")
add("- Do not create backup folder or backup file.")
add("- No push.")
add("- No site opened.")
add("")
add("TARGET CHECK")
add(f"target_url: http://localhost:1313{TARGET_REL}")
add(f"target_rel_permalink_expected: {TARGET_REL}")
add(f"target_rel_permalink_short_expected: {TARGET_REL_SHORT}")
add(f"target_public_html: {TARGET_PUBLIC}")
add("")

if not PARTIAL.exists():
    add(f"ERROR: partial not found: {PARTIAL}")
    finish(1)

text = PARTIAL.read_text(encoding="utf-8", errors="replace")
old_text = text

slug_pos = text.find(TARGET_REL_SHORT)
add(f"partial_has_target_rel_short: {slug_pos >= 0}")
if slug_pos < 0:
    add("ERROR: target RelPermalink marker not found in partial. File not written.")
    finish(1)

branch_start = text.rfind("{{ if", 0, slug_pos)
branch_else = text.find("{{ else }}", slug_pos)
branch_end = branch_else if branch_else >= 0 else text.find("{{ end }}", slug_pos)
add(f"branch_start_found: {branch_start >= 0}")
add(f"branch_else_found: {branch_else >= 0}")
add(f"branch_end_index: {branch_end}")

if branch_start < 0 or branch_end < 0:
    add("ERROR: could not isolate Cucurella branch. File not written.")
    finish(1)

prefix = text[:branch_start]
branch = text[branch_start:branch_end]
suffix = text[branch_end:]
old_branch = branch

add("")
add("BRANCH BEFORE CHECK")
add(f"branch_contains_target_rel: {TARGET_REL_SHORT in branch}")
add(f"branch_contains_value_label: {'value_label' in branch}")
add(f"branch_contains_cuc_point_date: {'$promyachikCucPoint249.date' in branch}")
add(f"branch_contains_date_class: {'promyachik-cucurella-price-label-249__date' in branch}")

replacements = []

def subn(name, pattern, repl=""):
    global branch
    new_branch, n = re.subn(pattern, repl, branch, flags=re.S)
    branch = new_branch
    replacements.append((name, n))
    add(f"{name}: replacements={n}")
    return n

add("")
add("EDIT")
# 1) Real 249 separate date span, if present.
subn(
    "remove 249 date span with any content",
    r'\s*<span\s+class="[^"]*promyachik-cucurella-price-label-249__date[^"]*"[^>]*>.*?</span>\s*',
    "\n"
)
# 2) Current compressed template form visible in GitHub state: date token directly before value_label.
subn(
    "remove default date/date_label token before value_label",
    r'\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}\s*(?=\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})',
    ""
)
subn(
    "remove default date_label/date token before value_label",
    r'\{\{\s*default\s+\$promyachikCucPoint249\.date_label\s+\$promyachikCucPoint249\.date\s*\}\}\s*(?=\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})',
    ""
)
# 3) Direct point date variants before value_label.
subn(
    "remove direct cuc point date before value_label",
    r'\{\{\s*\$promyachikCucPoint249\.date\s*\}\}\s*(?=\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})',
    ""
)
subn(
    "remove direct cuc point date_label before value_label",
    r'\{\{\s*\$promyachikCucPoint249\.date_label\s*\}\}\s*(?=\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})',
    ""
)
# 4) If date is in a small tag inside the isolated Cucurella branch, remove the small only.
subn(
    "remove small with cuc point/default date only",
    r'\s*<small[^>]*>\s*(?:\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}|\{\{\s*default\s+\$promyachikCucPoint249\.date_label\s+\$promyachikCucPoint249\.date\s*\}\}|\{\{\s*\$promyachikCucPoint249\.date\s*\}\}|\{\{\s*\$promyachikCucPoint249\.date_label\s*\}\})\s*</small>\s*',
    "\n"
)

total = sum(n for _, n in replacements)
new_text = prefix + branch + suffix

add("")
add("CHECKS BEFORE WRITE")
add(f"replacements_total: {total}")
add(f"branch_changed: {branch != old_branch}")
add(f"price_value_label_still_in_cucurella_branch: {'$promyachikCucPoint249.value_label' in branch}")
add(f"target_rel_still_in_partial: {TARGET_REL_SHORT in new_text}")
add(f"backup_created: False")

if total <= 0 or branch == old_branch:
    add("ERROR: no Cucurella year/date token was removed. File not written.")
    finish(1)

if "$promyachikCucPoint249.value_label" not in branch:
    add("ERROR: price value_label disappeared from Cucurella branch. File not written.")
    finish(1)

PARTIAL.write_text(new_text, encoding="utf-8")
add(f"CHANGED: {PARTIAL}")

add("")
add("HUGO")
proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-3000:])
add("--- STDERR tail ---")
add(proc.stderr[-3000:])

add("")
add("PUBLIC TARGET CHECK")
add(f"target_public_html_exists: {TARGET_PUBLIC.exists()}")
if TARGET_PUBLIC.exists():
    html = TARGET_PUBLIC.read_text(encoding="utf-8", errors="replace")
    add(f"target_public_html_size: {len(html)}")
    add(f"target_public_has_cucurella_text: {'Cucurella' in html or 'Кукурелья' in html or 'cucurella' in html.lower()}")
    add(f"target_public_has_249_date_class: {'promyachik-cucurella-price-label-249__date' in html}")
    add(f"target_public_has_249_value_class: {'promyachik-cucurella-price-label-249__value' in html}")
    add(f"target_public_has_euro_symbol: {'€' in html}")
else:
    add("ERROR: target public HTML was not generated.")

ok = proc.returncode == 0 and TARGET_PUBLIC.exists()
add("")
add("DONE" if ok else "FAILED")
finish(0 if ok else 1)
