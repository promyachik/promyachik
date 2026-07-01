from pathlib import Path
import subprocess
import datetime
import re

ROOT = Path.cwd()
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
REPORT = ROOT / "var" / "promyachik_294_konate_test_highlight_current_price_under_point_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 294 - KONATE TEST HIGHLIGHT CURRENT PRICE UNDER POINT - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Test only on Konate page.")
log.append("- Do not touch Ramos page/content.")
log.append("- Do not create backup.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- JS only adds a body class and marks the last/current price label on Konate.")
log.append("- CSS only colors/raises the current price label; does not move the whole chart.")
log.append("")

if not JS.exists():
    log.append(f"ERROR: JS not found: {JS}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)
if not CSS.exists():
    log.append(f"ERROR: CSS not found: {CSS}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

js_text = JS.read_text(encoding="utf-8", errors="ignore")
css_text = CSS.read_text(encoding="utf-8", errors="ignore")

js_text = re.sub(r"\n?/\* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START \*/.*?/\* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST END \*/\n?", "\n", js_text, flags=re.S)
css_text = re.sub(r"\n?/\* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START \*/.*?/\* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST END \*/\n?", "\n", css_text, flags=re.S)

js_block = """
/* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START */
(function () {
  "use strict";

  var KONATE_PATH = "/transfers/ibrahima-konate-real-madrid/";

  function isKonatePage() {
    return window.location && window.location.pathname && window.location.pathname.indexOf(KONATE_PATH) !== -1;
  }

  function markKonateCurrentPrice() {
    if (!isKonatePage() || !document.body) {
      return;
    }

    document.body.classList.add("promyachik-konate-current-price-highlight-294");

    var charts = Array.prototype.slice.call(document.querySelectorAll(".player-market-chart"));
    charts.forEach(function (chart) {
      if (!chart || chart.classList.contains("promyachik-konate-price-marked-294")) {
        return;
      }

      var pointItems = Array.prototype.slice.call(
        chart.querySelectorAll(".player-market-chart__points .player-market-chart__point, .player-market-chart__point")
      );

      if (!pointItems.length) {
        return;
      }

      var currentItem = pointItems[pointItems.length - 1];
      if (!currentItem) {
        return;
      }

      currentItem.classList.add("promyachik-konate-current-price-point-294");

      var valueNode = currentItem.querySelector("strong, .player-market-chart__value, .player-market-chart__point-value");
      if (valueNode) {
        valueNode.classList.add("promyachik-konate-current-price-value-294");
      }

      chart.classList.add("promyachik-konate-price-marked-294");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", markKonateCurrentPrice);
  } else {
    markKonateCurrentPrice();
  }

  window.addEventListener("load", markKonateCurrentPrice);
  window.addEventListener("resize", function () {
    window.setTimeout(markKonateCurrentPrice, 80);
  });
  window.setTimeout(markKonateCurrentPrice, 120);
  window.setTimeout(markKonateCurrentPrice, 600);
})();
/* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST END */
"""

css_block = """
/* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START */
body.promyachik-konate-current-price-highlight-294 .player-market-chart .promyachik-konate-current-price-point-294,
body.promyachik-konate-current-price-highlight-294 .player-market-chart .player-market-chart__points .player-market-chart__point:last-child {
  position: relative !important;
  z-index: 30 !important;
}

body.promyachik-konate-current-price-highlight-294 .player-market-chart .promyachik-konate-current-price-value-294,
body.promyachik-konate-current-price-highlight-294 .player-market-chart .player-market-chart__points .player-market-chart__point:last-child strong {
  color: #f3d45b !important;
  -webkit-text-fill-color: #f3d45b !important;
  text-shadow: 0 0 14px rgba(243, 212, 91, 0.55), 0 0 24px rgba(243, 212, 91, 0.22) !important;
  transform: translateY(-8px) scale(1.06) !important;
  transform-origin: center center !important;
  display: inline-block !important;
  position: relative !important;
  z-index: 31 !important;
  white-space: nowrap !important;
}
/* PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST END */
"""

JS.write_text(js_text.rstrip() + "\n" + js_block.strip() + "\n", encoding="utf-8")
CSS.write_text(css_text.rstrip() + "\n" + css_block.strip() + "\n", encoding="utf-8")
log.append(f"CHANGED: {JS}")
log.append(f"CHANGED: {CSS}")

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
public_js = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
public_css = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"

log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/ibrahima-konate-real-madrid/")
log.append(f"target_html_exists: {target.exists()}")
log.append(f"public_js_exists: {public_js.exists()}")
log.append(f"public_css_exists: {public_css.exists()}")

js_ok = "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START" in JS.read_text(encoding="utf-8", errors="ignore")
css_ok = "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START" in CSS.read_text(encoding="utf-8", errors="ignore")
public_js_ok = public_js.exists() and "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START" in public_js.read_text(encoding="utf-8", errors="ignore")
public_css_ok = public_css.exists() and "PROMYACHIK 294 KONATE CURRENT PRICE HIGHLIGHT TEST START" in public_css.read_text(encoding="utf-8", errors="ignore")

log.append(f"static_js_has_294: {js_ok}")
log.append(f"static_css_has_294: {css_ok}")
log.append(f"public_js_has_294: {public_js_ok}")
log.append(f"public_css_has_294: {public_css_ok}")
log.append("backup_created: False")

ok = proc.returncode == 0 and target.exists() and js_ok and css_ok and public_js_ok and public_css_ok
log.append("")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")

print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
