from pathlib import Path
import subprocess
import datetime
import re
import sys

root = Path(__file__).resolve().parents[1]
report = root / "var" / "promyachik_287_fix_ramos_graph_layout_to_working_grid_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 287 - FIX RAMOS GRAPH LAYOUT TO WORKING GRID - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {root}")
log.append("")
log.append("RULE")
log.append("- Fix only the visual Ramos chart label layout after the page schema rebuild.")
log.append("- Do not touch JS.")
log.append("- Do not touch common CSS.")
log.append("- Do not rebuild all content again.")
log.append("- Add a Ramos-page-only layout guard in layouts/transfers/single.html.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

single = root / "layouts" / "transfers" / "single.html"
target_md = root / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"

for p in [single, target_md]:
    log.append(f"exists {p.relative_to(root)}: {p.exists()}")

if not single.exists():
    log.append("ERROR: layouts/transfers/single.html not found")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {report}")
    sys.exit(1)

text = single.read_text(encoding="utf-8")
old = text

start = "{{/* PROMYACHIK 287 RAMOS GRAPH LAYOUT FIX START */}}"
end = "{{/* PROMYACHIK 287 RAMOS GRAPH LAYOUT FIX END */}}"
text, removed = re.subn(re.escape(start) + r".*?" + re.escape(end) + r"\s*", "", text, flags=re.S)
log.append(f"removed old 287 block: {removed}")

block = '''{{/* PROMYACHIK 287 RAMOS GRAPH LAYOUT FIX START */}}
{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }}
<style id="promyachik-287-ramos-graph-layout-fix">
  body.transfer-page .player-market-chart .player-market-chart__points {
    position: relative !important;
    left: auto !important;
    right: auto !important;
    top: auto !important;
    bottom: auto !important;
    display: grid !important;
    grid-template-columns: repeat(var(--market-point-count), minmax(0, 1fr)) !important;
    align-items: start !important;
    gap: 4px !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin-top: -7px !important;
    padding: 0 3px !important;
    transform: none !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    z-index: 7 !important;
  }

  body.transfer-page .player-market-chart .player-market-chart__point {
    position: static !important;
    left: auto !important;
    right: auto !important;
    top: auto !important;
    bottom: auto !important;
    display: grid !important;
    grid-template-rows: auto !important;
    min-width: 0 !important;
    width: auto !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    transform: none !important;
    pointer-events: none !important;
    overflow: visible !important;
  }

  body.transfer-page .player-market-chart .player-market-chart__point small {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
  }

  body.transfer-page .player-market-chart .player-market-chart__point strong {
    position: static !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    margin: 0 auto !important;
    padding: 0 !important;
    color: #f1f3f5 !important;
    font-size: 9px !important;
    line-height: 1.08 !important;
    white-space: nowrap !important;
    text-align: center !important;
    transform: none !important;
  }
</style>
{{ end }}
{{/* PROMYACHIK 287 RAMOS GRAPH LAYOUT FIX END */}}
'''

anchor = '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}'
if anchor in text:
    text = text.replace(anchor, block + "\n" + anchor, 1)
    inserted = "before cucurella move-prices partial"
else:
    text = text.rstrip() + "\n" + block + "\n"
    inserted = "end of layouts/transfers/single.html"

changed = text != old
if changed:
    single.write_text(text, encoding="utf-8")

log.append(f"CHANGED layouts/transfers/single.html: {changed}")
log.append(f"inserted 287 block: {inserted}")
log.append("")

proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2000:])
log.append("")

target_html = root / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
log.append(f"target_html_exists: {target_html.exists()}")
if target_html.exists():
    html = target_html.read_text(encoding="utf-8", errors="ignore")
    log.append(f"target_has_287_style: {'promyachik-287-ramos-graph-layout-fix' in html}")
    log.append(f"target_has_player_market_chart: {'player-market-chart' in html}")
    log.append(f"target_has_price_symbols: {'€' in html}")
else:
    html = ""

verified = (
    changed
    and proc.returncode == 0
    and target_html.exists()
    and 'promyachik-287-ramos-graph-layout-fix' in html
    and 'player-market-chart' in html
)
log.append("")
log.append(f"VERIFIED_OK: {verified}")
log.append("NO BACKUP CREATED.")
log.append("NO PUSH MADE.")
log.append("NO SITE OPENED.")
log.append("DONE" if verified else "FAILED")
report.write_text("\n".join(log), encoding="utf-8")

print("DONE" if verified else "FAILED")
print(f"REPORT: {report}")
sys.exit(0 if verified else 1)
