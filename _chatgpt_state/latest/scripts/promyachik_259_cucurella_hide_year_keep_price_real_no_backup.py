from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

PACKAGE = "259"
NAME = "CUCURELLA_HIDE_YEAR_KEEP_PRICE_REAL_NO_BACKUP"

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "var"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "promyachik_259_cucurella_hide_year_keep_price_real_no_backup_report.txt"

PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE = ROOT / "static" / "css" / "style.css"
CHART_CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"

MARKER_START = "/* PROMYACHIK 259 CUCURELLA HIDE YEAR KEEP PRICE START */"
MARKER_END = "/* PROMYACHIK 259 CUCURELLA HIDE YEAR KEEP PRICE END */"

CSS_BLOCK = f"""{MARKER_START}
/* Only the year/date row in the Cucurella 249 price layer is hidden. Price value stays visible. */
.promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249__date,
.promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249__date-hidden-259 {{
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 0 !important;
  overflow: hidden !important;
}}
.promyachik-cucurella-price-layer-249 .promyachik-cucurella-price-label-249__value {{
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.08 !important;
  white-space: nowrap !important;
}}
{MARKER_END}
"""

report: list[str] = []
changed_files: list[str] = []
errors: list[str] = []

def log(s: str = "") -> None:
    report.append(s)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text_if_changed(path: Path, text: str, label: str) -> bool:
    old = read_text(path) if path.exists() else None
    if old == text:
        log(f"UNCHANGED: {path} | {label}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    changed_files.append(str(path.relative_to(ROOT)))
    log(f"CHANGED: {path} | {label}")
    return True


def remove_marker_block(text: str) -> tuple[str, int]:
    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\s*", re.S)
    return pattern.subn("", text)


def patch_partial() -> None:
    if not PARTIAL.exists():
        errors.append(f"Missing partial: {PARTIAL}")
        return
    text = read_text(PARTIAL)
    original = text

    # Remove broken/empty previous 258 marker blocks if present, but do not touch the price value.
    text, n258 = re.subn(
        r"\n?\s*<!-- PROMYACHIK 258 CUCURELLA HIDE YEAR KEEP PRICE START -->.*?<!-- PROMYACHIK 258 CUCURELLA HIDE YEAR KEEP PRICE END -->\s*\n?",
        "\n",
        text,
        flags=re.S,
    )
    log(f"partial: removed old 258 marker blocks: {n258}")

    target = '<span class="promyachik-cucurella-price-label-249__date">'
    replacement = '<span class="promyachik-cucurella-price-label-249__date promyachik-cucurella-price-label-249__date-hidden-259" aria-hidden="true">'

    if replacement in text:
        log("partial: 259 date span already patched")
    elif target in text:
        text = text.replace(target, replacement, 1)
        log("partial: patched exact Cucurella 249 date span: replacements=1")
    else:
        # Fallback: add hidden class to date span even if attributes were reformatted.
        text2, n = re.subn(
            r'(<span\s+class="[^"]*promyachik-cucurella-price-label-249__date[^"]*)"([^>]*>)',
            lambda m: (m.group(1) if "date-hidden-259" in m.group(1) else m.group(1) + " promyachik-cucurella-price-label-249__date-hidden-259") + '" aria-hidden="true"' + m.group(2),
            text,
            count=1,
            flags=re.S,
        )
        text = text2
        log(f"partial: fallback patch date span: replacements={n}")
        if n == 0:
            errors.append("Could not find Cucurella 249 date span in partial")

    # Hard safety: value tag must stay in partial.
    if "promyachik-cucurella-price-label-249__value" not in text:
        errors.append("Price value class missing after partial patch")

    if text != original:
        write_text_if_changed(PARTIAL, text, "hide only Cucurella 249 date span; keep value strong")
    else:
        log(f"UNCHANGED: {PARTIAL} | no partial change needed")


def patch_css_file(path: Path) -> None:
    if not path.exists():
        log(f"SKIP: {path} | css file not found")
        return
    text = read_text(path)
    text, removed = remove_marker_block(text)
    if removed:
        log(f"{path.name}: removed previous 259 marker block: {removed}")
    if not text.endswith("\n"):
        text += "\n"
    text = text + "\n" + CSS_BLOCK + "\n"
    write_text_if_changed(path, text, "append exact 259 CSS: hide date only, force price visible")


def run_hugo() -> tuple[int | None, str, str]:
    try:
        cp = subprocess.run(
            ["hugo", "-D"],
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        return cp.returncode, cp.stdout, cp.stderr
    except FileNotFoundError:
        return None, "", "hugo executable not found"
    except subprocess.TimeoutExpired as exc:
        return None, exc.stdout or "", "hugo -D timed out"


def verify_public() -> None:
    public_root = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid"
    html = public_root / "index.html"
    if not html.exists():
        log("VERIFY: public Cucurella html not found")
        return
    h = read_text(html)
    log("VERIFY PUBLIC CUCURELLA")
    log(f"- html_exists: True")
    log(f"- has_249_date_class: {'promyachik-cucurella-price-label-249__date' in h}")
    log(f"- has_259_hidden_class: {'promyachik-cucurella-price-label-249__date-hidden-259' in h}")
    log(f"- has_249_value_class: {'promyachik-cucurella-price-label-249__value' in h}")
    euro_count = h.count('€')
    log(f"- euro_symbol_count: {euro_count}")


def main() -> int:
    log(f"PROMYACHIK {PACKAGE} - {NAME}")
    log("=" * 100)
    log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Project dir: {ROOT}")
    log("")
    log("RULE")
    log("- Hide only the year/date row in Cucurella 249 price labels.")
    log("- Keep price labels visible.")
    log("- Do not move prices in this package.")
    log("- Do not touch markdown content.")
    log("- Do not create any backup folder or file.")
    log("- No push.")
    log("- No site opened.")
    log("")
    log("NO BACKUP")
    log("- Full backup: NOT CREATED")
    log("- Safety backup: NOT CREATED")
    log("")

    patch_partial()
    patch_css_file(STYLE)
    patch_css_file(CHART_CSS)

    log("")
    log("CHANGED FILES")
    for f in changed_files:
        log(f"- {f}")
    log(f"EFFECTIVE_CHANGED_FILES: {len(changed_files)}")

    code, out, err = run_hugo()
    log("")
    log("HUGO")
    log("COMMAND: hugo -D")
    log(f"EXIT_CODE: {code}")
    if out:
        log("--- STDOUT tail ---")
        log("\n".join(out.splitlines()[-35:]))
    if err:
        log("--- STDERR tail ---")
        log("\n".join(err.splitlines()[-35:]))

    verify_public()

    partial_text = read_text(PARTIAL) if PARTIAL.exists() else ""
    style_text = read_text(STYLE) if STYLE.exists() else ""
    chart_css_text = read_text(CHART_CSS) if CHART_CSS.exists() else ""

    ok = (
        code == 0
        and not errors
        and "promyachik-cucurella-price-label-249__date-hidden-259" in partial_text
        and "promyachik-cucurella-price-label-249__value" in partial_text
        and MARKER_START in style_text
        and (not CHART_CSS.exists() or MARKER_START in chart_css_text)
    )

    log("")
    log("CHECKS")
    log(f"hugo_exit_code: {code}")
    log(f"backup_created: False")
    log(f"partial_has_259_hidden_date_class: {'promyachik-cucurella-price-label-249__date-hidden-259' in partial_text}")
    log(f"partial_has_value_class: {'promyachik-cucurella-price-label-249__value' in partial_text}")
    log(f"style_has_259_css: {MARKER_START in style_text}")
    log(f"chart_css_has_259_css: {(MARKER_START in chart_css_text) if CHART_CSS.exists() else 'SKIPPED'}")
    if errors:
        log("ERRORS")
        for e in errors:
            log(f"- {e}")
    log(f"VERIFIED_OK: {ok}")
    log("")
    log("NO BACKUP CREATED.")
    log("NO PUSH MADE.")
    log("NO SITE OPENED.")

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    print("DONE" if ok else "DONE_WITH_WARNINGS")
    print(f"REPORT: {REPORT_PATH}")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
