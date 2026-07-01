from pathlib import Path
import subprocess
import datetime
import sys

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
JS_PATH = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
REPORT_PATH = ROOT / "var" / "promyachik_280_shorten_thousand_euro_labels_to_k_no_backup_report.txt"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

START = "/* PROMYACHIK 280 SHORTEN THOUSAND EURO LABELS TO K START */"
END = "/* PROMYACHIK 280 SHORTEN THOUSAND EURO LABELS TO K END */"

BLOCK = r'''
/* PROMYACHIK 280 SHORTEN THOUSAND EURO LABELS TO K START */
(function () {
  "use strict";

  if (window.__promyachik280ShortenThousandEuroLabelsReady) {
    return;
  }
  window.__promyachik280ShortenThousandEuroLabelsReady = true;

  const normalizeMarketText280 = function (text) {
    if (!text || !/(тыс|тысяч)/i.test(text)) {
      return text;
    }

    return String(text)
      .replace(/€\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:тысяч|тыс\.?)\s*(?:евро)?/gi, "€$1K")
      .replace(/([0-9]+(?:[.,][0-9]+)?)\s*(?:тысяч|тыс\.?)\s*евро/gi, "$1K")
      .replace(/([0-9]+(?:[.,][0-9]+)?)\s*(?:тысяч|тыс\.?)\b/gi, "$1K")
      .replace(/\s+K\b/g, "K");
  };

  const normalizeChartNode280 = function (root) {
    const base = root && root.nodeType === 1 ? root : document;
    const charts = [];

    if (base.matches && base.matches(".player-market-chart")) {
      charts.push(base);
    }

    if (base.querySelectorAll) {
      base.querySelectorAll(".player-market-chart").forEach(function (chart) {
        charts.push(chart);
      });
    }

    charts.forEach(function (chart) {
      const walker = document.createTreeWalker(chart, NodeFilter.SHOW_TEXT);
      const textNodes = [];
      let node = walker.nextNode();

      while (node) {
        textNodes.push(node);
        node = walker.nextNode();
      }

      textNodes.forEach(function (textNode) {
        const nextValue = normalizeMarketText280(textNode.nodeValue);
        if (nextValue !== textNode.nodeValue) {
          textNode.nodeValue = nextValue;
        }
      });
    });
  };

  const runNormalize280 = function () {
    normalizeChartNode280(document);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runNormalize280, { once: true });
  } else {
    runNormalize280();
  }

  window.requestAnimationFrame(runNormalize280);
  window.setTimeout(runNormalize280, 150);
  window.setTimeout(runNormalize280, 500);

  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        normalizeChartNode280(node);
      });
    });
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
/* PROMYACHIK 280 SHORTEN THOUSAND EURO LABELS TO K END */
'''.strip() + "\n"

log = []
log.append("PROMYACHIK 280 - SHORTEN THOUSAND EURO LABELS TO K - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Convert visible thousand-euro labels like 300 тысяч / 300 тыс / €300 тысяч to 300K / €300K.")
log.append("- Apply to all current and future player market charts at runtime.")
log.append("- Do not move prices.")
log.append("- Do not touch JS positioning logic.")
log.append("- Do not touch CSS, templates, or content.")
log.append("- Do not create backup.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

try:
    if not JS_PATH.exists():
        raise FileNotFoundError(f"JS not found: {JS_PATH}")

    text = JS_PATH.read_text(encoding="utf-8")
    old_text = text

    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        text = before.rstrip() + "\n\n" + BLOCK + after.lstrip("\n")
        log.append("existing 280 block: replaced")
    else:
        text = text.rstrip() + "\n\n" + BLOCK
        log.append("existing 280 block: not found, appended")

    changed = text != old_text
    JS_PATH.write_text(text, encoding="utf-8")
    log.append(f"CHANGED: {JS_PATH} | changed={changed}")

    proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
    log.append("")
    log.append("HUGO")
    log.append("COMMAND: hugo -D")
    log.append(f"EXIT_CODE: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2500:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2500:])

    public_js = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
    static_text = JS_PATH.read_text(encoding="utf-8", errors="ignore")
    public_text = public_js.read_text(encoding="utf-8", errors="ignore") if public_js.exists() else ""

    log.append("")
    log.append("CHECKS")
    log.append(f"backup_created: False")
    log.append(f"static_js_has_280_marker: {START in static_text and END in static_text}")
    log.append(f"public_js_exists: {public_js.exists()}")
    log.append(f"public_js_has_280_marker: {START in public_text and END in public_text}")
    log.append(f"hugo_exit_code: {proc.returncode}")

    ok = proc.returncode == 0 and START in static_text and public_js.exists() and START in public_text
    log.append("")
    log.append("DONE" if ok else "FAILED")
    REPORT_PATH.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print(f"REPORT: {REPORT_PATH}")
    sys.exit(0 if ok else 1)

except Exception as exc:
    log.append(f"ERROR: {type(exc).__name__}: {exc}")
    log.append("")
    log.append("FAILED")
    REPORT_PATH.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT_PATH}")
    sys.exit(1)
