from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_299_konate_move_all_prices_under_dots_gold_no_border_no_backup_report.txt"
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_JS = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
PUBLIC_CSS = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"

START_JS = "// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START"
END_JS = "// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END"
START_CSS = "/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START */"
END_CSS = "/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END */"

report_lines = []

def log(msg):
    report_lines.append(str(msg))

def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def strip_block(text, start, end):
    if start in text and end in text:
        pattern = re.escape(start) + r".*?" + re.escape(end)
        text2, n = re.subn(pattern, "", text, flags=re.S)
        return text2, n
    return text, 0

def strip_old_promyachik_test_blocks(text):
    # Remove only our previous experimental blocks, if they were inserted into CSS/JS.
    patterns = [
        r"/\*\s*PROMYACHIK\s+(294|295|296|297|298)[\s\S]*?END\s*\*/",
        r"//\s*PROMYACHIK\s+(294|295|296|297|298)[\s\S]*?//\s*PROMYACHIK\s+\1[\s\S]*?END",
        r"/\*\s*KONATE[\s\S]*?(294|295|296|297|298)[\s\S]*?END\s*\*/",
    ]
    total = 0
    for p in patterns:
        text, n = re.subn(p, "", text, flags=re.I | re.S)
        total += n
    return text, total

JS_BLOCK = r'''
// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START
(function () {
  var KONATE_PATH = "/transfers/ibrahima-konate-real-madrid/";

  function isKonatePage() {
    return window.location && window.location.pathname && window.location.pathname.indexOf(KONATE_PATH) !== -1;
  }

  function removeOldKonatePriceOverlays(chart) {
    if (!chart) return;
    var candidates = chart.querySelectorAll([
      '.promyachik-konate-current-price-298',
      '.promyachik-konate-current-price-overlay-298',
      '.promyachik-current-price-overlay-298',
      '.promyachik-price-overlay-298',
      '.promyachik-konate-price-overlay',
      '.player-market-chart__current-price-overlay',
      '[class*="overlay-298"]',
      '[class*="current-price-298"]',
      '[class*="konate"][class*="price"]',
      '[data-promyachik-price-overlay]'
    ].join(','));

    candidates.forEach(function (el) {
      var cls = (el.getAttribute('class') || '');
      if (cls.indexOf('player-market-chart__point') !== -1 || cls.indexOf('player-market-chart__points') !== -1) {
        return;
      }
      if (el.parentNode) el.parentNode.removeChild(el);
    });
  }

  function movePrices(chart) {
    if (!chart) return false;

    removeOldKonatePriceOverlays(chart);

    var canvas = chart.querySelector('.player-market-chart__canvas');
    var pointsLayer = chart.querySelector('.player-market-chart__points');
    var points = Array.prototype.slice.call(chart.querySelectorAll('.player-market-chart__point'));
    var dots = Array.prototype.slice.call(chart.querySelectorAll('.player-market-chart__dot'));

    if (!canvas || !pointsLayer || !points.length || !dots.length) return false;

    chart.classList.add('promyachik-konate-price-layout-299');
    pointsLayer.classList.add('promyachik-konate-price-layer-299');

    var chartRect = chart.getBoundingClientRect();
    var canvasRect = canvas.getBoundingClientRect();
    var max = Math.min(points.length, dots.length);

    for (var i = 0; i < max; i += 1) {
      var point = points[i];
      var dot = dots[i];
      var value = point.querySelector('strong');
      if (!point || !dot || !value) continue;

      var dotRect = dot.getBoundingClientRect();
      var left = (dotRect.left + dotRect.width / 2) - chartRect.left;
      var top = (dotRect.top + dotRect.height) - chartRect.top + 9;
      var minTop = canvasRect.top - chartRect.top + 6;
      var maxTop = canvasRect.bottom - chartRect.top - 18;
      top = Math.max(minTop, Math.min(top, maxTop));

      point.style.setProperty('--pmk-price-left-299', left.toFixed(2) + 'px');
      point.style.setProperty('--pmk-price-top-299', top.toFixed(2) + 'px');
      point.classList.add('promyachik-konate-price-point-299');
      value.classList.add('promyachik-konate-price-value-299');

      // Remove pill/outline from any earlier experiment that changed the same value element.
      value.style.removeProperty('background');
      value.style.removeProperty('border');
      value.style.removeProperty('box-shadow');
      value.style.removeProperty('outline');
      value.style.removeProperty('padding');
    }

    return true;
  }

  var rafId = 0;
  function applyAll() {
    if (!isKonatePage()) return;
    document.body.classList.add('promyachik-konate-prices-under-dots-299');
    var charts = Array.prototype.slice.call(document.querySelectorAll('.player-market-chart'));
    charts.forEach(movePrices);
  }

  function schedule() {
    if (rafId) window.cancelAnimationFrame(rafId);
    rafId = window.requestAnimationFrame(function () {
      rafId = 0;
      applyAll();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule);
  } else {
    schedule();
  }
  window.addEventListener('load', schedule);
  window.addEventListener('resize', schedule);
  setTimeout(schedule, 250);
  setTimeout(schedule, 900);
})();
// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END
'''

