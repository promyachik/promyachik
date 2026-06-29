
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

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_230_before_center_market_value_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_230_center_market_value_under_chart_report.txt"

commands = []
changed = []

CSS_START = "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */"
CSS_END = "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"

CSS_BLOCK = '''
/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */

/*
   Точечная правка:
   белая стоимость игрока под блоком динамической стоимости
   не должна прилипать к левому краю.
   Главную, ticker, данные, фото, логотипы и карточки не трогаем.
*/

body.transfer-page .pfb-market-value-current,
body.transfer-page .pfb-market-value__current,
body.transfer-page .pfb-market-value__number,
body.transfer-page .pfb-market-value__price,
body.transfer-page .pfb-market-current-value,
body.transfer-page .pfb-current-market-value,
body.transfer-page .pfb-value-chart__current,
body.transfer-page .pfb-value-chart__current-value,
body.transfer-page .pfb-value-chart__price,
body.transfer-page .pfb-value-chart__number,
body.transfer-page .transfer-market-value__current,
body.transfer-page .transfer-market-value__number,
body.transfer-page .transfer-market-value__price,
body.transfer-page .transfer-value-chart__current,
body.transfer-page .transfer-value-chart__current-value,
body.transfer-page .transfer-value-chart__price,
body.transfer-page .market-value-chart__current,
body.transfer-page .market-value-chart__current-value,
body.transfer-page .market-value-chart__price,
body.transfer-page .market-chart__current,
body.transfer-page .market-chart__current-value,
body.transfer-page .market-chart__price,
body.transfer-page .player-value-chart__current,
body.transfer-page .player-value-chart__current-value,
body.transfer-page .player-value-chart__price,
body.transfer-page .value-chart__current,
body.transfer-page .value-chart__current-value,
body.transfer-page .value-chart__price,
body.transfer-page .dynamic-value__current,
body.transfer-page .dynamic-value__current-value,
body.transfer-page .dynamic-value__price,
body.transfer-page .dynamic-price__value,
body.transfer-page .player-price__value {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    max-width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    text-align: center !important;
}

/* Если стоимость лежит внутри строки/обёртки под графиком */
body.transfer-page .pfb-market-value,
body.transfer-page .pfb-market-value-row,
body.transfer-page .pfb-market-value__row,
body.transfer-page .pfb-current-value-row,
body.transfer-page .pfb-value-chart__footer,
body.transfer-page .pfb-value-chart__bottom,
body.transfer-page .pfb-value-chart__summary,
body.transfer-page .transfer-market-value,
body.transfer-page .transfer-market-value-row,
body.transfer-page .transfer-market-value__row,
body.transfer-page .transfer-value-chart__footer,
body.transfer-page .transfer-value-chart__bottom,
body.transfer-page .market-value-chart__footer,
body.transfer-page .market-value-chart__bottom,
body.transfer-page .market-chart__footer,
body.transfer-page .market-chart__bottom,
body.transfer-page .player-value-chart__footer,
body.transfer-page .player-value-chart__bottom,
body.transfer-page .value-chart__footer,
body.transfer-page .value-chart__bottom,
body.transfer-page .dynamic-value__footer,
body.transfer-page .dynamic-value__bottom {
    display: flex !important;
    justify-content: center !important;
    text-align: center !important;
}

/* Защита от абсолютного left:0 у самой белой цифры */
body.transfer-page .pfb-market-value-current,
body.transfer-page .pfb-market-value__current,
body.transfer-page .pfb-market-value__number,
body.transfer-page .pfb-market-value__price,
body.transfer-page .pfb-value-chart__current-value,
body.transfer-page .transfer-market-value__number,
body.transfer-page .transfer-value-chart__current-value,
body.transfer-page .market-value-chart__current-value,
body.transfer-page .market-chart__current-value,
body.transfer-page .player-value-chart__current-value,
body.transfer-page .value-chart__current-value,
body.transfer-page .dynamic-value__current-value,
body.transfer-page .dynamic-value__price {
    left: auto !important;
    right: auto !important;
    transform: none !important;
}

/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */
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

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    style = PROJECT / "static" / "css" / "style.css"

    if not style.exists():
        REPORT.write_text(f"ERROR: style.css not found: {style}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    existing = read(style)
    new_text = replace_block(existing, CSS_START, CSS_END, CSS_BLOCK)
    write(style, new_text, "center white market value numbers under dynamic chart")

    hugo = run(["hugo", "-D"])

    public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []
    sample_text = ""
    for page in public_transfer_pages[:5]:
        sample_text += read(page)[:2000]

    style_text = read(style)

    checks = {
        "hugo_exit_code": hugo.returncode,
        "style_css_exists": style.exists(),
        "style_has_230_css_block": CSS_START in style_text and CSS_END in style_text,
        "public_transfer_pages_found": len(public_transfer_pages),
        "public_no_literal_slash_n_in_sample": "\\n" not in sample_text,
    }

    ok = (
        hugo.returncode == 0
        and style.exists()
        and checks["style_has_230_css_block"]
        and checks["public_transfer_pages_found"] > 0
    )

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 230 - CENTER MARKET VALUE UNDER DYNAMIC CHART")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Only CSS alignment for white market value numbers under the dynamic value/chart block.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("CHANGED FILES")
    for path_rel, label, did, before, after in changed:
        lines.append(f"- {path_rel} | {label} | changed={did}")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    lines.append("HUGO")
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
