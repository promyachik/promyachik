from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_297_unified_chart_fallback_and_current_price_highlight_no_backup_report.txt"
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
TARGET_PUBLIC = ROOT / "public" / "transfers" / "ibrahima-konate-real-madrid" / "index.html"

START = "/* PROMYACHIK 297 CURRENT PRICE HIGHLIGHT START */"
END = "/* PROMYACHIK 297 CURRENT PRICE HIGHLIGHT END */"

PARTIAL_TEXT = r'''{{- $page := . -}}
{{- $chart := .Params.market_value_chart -}}
{{- $points := slice -}}
{{- $path := "" -}}
{{- $areaPath := "" -}}
{{- $currentLabel := "" -}}
{{- $updatedAt := "" -}}
{{- $sourceURL := "" -}}
{{- $sourceName := "Transfermarkt" -}}
{{- $note := "Оценочная стоимость, не сумма трансфера." -}}

{{- with $chart -}}
  {{- $points = default (slice) .points -}}
  {{- $path = default "" .path -}}
  {{- $areaPath = default "" .area_path -}}
  {{- $currentLabel = default (default "" .current_value) .current_label -}}
  {{- $updatedAt = default "" .updated_at -}}
  {{- $sourceURL = default "" .source_url -}}
  {{- $sourceName = default $sourceName .source_name -}}
  {{- $note = default $note .note -}}
{{- else -}}
  {{- $marketData := index .Site.Data "player-market-values" -}}
  {{- $playerID := printf "%v" .Params.player_id -}}
  {{- with $marketData -}}
    {{- $updatedAt = default "" .updated_at -}}
    {{- $sourceName = default $sourceName .source -}}
    {{- $note = default $note .note -}}
    {{- range .players -}}
      {{- if eq (printf "%v" .player_id) $playerID -}}
        {{- $points = default (slice) .points -}}
        {{- $path = default "" .path -}}
        {{- $areaPath = default "" .area_path -}}
        {{- $currentLabel = default "" .current_value_label -}}
        {{- $sourceURL = default "" .source_url -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- if gt (len $points) 0 -}}
  {{- $pointCount := len $points -}}
  {{- $lastIndex := sub $pointCount 1 -}}
  <section class="player-market-chart player-market-chart--zoomable" style="--market-point-count: {{ $pointCount }};" data-player-id="{{ .Params.player_id }}" data-player="{{ .Params.player }}">
    <div class="player-market-chart__canvas" aria-label="Динамика стоимости {{ .Params.player }}">
      <svg viewBox="0 0 320 120" role="img" aria-hidden="true" focusable="false">
        <path class="player-market-chart__grid" d="M 20 26 H 300 M 20 54 H 300 M 20 82 H 300 M 20 110 H 300"></path>
        {{- with $areaPath }}<path class="player-market-chart__area" d="{{ . }}"></path>{{ end -}}
        {{- with $path }}<path class="player-market-chart__line" d="{{ . }}"></path>{{ end -}}
        {{- range $index, $point := $points -}}
          {{- $x := float (default 20 $point.x) -}}
          {{- $y := float (default 110 $point.y) -}}
          <circle class="player-market-chart__dot{{ if eq $index $lastIndex }} player-market-chart__dot--current{{ end }}" cx="{{ printf "%.2f" $x }}" cy="{{ printf "%.2f" $y }}" r="3.8"></circle>
        {{- end -}}
      </svg>
      <div class="player-market-chart__club-layer" aria-hidden="true">
        {{- range $index, $point := $points -}}
          {{- $logo := default (default "" $point.club_logo) $point.logo -}}
          {{- if $logo -}}
            {{- $x := float (default 20 $point.x) -}}
            {{- $y := float (default 110 $point.y) -}}
            {{- $left := printf "%.4f%%" (mul (div $x 320.0) 100.0) -}}
            {{- $top := printf "%.4f%%" (mul (div $y 120.0) 100.0) -}}
            {{- $clubSlug := default "" $point.club_slug -}}
            <span class="player-market-chart__club-marker{{ if eq $index $lastIndex }} player-market-chart__club-marker--last{{ end }}" data-club-slug="{{ $clubSlug }}" style="left: {{ $left }}; top: {{ $top }};">
              <img class="player-market-chart__club-logo" src="{{ $logo | relURL }}" alt="">
            </span>
          {{- end -}}
        {{- end -}}
      </div>
    </div>
    <div class="player-market-chart__points">
      {{- range $index, $point := $points -}}
        {{- $dateLabel := default (default "" $point.date) $point.date_label -}}
        {{- $valueLabel := default "—" $point.value_label -}}
        <div class="player-market-chart__point{{ if eq $index $lastIndex }} player-market-chart__point--current{{ end }}">
          <small>{{ $dateLabel }}</small>
          <strong>{{ $valueLabel }}</strong>
        </div>
      {{- end -}}
    </div>
    <p class="player-market-chart__note">
      {{ $note }}{{ with $updatedAt }} Обновлено {{ . }}.{{ end }}{{ with $sourceURL }} Источник: <a href="{{ . }}" target="_blank" rel="nofollow noopener">{{ $sourceName }}</a>.{{ end }}
    </p>
  </section>
{{- end -}}
'''

CSS_BLOCK = f'''{START}
/* Unified current-price test. No content/front matter rewrite. */
body.transfer-page .player-market-chart__point--current strong,
body.transfer-page .player-market-chart__points .player-market-chart__point:last-child strong,
.player-market-chart-modal .player-market-chart__point--current strong,
.player-market-chart-modal .player-market-chart__points .player-market-chart__point:last-child strong {{
  display: inline-block !important;
  color: #f3cf57 !important;
  transform: translateY(-3px) !important;
  text-shadow: 0 0 9px rgba(243, 207, 87, 0.36), 0 0 18px rgba(243, 207, 87, 0.16) !important;
}}
body.transfer-page .player-market-chart__dot--current,
.player-market-chart-modal .player-market-chart__dot--current {{
  fill: #f3cf57 !important;
  stroke: #fff1a8 !important;
  filter: drop-shadow(0 0 6px rgba(243, 207, 87, 0.45)) !important;
}}
/* Compatibility with the old 249/279 price overlay layer, if it is present. */
body.transfer-page .promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249:last-child .promyachik-cucurella-price-label-249__value,
.player-market-chart-modal .promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249:last-child .promyachik-cucurella-price-label-249__value {{
  display: inline-block !important;
  color: #f3cf57 !important;
  transform: translateY(-3px) !important;
  text-shadow: 0 0 9px rgba(243, 207, 87, 0.36), 0 0 18px rgba(243, 207, 87, 0.16) !important;
}}
{END}
'''


def write_report(lines):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replace_marker_block(text: str, start: str, end: str, replacement: str = "") -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end) + r"\s*"
    return re.sub(pattern, replacement, text, flags=re.S)


def main():
    lines = []
    lines.append("PROMYACHIK 297 - unified chart fallback and current price highlight")
    lines.append("NO BACKUP CREATED")
    ok = True

    if not PARTIAL.exists():
        lines.append(f"ERROR: missing partial: {PARTIAL}")
        ok = False
    if not CSS.exists():
        lines.append(f"ERROR: missing css: {CSS}")
        ok = False
    if not ok:
        write_report(lines)
        return 1

    old_partial = PARTIAL.read_text(encoding="utf-8", errors="replace")
    lines.append(f"old_partial_size={len(old_partial)}")
    PARTIAL.write_text(PARTIAL_TEXT, encoding="utf-8")
    lines.append("partial_replaced=layouts/partials/transfer-player-market-value-chart.html")

    css = CSS.read_text(encoding="utf-8", errors="replace")
    css = replace_marker_block(css, START, END, "")
    css = css.rstrip() + "\n\n" + CSS_BLOCK + "\n"
    CSS.write_text(css, encoding="utf-8")
    lines.append("css_marker_written=True")

    # Clean only known failed-test markers if they exist; no broad content rewrites.
    for rel in [
        Path("static/js/transfer-player-market-value-chart.js"),
        Path("layouts/transfers/single.html"),
        Path("content/transfers/ibrahima-konate-real-madrid/index.md"),
    ]:
        p = ROOT / rel
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="replace")
            original = txt
            for n in ["294", "295", "296"]:
                for label in [
                    f"/* PROMYACHIK {n} KONATE HIGHLIGHT CURRENT PRICE START */",
                    f"/* PROMYACHIK {n} KONATE HIGHLIGHT CURRENT PRICE END */",
                    f"<!-- PROMYACHIK {n} KONATE HIGHLIGHT CURRENT PRICE START -->",
                    f"<!-- PROMYACHIK {n} KONATE HIGHLIGHT CURRENT PRICE END -->",
                ]:
                    pass
            # Conservative marker removal patterns.
            txt = re.sub(r"/\*\s*PROMYACHIK\s+(294|295|296)[\s\S]*?END\s*\*/\s*", "", txt)
            txt = re.sub(r"<!--\s*PROMYACHIK\s+(294|295|296)[\s\S]*?END\s*-->\s*", "", txt)
            if txt != original:
                p.write_text(txt, encoding="utf-8")
                lines.append(f"cleaned_failed_test_markers={rel}")

    # Build site and verify generated Konate page has the chart and current price label.
    try:
        proc = subprocess.run(["hugo", "-D"], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        lines.append(f"hugo_exit_code={proc.returncode}")
        if proc.stdout.strip():
            lines.append("hugo_stdout_START")
            lines.append(proc.stdout.strip()[-4000:])
            lines.append("hugo_stdout_END")
        if proc.stderr.strip():
            lines.append("hugo_stderr_START")
            lines.append(proc.stderr.strip()[-4000:])
            lines.append("hugo_stderr_END")
        if proc.returncode != 0:
            ok = False
    except Exception as e:
        lines.append(f"ERROR: hugo_exception={e!r}")
        ok = False

    html = ""
    if TARGET_PUBLIC.exists():
        html = TARGET_PUBLIC.read_text(encoding="utf-8", errors="replace")
        lines.append("target_html_exists=True")
    else:
        lines.append("target_html_exists=False")
        ok = False

    checks = {
        "target_has_player_market_chart": "player-market-chart" in html,
        "target_has_current_class": "player-market-chart__point--current" in html,
        "target_has_konate_price_45": ("€45" in html or "45 млн" in html),
        "css_has_297_marker": START in CSS.read_text(encoding="utf-8", errors="replace"),
        "partial_has_data_fallback": 'index .Site.Data "player-market-values"' in PARTIAL.read_text(encoding="utf-8", errors="replace"),
    }
    for k, v in checks.items():
        lines.append(f"{k}={v}")
        if not v:
            ok = False

    lines.append(f"VERIFIED_OK={ok}")
    write_report(lines)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
