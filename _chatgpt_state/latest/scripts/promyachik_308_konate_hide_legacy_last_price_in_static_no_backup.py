from pathlib import Path
import sys

PROJECT_ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT_PATH = PROJECT_ROOT / "var" / "promyachik_308_konate_hide_legacy_last_price_report.txt"

JS_CONTENT = r"""(function () {
  'use strict';

  var VERSION = '308-hide-last-legacy-price-only-after-gold-overlay';
  var PATH_RE = /ibrahima-konate-real-madrid/i;
  var HIDDEN_ATTR = 'data-promyachik-hide-konate-last-legacy-price-308';
  var BODY_ATTR = 'data-promyachik-konate-legacy-last-price-hidden-308';

  function isKonatePage() {
    return PATH_RE.test(window.location.pathname || '');
  }

  function normalizeText(value) {
    return String(value || '')
      .replace(/\u00a0/g, ' ')
      .replace(/\u202f/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function isTargetPrice(value) {
    var text = normalizeText(value);
    return text === '€45 млн' || text === '€45млн' || text === '45 млн';
  }

  function isHidden(el) {
    if (!el || !window.getComputedStyle) return false;
    var style = window.getComputedStyle(el);
    return style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0;
  }

  function getKonateChart() {
    return document.querySelector('.player-market-chart[data-market-chart-key="konate"]') ||
      document.querySelector('.player-market-chart');
  }

  function getDirectChildByTag(parent, tagName) {
    if (!parent) return null;
    tagName = String(tagName || '').toUpperCase();
    var children = Array.prototype.slice.call(parent.children || []);
    for (var i = 0; i < children.length; i += 1) {
      if (children[i].tagName === tagName) {
        return children[i];
      }
    }
    return null;
  }

  function getGoldOverlayLabels(chart) {
    if (!chart) return [];
    return Array.prototype.slice
      .call(chart.querySelectorAll('.promyachik-konate-price-layer-302 .promyachik-konate-price-label-302'))
      .filter(function (label) {
        return normalizeText(label.textContent).length > 0 && !isHidden(label);
      });
  }

  function isGoldOverlayReady(chart) {
    var labels = getGoldOverlayLabels(chart);
    if (labels.length >= 4) return true;
    return labels.some(function (label) {
      return isTargetPrice(label.textContent);
    });
  }

  function hideLegacyLastPriceInsideChart(chart) {
    if (!chart || !isGoldOverlayReady(chart)) return 0;

    var pointsRow = chart.querySelector('.player-market-chart__points');
    if (!pointsRow) return 0;

    var points = Array.prototype.slice.call(pointsRow.querySelectorAll('.player-market-chart__point'));
    if (!points.length) return 0;

    var lastPoint = points[points.length - 1];
    var strong = getDirectChildByTag(lastPoint, 'strong');
    if (!strong) return 0;

    if (strong.closest('.promyachik-konate-price-layer-302')) return 0;
    if (strong.closest('.promyachik-konate-price-label-302')) return 0;
    if (strong.getAttribute(HIDDEN_ATTR) === '1') return 0;

    strong.setAttribute(HIDDEN_ATTR, '1');
    strong.style.setProperty('display', 'none', 'important');
    strong.style.setProperty('visibility', 'hidden', 'important');
    strong.style.setProperty('opacity', '0', 'important');
    strong.style.setProperty('width', '0', 'important');
    strong.style.setProperty('height', '0', 'important');
    strong.style.setProperty('margin', '0', 'important');
    strong.style.setProperty('padding', '0', 'important');
    strong.style.setProperty('overflow', 'hidden', 'important');
    return 1;
  }

  function hideExternalWhiteDuplicateNearChart(chart) {
    if (!chart || !isGoldOverlayReady(chart)) return 0;

    var canvas = chart.querySelector('.player-market-chart__canvas') || chart;
    var canvasRect = canvas.getBoundingClientRect();
    var chartRect = chart.getBoundingClientRect();
    if (!canvasRect || !chartRect || chartRect.width <= 0 || chartRect.height <= 0) return 0;

    var root = chart.closest('.player-brief, .transfer-side-column, article, main') || document.body;
    var nodes = Array.prototype.slice.call(root.querySelectorAll('span,strong,b,em,small,p,div'));
    var hidden = 0;

    nodes.forEach(function (el) {
      if (!el || el.nodeType !== 1) return;
      if (el.getAttribute(HIDDEN_ATTR) === '1') return;
      if (el.closest('script,style,noscript,svg')) return;
      if (el.closest('.promyachik-konate-price-layer-302')) return;
      if (el.closest('.promyachik-konate-price-label-302')) return;
      if (chart.contains(el)) return;
      if (!isTargetPrice(el.textContent)) return;
      if (isHidden(el)) return;

      var rect = el.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) return;

      var isNearChartBottom =
        rect.top >= canvasRect.bottom - 12 &&
        rect.top <= chartRect.bottom + 180 &&
        rect.left >= chartRect.left - 40 &&
        rect.right <= chartRect.right + 40;

      if (!isNearChartBottom) return;

      el.setAttribute(HIDDEN_ATTR, '1');
      el.style.setProperty('display', 'none', 'important');
      el.style.setProperty('visibility', 'hidden', 'important');
      el.style.setProperty('opacity', '0', 'important');
      hidden += 1;
    });

    return hidden;
  }

  function applyFix() {
    if (!isKonatePage()) return;

    var chart = getKonateChart();
    if (!chart) return;

    var hiddenInside = hideLegacyLastPriceInsideChart(chart);
    var hiddenOutside = hideExternalWhiteDuplicateNearChart(chart);
    var total = hiddenInside + hiddenOutside;

    if (total > 0) {
      document.body.setAttribute(BODY_ATTR, String(total));
    }

    document.body.setAttribute('data-promyachik-konate-hide-legacy-last-price-version', VERSION);
  }

  var timer = 0;
  function schedule() {
    if (!isKonatePage()) return;
    window.clearTimeout(timer);
    timer = window.setTimeout(applyFix, 40);
  }

  function runMany() {
    applyFix();
    window.setTimeout(applyFix, 80);
    window.setTimeout(applyFix, 180);
    window.setTimeout(applyFix, 400);
    window.setTimeout(applyFix, 900);
    window.setTimeout(applyFix, 1600);
    window.setTimeout(applyFix, 2600);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runMany);
  } else {
    runMany();
  }

  window.addEventListener('load', runMany);
  window.addEventListener('resize', runMany);

  if (window.MutationObserver) {
    var started = false;
    var startObserver = function () {
      if (started || !document.body || !isKonatePage()) return;
      started = true;
      var observer = new MutationObserver(schedule);
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'data-promyachik-konate-302']
      });
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', startObserver);
    } else {
      startObserver();
    }
  }
})();
"""