CSS_BLOCK = r'''
/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START */
body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 {
  position: relative !important;
}

body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 .player-market-chart__points.promyachik-konate-price-layer-299 {
  position: absolute !important;
  inset: 0 !important;
  z-index: 5 !important;
  display: block !important;
  grid-template-columns: none !important;
  gap: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  pointer-events: none !important;
}

body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 .player-market-chart__point.promyachik-konate-price-point-299 {
  position: absolute !important;
  left: var(--pmk-price-left-299) !important;
  top: var(--pmk-price-top-299) !important;
  display: block !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  transform: translate(-50%, 0) !important;
  text-align: center !important;
  pointer-events: none !important;
}

body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 .player-market-chart__point.promyachik-konate-price-point-299 small {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}

body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 .player-market-chart__point.promyachik-konate-price-point-299 strong,
body.promyachik-konate-prices-under-dots-299 .player-market-chart.promyachik-konate-price-layout-299 .player-market-chart__point.promyachik-konate-price-point-299 strong.promyachik-konate-price-value-299 {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  width: auto !important;
  height: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  background: transparent !important;
  color: #f0d16d !important;
  font-family: "Russo One", "Montserrat", Arial, sans-serif !important;
  font-size: 10px !important;
  font-weight: 400 !important;
  line-height: 1 !important;
  letter-spacing: 0.01em !important;
  white-space: nowrap !important;
  text-shadow: 0 0 8px rgba(231, 198, 91, 0.28) !important;
}

body.promyachik-konate-prices-under-dots-299 .player-market-chart [class*="overlay-298"],
body.promyachik-konate-prices-under-dots-299 .player-market-chart [class*="current-price-298"],
body.promyachik-konate-prices-under-dots-299 .player-market-chart [data-promyachik-price-overlay] {
  display: none !important;
}
/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END */
'''

try:
    log("PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER")
    log(f"started_at={datetime.now().isoformat(timespec='seconds')}")
    log(f"root={ROOT}")

    if not ROOT.exists():
        raise RuntimeError(f"Project root not found: {ROOT}")
    if not JS.exists():
        raise RuntimeError(f"JS file not found: {JS}")
    if not CSS.exists():
        raise RuntimeError(f"CSS file not found: {CSS}")

    js_text = read_text(JS)
    css_text = read_text(CSS)

    js_text, n299_js_old = strip_block(js_text, START_JS, END_JS)
    css_text, n299_css_old = strip_block(css_text, START_CSS, END_CSS)
    js_text, n_old_js = strip_old_promyachik_test_blocks(js_text)
    css_text, n_old_css = strip_old_promyachik_test_blocks(css_text)

    js_text = js_text.rstrip() + "\n\n" + JS_BLOCK.strip() + "\n"
    css_text = css_text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"

    write_text(JS, js_text)
    write_text(CSS, css_text)

    log(f"updated_js={JS}")
    log(f"updated_css={CSS}")
    log(f"removed_existing_299_js_blocks={n299_js_old}")
    log(f"removed_existing_299_css_blocks={n299_css_old}")
    log(f"removed_old_294_298_js_blocks={n_old_js}")
    log(f"removed_old_294_298_css_blocks={n_old_css}")

    # If public already exists, keep it in sync for local stale/public checks. Hugo will rebuild too.
    if PUBLIC_JS.exists():
        write_text(PUBLIC_JS, js_text)
        log(f"synced_public_js={PUBLIC_JS}")
    else:
        log("synced_public_js=skipped_missing")
    if PUBLIC_CSS.exists():
        write_text(PUBLIC_CSS, css_text)
        log(f"synced_public_css={PUBLIC_CSS}")
    else:
        log("synced_public_css=skipped_missing")

    hugo = subprocess.run(["hugo", "-D"], cwd=str(ROOT), text=True, capture_output=True, timeout=120)
    log(f"hugo_exit_code={hugo.returncode}")
    if hugo.stdout:
        log("hugo_stdout_start")
        log(hugo.stdout[-4000:])
        log("hugo_stdout_end")
    if hugo.stderr:
        log("hugo_stderr_start")
        log(hugo.stderr[-4000:])
        log("hugo_stderr_end")

    target = ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"
    html = read_text(target) if target.exists() else ""
    js_public_after = read_text(PUBLIC_JS) if PUBLIC_JS.exists() else ""
    css_public_after = read_text(PUBLIC_CSS) if PUBLIC_CSS.exists() else ""

    checks = {
        "target_html_exists": target.exists(),
        "js_has_299_marker": START_JS in read_text(JS),
        "css_has_299_marker": START_CSS in read_text(CSS),
        "public_js_has_299_marker": START_JS in js_public_after,
        "public_css_has_299_marker": START_CSS in css_public_after,
        "target_references_chart_js": "transfer-player-market-value-chart.js" in html,
        "target_references_chart_css_or_css_bundle": ("transfer-player-market-value-chart.css" in html) or ("css" in html.lower()),
        "target_is_konate": "ibrahima" in html.lower() and "konate" in html.lower(),
    }
    for k, v in checks.items():
        log(f"{k}: {v}")

    ok = (hugo.returncode == 0 and all(checks.values()))
    log(f"VERIFIED_OK={ok}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_text(REPORT, "\n".join(report_lines) + "\n")
    if not ok:
        sys.exit(1)

except Exception as e:
    log(f"ERROR={type(e).__name__}: {e}")
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        write_text(REPORT, "\n".join(report_lines) + "\n")
    except Exception:
        pass
    sys.exit(1)
