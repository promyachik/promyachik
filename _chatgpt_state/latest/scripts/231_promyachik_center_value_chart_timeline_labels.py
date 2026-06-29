
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_231_before_value_chart_labels_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_231_center_value_chart_timeline_labels_report.txt"

commands = []
changed = []
observed_fragments = []

CSS_START = "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */"
CSS_END = "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */"

CSS_BLOCK = '''
/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */

/*
   Точечная правка:
   выровнять подписи дат и белые цифры стоимости под динамическим графиком.
   Это именно нижняя шкала графика: июнь 2022 / €20 млн / €23 млн / €90 млн / €100 млн.
   Главную, бегущие строки, API-логотипы, фото, data/transfers и карточки не трогаем.
*/

/* Строка/контейнер с подписями под графиком */
body.transfer-page .pfb-value-chart__labels,
body.transfer-page .pfb-value-chart__ticks,
body.transfer-page .pfb-value-chart__timeline,
body.transfer-page .pfb-value-chart__axis,
body.transfer-page .pfb-market-chart__labels,
body.transfer-page .pfb-market-chart__ticks,
body.transfer-page .pfb-market-chart__timeline,
body.transfer-page .pfb-market-chart__axis,
body.transfer-page .pfb-market-value-chart__labels,
body.transfer-page .pfb-market-value-chart__ticks,
body.transfer-page .pfb-market-value-chart__timeline,
body.transfer-page .transfer-value-chart__labels,
body.transfer-page .transfer-value-chart__ticks,
body.transfer-page .transfer-value-chart__timeline,
body.transfer-page .transfer-value-chart__axis,
body.transfer-page .market-value-chart__labels,
body.transfer-page .market-value-chart__ticks,
body.transfer-page .market-value-chart__timeline,
body.transfer-page .market-value-chart__axis,
body.transfer-page .market-chart__labels,
body.transfer-page .market-chart__ticks,
body.transfer-page .market-chart__timeline,
body.transfer-page .market-chart__axis,
body.transfer-page .player-value-chart__labels,
body.transfer-page .player-value-chart__ticks,
body.transfer-page .player-value-chart__timeline,
body.transfer-page .player-value-chart__axis,
body.transfer-page .value-chart__labels,
body.transfer-page .value-chart__ticks,
body.transfer-page .value-chart__timeline,
body.transfer-page .value-chart__axis,
body.transfer-page [class*="value-chart"][class*="labels"],
body.transfer-page [class*="value-chart"][class*="ticks"],
body.transfer-page [class*="value-chart"][class*="timeline"],
body.transfer-page [class*="market-chart"][class*="labels"],
body.transfer-page [class*="market-chart"][class*="ticks"],
body.transfer-page [class*="market-chart"][class*="timeline"] {
    width: 100% !important;
    max-width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
    text-align: center !important;
}

/*
   Сами блоки подписи каждой точки.
   Делаем не left-aligned, а центрируем дату и цену внутри каждого пункта.
*/
body.transfer-page .pfb-value-chart__labels > *,
body.transfer-page .pfb-value-chart__ticks > *,
body.transfer-page .pfb-value-chart__timeline > *,
body.transfer-page .pfb-value-chart__axis > *,
body.transfer-page .pfb-market-chart__labels > *,
body.transfer-page .pfb-market-chart__ticks > *,
body.transfer-page .pfb-market-chart__timeline > *,
body.transfer-page .pfb-market-chart__axis > *,
body.transfer-page .pfb-market-value-chart__labels > *,
body.transfer-page .pfb-market-value-chart__ticks > *,
body.transfer-page .pfb-market-value-chart__timeline > *,
body.transfer-page .transfer-value-chart__labels > *,
body.transfer-page .transfer-value-chart__ticks > *,
body.transfer-page .transfer-value-chart__timeline > *,
body.transfer-page .transfer-value-chart__axis > *,
body.transfer-page .market-value-chart__labels > *,
body.transfer-page .market-value-chart__ticks > *,
body.transfer-page .market-value-chart__timeline > *,
body.transfer-page .market-value-chart__axis > *,
body.transfer-page .market-chart__labels > *,
body.transfer-page .market-chart__ticks > *,
body.transfer-page .market-chart__timeline > *,
body.transfer-page .market-chart__axis > *,
body.transfer-page .player-value-chart__labels > *,
body.transfer-page .player-value-chart__ticks > *,
body.transfer-page .player-value-chart__timeline > *,
body.transfer-page .player-value-chart__axis > *,
body.transfer-page .value-chart__labels > *,
body.transfer-page .value-chart__ticks > *,
body.transfer-page .value-chart__timeline > *,
body.transfer-page .value-chart__axis > *,
body.transfer-page [class*="value-chart"][class*="labels"] > *,
body.transfer-page [class*="value-chart"][class*="ticks"] > *,
body.transfer-page [class*="value-chart"][class*="timeline"] > *,
body.transfer-page [class*="market-chart"][class*="labels"] > *,
body.transfer-page [class*="market-chart"][class*="ticks"] > *,
body.transfer-page [class*="market-chart"][class*="timeline"] > * {
    min-width: 72px !important;
    max-width: 96px !important;
    text-align: center !important;
    white-space: nowrap !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
}

/* Дата и цена внутри подписи */
body.transfer-page .pfb-value-chart__labels span,
body.transfer-page .pfb-value-chart__ticks span,
body.transfer-page .pfb-value-chart__timeline span,
body.transfer-page .pfb-market-chart__labels span,
body.transfer-page .pfb-market-chart__ticks span,
body.transfer-page .pfb-market-chart__timeline span,
body.transfer-page .transfer-value-chart__labels span,
body.transfer-page .transfer-value-chart__ticks span,
body.transfer-page .transfer-value-chart__timeline span,
body.transfer-page .market-value-chart__labels span,
body.transfer-page .market-value-chart__ticks span,
body.transfer-page .market-value-chart__timeline span,
body.transfer-page .market-chart__labels span,
body.transfer-page .market-chart__ticks span,
body.transfer-page .market-chart__timeline span,
body.transfer-page .player-value-chart__labels span,
body.transfer-page .player-value-chart__ticks span,
body.transfer-page .player-value-chart__timeline span,
body.transfer-page .value-chart__labels span,
body.transfer-page .value-chart__ticks span,
body.transfer-page .value-chart__timeline span,
body.transfer-page [class*="value-chart"][class*="labels"] span,
body.transfer-page [class*="value-chart"][class*="ticks"] span,
body.transfer-page [class*="value-chart"][class*="timeline"] span,
body.transfer-page [class*="market-chart"][class*="labels"] span,
body.transfer-page [class*="market-chart"][class*="ticks"] span,
body.transfer-page [class*="market-chart"][class*="timeline"] span {
    display: block !important;
    width: 100% !important;
    text-align: center !important;
}

/*
   Если подписи расставлены absolute/left по точкам графика:
   центрируем блок относительно координаты точки, а не от левого края текста.
*/
body.transfer-page .pfb-value-chart__label,
body.transfer-page .pfb-value-chart__tick,
body.transfer-page .pfb-market-chart__label,
body.transfer-page .pfb-market-chart__tick,
body.transfer-page .transfer-value-chart__label,
body.transfer-page .transfer-value-chart__tick,
body.transfer-page .market-value-chart__label,
body.transfer-page .market-value-chart__tick,
body.transfer-page .market-chart__label,
body.transfer-page .market-chart__tick,
body.transfer-page .player-value-chart__label,
body.transfer-page .player-value-chart__tick,
body.transfer-page .value-chart__label,
body.transfer-page .value-chart__tick,
body.transfer-page [class*="value-chart"][class*="label"],
body.transfer-page [class*="value-chart"][class*="tick"],
body.transfer-page [class*="market-chart"][class*="label"],
body.transfer-page [class*="market-chart"][class*="tick"] {
    text-align: center !important;
    align-items: center !important;
}

/* Первый и последний пункт не должны вылезать за рамку карточки */
body.transfer-page .pfb-value-chart__labels > *:first-child,
body.transfer-page .pfb-value-chart__ticks > *:first-child,
body.transfer-page .pfb-value-chart__timeline > *:first-child,
body.transfer-page .pfb-market-chart__labels > *:first-child,
body.transfer-page .pfb-market-chart__ticks > *:first-child,
body.transfer-page .pfb-market-chart__timeline > *:first-child,
body.transfer-page .transfer-value-chart__labels > *:first-child,
body.transfer-page .transfer-value-chart__ticks > *:first-child,
body.transfer-page .transfer-value-chart__timeline > *:first-child,
body.transfer-page .market-value-chart__labels > *:first-child,
body.transfer-page .market-value-chart__ticks > *:first-child,
body.transfer-page .market-value-chart__timeline > *:first-child,
body.transfer-page .market-chart__labels > *:first-child,
body.transfer-page .market-chart__ticks > *:first-child,
body.transfer-page .market-chart__timeline > *:first-child,
body.transfer-page .value-chart__labels > *:first-child,
body.transfer-page .value-chart__ticks > *:first-child,
body.transfer-page .value-chart__timeline > *:first-child {
    align-items: center !important;
    text-align: center !important;
}

body.transfer-page .pfb-value-chart__labels > *:last-child,
body.transfer-page .pfb-value-chart__ticks > *:last-child,
body.transfer-page .pfb-value-chart__timeline > *:last-child,
body.transfer-page .pfb-market-chart__labels > *:last-child,
body.transfer-page .pfb-market-chart__ticks > *:last-child,
body.transfer-page .pfb-market-chart__timeline > *:last-child,
body.transfer-page .transfer-value-chart__labels > *:last-child,
body.transfer-page .transfer-value-chart__ticks > *:last-child,
body.transfer-page .transfer-value-chart__timeline > *:last-child,
body.transfer-page .market-value-chart__labels > *:last-child,
body.transfer-page .market-value-chart__ticks > *:last-child,
body.transfer-page .market-value-chart__timeline > *:last-child,
body.transfer-page .market-chart__labels > *:last-child,
body.transfer-page .market-chart__ticks > *:last-child,
body.transfer-page .market-chart__timeline > *:last-child,
body.transfer-page .value-chart__labels > *:last-child,
body.transfer-page .value-chart__ticks > *:last-child,
body.transfer-page .value-chart__timeline > *:last-child {
    align-items: center !important;
    text-align: center !important;
}

/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */
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

def remove_old_230_block(text: str) -> str:
    return re.sub(
        re.escape("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */")
        + r".*?"
        + re.escape("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"),
        "",
        text,
        flags=re.S,
    )

def collect_fragments():
    fragments = []
    public_transfers = PROJECT / "public" / "transfers"
    if not public_transfers.exists():
        return fragments

    tokens = ["€20 млн", "€23 млн", "€90 млн", "€100 млн"]
    for page in list(public_transfers.glob("*/index.html"))[:20]:
        text = read(page)
        for token in tokens:
            idx = text.find(token)
            if idx != -1:
                start = max(0, idx - 260)
                end = min(len(text), idx + 260)
                fragment = text[start:end].replace("\n", " ")
                fragments.append((rel(page), token, fragment[:520]))
                break
    return fragments[:8]

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
    existing = remove_old_230_block(existing)
    new_text = replace_block(existing, CSS_START, CSS_END, CSS_BLOCK)
    write(style, new_text, "center date/value timeline labels under dynamic value chart")

    hugo = run(["hugo", "-D"])

    fragments = collect_fragments()

    public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []
    sample_text = ""
    for page in public_transfer_pages[:5]:
        sample_text += read(page)[:2000]

    style_text = read(style)

    checks = {
        "hugo_exit_code": hugo.returncode,
        "style_css_exists": style.exists(),
        "style_has_231_css_block": CSS_START in style_text and CSS_END in style_text,
        "style_removed_old_230_block": "PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START" not in style_text,
        "public_transfer_pages_found": len(public_transfer_pages),
        "observed_value_label_fragments": len(fragments),
        "public_no_literal_slash_n_in_sample": "\\n" not in sample_text,
    }

    ok = (
        hugo.returncode == 0
        and style.exists()
        and checks["style_has_231_css_block"]
        and checks["style_removed_old_230_block"]
        and checks["public_transfer_pages_found"] > 0
    )

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 231 - CENTER VALUE CHART TIMELINE LABELS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Only CSS alignment for timeline date/value labels under the dynamic player value chart.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("CHANGED FILES")
    for path_rel, label, did, before, after in changed:
        lines.append(f"- {path_rel} | {label} | changed={did}")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    lines.append("OBSERVED VALUE LABEL FRAGMENTS")
    if fragments:
        for page, token, fragment in fragments:
            lines.append(f"- {page} | token={token} | {fragment}")
    else:
        lines.append("- none found in first 20 public transfer pages")
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
