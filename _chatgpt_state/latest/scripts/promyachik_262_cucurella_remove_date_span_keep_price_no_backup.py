from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

ROOT = Path.cwd()
REPORT = ROOT / "var" / "promyachik_262_cucurella_remove_date_span_keep_price_no_backup_report.txt"
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
PUBLIC_CUC = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

report_lines = []

def log(s=""):
    print(s)
    report_lines.append(str(s))

def write_report():
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"REPORT_WRITE_FAILED: {e}")

log("PROMYACHIK 262 - CUCURELLA REMOVE DATE SPAN KEEP PRICE - NO BACKUP")
log("=" * 100)
log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Project dir: {ROOT}")
log("")
log("RULE")
log("- Remove Cucurella date/year span from the 249 price label layer.")
log("- Keep Cucurella price value strong visible.")
log("- Do not move prices in this package.")
log("- Do not create any backup folder or backup file.")
log("- No push.")
log("- No site opened.")
log("")

ok = True
if not PARTIAL.exists():
    log(f"ERROR: partial not found: {PARTIAL}")
    ok = False
else:
    text = PARTIAL.read_text(encoding="utf-8", errors="replace")
    original = text
    log(f"partial exists: True")
    log(f"partial size before: {len(text)}")

    # Work only inside the existing Cucurella 249 block when possible.
    start_marker = "<!-- PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT START -->"
    end_marker = "<!-- PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT END -->"
    start = text.find(start_marker)
    end = text.find(end_marker)
    replacements = 0
    strategy = "none"

    date_span_re = re.compile(
        r"\n?\s*<span\s+class=[\"']promyachik-cucurella-price-label-249__date[\"']>\s*.*?\s*</span>\s*",
        re.IGNORECASE | re.DOTALL,
    )

    if start != -1 and end != -1 and end > start:
        block = text[start:end]
        new_block, replacements = date_span_re.subn("\n", block)
        if replacements > 0:
            text = text[:start] + new_block + text[end:]
            strategy = "removed exact Cucurella 249 date span inside marker block"
        else:
            strategy = "Cucurella 249 marker found, date span regex found 0"
    else:
        strategy = "Cucurella 249 marker block not found, trying global exact class"
        text, replacements = date_span_re.subn("\n", text)
        if replacements > 0:
            strategy = "removed exact Cucurella 249 date span globally"

    log(f"start_marker_found: {start != -1}")
    log(f"end_marker_found: {end != -1}")
    log(f"date_span_replacements: {replacements}")
    log(f"strategy: {strategy}")

    value_class_present_after = "promyachik-cucurella-price-label-249__value" in text
    value_label_present_after = "value_label" in text
    date_class_present_after = "promyachik-cucurella-price-label-249__date" in text
    log(f"value_class_present_after: {value_class_present_after}")
    log(f"value_label_present_after: {value_label_present_after}")
    log(f"date_class_present_after: {date_class_present_after}")

    if replacements <= 0:
        log("ERROR: no Cucurella date span removed; file not written.")
        ok = False
    elif not value_class_present_after or not value_label_present_after:
        log("ERROR: price value marker missing after edit; file not written.")
        ok = False
    else:
        PARTIAL.write_text(text, encoding="utf-8", newline="\n")
        log("CHANGED: layouts/partials/transfer-player-market-value-chart.html")
        log(f"partial size after: {len(text)}")

if ok:
    log("")
    log("HUGO")
    log("COMMAND: hugo -D")
    try:
        proc = subprocess.run(["hugo", "-D"], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except Exception as e:
        log(f"ERROR: hugo failed to start: {e}")
        ok = False
        proc = None
    if proc is not None:
        log(f"EXIT_CODE: {proc.returncode}")
        log("--- STDOUT tail ---")
        log("\n".join(proc.stdout.splitlines()[-20:]))
        log("--- STDERR tail ---")
        log("\n".join(proc.stderr.splitlines()[-20:]))
        if proc.returncode != 0:
            ok = False

if ok:
    log("")
    log("PUBLIC CUCURELLA CHECK")
    if PUBLIC_CUC.exists():
        public_text = PUBLIC_CUC.read_text(encoding="utf-8", errors="replace")
        has_date_class = "promyachik-cucurella-price-label-249__date" in public_text
        has_value_class = "promyachik-cucurella-price-label-249__value" in public_text
        log(f"public_cucurella_exists: True")
        log(f"public_has_cucurella_date_class: {has_date_class}")
        log(f"public_has_cucurella_value_class: {has_value_class}")
        if has_date_class or not has_value_class:
            ok = False
    else:
        log(f"public_cucurella_exists: False ({PUBLIC_CUC})")
        ok = False

log("")
log("CHECKS")
log("backup_created: False")
log(f"verified_ok: {ok}")

if ok:
    log("")
    log("DONE")
    write_report()
    print(f"REPORT: {REPORT}")
    sys.exit(0)
else:
    log("")
    log("FAILED")
    write_report()
    print(f"REPORT: {REPORT}")
    sys.exit(1)
