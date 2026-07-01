from pathlib import Path

PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
JS_REL = Path("static/js/promyachik-konate-hide-white-45-303.js")
PUBLIC_JS_REL = Path("public/js/promyachik-konate-hide-white-45-303.js")
REPORT_REL = Path(r"var\promyachik_306_konate_hide_last_legacy_price_only_report.txt")

PATCH_MARKER_START = "/* PROMYACHIK 306 KONATE HIDE LAST LEGACY PRICE ONLY START */"
PATCH_MARKER_END = "/* PROMYACHIK 306 KONATE HIDE LAST LEGACY PRICE ONLY END */"

PATCH = """
/* PROMYACHIK 306 KONATE HIDE LAST LEGACY PRICE ONLY START */
(function () {
  'use strict';

  var PATH_RE = /ibrahima-konate-real-madrid/i;
  var ATTR = 'data-promyachik-hidden-last-legacy-price-306';

  function isKonatePage() {
    return PATH_RE.test(window.location.pathname || '');
  }

  function hideLastLegacyPriceOnly() {
    if (!isKonatePage()) return;

    var charts = Array.prototype.slice.call(
      document.querySelectorAll('.player-market-chart:not(.player-market-chart--enlarged)')
    );

    charts.forEach(function (chart) {
      if (!chart || chart.getAttribute('data-market-chart-key') !== 'konate') {
        return;
      }

      var legacyRow = chart.querySelector('.player-market-chart__points');
      if (!legacyRow) {
        return;
      }

      var legacyPoints = Array.prototype.slice.call(
        legacyRow.querySelectorAll(':scope > .player-market-chart__point')
      );

      if (!legacyPoints.length) {
        legacyPoints = Array.prototype.slice.call(
          legacyRow.children
        ).filter(function (child) {
          return child && child.classList && child.classList.contains('player-market-chart__point');
        });
      }

      var lastPoint = legacyPoints[legacyPoints.length - 1];
      if (!lastPoint) {
        return;
      }

      var value = lastPoint.querySelector(':scope > strong') || lastPoint.querySelector('strong');
      if (!value) {
        return;
      }

      if (
        value.closest('.promyachik-konate-price-layer-302') ||
        value.closest('.promyachik-konate-price-label-302') ||
        value.closest('.promyachik-konate-price-layer-299')
      ) {
        return;
      }

      value.setAttribute(ATTR, '1');
      value.style.setProperty('display', 'none', 'important');
      value.style.setProperty('visibility', 'hidden', 'important');
      value.style.setProperty('opacity', '0', 'important');
      value.style.setProperty('width', '0', 'important');
      value.style.setProperty('height', '0', 'important');
      value.style.setProperty('overflow', 'hidden', 'important');
    });
  }

  function runMany() {
    hideLastLegacyPriceOnly();
    window.setTimeout(hideLastLegacyPriceOnly, 80);
    window.setTimeout(hideLastLegacyPriceOnly, 240);
    window.setTimeout(hideLastLegacyPriceOnly, 700);
    window.setTimeout(hideLastLegacyPriceOnly, 1400);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runMany);
  } else {
    runMany();
  }

  window.addEventListener('load', runMany);
  window.addEventListener('resize', runMany);

  if (window.MutationObserver) {
    var observerStarted = false;
    var startObserver = function () {
      if (observerStarted || !document.body || !isKonatePage()) return;
      observerStarted = true;

      var timer = 0;
      var observer = new MutationObserver(function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(hideLastLegacyPriceOnly, 30);
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', startObserver);
    } else {
      startObserver();
    }
  }
})();
/* PROMYACHIK 306 KONATE HIDE LAST LEGACY PRICE ONLY END */
""".strip() + "\n"

def fail(message):
    report_path = PROJECT / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("FAILED\n" + message + "\n\nNo backup was created.\nNo push was made.\n", encoding="utf-8")
    print("FAILED")
    print(message)
    print()
    print("No backup was created.")
    print("No push was made.")
    return 1

def update_file(path):
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
    static_result = update_file(PROJECT / JS_REL)
    results.append((str(JS_REL), static_result))

    public_path = PROJECT / PUBLIC_JS_REL
    if public_path.exists():
        public_result = update_file(public_path)
        results.append((str(PUBLIC_JS_REL), public_result))
    else:
        results.append((str(PUBLIC_JS_REL), "missing-ok"))

    if static_result == "missing":
        return fail("Required file was not found: " + str(JS_REL))

    report_path = PROJECT / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "DONE",
        "PROMYACHIK 306 - KONATE HIDE LAST LEGACY PRICE ONLY - NO BACKUP",
        "",
        "Changed files:",
    ]

    for name, result in results:
        report_lines.append("- " + name + ": " + result)

    report_lines.extend([
        "",
        "What changed:",
        "- Added a Konate-only runtime guard to static/js/promyachik-konate-hide-white-45-303.js.",
        "- It hides only the last legacy <strong> inside .player-market-chart__points.",
        "- It does not target .promyachik-konate-price-layer-302 or gold overlay labels.",
        "- It does not touch Ramos or other players.",
        "",
        "No backup was created.",
        "No push was made.",
    ])

    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("DONE")
    print("PROMYACHIK 306 - KONATE HIDE LAST LEGACY PRICE ONLY - NO BACKUP")
    for name, result in results:
        print(name + ": " + result)
    print()
    print("Report:", report_path)
    print("No backup was created.")
    print("No push was made.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
