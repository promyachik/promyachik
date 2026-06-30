from pathlib import Path
import re
import subprocess
import datetime
import sys

ROOT = Path.cwd()
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
TARGET_PUBLIC = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
REPORT = ROOT / "var" / "promyachik_264_cucurella_remove_inline_date_keep_price_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 264 - CUCURELLA REMOVE INLINE DATE KEEP PRICE - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Remove only Cucurella inline date/year token before the price.")
log.append("- Keep Cucurella value_label price token.")
log.append("- Do not move prices in this package.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")
log.append("TARGET")
log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
log.append(f"target_public_html: {TARGET_PUBLIC}")
log.append("")

try:
    if not PARTIAL.exists():
        log.append(f"ERROR: partial not found: {PARTIAL}")
        REPORT.write_text("\n".join(log), encoding="utf-8")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        sys.exit(1)

    text = PARTIAL.read_text(encoding="utf-8")
    original = text

    # The current real Cucurella branch is inline:
    # {{ default $promyachikCucPoint249.date $promyachikCucPoint249.date_label }}  {{ $promyachikCucPoint249.value_label }}
    # Replace only the date/default token, keep the price token.
    patterns = [
        (
            "remove exact Cucurella default date/date_label before value_label",
            re.compile(
                r"\{\{\s*default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label\s*\}\}\s+(\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})"
            ),
            r"\1",
        ),
        (
            "remove Cucurella direct date before value_label",
            re.compile(
                r"\{\{\s*\$promyachikCucPoint249\.date\s*\}\}\s+(\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})"
            ),
            r"\1",
        ),
        (
            "remove Cucurella direct date_label before value_label",
            re.compile(
                r"\{\{\s*\$promyachikCucPoint249\.date_label\s*\}\}\s+(\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\})"
            ),
            r"\1",
        ),
    ]

    total = 0
    for name, rx, repl in patterns:
        text, n = rx.subn(repl, text)
        total += n
        log.append(f"{name}: replacements={n}")

    price_token_still_exists = "{{ $promyachikCucPoint249.value_label }}" in text or "$promyachikCucPoint249.value_label" in text
    date_before_price_still_exists = bool(re.search(
        r"\{\{\s*(?:default\s+\$promyachikCucPoint249\.date\s+\$promyachikCucPoint249\.date_label|\$promyachikCucPoint249\.(?:date|date_label))\s*\}\}\s+\{\{\s*\$promyachikCucPoint249\.value_label\s*\}\}",
        text,
    ))

    log.append("")
    log.append("CHECKS BEFORE WRITE")
    log.append(f"replacements_total: {total}")
    log.append(f"price_token_still_exists: {price_token_still_exists}")
    log.append(f"date_before_price_still_exists: {date_before_price_still_exists}")

    if total <= 0:
        log.append("ERROR: no matching Cucurella inline date-before-price token found. File not written.")
        REPORT.write_text("\n".join(log), encoding="utf-8")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        sys.exit(1)

    if not price_token_still_exists:
        log.append("ERROR: price token missing after edit. File not written.")
        REPORT.write_text("\n".join(log), encoding="utf-8")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        sys.exit(1)

    PARTIAL.write_text(text, encoding="utf-8")
    log.append(f"CHANGED: {PARTIAL}")

    proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
    log.append("")
    log.append("HUGO")
    log.append("COMMAND: hugo -D")
    log.append(f"EXIT_CODE: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2500:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2500:])

    target_exists = TARGET_PUBLIC.exists()
    log.append("")
    log.append("TARGET CHECK")
    log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
    log.append(f"target_public_html_exists: {target_exists}")
    log.append(f"target_public_html: {TARGET_PUBLIC}")

    if target_exists:
        html = TARGET_PUBLIC.read_text(encoding="utf-8", errors="ignore")
        log.append(f"target_html_bytes: {len(html.encode('utf-8', errors='ignore'))}")
        # We do not search generic year numbers here because chart axes/other content may legally contain years.
        log.append(f"target_html_has_euro: {'€' in html}")

    ok = proc.returncode == 0 and target_exists
    log.append("")
    log.append("NO BACKUP CREATED.")
    log.append("NO PUSH MADE.")
    log.append("NO SITE OPENED.")
    log.append("DONE" if ok else "FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")

    print("DONE" if ok else "FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(0 if ok else 1)

except Exception as e:
    log.append("")
    log.append(f"EXCEPTION: {type(e).__name__}: {e}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise
