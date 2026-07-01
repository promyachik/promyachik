from pathlib import Path
import re
import subprocess
import sys
import hashlib

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_298_konate_current_price_overlay_and_ticker_stabilize_no_backup_report.txt"

PATCH_NAME = "298_KONATE_CURRENT_PRICE_OVERLAY_AND_TICKER_STABILIZE_NO_BACKUP"
KONATE_SLUG = "ibrahima-konate-real-madrid"

PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
CHART_CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
TICKER_CSS = ROOT / "static" / "css" / "transfer-ticker.css"
PUBLIC_CHART_CSS = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_TICKER_CSS = ROOT / "public" / "css" / "transfer-ticker.css"
KONATE_CONTENT = ROOT / "content" / "transfers" / KONATE_SLUG / "index.md"
RAMOS_CONTENT = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
TARGET_HTML = ROOT / "public" / "transfers" / KONATE_SLUG / "index.html"

log = []

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def sha(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def remove_blocks(text: str, numbers=(294, 295, 296, 297, 298)) -> str:
    original = text
    for n in numbers:
        # Remove our marked CSS/HTML/JS blocks even if the middle title differs.
        text = re.sub(
            rf"\s*/\*\s*(?:PROMYACHIK|PROFUTBIK)\s+{n}\b[\s\S]*?START\s*\*/[\s\S]*?/\*\s*(?:PROMYACHIK|PROFUTBIK)\s+{n}\b[\s\S]*?END\s*\*/\s*",
            "\n",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"\s*<!--\s*(?:PROMYACHIK|PROFUTBIK)\s+{n}\b[\s\S]*?START\s*-->[\s\S]*?<!--\s*(?:PROMYACHIK|PROFUTBIK)\s+{n}\b[\s\S]*?END\s*-->\s*",
            "\n",
            text,
            flags=re.IGNORECASE,
        )
    return text

def ensure_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(str(path))

try:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    log.append(f"PATCH: {PATCH_NAME}")
    log.append("GOAL: leave Ramos untouched, stabilize ticker, and add a true Konate current-price overlay under the final chart dot.")
    log.append("NO BACKUP CREATED")
    log.append("")

    for p in [PARTIAL, CHART_CSS, TICKER_CSS, KONATE_CONTENT]:
        ensure_file(p)
        log.append(f"exists: {p.relative_to(ROOT)}")

    ramos_sha_before = sha(RAMOS_CONTENT)
    konate_sha_before = sha(KONATE_CONTENT)

    # 1) Clean failed experiment blocks from the chart partial and CSS files.
    partial_text = read(PARTIAL)
    partial_text_clean = remove_blocks(partial_text)

    konate_overlay_block = r'''
{{- if in .RelPermalink "ibrahima-konate-real-madrid" -}}
<!-- PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY START -->
<script>
(function(){
  function applyPromyachikKonateCurrentPrice298(){
    if (!/\/transfers\/ibrahima-konate-real-madrid\/?/.test(window.location.pathname)) return;
    document.querySelectorAll('.player-market-chart').forEach(function(chart){
      var canvas = chart.querySelector('.player-market-chart__canvas');
      var svg = canvas && canvas.querySelector('svg');
      var dots = svg ? svg.querySelectorAll('.player-market-chart__dot') : [];
      var lastDot = dots.length ? dots[dots.length - 1] : null;
      var points = chart.querySelectorAll('.player-market-chart__point');
      var lastPoint = points.length ? points[points.length - 1] : null;
      var strong = lastPoint ? lastPoint.querySelector('strong') : null;
      var text = strong ? strong.textContent.trim() : '';
      if (!canvas || !svg || !lastDot || !text) return;

      chart.classList.add('promyachik-konate-chart-298');
      if (lastPoint) lastPoint.classList.add('player-market-chart__point--promyachik-298-current');

      var badge = chart.querySelector('.promyachik-current-price-badge-298');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'promyachik-current-price-badge-298';
        canvas.appendChild(badge);
      }
      badge.textContent = text;

      function placeBadge(){
        var canvasRect = canvas.getBoundingClientRect();
        var dotRect = lastDot.getBoundingClientRect();
        var left = dotRect.left - canvasRect.left + dotRect.width / 2;
        var top = dotRect.bottom - canvasRect.top + 7;
        badge.style.left = left + 'px';
        badge.style.top = top + 'px';
      }

      placeBadge();
      if (!chart.dataset.promyachik298ResizeBound) {
        chart.dataset.promyachik298ResizeBound = '1';
        window.addEventListener('resize', placeBadge, { passive: true });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyPromyachikKonateCurrentPrice298);
  } else {
    applyPromyachikKonateCurrentPrice298();
  }
  window.addEventListener('load', applyPromyachikKonateCurrentPrice298, { once: true });
})();
</script>
<!-- PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY END -->
{{- end -}}
'''

    if konate_overlay_block.strip() not in partial_text_clean:
        end_token = "{{- end -}}"
        idx = partial_text_clean.rfind(end_token)
        if idx >= 0:
            partial_text_clean = partial_text_clean[:idx] + "\n" + konate_overlay_block + "\n" + partial_text_clean[idx:]
        else:
            partial_text_clean += "\n" + konate_overlay_block + "\n"

    write(PARTIAL, partial_text_clean)
    log.append("patched: layouts/partials/transfer-player-market-value-chart.html")

    chart_css = read(CHART_CSS)
    chart_css = remove_blocks(chart_css)
    chart_css_block = r'''
/* PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY START */
body.transfer-page .promyachik-konate-chart-298 .promyachik-current-price-badge-298 {
  position: absolute;
  z-index: 9;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 7px 2px;
  border: 1px solid rgba(245, 203, 92, 0.46);
  border-radius: 999px;
  color: #f5cb5c !important;
  background: rgba(8, 10, 13, 0.86);
  box-shadow: 0 0 14px rgba(245, 203, 92, 0.24), 0 4px 14px rgba(0, 0, 0, 0.34);
  font-family: "Russo One", "Montserrat", Arial, sans-serif;
  font-size: 9px;
  font-weight: 400;
  line-height: 1;
  letter-spacing: 0.012em;
  white-space: nowrap;
  pointer-events: none;
  transform: translate(-50%, 0);
}
body.transfer-page .promyachik-konate-chart-298 .player-market-chart__point--promyachik-298-current strong {
  color: #f1f3f5 !important;
  text-shadow: 0 0 8px rgba(231, 198, 91, 0.14) !important;
}
.player-market-chart-modal .promyachik-konate-chart-298 .promyachik-current-price-badge-298 {
  font-size: 14px;
  padding: 5px 10px 4px;
}
/* PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY END */
'''
    chart_css = chart_css.rstrip() + "\n" + chart_css_block + "\n"
    write(CHART_CSS, chart_css)
    log.append("patched: static/css/transfer-player-market-value-chart.css")

    # Sync public CSS if it exists. Hugo will regenerate too, but this helps local static serving.
    if PUBLIC_CHART_CSS.exists():
        public_chart_css = read(PUBLIC_CHART_CSS)
        public_chart_css = remove_blocks(public_chart_css)
        public_chart_css = public_chart_css.rstrip() + "\n" + chart_css_block + "\n"
        write(PUBLIC_CHART_CSS, public_chart_css)
        log.append("synced: public/css/transfer-player-market-value-chart.css")

    # 2) Stabilize ticker without changing its position or layout.
    ticker_css = read(TICKER_CSS)
    ticker_css = remove_blocks(ticker_css, numbers=(298,))
    ticker_block = r'''
/* PROMYACHIK 298 TICKER STABILIZE START */
.pf-ticker,
.pf-ticker__viewport,
.pf-ticker__track {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  transform-style: preserve-3d;
}
.pf-ticker {
  contain: paint;
  transform: translateZ(0);
}
.pf-ticker__track {
  will-change: transform;
}
@keyframes pfTickerScroll {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-50%, 0, 0); }
}
/* PROMYACHIK 298 TICKER STABILIZE END */
'''
    ticker_css = ticker_css.rstrip() + "\n" + ticker_block + "\n"
    write(TICKER_CSS, ticker_css)
    log.append("patched: static/css/transfer-ticker.css")

    if PUBLIC_TICKER_CSS.exists():
        public_ticker_css = read(PUBLIC_TICKER_CSS)
        public_ticker_css = remove_blocks(public_ticker_css, numbers=(298,))
        public_ticker_css = public_ticker_css.rstrip() + "\n" + ticker_block + "\n"
        write(PUBLIC_TICKER_CSS, public_ticker_css)
        log.append("synced: public/css/transfer-ticker.css")

    # Confirm we did not touch content files.
    konate_sha_after = sha(KONATE_CONTENT)
    ramos_sha_after = sha(RAMOS_CONTENT)
    log.append("")
    log.append(f"konate_content_unchanged: {konate_sha_before == konate_sha_after}")
    log.append(f"ramos_content_unchanged: {ramos_sha_before == ramos_sha_after}")

    # Run Hugo.
    hugo = subprocess.run(["hugo", "-D"], cwd=str(ROOT), text=True, capture_output=True)
    log.append("")
    log.append(f"hugo_exit_code: {hugo.returncode}")
    if hugo.stdout:
        log.append("hugo_stdout:")
        log.append(hugo.stdout[-3000:])
    if hugo.stderr:
        log.append("hugo_stderr:")
        log.append(hugo.stderr[-3000:])

    target_html_exists = TARGET_HTML.exists()
    target_html = read(TARGET_HTML) if target_html_exists else ""
    checks = {
        "target_html_exists": target_html_exists,
        "target_has_298_script": "promyachik-current-price-badge-298" in target_html,
        "target_is_konate": KONATE_SLUG in str(TARGET_HTML),
        "ticker_css_has_298": "PROMYACHIK 298 TICKER STABILIZE START" in read(TICKER_CSS),
        "chart_css_has_298": "PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY START" in read(CHART_CSS),
        "partial_has_298": "PROMYACHIK 298 KONATE CURRENT PRICE OVERLAY START" in read(PARTIAL),
        "ramos_content_unchanged": ramos_sha_before == ramos_sha_after,
        "konate_content_unchanged": konate_sha_before == konate_sha_after,
        "hugo_ok": hugo.returncode == 0,
    }
    log.append("")
    log.append("CHECKS:")
    for k, v in checks.items():
        log.append(f"{k}: {v}")

    ok = all(checks.values())
    log.append("")
    log.append(f"VERIFIED_OK: {ok}")
    write(REPORT, "\n".join(log) + "\n")

    if not ok:
        sys.exit(1)
    sys.exit(0)

except Exception as e:
    log.append("")
    log.append("EXCEPTION:")
    log.append(repr(e))
    try:
        write(REPORT, "\n".join(log) + "\n")
    except Exception:
        pass
    sys.exit(1)
