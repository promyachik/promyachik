from pathlib import Path
import re
import subprocess
import datetime
import sys

PROJECT = Path(__file__).resolve().parents[1]
PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
TARGET_HTML = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
REPORT = PROJECT / "var" / "promyachik_265_cucurella_remove_date_from_real_rel_branch_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
def add(s=""):
    log.append(str(s))

def write_report():
    REPORT.write_text("\n".join(log), encoding="utf-8")

add("PROMYACHIK 265 - CUCURELLA REMOVE DATE FROM REAL RELPERMALINK BRANCH - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {PROJECT}")
add("")
add("RULE")
add("- Work only with real target URL branch: /transfers/marc-cucurella-real-madrid/")
add("- Remove year/date token only.")
add("- Keep price/value_label token.")
add("- Do not move prices.")
add("- Do not edit CSS.")
add("- Do not edit JS.")
add("- Do not edit markdown content.")
add("- Do not create backup folder or backup file.")
add("- No push.")
add("- No site opened.")
add("")

if not PARTIAL.exists():
    add(f"ERROR: partial not found: {PARTIAL}")
    write_report()
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

text = PARTIAL.read_text(encoding="utf-8", errors="ignore")
old_text = text

target_rel = '/transfers/marc-cucurella-real-madrid/'
start = text.find(target_rel)
add("TARGET CHECK BEFORE")
add(f"target_relpermalink_token_found: {start >= 0}")
add(f"target_relpermalink_token_index: {start}")

if start < 0:
    add("ERROR: target RelPermalink token not found in partial. File not written.")
    write_report()
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

# Expand to the surrounding Hugo if/else branch for Cucurella.
branch_if = text.rfind("{{ if", 0, start)
branch_else = text.find("{{ else }}", start)
if branch_if < 0:
    branch_if = max(0, start - 1000)
if branch_else < 0:
    branch_else = min(len(text), start + 5000)

branch = text[branch_if:branch_else]
add(f"branch_if_index: {branch_if}")
add(f"branch_else_index: {branch_else}")
add(f"branch_length: {len(branch)}")
add(f"branch_has_value_label_before: {'value_label' in branch}")
add(f"branch_has_date_default_before: {'default $promyachikCucPoint249.date $promyachikCucPoint249.date_label' in branch}")
add("")

new_branch = branch
replacements_total = 0

# Case 1: the exact current inline line seen in GitHub state.
exact = "{{ default $promyachikCucPoint249.date $promyachikCucPoint249.date_label }}  {{ $promyachikCucPoint249.value_label }}"
if exact in new_branch:
    new_branch = new_branch.replace(exact, "{{ $promyachikCucPoint249.value_label }}")
    replacements_total += 1
    add("replace exact inline date+price: replacements=1")
else:
    add("replace exact inline date+price: replacements=0")

# Case 2: date token followed by price token with arbitrary whitespace/newlines.
rx_inline = re.compile(
    r"\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}\s*(?=\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})",
    re.S,
)
new_branch, n = rx_inline.subn("", new_branch)
replacements_total += n
add(f"remove inline date token before value_label: replacements={n}")

# Case 3: date span/class if it exists locally.
rx_span = re.compile(
    r"\s*<span\s+class=[\"']promyachik-cucurella-price-label-249__date[\"']\s*>\s*.*?\s*</span>\s*",
    re.S,
)
new_branch, n = rx_span.subn("\n", new_branch)
replacements_total += n
add(f"remove cucurella 249 date span: replacements={n}")

# Case 4: any single Hugo default date token in Cucurella branch.
rx_any_date = re.compile(
    r"\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}\s*",
    re.S,
)
new_branch, n = rx_any_date.subn("", new_branch)
replacements_total += n
add(f"remove any remaining cucurella default date token: replacements={n}")

# Safety: never remove value label.
value_before = "value_label" in branch
value_after = "value_label" in new_branch
remaining_date_token = "default $promyachikCucPoint249.date $promyachikCucPoint249.date_label" in new_branch
add("")
add("EDIT CHECK")
add(f"replacements_total: {replacements_total}")
add(f"value_label_before: {value_before}")
add(f"value_label_after: {value_after}")
add(f"remaining_cucurella_default_date_token_in_branch: {remaining_date_token}")

if replacements_total <= 0:
    add("ERROR: no Cucurella date token matched. File not written.")
    write_report()
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

if not value_before or not value_after:
    add("ERROR: value_label missing before/after edit. File not written.")
    write_report()
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

if remaining_date_token:
    add("ERROR: Cucurella default date token still remains in target branch. File not written.")
    write_report()
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

text = text[:branch_if] + new_branch + text[branch_else:]

# Add a harmless HTML marker inside the target branch for public HTML verification, only once.
marker = "PROMYACHIK_265_CUCURELLA_DATE_REMOVED_KEEP_PRICE"
if marker not in text:
    insert_at = text.find(target_rel)
    close_if_line = text.find("}}", insert_at)
    if close_if_line >= 0:
        close_if_line += 2
        text = text[:close_if_line] + f"\n<!-- {marker} -->" + text[close_if_line:]
        add("inserted public verification marker: yes")
    else:
        add("inserted public verification marker: no")
else:
    add("inserted public verification marker: already_exists")

PARTIAL.write_text(text, encoding="utf-8")
add(f"CHANGED: {PARTIAL}")
add("")

# Build Hugo.
proc = subprocess.run(["hugo", "-D"], cwd=PROJECT, text=True, capture_output=True, encoding="utf-8", errors="replace")
add("HUGO")
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-2500:])
add("--- STDERR tail ---")
add(proc.stderr[-2500:])
add("")

# Target public HTML verification.
add("TARGET CHECK AFTER")
add("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
add(f"target_public_html: {TARGET_HTML}")
add(f"target_public_html_exists: {TARGET_HTML.exists()}")
html_has_marker = False
html_has_price_symbol = False
html_has_player = False
if TARGET_HTML.exists():
    html = TARGET_HTML.read_text(encoding="utf-8", errors="ignore")
    html_has_marker = marker in html
    html_has_price_symbol = "€" in html or "£" in html
    html_has_player = "Cucurella" in html or "Кукурель" in html
add(f"target_html_has_265_marker: {html_has_marker}")
add(f"target_html_has_price_symbol: {html_has_price_symbol}")
add(f"target_html_has_cucurella_name: {html_has_player}")
add(f"backup_created: False")

ok = (
    proc.returncode == 0
    and TARGET_HTML.exists()
    and html_has_marker
    and html_has_price_symbol
    and html_has_player
)
add("")
add("VERIFIED_OK: " + ("True" if ok else "False"))
add("DONE" if ok else "FAILED")
write_report()

print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
sys.exit(0 if ok else 1)
