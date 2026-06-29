
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_238_before_fix_value_chart_axis_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_238_fix_value_chart_axis_inset_report.txt"

commands = []
changed = []

TARGET = PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html"
STYLE = PROJECT / "static" / "css" / "style.css"

CSS_START = "/* PROMYACHIK 238 VALUE CHART AXIS FIX START */"
CSS_END = "/* PROMYACHIK 238 VALUE CHART AXIS FIX END */"

BAD_CSS_BLOCKS = [
    ("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */", "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"),
    ("/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */", "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */"),
    ("/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS START */", "/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS END */"),
    ("/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS START */", "/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS END */"),
    ("/* PROMYACHIK 234 VALUE CHART SVG LABELS START */", "/* PROMYACHIK 234 VALUE CHART SVG LABELS END */"),
    ("/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT START */", "/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT END */"),
    ("/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT START */", "/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT END */"),
    (CSS_START, CSS_END),
]

BAD_INCLUDES = [
    '{{ partial "promyachik-align-value-labels-232.html" . }}',
    '{{ partial "promyachik-force-align-value-labels-233.html" . }}',
]

CSS_BLOCK = '''
/* PROMYACHIK 238 VALUE CHART AXIS FIX START */

/*
   Реальная правка графика:
   каждая точка, дата и цена находятся в одной SVG-группе с общей осью X.
   Крайние оси сдвинуты внутрь: leftPad/rightPad = 92.
*/

body.transfer-page .pfb-market-chart-static--238 {
    width: 100% !important;
    margin: 18px 0 0 !important;
    padding: 18px 18px 14px !important;
    border: 1px solid rgba(212, 175, 55, 0.20) !important;
    border-radius: 24px !important;
    background:
        radial-gradient(circle at 72% 12%, rgba(212, 175, 55, 0.10), transparent 34%),
        linear-gradient(180deg, rgba(14, 18, 24, 0.96), rgba(5, 7, 10, 0.96)) !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__head {
    display: flex !important;
    align-items: flex-start !important;
    justify-content: space-between !important;
    gap: 18px !important;
    margin-bottom: 10px !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__eyebrow {
    margin: 0 0 7px !important;
    color: #d8b34a !important;
    font-size: 10px !important;
    font-weight: 900 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__title {
    margin: 0 !important;
    color: #ffffff !important;
    font-size: 19px !important;
    font-weight: 900 !important;
    line-height: 1.1 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__subtitle {
    margin: 8px 0 0 !important;
    color: rgba(255, 255, 255, 0.62) !important;
    font-size: 12px !important;
    line-height: 1.35 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__current {
    display: grid !important;
    justify-items: end !important;
    gap: 3px !important;
    color: rgba(255, 255, 255, 0.65) !important;
    font-size: 10px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__current strong {
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: 950 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__svg {
    display: block !important;
    width: 100% !important;
    height: auto !important;
    overflow: visible !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__background {
    fill: rgba(5, 7, 10, 0.78) !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__grid {
    stroke: rgba(255, 255, 255, 0.08) !important;
    stroke-width: 2 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__logo {
    filter: drop-shadow(0 8px 12px rgba(0, 0, 0, 0.56)) !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__fallback-circle {
    fill: rgba(212, 175, 55, 0.08) !important;
    stroke: #d8b34a !important;
    stroke-width: 4 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__fallback-text {
    fill: #f2d374 !important;
    font-size: 18px !important;
    font-weight: 950 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    text-anchor: middle !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__dot-outer {
    fill: #090b0f !important;
    stroke: #f2d374 !important;
    stroke-width: 6 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__dot-inner {
    fill: #11151b !important;
    stroke: none !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__date-label {
    fill: #87a7cf !important;
    font-size: 17px !important;
    font-weight: 900 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    letter-spacing: 0.01em !important;
    text-anchor: middle !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__value-label {
    fill: #ffffff !important;
    font-size: 19px !important;
    font-weight: 950 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    text-anchor: middle !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__note {
    margin: 8px 0 0 !important;
    color: rgba(255, 255, 255, 0.48) !important;
    font-size: 11px !important;
    line-height: 1.35 !important;
}

body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__note a {
    color: #d8b34a !important;
    text-decoration: none !important;
}

@media (max-width: 680px) {
    body.transfer-page .pfb-market-chart-static--238 {
        padding-left: 12px !important;
        padding-right: 12px !important;
    }

    body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__date-label {
        font-size: 15px !important;
    }

    body.transfer-page .pfb-market-chart-static--238 .pfb-market-chart-static__value-label {
        font-size: 17px !important;
    }
}

/* PROMYACHIK 238 VALUE CHART AXIS FIX END */
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
    changed.append((rel(dst), label, before != after, before, after))

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

def replace_chart_partial():
    copy_file(
        RESTORE / "layouts" / "partials" / "profutbik-market-chart-static.html",
        TARGET,
        "replace actual static value-chart partial with shared dot/date/value X axis"
    )

def cleanup_style():
    if not STYLE.exists():
        raise RuntimeError(f"style.css not found: {STYLE}")

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "remove old bad chart CSS and add 238 chart-axis CSS")

def cleanup_bad_includes_and_partials():
    for rel_path in [
        "layouts/_default/baseof.html",
        "layouts/transfers/single.html",
    ]:
        path = PROJECT / rel_path

        if not path.exists():
            continue

        text = read(path)
        old = text

        for include in BAD_INCLUDES:
            text = text.replace(include, "")

        text = re.sub(r"\n{4,}", "\n\n\n", text)

        if text != old:
            write(path, text, "remove old bad 232/233 includes")

    for rel_path in [
        "layouts/partials/promyachik-align-value-labels-232.html",
        "layouts/partials/promyachik-force-align-value-labels-233.html",
    ]:
        path = PROJECT / rel_path
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete old bad chart JS partial", True, "exists", "deleted"))

def collect_fragments():
    fragments = []
    public_transfers = PROJECT / "public" / "transfers"

    if not public_transfers.exists():
        return fragments

    for page in list(public_transfers.glob("*/index.html"))[:30]:
        text = read(page)
        if "pfb-market-chart-static--238" in text:
            idx = text.find("pfb-market-chart-static--238")
            fragments.append((rel(page), text[max(0, idx - 260): idx + 1600].replace("\n", " ")[:1800]))
    return fragments[:8]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []

    try:
        replace_chart_partial()
        cleanup_style()
        cleanup_bad_includes_and_partials()

        hugo = run(["hugo", "-D"])

        partial_text = read(TARGET)
        style_text = read(STYLE)
        public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []

        public_sample = ""
        for page in public_transfer_pages[:10]:
            public_sample += read(page)[:11000]

        fragments = collect_fragments()

        bad_markers = [
            "PROMYACHIK 230 CENTER MARKET VALUE",
            "PROMYACHIK 231 CENTER VALUE",
            "PROMYACHIK 232 ALIGN VALUE",
            "PROMYACHIK 233 FORCE ALIGN",
            "PROMYACHIK 234 VALUE CHART SVG",
            "PROMYACHIK 235 VERTICAL VALUE",
            "pfb-market-chart-static--234",
            "pfb-market-chart-static--235",
            "pfb-market-chart-static--236",
            "promyachik-align-value-labels-232",
            "promyachik-force-align-value-labels-233",
            "__promyachikForceAlignValueLabels233Ready",
            "__promyachikAlignValueLabels232Ready",
        ]

        checks = {
            "hugo_exit_code": hugo.returncode,
            "target_partial_exists": TARGET.exists(),
            "partial_has_238_class": "pfb-market-chart-static--238" in partial_text,
            "partial_left_pad_92": "{{- $leftPad := 92.0 -}}" in partial_text,
            "partial_right_pad_92": "{{- $rightPad := 92.0 -}}" in partial_text,
            "partial_axis_group": 'class="pfb-market-chart-static__axis-group"' in partial_text,
            "partial_group_translate_x": 'transform="translate({{ printf "%.2f" $x }} 0)"' in partial_text,
            "dot_and_label_share_x_zero": 'cx="0"' in partial_text and 'x="0"' in partial_text,
            "style_has_238_css": CSS_START in style_text and CSS_END in style_text,
            "bad_markers_absent_from_style_and_public": all(marker not in style_text and marker not in public_sample for marker in bad_markers),
            "public_transfer_pages_found": len(public_transfer_pages),
            "public_has_238_chart": "pfb-market-chart-static--238" in public_sample,
            "public_has_axis_group": "pfb-market-chart-static__axis-group" in public_sample,
            "public_has_dot_cx_zero": 'cx="0"' in public_sample,
            "public_has_label_x_zero": 'x="0"' in public_sample,
            "observed_238_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["target_partial_exists"]
            and checks["partial_has_238_class"]
            and checks["partial_left_pad_92"]
            and checks["partial_right_pad_92"]
            and checks["partial_axis_group"]
            and checks["partial_group_translate_x"]
            and checks["dot_and_label_share_x_zero"]
            and checks["style_has_238_css"]
            and checks["bad_markers_absent_from_style_and_public"]
            and checks["public_transfer_pages_found"] > 0
            and checks["public_has_238_chart"]
            and checks["public_has_axis_group"]
            and checks["public_has_dot_cx_zero"]
            and checks["public_has_label_x_zero"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 238 - FIX VALUE CHART AXIS + INSET LABELS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Replaces the actual static value-chart partial.")
    lines.append("- Each point/date/value uses one SVG axis group: group translate(X 0), dot cx=0, labels x=0.")
    lines.append("- First and last axes are inset: leftPad/rightPad = 92.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
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
    lines.append("OBSERVED 238 PUBLIC FRAGMENTS")
    if fragments:
        for page, fragment in fragments:
            lines.append(f"- {page} | {fragment}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
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
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
