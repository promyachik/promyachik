from pathlib import Path
import subprocess
import datetime
import re

ROOT = Path.cwd()
REPORT = ROOT / "var" / "promyachik_295_konate_test_highlight_current_price_layout_css_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

LAYOUT = ROOT / "layouts" / "transfers" / "single.html"
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"

START = "{{/* PROMYACHIK 295 KONATE CURRENT PRICE HIGHLIGHT TEST START */}}"
END = "{{/* PROMYACHIK 295 KONATE CURRENT PRICE HIGHLIGHT TEST END */}}"

log = []
log.append("PROMYACHIK 295 - KONATE CURRENT PRICE HIGHLIGHT VIA LAYOUT CSS - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Test only Konate page by RelPermalink condition in layouts/transfers/single.html.")
log.append("- No backup.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- Do not touch Ramos content/page.")
log.append("- Remove old ineffective 294 helper blocks if present.")
log.append("")

if not LAYOUT.exists():
    log.append(f"ERROR: layout not found: {LAYOUT}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

changed = []

# Remove ineffective 294 helper blocks from JS/CSS if present.
def remove_between(text: str, start: str, end: str):
    rx = re.compile(r"\n?/\*\s*" + re.escape(start) + r"\s*\*/.*?/\*\s*" + re.escape(end) + r"\s*\*/\n?", re.S)
    new_text, n = rx.subn("\n", text)
    return new_text, n

# Exact 294 markers are simple block comments.
old_294_start = "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START"
old_294_end = "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST END"
for path in [JS, CSS]:
    if path.exists():
        txt = path.read_text(encoding="utf-8", errors="ignore")
        new_txt, n = remove_between(txt, old_294_start, old_294_end)
        log.append(f"removed old 294 blocks from {path.relative_to(ROOT)}: {n}")
        if new_txt != txt:
            path.write_text(new_txt, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    else:
        log.append(f"skip missing optional file: {path}")

layout = LAYOUT.read_text(encoding="utf-8", errors="ignore")
old_layout = layout

# Remove old 295 if re-run.
layout, removed_295 = re.subn(re.escape(START) + r".*?" + re.escape(END), "", layout, flags=re.S)
log.append(f"removed old 295 layout blocks: {removed_295}")

style_block = f"""
{START}
{{{{- if in .RelPermalink "/transfers/ibrahima-konate-real-madrid/" -}}}}
<style>
  /* Konate-only test: make the current/last price look like the good Ramos idea.
     Layout-only CSS: no DOM deletion, no runtime coordinate recalculation. */
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child {{
    z-index: 60 !important;
  }}

  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child strong,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child .player-market-chart__value,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child .player-market-chart__point-value {{
    color: #f3d45b !important;
    -webkit-text-fill-color: #f3d45b !important;
    text-shadow: 0 0 14px rgba(243, 212, 91, 0.70), 0 0 26px rgba(243, 212, 91, 0.28) !important;
    transform: translateY(-10px) scale(1.08) !important;
    transform-origin: center center !important;
    display: inline-block !important;
    position: relative !important;
    z-index: 61 !important;
    white-space: nowrap !important;
    font-weight: 950 !important;
  }}
</style>
{{{{- end -}}}}
{END}
""".strip()

# Prefer injecting before </head> if present, otherwise before </body>, otherwise append.
if "</head>" in layout:
    layout = layout.replace("</head>", style_block + "\n</head>", 1)
    injected_at = "before </head>"
elif "</body>" in layout:
    layout = layout.replace("</body>", style_block + "\n</body>", 1)
    injected_at = "before </body>"
else:
    layout = layout.rstrip() + "\n" + style_block + "\n"
    injected_at = "append end of file"

if layout != old_layout:
    LAYOUT.write_text(layout, encoding="utf-8")
    changed.append(str(LAYOUT.relative_to(ROOT)))
    log.append(f"CHANGED: {LAYOUT}")
    log.append(f"injected_at: {injected_at}")
else:
    log.append("UNCHANGED: layout text unchanged")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2000:])

target = ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/ibrahima-konate-real-madrid/")
log.append(f"target_html_exists: {target.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    has_295 = "Konate-only test: make the current/last price" in html
    has_yellow = "#f3d45b" in html
    has_selector = ".player-market-chart__point:last-child" in html
    log.append(f"target_has_295_css: {has_295}")
    log.append(f"target_has_yellow: {has_yellow}")
    log.append(f"target_has_last_child_selector: {has_selector}")
    ok = ok and has_295 and has_yellow and has_selector

ramos_target = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
if ramos_target.exists():
    rh = ramos_target.read_text(encoding="utf-8", errors="ignore")
    log.append(f"ramos_target_has_295_css: {'Konate-only test: make the current/last price' in rh}")

log.append("")
log.append("CHANGED FILES")
for f in changed:
    log.append(f"- {f}")
log.append(f"EFFECTIVE_CHANGED_FILES: {len(changed)}")
log.append("backup_created: False")
log.append("push_made: False")
log.append(f"VERIFIED_OK: {ok}")
log.append("")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
