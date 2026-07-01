from pathlib import Path
import subprocess, datetime, sys

root = Path(__file__).resolve().parents[1]
js = root / "static" / "js" / "transfer-player-market-value-chart.js"
public_js = root / "public" / "js" / "transfer-player-market-value-chart.js"
report = root / "var" / "promyachik_274_remove_year_lines_from_runtime_chart_keep_prices_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 274 - REMOVE YEAR LINES FROM RUNTIME CHART KEEP PRICES - NO BACKUP")
log.append("=" * 100)
log.append("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
log.append("Project dir: " + str(root))
log.append("")
log.append("RULE")
log.append("- Edit only static/js/transfer-player-market-value-chart.js")
log.append("- Remove year/label line from runtime chart labels")
log.append("- Keep price/value_label strong tag")
log.append("- Do not move prices")
log.append("- Do not touch CSS")
log.append("- Do not touch templates")
log.append("- Do not create backup")
log.append("- No push")
log.append("- No site opened")
log.append("")

if not js.exists():
    log.append("ERROR: JS not found: " + str(js))
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(report))
    sys.exit(1)

text = js.read_text(encoding="utf-8")
original = text

start = text.find("const labels = player.points.map((item)")
log.append("labels_block_start_index: " + str(start))

if start < 0:
    start = text.find("const labels = player.points.map")
    log.append("labels_block_start_index_fallback: " + str(start))

if start < 0:
    log.append("ERROR: labels block start not found. File not changed.")
    log.append("SNIPPET SEARCH TOKENS:")
    for token in ["player-market-chart__point", "item.value_label", "item.label", "value_label"]:
        idx = text.find(token)
        log.append(token + ": " + str(idx))
        if idx >= 0:
            log.append(text[max(0, idx-300):idx+500])
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(report))
    sys.exit(1)

end_marker = ").join(\"\");"
end = text.find(end_marker, start)
log.append("labels_block_end_index: " + str(end))

if end < 0:
    log.append("ERROR: labels block end marker not found. File not changed.")
    log.append("SNIPPET AROUND START:")
    log.append(text[start:start+1500])
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(report))
    sys.exit(1)

end += len(end_marker)
old_block = text[start:end]
log.append("")
log.append("OLD LABELS BLOCK SNIPPET")
log.append(old_block[:2000])

for token in ["player-market-chart__point", "item.value_label", "<small>", "item.label"]:
    log.append("old_block_has_" + token.replace(" ", "_") + ": " + str(token in old_block))

if "item.value_label" not in old_block:
    log.append("ERROR: labels block does not contain item.value_label. File not changed.")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(report))
    sys.exit(1)

new_block = '''const labels = player.points.map((item) => {
            /* PROMYACHIK 274: remove year line; keep price only */
            const marketPriceLabel = escapeHTML(
                item.value_label.replace(/^€\\s*/, "€\\u202F")
            );

            return `
            <span class="player-market-chart__point">
                <strong>${marketPriceLabel}</strong>
            </span>
        `;
        }).join("");'''

text2 = text[:start] + new_block + text[end:]

checks = {
    "new_has_274_marker": "PROMYACHIK 274: remove year line" in text2,
    "new_has_price_value_label": "item.value_label" in text2,
    "new_labels_block_has_no_small": "<small>${escapeHTML(item.label)}</small>" not in text2[start:start+len(new_block)+100],
}
for k, v in checks.items():
    log.append(k + ": " + str(v))

if not all(checks.values()):
    log.append("ERROR: safety check failed. File not changed.")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(report))
    sys.exit(1)

if text2 != original:
    js.write_text(text2, encoding="utf-8")
    log.append("CHANGED: " + str(js))
else:
    log.append("UNCHANGED: JS already has target block")

proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("exit_code: " + str(proc.returncode))
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2000:])

log.append("")
log.append("PUBLIC JS CHECK")
log.append("public_js_exists: " + str(public_js.exists()))
public_has_marker = False
public_has_price = False
public_has_small_old = False
if public_js.exists():
    ptext = public_js.read_text(encoding="utf-8", errors="ignore")
    public_has_marker = "PROMYACHIK 274: remove year line" in ptext
    public_has_price = "item.value_label" in ptext
    public_has_small_old = "<small>${escapeHTML(item.label)}</small>" in ptext
    log.append("public_js_has_274_marker: " + str(public_has_marker))
    log.append("public_js_has_price_value_label: " + str(public_has_price))
    log.append("public_js_has_old_small_label_line: " + str(public_has_small_old))

target = root / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
log.append("target_public_html_exists: " + str(target.exists()))

ok = proc.returncode == 0 and public_js.exists() and public_has_marker and public_has_price and (not public_has_small_old) and target.exists()
log.append("VERIFIED_OK: " + str(ok))
log.append("")
log.append("DONE" if ok else "FAILED")
report.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print("REPORT: " + str(report))
sys.exit(0 if ok else 1)
