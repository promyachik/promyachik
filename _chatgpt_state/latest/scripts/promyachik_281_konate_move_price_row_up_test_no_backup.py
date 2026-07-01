from pathlib import Path
import subprocess
import datetime
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "var" / "promyachik_281_konate_move_price_row_up_test_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 281 - KONATE MOVE PRICE ROW UP TEST - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Test only on Ibrahima Konate transfer page.")
log.append("- Move chart price row upward, closer to the chart points.")
log.append("- Keep prices and hidden years unchanged.")
log.append("- Do not touch JS.")
log.append("- Do not touch content markdown.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

layout = ROOT / "layouts" / "transfers" / "single.html"
if not layout.exists():
    log.append(f"ERROR: layout not found: {layout}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

text = layout.read_text(encoding="utf-8")
old = text

start = "{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST START */}}"
end = "{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST END */}}"
block_re = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
text, removed = block_re.subn("", text)
log.append(f"removed old 281 marker blocks: {removed}")

needle = '{{ partial "transfer-player-market-value-chart.html" . }}'
if needle not in text:
    log.append("ERROR: transfer-player-market-value-chart partial call not found. File not changed.")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

style_block = """
{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST START */}}
{{- if in .RelPermalink "/transfers/ibrahima-konate-real-madrid/" -}}
<style id="promyachik-281-konate-price-row-up-test">
body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points {
  margin-top: 1px !important;
  transform: translateY(-6px) !important;
}
</style>
{{- end -}}
{{/* PROMYACHIK 281 KONATE PRICE ROW UP TEST END */}}
"""

text = text.replace(needle, needle + style_block, 1)

if text == old:
    log.append("ERROR: layout text unchanged after planned edit.")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

layout.write_text(text, encoding="utf-8")
log.append(f"CHANGED: {layout}")
log.append("inserted Konate-only CSS after chart partial")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2500:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2500:])

target = ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"
other = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/ibrahima-konate-real-madrid/")
log.append(f"target_public_html_exists: {target.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    log.append(f"target_has_281_style_id: {'promyachik-281-konate-price-row-up-test' in html}")
    log.append(f"target_has_translateY_minus_6: {'translateY(-6px)' in html}")
    ok = ok and ('promyachik-281-konate-price-row-up-test' in html) and ('translateY(-6px)' in html)

log.append(f"other_cucurella_public_html_exists: {other.exists()}")
if other.exists():
    other_html = other.read_text(encoding="utf-8", errors="ignore")
    log.append(f"other_cucurella_has_281_style_id: {'promyachik-281-konate-price-row-up-test' in other_html}")
    ok = ok and ('promyachik-281-konate-price-row-up-test' not in other_html)

log.append("")
log.append("CHECKS")
log.append("backup_created: False")
log.append("js_touched: False")
log.append("content_touched: False")
log.append(f"VERIFIED_OK: {ok}")
log.append("")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
