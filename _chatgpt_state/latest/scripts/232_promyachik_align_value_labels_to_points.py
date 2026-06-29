
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_232_before_align_value_labels_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_232_align_value_labels_to_points_report.txt"

commands = []
changed = []

CSS_START = "/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS START */"
CSS_END = "/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS END */"

PARTIAL_INCLUDE = '{{ partial "promyachik-align-value-labels-232.html" . }}'
PARTIAL_NAME = "promyachik-align-value-labels-232.html"

CSS_BLOCK = '''
/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS START */

/*
   Точечная правка:
   подписи дат/цен под графиком стоимости игрока
   выравниваются относительно точек прогресса, а не от левого края карточки.
*/

body.transfer-page .promyachik-value-label-row-232 {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}

body.transfer-page .promyachik-value-label-item-232 {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: center !important;
    white-space: nowrap !important;
    line-height: 1.08 !important;
    box-sizing: border-box !important;
}

body.transfer-page .promyachik-value-label-item-232 span,
body.transfer-page .promyachik-value-label-item-232 strong,
body.transfer-page .promyachik-value-label-item-232 em {
    display: block !important;
    width: 100% !important;
    text-align: center !important;
}

/* Убираем прошлые попытки, если браузер их ещё держит в каскаде */
body.transfer-page .promyachik-value-label-row-232 > * {
    float: none !important;
}

/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS END */
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

def replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), flags=re.S)
    text = pattern.sub("", text)
    return text.rstrip() + "\n\n" + block.strip() + "\n"

def remove_old_blocks(text: str) -> str:
    for start, end in [
        ("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */", "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"),
        ("/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */", "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */"),
        (CSS_START, CSS_END),
    ]:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
    return text

def update_style():
    style = PROJECT / "static" / "css" / "style.css"
    if not style.exists():
        raise RuntimeError(f"style.css not found: {style}")

    existing = read(style)
    existing = remove_old_blocks(existing)
    new_text = replace_block(existing, CSS_START, CSS_END, CSS_BLOCK)
    write(style, new_text, "add CSS support for value labels aligned to chart points")

def install_partial():
    src = RESTORE / "layouts" / "partials" / PARTIAL_NAME
    dst = PROJECT / "layouts" / "partials" / PARTIAL_NAME
    copy_file(src, dst, "install value-label alignment JS partial")

def ensure_partial_include():
    baseof = PROJECT / "layouts" / "_default" / "baseof.html"
    if not baseof.exists():
        raise RuntimeError(f"baseof.html not found: {baseof}")

    text = read(baseof)

    # Remove duplicate includes from previous runs.
    text = text.replace(PARTIAL_INCLUDE, "")

    if "</body>" in text:
        new_text = text.replace("</body>", f"{PARTIAL_INCLUDE}\n</body>", 1)
    else:
        new_text = text.rstrip() + "\n" + PARTIAL_INCLUDE + "\n"

    write(baseof, new_text, "include value-label alignment partial before closing body")

def collect_fragments():
    fragments = []
    public_transfers = PROJECT / "public" / "transfers"
    if not public_transfers.exists():
        return fragments

    tokens = ["€20 млн", "€23 млн", "€90 млн", "€100 млн"]
    for page in list(public_transfers.glob("*/index.html"))[:30]:
        text = read(page)
        for token in tokens:
            idx = text.find(token)
            if idx != -1:
                start = max(0, idx - 320)
                end = min(len(text), idx + 320)
                fragment = text[start:end].replace("\n", " ")
                fragments.append((rel(page), token, fragment[:640]))
                break
    return fragments[:10]

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
    fragments = []
    checks = {}

    try:
        update_style()
        install_partial()
        ensure_partial_include()

        hugo = run(["hugo", "-D"])
        fragments = collect_fragments()

        style_text = read(PROJECT / "static" / "css" / "style.css")
        baseof_text = read(PROJECT / "layouts" / "_default" / "baseof.html")
        public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []

        public_sample = ""
        for page in public_transfer_pages[:8]:
            public_sample += read(page)[:5000]

        checks = {
            "hugo_exit_code": hugo.returncode,
            "style_has_232_css_block": CSS_START in style_text and CSS_END in style_text,
            "old_230_block_removed": "PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START" not in style_text,
            "old_231_block_removed": "PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START" not in style_text,
            "baseof_includes_232_partial": PARTIAL_INCLUDE in baseof_text,
            "public_transfer_pages_found": len(public_transfer_pages),
            "public_has_232_script": "__promyachikAlignValueLabels232Ready" in public_sample,
            "observed_value_label_fragments": len(fragments),
            "public_no_literal_slash_n_in_sample": "\\n" not in public_sample,
        }

        ok = (
            hugo.returncode == 0
            and checks["style_has_232_css_block"]
            and checks["old_230_block_removed"]
            and checks["old_231_block_removed"]
            and checks["baseof_includes_232_partial"]
            and checks["public_has_232_script"]
            and checks["public_transfer_pages_found"] > 0
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 232 - ALIGN VALUE CHART LABELS TO POINTS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Aligns the date/value labels under the dynamic player value chart relative to the chart points.")
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
    lines.append("OBSERVED VALUE LABEL FRAGMENTS")
    if fragments:
        for page, token, fragment in fragments:
            lines.append(f"- {page} | token={token} | {fragment}")
    else:
        lines.append("- none found")
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
