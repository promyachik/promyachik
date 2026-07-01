from pathlib import Path
import subprocess
import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "var" / "promyachik_279_align_all_player_chart_prices_to_points_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

JS_PATH = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS_PATH = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_JS_PATH = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
PUBLIC_CSS_PATH = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"
TARGET_HTML = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

JS_START = "/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS START */"
JS_END = "/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS END */"
CSS_START = "/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS CSS START */"
CSS_END = "/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS CSS END */"

JS_BLOCK = r'''
/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS START */
(function () {
  if (window.__promyachikAlignMarketPrices279Ready) {
    return;
  }
  window.__promyachikAlignMarketPrices279Ready = true;

  const CHART_SELECTOR = ".player-market-chart";
  const ROW_SELECTOR = ".player-market-chart__points";
  const ITEM_SELECTOR = ".player-market-chart__point";
  const DOT_SELECTOR = ".player-market-chart__dot";
  const CLUB_MARKER_SELECTOR = ".player-market-chart__club-marker";

  const roundPx = function (value) {
    return Math.round(value * 100) / 100;
  };

  const getElementCenterX = function (element) {
    const rect = element.getBoundingClientRect();
    return rect.left + rect.width / 2;
  };

  const getTargetCenters = function (chart) {
    const dots = Array.from(chart.querySelectorAll(DOT_SELECTOR));
    if (dots.length) {
      return dots.map(getElementCenterX);
    }

    const clubMarkers = Array.from(chart.querySelectorAll(CLUB_MARKER_SELECTOR));
    if (clubMarkers.length) {
      return clubMarkers.map(getElementCenterX);
    }

    return [];
  };

  const clearAlignment = function (row) {
    const items = Array.from(row.querySelectorAll(ITEM_SELECTOR));
    row.classList.remove("promyachik-price-align-279");
    row.style.removeProperty("position");
    row.style.removeProperty("display");
    row.style.removeProperty("height");
    row.style.removeProperty("min-height");

    items.forEach(function (item) {
      item.classList.remove("promyachik-price-align-item-279");
      item.style.removeProperty("position");
      item.style.removeProperty("left");
      item.style.removeProperty("top");
      item.style.removeProperty("transform");
      item.style.removeProperty("width");
      item.style.removeProperty("max-width");
      item.style.removeProperty("text-align");
    });
  };

  const alignChart = function (chart) {
    const row = chart.querySelector(ROW_SELECTOR);
    if (!row) {
      return;
    }

    const items = Array.from(row.querySelectorAll(ITEM_SELECTOR));
    if (!items.length) {
      return;
    }

    const centers = getTargetCenters(chart);
    if (!centers.length) {
      clearAlignment(row);
      return;
    }

    clearAlignment(row);

    const rowRect = row.getBoundingClientRect();
    const currentHeights = items.map(function (item) {
      return item.getBoundingClientRect().height || 0;
    });
    const rowHeight = Math.max(rowRect.height || 0, currentHeights.reduce(function (max, value) {
      return Math.max(max, value);
    }, 0), 20);

    row.classList.add("promyachik-price-align-279");
    row.style.position = "relative";
    row.style.display = "block";
    row.style.minHeight = Math.ceil(rowHeight) + "px";
    row.style.height = Math.ceil(rowHeight) + "px";

    items.forEach(function (item, index) {
      const center = centers[Math.min(index, centers.length - 1)];
      const x = roundPx(center - rowRect.left);
      item.classList.add("promyachik-price-align-item-279");
      item.style.position = "absolute";
      item.style.left = x + "px";
      item.style.top = "0";
      item.style.transform = "translateX(-50%)";
      item.style.width = "max-content";
      item.style.maxWidth = "78px";
      item.style.textAlign = "center";
    });
  };

  const alignAllCharts = function () {
    Array.from(document.querySelectorAll(CHART_SELECTOR)).forEach(alignChart);
  };

  let timer = null;
  const scheduleAlign = function () {
    if (timer) {
      window.clearTimeout(timer);
    }
    window.requestAnimationFrame(function () {
      alignAllCharts();
      timer = window.setTimeout(alignAllCharts, 120);
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleAlign);
  } else {
    scheduleAlign();
  }

  window.addEventListener("load", scheduleAlign);
  window.addEventListener("resize", scheduleAlign);

  const observer = new MutationObserver(scheduleAlign);
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS END */
'''.strip() + "\n"

CSS_BLOCK = r'''
/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS CSS START */
body.transfer-page .player-market-chart__points.promyachik-price-align-279,
.player-market-chart-modal .player-market-chart__points.promyachik-price-align-279 {
  position: relative !important;
  display: block !important;
  width: 100% !important;
  overflow: visible !important;
}

body.transfer-page .player-market-chart__point.promyachik-price-align-item-279,
.player-market-chart-modal .player-market-chart__point.promyachik-price-align-item-279 {
  position: absolute !important;
  top: 0 !important;
  transform: translateX(-50%) !important;
  display: grid !important;
  justify-items: center !important;
  align-items: start !important;
  gap: 0 !important;
  min-width: 0 !important;
  width: max-content !important;
  max-width: 78px !important;
  text-align: center !important;
  white-space: nowrap !important;
}

body.transfer-page .player-market-chart__point.promyachik-price-align-item-279 strong,
.player-market-chart-modal .player-market-chart__point.promyachik-price-align-item-279 strong {
  display: block !important;
  text-align: center !important;
}
/* PROMYACHIK 279 ALIGN MARKET PRICE LABELS TO POINTS CSS END */
'''.strip() + "\n"