TARGETS = [
    PROJECT_ROOT / "static" / "js" / "promyachik-konate-hide-white-45-303.js",
    PROJECT_ROOT / "public" / "js" / "promyachik-konate-hide-white-45-303.js",
]

PARTIAL_PATH = PROJECT_ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
PUBLIC_HTML_PATH = PROJECT_ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"

def write_report(lines):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

def replace_version(path, old, new, label, lines):
    if not path.exists():
        lines.append(f"SKIP {label}: missing {path}")
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    if new in text:
        lines.append(f"OK {label}: already has v=308")
        return True
    if old not in text:
        lines.append(f"WARN {label}: expected v=303 string not found")
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    lines.append(f"OK {label}: changed v=303 to v=308")
    return True

def main():
    lines = [
        "PROMYACHIK 308 - KONATE HIDE LEGACY LAST PRICE IN STATIC - NO BACKUP",
        "Project: C:\\Users\\Dmitrii\\Promyachik",
        "Backup: not created",
        "Push: not made",
        "",
    ]

    if not PROJECT_ROOT.exists():
        lines.append("FAILED: project root not found")
        write_report(lines)
        return 1

    wrote_static = False
    for target in TARGETS:
        if target.parent.exists():
            target.write_text(JS_CONTENT, encoding="utf-8", newline="\n")
            lines.append(f"OK wrote {target}")
            if "\\static\\js\\" in str(target):
                wrote_static = True
        else:
            lines.append(f"SKIP missing folder for {target}")

    replace_version(
        PARTIAL_PATH,
        'promyachik-konate-hide-white-45-303.js" | relURL }}?v=303',
        'promyachik-konate-hide-white-45-303.js" | relURL }}?v=308',
        "layout partial",
        lines,
    )

    replace_version(
        PUBLIC_HTML_PATH,
        "/promyachik/js/promyachik-konate-hide-white-45-303.js?v=303",
        "/promyachik/js/promyachik-konate-hide-white-45-303.js?v=308",
        "public Konate HTML",
        lines,
    )

    root_wrong_js = PROJECT_ROOT / "js" / "transfer-player-market-value-chart.js"
    if root_wrong_js.exists():
        lines.append(f"NOTE: found unused root-level file from earlier package: {root_wrong_js}")
        lines.append("NOTE: it was not deleted by this package.")

    if not wrote_static:
        lines.append("")
        lines.append("FAILED: static/js target was not written")
        write_report(lines)
        return 1

    lines.append("")
    lines.append("DONE")
    write_report(lines)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
