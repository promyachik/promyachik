from pathlib import Path
import subprocess, datetime, re, sys

root = Path(__file__).resolve().parents[1]
js = root / 'static' / 'js' / 'transfer-player-market-value-chart.js'
public_js = root / 'public' / 'js' / 'transfer-player-market-value-chart.js'
report = root / 'var' / 'promyachik_273_cucurella_hide_year_in_real_js_keep_price_no_backup_report.txt'
report.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append('PROMYACHIK 273 - CUCURELLA HIDE YEAR IN REAL JS KEEP PRICE - NO BACKUP')
log.append('=' * 100)
log.append('Time: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
log.append('Project dir: ' + str(root))
log.append('')
log.append('RULE')
log.append('- Real source from report 270 is static/js/transfer-player-market-value-chart.js')
log.append('- Hide only the small year label for player.key === "cucurella"')
log.append('- Keep strong price/value_label')
log.append('- Do not move prices')
log.append('- Do not touch CSS')
log.append('- Do not touch templates')
log.append('- Do not create backup')
log.append('- No push')
log.append('- No site opened')
log.append('')

if not js.exists():
    log.append('ERROR: JS not found: ' + str(js))
    report.write_text('\n'.join(log), encoding='utf-8')
    print('FAILED')
    print('REPORT: ' + str(report))
    sys.exit(1)

text = js.read_text(encoding='utf-8')
original = text

# Remove previous failed 271 marker block if it somehow exists, without touching labels.
text, cleanup_n = re.subn(
    r"\n?\s*/\* PROMYACHIK 271[\s\S]*?PROMYACHIK 271[\s\S]*?\*/\s*\n?",
    "\n",
    text,
)
log.append('cleanup_failed_271_marker_blocks: replacements=' + str(cleanup_n))

old_exact = """const labels = player.points.map((item) => `
            <span class="player-market-chart__point">
                <small>${escapeHTML(item.label)}</small>
                <strong>${escapeHTML(
                    item.value_label.replace(/^€\s*/, "€\u202F")
                )}</strong>
            </span>
        `).join("");"""

new_exact = """const labels = player.points.map((item) => {
            /* PROMYACHIK 273: hide year label only for Cucurella; keep price */
            const labelHTML = player.key === "cucurella"
                ? ""
                : `<small>${escapeHTML(item.label)}</small>`;
            return `
            <span class="player-market-chart__point">
                ${labelHTML}
                <strong>${escapeHTML(
                    item.value_label.replace(/^€\s*/, "€\u202F")
                )}</strong>
            </span>
        `;
        }).join("");"""

replacements = 0
if old_exact in text:
    text = text.replace(old_exact, new_exact, 1)
    replacements = 1
    log.append('edit_method: exact labels block replacement')
elif 'PROMYACHIK 273: hide year label only for Cucurella' in text:
    log.append('edit_method: already has 273 marker')
else:
    # Regex fallback for same labels block with whitespace differences.
    pattern = re.compile(
        r'const\s+labels\s*=\s*player\.points\.map\(\(item\)\s*=>\s*`\s*'
        r'<span\s+class="player-market-chart__point">\s*'
        r'<small>\$\{escapeHTML\(item\.label\)\}</small>\s*'
        r'<strong>\$\{escapeHTML\(\s*item\.value_label\.replace\(/\^€\\s\*/,\s*"€\\u202F"\s*\)\s*\)\}</strong>\s*'
        r'</span>\s*`\)\.join\(""\);',
        re.S
    )
    text, replacements = pattern.subn(new_exact, text, count=1)
    log.append('edit_method: regex labels block replacement')

log.append('labels_block_replacements: ' + str(replacements))

compact = text.replace(' ', '')
checks = {
    'has_cucurella_player_data': 'key":"cucurella"' in compact,
    'has_273_marker': 'PROMYACHIK 273: hide year label only for Cucurella' in text,
    'has_price_value_label': 'item.value_label.replace' in text,
    'has_original_small_for_other_players': '<small>${escapeHTML(item.label)}</small>' in text,
}

for k, v in checks.items():
    log.append(k + ': ' + str(v))

if not checks['has_cucurella_player_data']:
    log.append('ERROR: Cucurella player data not found in JS. File not written.')
    report.write_text('\n'.join(log), encoding='utf-8')
    print('FAILED')
    print('REPORT: ' + str(report))
    sys.exit(1)

if replacements < 1 and not checks['has_273_marker']:
    log.append('ERROR: labels block not found. File not written.')
    report.write_text('\n'.join(log), encoding='utf-8')
    print('FAILED')
    print('REPORT: ' + str(report))
    sys.exit(1)

if not checks['has_price_value_label']:
    log.append('ERROR: price code missing after edit. File not written.')
    report.write_text('\n'.join(log), encoding='utf-8')
    print('FAILED')
    print('REPORT: ' + str(report))
    sys.exit(1)

if text != original:
    js.write_text(text, encoding='utf-8')
    log.append('CHANGED: ' + str(js))
else:
    log.append('UNCHANGED: JS already contains 273 edit')

proc = subprocess.run(['hugo', '-D'], cwd=root, text=True, capture_output=True)
log.append('')
log.append('HUGO')
log.append('exit_code: ' + str(proc.returncode))
log.append('--- STDOUT tail ---')
log.append(proc.stdout[-1500:])
log.append('--- STDERR tail ---')
log.append(proc.stderr[-1500:])

log.append('')
log.append('PUBLIC JS CHECK')
log.append('public_js_exists: ' + str(public_js.exists()))
public_has_marker = False
public_has_price = False
if public_js.exists():
    ptxt = public_js.read_text(encoding='utf-8', errors='ignore')
    public_has_marker = 'PROMYACHIK 273: hide year label only for Cucurella' in ptxt
    public_has_price = 'item.value_label.replace' in ptxt
    log.append('public_js_has_273_marker: ' + str(public_has_marker))
    log.append('public_js_has_price_code: ' + str(public_has_price))

target = root / 'public' / 'transfers' / 'marc-cucurella-real-madrid' / 'index.html'
log.append('')
log.append('TARGET CHECK')
log.append('target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/')
log.append('target_public_html_exists: ' + str(target.exists()))

ok = proc.returncode == 0 and public_js.exists() and public_has_marker and public_has_price and target.exists()
log.append('VERIFIED_OK: ' + str(ok))
log.append('')
log.append('DONE' if ok else 'FAILED')
report.write_text('\n'.join(log), encoding='utf-8')
print('DONE' if ok else 'FAILED')
print('REPORT: ' + str(report))
sys.exit(0 if ok else 1)