def remove_block(text: str, start: str, end: str):
    count = 0
    while True:
        a = text.find(start)
        if a == -1:
            break
        b = text.find(end, a)
        if b == -1:
            break
        b += len(end)
        text = text[:a].rstrip() + "\n\n" + text[b:].lstrip()
        count += 1
    return text, count

log = []
log.append("PROMYACHIK 279 - ALIGN ALL PLAYER CHART PRICES TO POINTS - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Align price labels under the real chart points for all current and future player market charts.")
log.append("- Do not hide years in this package; keep the already working CSS-only year hiding from 277.")
log.append("- Do not remove DOM nodes.")
log.append("- Do not touch partial/templates/content.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")
log.append("NO BACKUP")
log.append("- Full backup: NOT CREATED")
log.append("- Safety backup: NOT CREATED")
log.append("")

try:
    if not JS_PATH.exists():
        raise FileNotFoundError(f"JS not found: {JS_PATH}")
    if not CSS_PATH.exists():
        raise FileNotFoundError(f"CSS not found: {CSS_PATH}")

    js_text = JS_PATH.read_text(encoding="utf-8")
    css_text = CSS_PATH.read_text(encoding="utf-8")

    js_text, js_removed = remove_block(js_text, JS_START, JS_END)
    css_text, css_removed = remove_block(css_text, CSS_START, CSS_END)

    js_text = js_text.rstrip() + "\n\n" + JS_BLOCK
    css_text = css_text.rstrip() + "\n\n" + CSS_BLOCK

    if "value_label" not in js_text:
        raise RuntimeError("price token value_label is missing in JS before write")
    if "promyachikAlignMarketPrices279Ready" not in js_text:
        raise RuntimeError("279 JS marker missing before write")
    if "promyachik-price-align-279" not in css_text:
        raise RuntimeError("279 CSS marker missing before write")

    JS_PATH.write_text(js_text, encoding="utf-8")
    CSS_PATH.write_text(css_text, encoding="utf-8")

    log.append("CHANGED FILES")
    log.append(f"- {JS_PATH.relative_to(ROOT)} | appended safe runtime alignment helper | previous_279_blocks_removed={js_removed}")
    log.append(f"- {CSS_PATH.relative_to(ROOT)} | appended alignment CSS | previous_279_blocks_removed={css_removed}")
    log.append("EFFECTIVE_CHANGED_FILES: 2")
    log.append("")

    proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
    log.append("HUGO")
    log.append("COMMAND: hugo -D")
    log.append(f"EXIT_CODE: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2500:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2500:])
    log.append("")

    public_js_has_marker = PUBLIC_JS_PATH.exists() and "promyachikAlignMarketPrices279Ready" in PUBLIC_JS_PATH.read_text(encoding="utf-8", errors="ignore")
    public_css_has_marker = PUBLIC_CSS_PATH.exists() and "promyachik-price-align-279" in PUBLIC_CSS_PATH.read_text(encoding="utf-8", errors="ignore")
    target_exists = TARGET_HTML.exists()
    target_links_chart_js = False
    target_links_chart_css = False
    if target_exists:
        target_html = TARGET_HTML.read_text(encoding="utf-8", errors="ignore")
        target_links_chart_js = "transfer-player-market-value-chart.js" in target_html
        target_links_chart_css = "transfer-player-market-value-chart.css" in target_html

    verified = proc.returncode == 0 and public_js_has_marker and public_css_has_marker and target_exists and target_links_chart_js and target_links_chart_css

    log.append("CHECKS")
    log.append("backup_created: False")
    log.append(f"static_js_has_279_marker: {'promyachikAlignMarketPrices279Ready' in js_text}")
    log.append(f"static_css_has_279_marker: {'promyachik-price-align-279' in css_text}")
    log.append(f"public_js_has_279_marker: {public_js_has_marker}")
    log.append(f"public_css_has_279_marker: {public_css_has_marker}")
    log.append(f"target_cucurella_html_exists: {target_exists}")
    log.append(f"target_links_chart_js: {target_links_chart_js}")
    log.append(f"target_links_chart_css: {target_links_chart_css}")
    log.append(f"VERIFIED_OK: {verified}")
    log.append("")

    if verified:
        log.append("DONE")
    else:
        log.append("DONE_WITH_WARNINGS")

    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if verified else "DONE_WITH_WARNINGS")
    print(f"REPORT: {REPORT}")
    raise SystemExit(0 if proc.returncode == 0 else 1)

except Exception as exc:
    log.append("ERROR")
    log.append(repr(exc))
    log.append("")
    log.append("FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)
