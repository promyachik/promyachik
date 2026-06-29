
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import re
import sys

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])
PACKAGE_DIR = Path(__file__).resolve().parents[1]
RESTORE = PACKAGE_DIR / "restore_files"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_244_before_cucurella_move_prices_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_244_cucurella_move_prices_to_club_x_by_python_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
SINGLE = PROJECT / "layouts" / "transfers" / "single.html"
STYLE = PROJECT / "static" / "css" / "style.css"
ALIGN_PARTIAL = PROJECT / "layouts" / "partials" / "promyachik-cucurella-move-prices-to-club-x-244.html"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

INCLUDE_244 = '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}'
OLD_INCLUDES = [
    '{{ partial "promyachik-cucurella-align-price-labels-242.html" . }}',
]

commands = []
changed = []
candidate_log = []
warnings = []

BAD_CSS_BLOCKS = [
    ("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */", "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"),
    ("/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */", "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */"),
    ("/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS START */", "/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS END */"),
    ("/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS START */", "/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS END */"),
    ("/* PROMYACHIK 234 VALUE CHART SVG LABELS START */", "/* PROMYACHIK 234 VALUE CHART SVG LABELS END */"),
    ("/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT START */", "/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT END */"),
    ("/* PROMYACHIK 238 VALUE CHART AXIS FIX START */", "/* PROMYACHIK 238 VALUE CHART AXIS FIX END */"),
    ("/* PROMYACHIK 239 ACTUAL VALUE CHART START */", "/* PROMYACHIK 239 ACTUAL VALUE CHART END */"),
    ("/* PROMYACHIK 240 VALUE HISTORY CHART START */", "/* PROMYACHIK 240 VALUE HISTORY CHART END */"),
    ("/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN START */", "/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN END */"),
    ("/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START */", "/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END */"),
    ("/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT START */", "/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT END */"),
]

BAD_MARKERS_IN_CHART = [
    "pfb-value-chart-v239",
    "pfb-value-chart-v240",
    "PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS",
]

CSS_BLOCK = '''
/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT START */

/*
   244 не меняет график.
   Скрипт на странице Кукурельи двигает только элементы с ценами
   по центрам существующих клубных логотипов/точек.
*/

body.transfer-page .promyachik-cucurella-price-moved-244 {
    pointer-events: auto !important;
    text-align: center !important;
}

/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT END */
'''

def sha(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except Exception:
        return str(path)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def backup(path: Path):
    if path.exists():
        dst = BACKUP_DIR / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def copy_file(src: Path, dst: Path, label: str):
    before = sha(dst)
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((rel(dst), f"{label} <= {src}", before != after, before, after))

def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False
    )
    commands.append({
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout[-3500:],
        "stderr": p.stderr[-3500:],
    })
    return p

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)

def score_backup(path: Path) -> int:
    if not path.exists() or path.name != "transfer-player-market-value-chart.html":
        return -999999

    text = read(path)
    low = str(path).lower().replace("\\", "/")

    if len(text) < 120:
        return -999999

    if "/public/" in low or "/resources/" in low or "/.git/" in low or "/var/" in low:
        return -999999

    if any(marker in text for marker in BAD_MARKERS_IN_CHART):
        return -999999

    if "/restore_files/" in low and any(v in low for v in ["239", "240", "242", "243", "244"]):
        return -999999

    score = 0

    if "_backup_promyachik_239_before_replace_actual_dynamic_value_chart" in low:
        score += 5000

    if "_backup_promyachik_240_before_value_history_chart" in low:
        score -= 2500

    if "_backup_promyachik_243_before" in low or "_backup_promyachik_242_before" in low:
        score += 1400

    if "_backup_promyachik_" in low:
        score += 600

    if ".Params.market_value_chart" in text:
        score += 500

    if "chart.points" in text:
        score += 300

    if "area_path" in text:
        score += 250

    if "value_history" in text:
        score -= 400

    return score

