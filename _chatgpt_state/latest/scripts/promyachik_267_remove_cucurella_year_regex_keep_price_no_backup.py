from pathlib import Path
import re
import subprocess
import datetime
import sys

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
REPORT = ROOT / "var" / "promyachik_267_remove_cucurella_year_regex_keep_price_no_backup_report.txt"
TARGET = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

REPORT.parent.mkdir(parents=True, exist_ok=True)
log = []
log.append("PROMYACHIK 267 - REMOVE CUCURELLA YEAR REGEX KEEP PRICE - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- No backup created.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- Edit only layouts/partials/transfer-player-market-value-chart.html")
log.append("- Remove Cucurella date/year token by regex, not by exact full line.")
log.append("- Keep Cucurella value_label price token.")
log.append("")

def finish(ok: bool):
    log.append("")
    log.append("DONE" if ok else "FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(0 if ok else 1)

if not PARTIAL.exists():
    log.append(f"ERROR: partial not found: {PARTIAL}")
    finish(False)

text = PARTIAL.read_text(encoding="utf-8", errors="strict")
original = text

price_token = r"{{ $promyachikCucPoint249.value_label }}"
price_regex = re.compile(r"\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\}")
if not price_regex.search(text):
    log.append("ERROR: Cucurella price token $promyachikCucPoint249.value_label not found before edit. File not changed.")
    finish(False)

patterns = [
    (
        "default date/date_label token",
        re.compile(r"\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}\s*", re.S),
        ""
    ),
    (
        "direct date_label token",
        re.compile(r"\{\{\s*\$promyachikCucPoint249\.date_label\s*\}\}\s*", re.S),
        ""
    ),
    (
        "direct date token",
        re.compile(r"\{\{\s*\$promyachikCucPoint249\.date\s*\}\}\s*", re.S),
        ""
    ),
]

total = 0
for name, rx, repl in patterns:
    text, n = rx.subn(repl, text)
    log.append(f"{name}: replacements={n}")
    total += n

log.append("")
log.append("CHECK BEFORE WRITE")
log.append(f"replacements_total: {total}")
log.append(f"price_token_still_exists: {bool(price_regex.search(text))}")

if total <= 0:
    log.append("ERROR: no Cucurella date/year token matched. File not changed.")
    finish(False)

if not price_regex.search(text):
    log.append("ERROR: price token disappeared after edit. File not changed.")
    finish(False)

if text == original:
    log.append("ERROR: text unchanged after replacements. File not changed.")
    finish(False)

PARTIAL.write_text(text, encoding="utf-8")
log.append(f"CHANGED: {PARTIAL}")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append(f"exit_code: {proc.returncode}")
log.append("--- stdout tail ---")
log.append(proc.stdout[-2000:])
log.append("--- stderr tail ---")
log.append(proc.stderr[-2000:])

log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
log.append(f"target_public_html: {TARGET}")
log.append(f"target_public_html_exists: {TARGET.exists()}")
if TARGET.exists():
    html = TARGET.read_text(encoding="utf-8", errors="ignore")
    log.append(f"target_has_price_symbol: {'€' in html}")
    log.append(f"target_has_cucurella_slug: {'marc-cucurella-real-madrid' in html}")

ok = proc.returncode == 0 and TARGET.exists()
finish(ok)
