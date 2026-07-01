from pathlib import Path
import subprocess
import datetime
import re
import sys

root = Path(__file__).resolve().parents[1]
report = root / "var" / "promyachik_271_cucurella_hide_year_runtime_js_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 271 - CUCURELLA HIDE YEAR RUNTIME JS - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {root}")
log.append("")
log.append("RULE")
log.append("- Hide only visible year/date labels in the Cucurella dynamic value chart.")
log.append("- Keep visible euro price labels.")
log.append("- Do not move prices in this package.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- Work with the real source found by report 270: static/js/transfer-player-market-value-chart.js")
log.append("")

js_path = root / "static" / "js" / "transfer-player-market-value-chart.js"
if not js_path.exists():
    log.append(f"ERROR: JS source not found: {js_path}")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {report}")
    sys.exit(1)

text = js_path.read_text(encoding="utf-8", errors="ignore")
old_text = text

start_marker = "/* PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME START */"
end_marker = "/* PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME END */"
block_re = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
text, removed_old = block_re.subn("", text)
log.append(f"old_271_blocks_removed: {removed_old}")

runtime_patch = r'''
/* PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME START */
(function () {
  const TARGET_TRANSFER_PATH = "/transfers/marc-cucurella-real-madrid/";
  const PRICE_RE = /€\s*\d+(?:[.,]\d+)?\s*(?:M|m|млн|тыс|k)?/i;
  const YEAR_RE = /\b20\d{2}\b/g;
  function isTargetPage() {
    const path = window.location && window.location.pathname ? window.location.pathname : "";
    return path.indexOf(TARGET_TRANSFER_PATH) !== -1;
  }
  function hideNode(node) {
    if (!node || node.dataset.promyachik271HiddenYear === "1") return;
    node.dataset.promyachik271HiddenYear = "1";
    node.setAttribute("aria-hidden", "true");
    node.style.setProperty("display", "none", "important");
    node.style.setProperty("visibility", "hidden", "important");
    node.style.setProperty("opacity", "0", "important");
    node.style.setProperty("height", "0", "important");
    node.style.setProperty("min-height", "0", "important");
    node.style.setProperty("max-height", "0", "important");
    node.style.setProperty("margin", "0", "important");
    node.style.setProperty("padding", "0", "important");
    node.style.setProperty("line-height", "0", "important");
    node.style.setProperty("overflow", "hidden", "important");
  }
  function cleanLeafText(node) {
    if (!node || node.dataset.promyachik271Cleaned === "1") return;
    const original = (node.textContent || "").replace(/\s+/g, " ").trim();
    if (!original || original.length > 90) return;
    const price = original.match(PRICE_RE);
    const years = original.match(YEAR_RE);
    if (price && years) {
      node.textContent = price[0].trim();
      node.dataset.promyachik271Cleaned = "1";
      return;
    }
    if (!price && years && original.length <= 20) hideNode(node);
  }
  function applyCucurellaYearCleanup() {
    if (!isTargetPage()) return;
    document.querySelectorAll(".player-market-chart").forEach(function (chart) {
      chart.dataset.promyachik271CucurellaYearCleanup = "1";
      chart.querySelectorAll(".player-market-chart__point small, .promyachik-cucurella-price-label-249__date, .promyachik-cucurella-price-label-249__date-hidden-259").forEach(function (node) {
        const text = (node.textContent || "").replace(/\s+/g, " ").trim();
        if (/\b20\d{2}\b/.test(text) || !PRICE_RE.test(text)) hideNode(node);
      });
      chart.querySelectorAll(".player-market-chart__point, .player-market-chart__point strong, .promyachik-cucurella-price-label-249, .promyachik-cucurella-price-moved-244, [class*='price']").forEach(cleanLeafText);
      chart.querySelectorAll("*").forEach(function (node) { if (node.children.length === 0) cleanLeafText(node); });
    });
  }
  let scheduled = false;
  function scheduleCleanup() {
    if (scheduled) return;
    scheduled = true;
    window.setTimeout(function () { scheduled = false; applyCucurellaYearCleanup(); }, 50);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", scheduleCleanup); else scheduleCleanup();
  window.addEventListener("load", scheduleCleanup);
  let attempts = 0;
  const interval = window.setInterval(function () { attempts += 1; scheduleCleanup(); if (attempts >= 30) window.clearInterval(interval); }, 200);
  const observer = new MutationObserver(scheduleCleanup);
  observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
/* PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME END */
'''
text = text.rstrip() + "\n\n" + runtime_patch.strip() + "\n"

if text == old_text:
    log.append("ERROR: JS text did not change.")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {report}")
    sys.exit(1)
if "PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME START" not in text or "PRICE_RE" not in text:
    log.append("ERROR: required marker/token missing after edit.")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {report}")
    sys.exit(1)

js_path.write_text(text, encoding="utf-8")
log.append(f"CHANGED: {js_path}")

proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2000:])

public_js = root / "public" / "js" / "transfer-player-market-value-chart.js"
target_html = root / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
log.append(f"static_js_has_271_marker: {'PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME START' in js_path.read_text(encoding='utf-8', errors='ignore')}")
log.append(f"public_js_exists: {public_js.exists()}")
public_js_has_marker = False
if public_js.exists():
    public_js_text = public_js.read_text(encoding="utf-8", errors="ignore")
    public_js_has_marker = "PROMYACHIK 271 CUCURELLA HIDE CHART YEAR RUNTIME START" in public_js_text
    log.append(f"public_js_has_271_marker: {public_js_has_marker}")
log.append(f"target_html_exists: {target_html.exists()}")
if target_html.exists():
    html = target_html.read_text(encoding="utf-8", errors="ignore")
    log.append(f"target_html_links_chart_js: {'transfer-player-market-value-chart.js' in html}")

ok = proc.returncode == 0 and public_js.exists() and public_js_has_marker and target_html.exists()
log.append("")
log.append("VERIFIED_OK: " + ("True" if ok else "False"))
log.append("DONE" if ok else "FAILED")
report.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {report}")
sys.exit(0 if ok else 1)
