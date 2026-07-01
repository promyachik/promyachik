from pathlib import Path

PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TARGETS = [
    Path("static/js/transfer-player-market-value-chart.js"),
    Path("public/js/transfer-player-market-value-chart.js"),
]
REPORT_REL = Path(r"var\promyachik_307_konate_hide_legacy_45_loaded_chart_js_report.txt")

PATCH_MARKER_START = "/* PROMYACHIK 307 KONATE HIDE LEGACY 45 IN LOADED CHART JS START */"
PATCH_MARKER_END = "/* PROMYACHIK 307 KONATE HIDE LEGACY 45 IN LOADED CHART JS END */"

PATCH = r"""
/* PROMYACHIK 307 KONATE HIDE LEGACY 45 IN LOADED CHART JS START */
(function () {
  'use strict';

  var PATH_RE = /ibrahima-konate-real-madrid/i;
  var ATTR = 'data-promyachik-hidden-legacy-45-307';

  function isKonatePage() {
    return !!(window.location && PATH_RE.test(window.location.pathname || ''));
  }

  function normalizeText(value) {
    return String(value || '')
      .replace(/\u00a0/g, ' ')
      .replace(/\u202f/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function isPrice45(value) {
    var text = normalizeText(value);
    return text === '€45 млн' || text === '€45млн' || text === '45 млн';
  }

  function hasVisibleGoldOverlay45(chart) {
    if (!chart) return false;

    var labels = Array.prototype.slice.call(
      chart.querySelectorAll('.promyachik-konate-price-layer-302 .promyachik-konate-price-label-302')
    );

    return labels.some(function (label) {
      var cs = window.getComputedStyle ? window.getComputedStyle(label) : null;
      if (!isPrice45(label.textContent)) return false;
      if (!cs) return true;
      return cs.display !== 'none' && cs.visibility !== 'hidden' && Number(cs.opacity) !== 0;
    });
  }

  function hideLegacy45OnlyWhenGoldExists() {
    if (!isKonatePage()) return;

    var charts = Array.prototype.slice.call(
      document.querySelectorAll('.player-market-chart:not(.player-market-chart--enlarged)')
    );

    charts.forEach(function (chart) {
      if (!chart || chart.getAttribute('data-market-chart-key') !== 'konate') {
        return;
      }

      if (!hasVisibleGoldOverlay45(chart)) {
        return;
      }

      var row = chart.querySelector('.player-market-chart__points');
      if (!row) return;

      var values = Array.prototype.slice.call(
        row.querySelectorAll('.player-market-chart__point > strong, .player-market-chart__point strong')
      );

      values.forEach(function (value) {
        if (!isPrice45(value.textContent)) return;
        if (value.closest('.promyachik-konate-price-layer-302')) return;
        if (value.closest('.promyachik-konate-price-label-302')) return;

        value.setAttribute(ATTR, '1');
        value.style.setProperty('display', 'none', 'important');
        value.style.setProperty('visibility', 'hidden', 'important');
        value.style.setProperty('opacity', '0', 'important');
        value.style.setProperty('width', '0', 'important');
        value.style.setProperty('height', '0', 'important');
        value.style.setProperty('overflow', 'hidden', 'important');
      });

      document.body.setAttribute('data-promyachik-konate-307-ran', '1');
    });
  }

  function runMany() {
    hideLegacy45OnlyWhenGoldExists();
    window.setTimeout(hideLegacy45OnlyWhenGoldExists, 80);
    window.setTimeout(hideLegacy45OnlyWhenGoldExists, 220);
    window.setTimeout(hideLegacy45OnlyWhenGoldExists, 600);
    window.setTimeout(hideLegacy45OnlyWhenGoldExists, 1200);
    window.setTimeout(hideLegacy45OnlyWhenGoldExists, 2400);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runMany);
  } else {
    runMany();
  }

  window.addEventListener('load', runMany);
  window.addEventListener('resize', runMany);

  if (window.MutationObserver) {
    var timer = 0;
    var observerStarted = false;

    var startObserver = function () {
      if (observerStarted || !document.body || !isKonatePage()) return;
      observerStarted = true;

      var observer = new MutationObserver(function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(hideLegacy45OnlyWhenGoldExists, 35);
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
      });
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', startObserver);
    } else {
      startObserver();
    }
  }
})();
/* PROMYACHIK 307 KONATE HIDE LEGACY 45 IN LOADED CHART JS END */
""".strip() + "\n"

def write_report(status, lines):
    report = PROJECT / REPORT_REL
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(status + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

def fail(message):
    write_report("FAILED", [
        message,
        "",
        "No backup was created.",
        "No push was made.",
    ])
    print("FAILED")
    print(message)
    print()
    print("No backup was created.")
    print("No push was made.")
    return 1

def patch_file(path):
    if not path.exists():
        return "missing"

    text = path.read_text(encoding="utf-8")

    if PATCH_MARKER_START in text and PATCH_MARKER_END in text:
        return "already-present"

    text = text.rstrip() + "\n\n" + PATCH
    path.write_text(text, encoding="utf-8")
    return "patched"

def main():
    if not PROJECT.exists():
        return fail("Project folder was not found: " + str(PROJECT))

    results = []
    for rel in TARGETS:
        result = patch_file(PROJECT / rel)
        results.append((str(rel), result))

    static_result = dict(results).get("static/js/transfer-player-market-value-chart.js")
    if static_result == "missing":
        return fail("Required loaded JS file was not found: static/js/transfer-player-market-value-chart.js")

    write_report("DONE", [
        "PROMYACHIK 307 - KONATE HIDE LEGACY 45 IN LOADED CHART JS - NO BACKUP",
        "",
        "Changed files:",
        *["- " + name + ": " + result for name, result in results],
        "",
        "Why this package is different:",
        "- It patches the JS file that single.html definitely loads: transfer-player-market-value-chart.js.",
        "- It hides legacy €45 млн only after a visible gold 302 overlay label already exists.",
        "- If the gold overlay is absent, it does nothing, so it should not create an empty/blank price state.",
        "- It affects only the Konate transfer page and only the Konate chart.",
        "",
        "No backup was created.",
        "No push was made.",
    ])

    print("DONE")
    print("PROMYACHIK 307 - KONATE HIDE LEGACY 45 IN LOADED CHART JS - NO BACKUP")
    for name, result in results:
        print(name + ": " + result)
    print()
    print("Report:", PROJECT / REPORT_REL)
    print("No backup was created.")
    print("No push was made.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
