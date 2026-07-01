from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_301_revert_300_restore_konate_299_no_backup_report.txt"
JS = ROOT / "static" / "js" / "transfer-player-market-value-chart.js"
CSS = ROOT / "static" / "css" / "transfer-player-market-value-chart.css"
PUBLIC_JS = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
PUBLIC_CSS = ROOT / "public" / "css" / "transfer-player-market-value-chart.css"

START_300 = "// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE START"
END_300 = "// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE END"
START_299_JS = "// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START"
END_299_JS = "// PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END"
START_299_CSS = "/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER START */"
END_299_CSS = "/* PROMYACHIK 299 KONATE MOVE ALL PRICES UNDER DOTS GOLD NO BORDER END */"

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

try:
    log("PROMYACHIK 301 REVERT 300 RESTORE KONATE 299")
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

    js_text, removed_300_static = strip_block(js_text, START_300, END_300)
    write_text(JS, js_text.rstrip() + "\n")
    log(f"removed_300_from_static_js={removed_300_static}")

    removed_300_public = 0
    if PUBLIC_JS.exists():
        public_js_text = read_text(PUBLIC_JS)
        public_js_text, removed_300_public = strip_block(public_js_text, START_300, END_300)
        write_text(PUBLIC_JS, public_js_text.rstrip() + "\n")
        log(f"removed_300_from_public_js={removed_300_public}")
    else:
        log("removed_300_from_public_js=skipped_missing")

    # Do not remove or change 299. This is a one-step rollback from 300 to the approved 299 visual state.
    static_js_after = read_text(JS)
    static_css_after = read_text(CSS)
    log(f"static_js_has_299={START_299_JS in static_js_after and END_299_JS in static_js_after}")
    log(f"static_css_has_299={START_299_CSS in static_css_after and END_299_CSS in static_css_after}")
    log(f"static_js_has_300={START_300 in static_js_after or END_300 in static_js_after}")

    # Keep public CSS in sync only if present; no content/layout edits.
    if PUBLIC_CSS.exists():
        write_text(PUBLIC_CSS, static_css_after)
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
    public_js_final = read_text(PUBLIC_JS) if PUBLIC_JS.exists() else ""
    public_css_final = read_text(PUBLIC_CSS) if PUBLIC_CSS.exists() else ""
    html = read_text(target) if target.exists() else ""

    checks = {
        "target_html_exists": target.exists(),
        "static_js_300_removed": START_300 not in read_text(JS) and END_300 not in read_text(JS),
        "public_js_300_removed": (not PUBLIC_JS.exists()) or (START_300 not in public_js_final and END_300 not in public_js_final),
        "static_js_has_299": START_299_JS in read_text(JS) and END_299_JS in read_text(JS),
        "static_css_has_299": START_299_CSS in read_text(CSS) and END_299_CSS in read_text(CSS),
        "public_js_has_299": START_299_JS in public_js_final,
        "public_css_has_299": START_299_CSS in public_css_final,
        "target_references_chart_js": "transfer-player-market-value-chart.js" in html,
        "target_is_konate": "ibrahima" in html.lower() and "konate" in html.lower(),
    }
    for k, v in checks.items():
        log(f"{k}: {v}")

    ok = hugo.returncode == 0 and all(checks.values())
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