def restore_original_chart_if_needed():
    if not DYNAMIC_PARTIAL.exists():
        warnings.append(f"missing dynamic partial: {DYNAMIC_PARTIAL}")
        return "missing", 0

    current = read(DYNAMIC_PARTIAL)

    if not any(marker in current for marker in BAD_MARKERS_IN_CHART) and "value_history" not in current:
        candidate_log.append("dynamic partial already looks original; no restore needed")
        return "not needed", 0

    candidates = []

    for path in PROJECT.rglob("transfer-player-market-value-chart.html"):
        try:
            score = score_backup(path)
        except Exception:
            continue

        if score > 0:
            candidates.append((score, path, sha(path), path.stat().st_size))

    candidates.sort(key=lambda item: item[0], reverse=True)

    for score, path, digest, size in candidates[:15]:
        candidate_log.append(f"score={score} | size={size} | sha={digest} | {path}")

    if not candidates:
        warnings.append("original transfer-player-market-value-chart.html backup not found; keeping current partial")
        return "not restored", 0

    score, source, _, _ = candidates[0]
    copy_file(source, DYNAMIC_PARTIAL, f"restore original chart partial before moving labels score={score}")
    return str(source), score

def install_244_partial():
    src = RESTORE / "layouts" / "partials" / "promyachik-cucurella-move-prices-to-club-x-244.html"
    copy_file(src, ALIGN_PARTIAL, "install Cucurella hard price mover partial")

def update_single_include():
    if not SINGLE.exists():
        raise RuntimeError(f"missing transfer single template: {SINGLE}")

    text = read(SINGLE)

    for inc in OLD_INCLUDES + [INCLUDE_244]:
        text = text.replace(inc, "")

    text = text.rstrip() + "\n" + INCLUDE_244 + "\n"
    write(SINGLE, text, "include Cucurella hard price mover after transfer page content")

def cleanup_old_partials():
    for rel_path in [
        "layouts/partials/promyachik-cucurella-align-price-labels-242.html",
    ]:
        path = PROJECT / rel_path
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete old 242 aligner partial", True, "exists", "deleted"))

def cleanup_style():
    if not STYLE.exists():
        warnings.append(f"style.css missing: {STYLE}")
        return

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "remove failed chart/label CSS and add 244 minimal support")

