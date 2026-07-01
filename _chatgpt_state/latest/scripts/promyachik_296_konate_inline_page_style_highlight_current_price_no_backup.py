from pathlib import Path
import subprocess
import datetime
import re
import sys

ROOT = Path.cwd()
REPORT = ROOT / "var" / "promyachik_296_konate_inline_page_style_highlight_current_price_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

KONATE = ROOT / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
LAYOUT = ROOT / "layouts" / "transfers" / "single.html"
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"

START = "<!-- PROMYACHIK 296 KONATE INLINE CURRENT PRICE STYLE START -->"
END = "<!-- PROMYACHIK 296 KONATE INLINE CURRENT PRICE STYLE END -->"

log = []
log.append("PROMYACHIK 296 - KONATE INLINE PAGE STYLE HIGHLIGHT CURRENT PRICE - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Test only Konate page by placing inline style inside Konate content file.")
log.append("- Do not touch Ramos.")
log.append("- No backup.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- Remove failed 294/295 test leftovers if present.")
log.append("")

changed = []

def write_fail(msg: str, code: int = 1):
    log.append(msg)
    log.append("")
    log.append("FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(code)

if not KONATE.exists():
    write_fail(f"ERROR: Konate content not found: {KONATE}")

# Clean old ineffective 294 blocks from JS/CSS if present.
def remove_css_js_block(text: str, marker_num: str):
    start = f"/* PROMYACHIK {marker_num} KONATE CURRENT PRICE HIGHLIGHT TEST START */"
    end = f"/* PROMYACHIK {marker_num} KONATE CURRENT PRICE HIGHLIGHT TEST END */"
    rx = re.compile(r"\n?" + re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    return rx.subn("\n", text)

for p in [JS, CSS]:
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="ignore")
        txt2, n294 = remove_css_js_block(txt, "294")
        if txt2 != txt:
            p.write_text(txt2, encoding="utf-8")
            changed.append(str(p.relative_to(ROOT)))
        log.append(f"clean 294 leftovers in {p.relative_to(ROOT)}: {n294}")
    else:
        log.append(f"skip optional missing file: {p.relative_to(ROOT)}")

# Clean failed 295 layout block if it was written before failing.
if LAYOUT.exists():
    layout = LAYOUT.read_text(encoding="utf-8", errors="ignore")
    old_layout = layout
    layout, n295 = re.subn(
        r"\n?\{\{/\* PROMYACHIK 295 KONATE CURRENT PRICE HIGHLIGHT TEST START \*/\}\}.*?\{\{/\* PROMYACHIK 295 KONATE CURRENT PRICE HIGHLIGHT TEST END \*/\}\}\n?",
        "\n",
        layout,
        flags=re.S,
    )
    log.append(f"clean 295 layout leftovers: {n295}")
    if layout != old_layout:
        LAYOUT.write_text(layout, encoding="utf-8")
        changed.append(str(LAYOUT.relative_to(ROOT)))
else:
    log.append(f"skip missing layout: {LAYOUT}")

text = KONATE.read_text(encoding="utf-8", errors="ignore")
old = text

# Remove previous 296 block on rerun.
text, old296 = re.subn(re.escape(START) + r".*?" + re.escape(END), "", text, flags=re.S)
log.append(f"removed old 296 blocks: {old296}")

style_block = f"""
{START}
<style>
  /* Konate-only inline page test. This lives only in the Konate markdown file,
     so Ramos and other players are not affected. */
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points > *:last-child {{
    position: relative !important;
    z-index: 80 !important;
  }}

  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child strong,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points > *:last-child strong,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child .player-market-chart__value,
  body.transfer-page .player-market-chart:not(.player-market-chart--enlarged) .player-market-chart__points .player-market-chart__point:last-child .player-market-chart__point-value {{
    color: #f3d45b !important;
    -webkit-text-fill-color: #f3d45b !important;
    text-shadow: 0 0 14px rgba(243, 212, 91, 0.72), 0 0 28px rgba(243, 212, 91, 0.30) !important;
    transform: translateY(-10px) scale(1.08) !important;
    transform-origin: center center !important;
    display: inline-block !important;
    position: relative !important;
    z-index: 81 !important;
    white-space: nowrap !important;
    font-weight: 950 !important;
  }}
</style>
{END}
""".strip()

# Put style right after front matter, so it is early in page HTML but after site CSS when rendered in content.
if text.startswith("---"):
    second = text.find("\n---", 3)
    if second != -1:
        insert_at = second + len("\n---")
        text = text[:insert_at] + "\n\n" + style_block + "\n" + text[insert_at:]
        log.append("injected: after front matter")
    else:
        text = style_block + "\n\n" + text
        log.append("injected: top fallback, malformed front matter")
else:
    text = style_block + "\n\n" + text
    log.append("injected: file top, no front matter marker")

if text == old:
    write_fail("ERROR: Konate content unchanged before Hugo.")

KONATE.write_text(text, encoding="utf-8")
changed.append(str(KONATE.relative_to(ROOT)))
log.append(f"CHANGED: {KONATE}")

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
ramos = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/ibrahima-konate-real-madrid/")
log.append(f"target_html_exists: {target.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    has_marker = "PROMYACHIK 296 KONATE INLINE CURRENT PRICE STYLE START" in html
    has_yellow = "#f3d45b" in html
    has_last_child = "player-market-chart__point:last-child" in html
    log.append(f"target_has_296_marker: {has_marker}")
    log.append(f"target_has_yellow: {has_yellow}")
    log.append(f"target_has_last_child_selector: {has_last_child}")
    ok = ok and has_marker and has_yellow and has_last_child

if ramos.exists():
    rh = ramos.read_text(encoding="utf-8", errors="ignore")
    log.append(f"ramos_has_296_marker: {'PROMYACHIK 296 KONATE INLINE CURRENT PRICE STYLE START' in rh}")

log.append("")
log.append("CHANGED FILES")
for f in sorted(set(changed)):
    log.append(f"- {f}")
log.append("backup_created: False")
log.append("push_made: False")
log.append(f"VERIFIED_OK: {ok}")
log.append("")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")

print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
