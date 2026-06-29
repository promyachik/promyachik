
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_242_before_cucurella_label_align_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_242_cucurella_align_price_labels_only_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE = PROJECT / "static" / "css" / "style.css"
SINGLE = PROJECT / "layouts" / "transfers" / "single.html"
ALIGN_PARTIAL = PROJECT / "layouts" / "partials" / "promyachik-cucurella-align-price-labels-242.html"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"

INCLUDE = '{{ partial "promyachik-cucurella-align-price-labels-242.html" . }}'

commands = []
changed = []
candidate_log = []
warnings = []

CSS_START = "/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN START */"
CSS_END = "/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN END */"

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
    (CSS_START, CSS_END),
]

BAD_MARKERS = [
    "pfb-value-chart-v239",
    "pfb-value-chart-v240",
    "PROMYACHIK 239",
    "PROMYACHIK 240",
]

CSS_BLOCK = '''
/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN START */

/*
   Только страница Marc Cucurella.
   График/линия/точки не перерисовываются.
   JS двигает только нижние подписи цены/года по X-координатам существующих точек.
*/

body.transfer-page .promyachik-cucurella-label-row-242 {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}

body.transfer-page .promyachik-cucurella-price-label-242 {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: center !important;
    white-space: nowrap !important;
    line-height: 1.08 !important;
    box-sizing: border-box !important;
    float: none !important;
}

body.transfer-page .promyachik-cucurella-price-label-242 span,
body.transfer-page .promyachik-cucurella-price-label-242 strong,
body.transfer-page .promyachik-cucurella-price-label-242 em {
    display: block !important;
    width: 100% !important;
    text-align: center !important;
}

/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN END */
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

    if any(marker in text for marker in BAD_MARKERS):
        return -999999

    if "/restore_files/" in low and any(v in low for v in ["239", "240", "242"]):
        return -999999

    score = 0

    if "_backup_promyachik_239_before_replace_actual_dynamic_value_chart" in low:
        score += 5000

    if "_backup_promyachik_240_before_value_history_chart" in low:
        score -= 2000

    if "_backup_promyachik_" in low:
        score += 500

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
        raise RuntimeError(f"missing {DYNAMIC_PARTIAL}")

    current = read(DYNAMIC_PARTIAL)

    if "pfb-value-chart-v239" not in current and "pfb-value-chart-v240" not in current and "value_history" not in current:
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

    for score, path, digest, size in candidates[:12]:
        candidate_log.append(f"score={score} | size={size} | sha={digest} | {path}")

    if not candidates:
        raise RuntimeError("Нужно восстановить старый график, но backup transfer-player-market-value-chart.html не найден.")

    score, source, _, _ = candidates[0]
    copy_file(source, DYNAMIC_PARTIAL, f"restore original chart partial before 239/240 replacement score={score}")
    return str(source), score

def cleanup_style():
    if not STYLE.exists():
        raise RuntimeError(f"missing {STYLE}")

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "remove failed chart CSS blocks and add Cucurella-only label alignment CSS")

def install_partial():
    src = RESTORE / "layouts" / "partials" / "promyachik-cucurella-align-price-labels-242.html"
    copy_file(src, ALIGN_PARTIAL, "install Cucurella-only label alignment JS partial")

def include_partial():
    if not SINGLE.exists():
        raise RuntimeError(f"missing {SINGLE}")

    text = read(SINGLE)
    text = text.replace(INCLUDE, "")

    text = text.rstrip() + "\n" + INCLUDE + "\n"
    write(SINGLE, text, "include Cucurella-only label alignment partial in transfer template")

def find_cucurella_page():
    candidates = []
    for path in (PROJECT / "content" / "transfers").glob("*/index.md"):
        text = read(path)
        if "Cucurella" in text or "Кукурель" in text or "cucurella" in str(path).lower():
            candidates.append(path)

    return candidates

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in [
        "__promyachikCucurellaAlignPriceLabels242Ready",
        "promyachik-cucurella-price-label-242",
        "pfb-value-chart-v240",
        "pfb-value-chart-v239",
        "€",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 400): idx + 900].replace("\n", " ")[:1300]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ramos_before = sha(RAMOS_PAGE)
    ramos_exists_before = RAMOS_PAGE.exists()

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []
    restored_source = ""
    restored_score = 0

    try:
        restored_source, restored_score = restore_original_chart_if_needed()
        cleanup_style()
        install_partial()
        include_partial()

        hugo = run(["hugo", "-D"])

        dynamic_text = read(DYNAMIC_PARTIAL)
        style_text = read(STYLE)
        single_text = read(SINGLE)
        cucurella_pages = find_cucurella_page()
        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""
        fragments = collect_public_fragments()

        ramos_after = sha(RAMOS_PAGE)
        ramos_exists_after = RAMOS_PAGE.exists()

        checks = {
            "hugo_exit_code": hugo.returncode,
            "ramos_page_existed_before": ramos_exists_before,
            "ramos_page_exists_after": ramos_exists_after,
            "ramos_content_untouched": ramos_before == ramos_after,
            "restored_source": restored_source,
            "restored_score": restored_score,
            "dynamic_partial_no_v239_v240": "pfb-value-chart-v239" not in dynamic_text and "pfb-value-chart-v240" not in dynamic_text,
            "style_has_242_css": CSS_START in style_text and CSS_END in style_text,
            "single_includes_242_partial": INCLUDE in single_text,
            "align_partial_exists": ALIGN_PARTIAL.exists(),
            "cucurella_pages_found": [rel(p) for p in cucurella_pages],
            "public_cucurella_exists": public_cucurella.exists(),
            "public_has_242_script": "__promyachikCucurellaAlignPriceLabels242Ready" in public_text,
            "public_no_v239_v240": "pfb-value-chart-v239" not in public_text and "pfb-value-chart-v240" not in public_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["dynamic_partial_no_v239_v240"]
            and checks["style_has_242_css"]
            and checks["single_includes_242_partial"]
            and checks["align_partial_exists"]
            and len(cucurella_pages) > 0
            and checks["public_cucurella_exists"]
            and checks["public_has_242_script"]
            and checks["public_no_v239_v240"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 242 - CUCURELLA ALIGN PRICE LABELS ONLY")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Work target: Marc Cucurella page only.")
    lines.append("- Ramos content is not touched.")
    lines.append("- The graph design/line/points are not redrawn.")
    lines.append("- If 239/240 replaced the chart partial, restore the original chart partial from backup.")
    lines.append("- Add JS only for /transfers/marc-cucurella-real-madrid/ to align bottom price/year labels to existing point X positions.")
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
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