def patch_public_html_direct():
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
    if not public_path.exists():
        warnings.append(f"public Cucurella HTML not found after hugo: {public_path}")
        return False

    html = read(public_path)

    if "__promyachikCucurellaMovePrices244Ready" in html:
        return True

    script = read(ALIGN_PARTIAL)
    script = re.sub(r"{{\s*if\s+in\s+\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*}}", "", script)
    script = re.sub(r"{{\s*end\s*}}\s*$", "", script)

    if "</body>" in html:
        html = html.replace("</body>", script + "\n</body>")
    else:
        html += "\n" + script + "\n"

    write(public_path, html, "directly inject 244 mover into built public Cucurella HTML")
    return True

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in [
        "__promyachikCucurellaMovePrices244Ready",
        "promyachik-cucurella-price-moved-244",
        "getClubTargets",
        "moveHtmlPrices",
        "pfb-value-chart-v240",
        "pfb-value-chart-v239",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 450): idx + 1450].replace("\n", " ")[:1900]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ramos_before = sha(RAMOS_PAGE)
    cucurella_before = sha(CUCURELLA_PAGE)

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []
    restored_source = ""
    restored_score = 0
    direct_public_patched = False

    try:
        restored_source, restored_score = restore_original_chart_if_needed()
        install_244_partial()
        cleanup_old_partials()
        update_single_include()
        cleanup_style()

        hugo = run(["hugo", "-D"])

        direct_public_patched = patch_public_html_direct()

        dynamic_text = read(DYNAMIC_PARTIAL) if DYNAMIC_PARTIAL.exists() else ""
        single_text = read(SINGLE) if SINGLE.exists() else ""
        style_text = read(STYLE) if STYLE.exists() else ""

        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""

        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_ramos_text = read(public_ramos) if public_ramos.exists() else ""

        fragments = collect_public_fragments()

        ramos_after = sha(RAMOS_PAGE)
        cucurella_after = sha(CUCURELLA_PAGE)

        checks = {
            "hugo_exit_code": hugo.returncode,
            "ramos_content_untouched": ramos_before == ramos_after,
            "cucurella_content_untouched": cucurella_before == cucurella_after,
            "restored_source": restored_source,
            "restored_score": restored_score,
            "single_has_244_include": INCLUDE_244 in single_text,
            "align_partial_exists": ALIGN_PARTIAL.exists(),
            "style_has_244_support": "PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT START" in style_text,
            "dynamic_partial_no_v239_v240": "pfb-value-chart-v239" not in dynamic_text and "pfb-value-chart-v240" not in dynamic_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_has_244_script": "__promyachikCucurellaMovePrices244Ready" in public_text,
            "public_has_move_function": "moveHtmlPrices" in public_text and "getClubTargets" in public_text,
            "public_direct_patched": direct_public_patched,
            "public_ramos_has_no_244_script": "__promyachikCucurellaMovePrices244Ready" not in public_ramos_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["single_has_244_include"]
            and checks["align_partial_exists"]
            and checks["style_has_244_support"]
            and checks["public_cucurella_exists"]
            and checks["public_has_244_script"]
            and checks["public_has_move_function"]
            and checks["public_ramos_has_no_244_script"]
        )

    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 244 - CUCURELLA MOVE PRICES TO CLUB X BY PYTHON")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Target: Cucurella page only.")
    lines.append("- Ramos content is not touched.")
    lines.append("- Cucurella content data is not touched.")
    lines.append("- The chart line/dots/logos are not redrawn.")
    lines.append("- Python installs a hard aligner that moves the existing PRICE LABEL elements by X.")
    lines.append("- Target X values are read from existing club logo / dot centers in the browser.")
    lines.append("- It moves real elements with inline style: position absolute + left = club center + translateX(-50%).")
    lines.append("- It also injects the script directly into public Cucurella HTML after Hugo build.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("RESTORE")
    lines.append(f"- restored_source: {restored_source}")
    lines.append(f"- restored_score: {restored_score}")
    lines.append("")
    lines.append("CANDIDATES")
    if candidate_log:
        for item in candidate_log[:20]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHANGED FILES")
    if changed:
        for path_rel, label, did, before, after in changed:
            lines.append(f"- {path_rel} | {label} | changed={did}")
    else:
        lines.append("- none")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    if error_text:
        lines.append("ERROR")
        lines.append(error_text)
        lines.append("")
    lines.append("OBSERVED CUCURELLA PUBLIC FRAGMENTS")
    if fragments:
        for token, fragment in fragments:
            lines.append(f"- token={token} | {fragment}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("HUGO")
    if hugo is None:
        lines.append("- not run")
    else:
        lines.append(f"- exit_code: {hugo.returncode}")
        lines.append("--- STDOUT tail ---")
        lines.append(hugo.stdout[-2500:])
        lines.append("--- STDERR tail ---")
        lines.append(hugo.stderr[-2500:])
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands:
        lines.append("-" * 70)
        lines.append(f"COMMAND: {c['cmd']}")
        lines.append(f"EXIT_CODE: {c['returncode']}")
        if c["stdout"]:
            lines.append("--- STDOUT ---")
            lines.append(c["stdout"])
        if c["stderr"]:
            lines.append("--- STDERR ---")
            lines.append(c["stderr"])
    lines.append("")
    lines.append("NO RAMOS CONTENT CHANGE.")
    lines.append("NO CUCURELLA CONTENT CHANGE.")
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
