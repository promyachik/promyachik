from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_300_konate_hide_duplicate_white_current_price_no_backup_report.txt"
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
PUBLIC_JS = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"

START_JS = "// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE START"
END_JS = "// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE END"

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

JS_BLOCK = r'''
// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE START
(function () {
  var KONATE_PATH = "/transfers/ibrahima-konate-real-madrid/";
  var rafId = 0;
  var observerStarted = false;

  function isKonatePage() {
    return window.location && window.location.pathname && window.location.pathname.indexOf(KONATE_PATH) !== -1;
  }

  function norm(text) {
    return String(text || "")
      .replace(/\u00a0/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function isCurrentKonatePrice(text) {
    var t = norm(text);
    return t === "€45 млн" || t === "€45m" || t === "€45 m" || t === "€45млн" || t === "45 млн";
  }

  function hasChildWithSameExactPrice(el) {
    var children = Array.prototype.slice.call(el.children || []);
    return children.some(function (child) {
      return isCurrentKonatePrice(child.textContent);
    });
  }

  function hideDuplicateWhitePrice() {
    if (!isKonatePage()) return false;

    var chart = document.querySelector('.player-market-chart');
    if (!chart) return false;

    var chartRect = chart.getBoundingClientRect();
    if (!chartRect || chartRect.width <= 0 || chartRect.height <= 0) return false;

    var hidden = 0;
    var all = Array.prototype.slice.call(document.querySelectorAll('body *'));

    all.forEach(function (el) {
      if (!el || el === chart || chart.contains(el)) return;
      if (el.closest && el.closest('.player-market-chart')) return;
      if (el.closest && el.closest('script, style, noscript')) return;

      var text = norm(el.textContent);
      if (!isCurrentKonatePrice(text)) return;

      // Prefer hiding the deepest visible exact-price node, not a large wrapper.
      if (hasChildWithSameExactPrice(el)) return;

      var rect = el.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) return;

      // The duplicate from the screenshot is below the chart. Do not touch any title/hero price above it.
      if (rect.top < chartRect.bottom - 4) return;

      el.setAttribute('data-promyachik-hidden-konate-duplicate-current-price-300', '1');
      el.style.setProperty('display', 'none', 'important');
      el.style.setProperty('visibility', 'hidden', 'important');
      el.style.setProperty('opacity', '0', 'important');
      hidden += 1;
    });

    if (hidden > 0) {
      document.body.classList.add('promyachik-konate-duplicate-current-price-hidden-300');
    }
    return hidden > 0;
  }

  function schedule() {
    if (!isKonatePage()) return;
    if (rafId) window.cancelAnimationFrame(rafId);
    rafId = window.requestAnimationFrame(function () {
      rafId = 0;
      hideDuplicateWhitePrice();
    });
  }

  function startObserver() {
    if (observerStarted || !isKonatePage() || !document.body || !window.MutationObserver) return;
    observerStarted = true;
    var mo = new MutationObserver(function () {
      schedule();
    });
    mo.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      schedule();
      startObserver();
    });
  } else {
    schedule();
    startObserver();
  }

  window.addEventListener('load', schedule);
  window.addEventListener('resize', schedule);
  setTimeout(schedule, 120);
  setTimeout(schedule, 350);
  setTimeout(schedule, 900);
  setTimeout(schedule, 1600);
})();
// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE END
'''

try:
    log("PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE")
    log(f"started_at={datetime.now().isoformat(timespec='seconds')}")
    log(f"root={ROOT}")

    if not ROOT.exists():
        raise RuntimeError(f"Project root not found: {ROOT}")
    if not JS.exists():
        raise RuntimeError(f"JS file not found: {JS}")

    js_text = read_text(JS)
    js_text, removed_300 = strip_block(js_text, START_JS, END_JS)
    js_text = js_text.rstrip() + "\n\n" + JS_BLOCK.strip() + "\n"
    write_text(JS, js_text)
    log(f"updated_js={JS}")
    log(f"removed_existing_300_js_blocks={removed_300}")

    if PUBLIC_JS.exists():
        write_text(PUBLIC_JS, js_text)
        log(f"synced_public_js={PUBLIC_JS}")
    else:
        log("synced_public_js=skipped_missing")

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
    public_js_text = read_text(PUBLIC_JS) if PUBLIC_JS.exists() else ""
    static_js_text = read_text(JS)

    checks = {
        "target_html_exists": target.exists(),
        "static_js_has_300_marker": START_JS in static_js_text and END_JS in static_js_text,
        "public_js_has_300_marker": START_JS in public_js_text and END_JS in public_js_text,
        "target_references_chart_js": "transfer-player-market-value-chart.js" in html,
        "target_is_konate": "konate" in html.lower() or "konaté" in html.lower(),
        "target_contains_current_price_text": "€45" in html or "45 млн" in html,
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
