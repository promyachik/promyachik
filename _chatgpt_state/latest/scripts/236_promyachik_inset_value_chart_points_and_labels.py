
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_236_before_inset_value_chart_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_236_inset_value_chart_points_and_labels_report.txt"

commands = []
changed = []

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

def patch_chart_partial():
    path = PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html"
    if not path.exists():
        raise RuntimeError(f"chart partial not found: {path}")

    text = read(path)
    original = text

    if 'pfb-market-chart-static__point-group' not in text:
        raise RuntimeError("current chart partial does not contain 235 point-group axis logic; refusing to patch the wrong file")

    # 235 already put dot/date/value on one vertical axis.
    # 236 only moves the whole axis inside the card so the first/last labels do not hug the edges.
    text = re.sub(
        r'{{-\s*\$leftPad\s*:=\s*[0-9.]+\s*-}}',
        '{{- $leftPad := 92.0 -}}',
        text,
        count=1
    )
    text = re.sub(
        r'{{-\s*\$rightPad\s*:=\s*[0-9.]+\s*-}}',
        '{{- $rightPad := 92.0 -}}',
        text,
        count=1
    )

    # Keep grid lines visually aligned with the new first/last point area.
    text = re.sub(
        r'<line x1="[0-9.]+" y1="90" x2="[0-9.]+" y2="90" class="pfb-market-chart-static__grid" />',
        '<line x1="92" y1="90" x2="888" y2="90" class="pfb-market-chart-static__grid" />',
        text
    )
    text = re.sub(
        r'<line x1="[0-9.]+" y1="185" x2="[0-9.]+" y2="185" class="pfb-market-chart-static__grid" />',
        '<line x1="92" y1="185" x2="888" y2="185" class="pfb-market-chart-static__grid" />',
        text
    )
    text = re.sub(
        r'<line x1="[0-9.]+" y1="280" x2="[0-9.]+" y2="280" class="pfb-market-chart-static__grid" />',
        '<line x1="92" y1="280" x2="888" y2="280" class="pfb-market-chart-static__grid" />',
        text
    )

    # Mark the exact tuning version in the section class without touching chart data.
    text = text.replace(
        'pfb-market-chart-static pfb-market-chart-static--235',
        'pfb-market-chart-static pfb-market-chart-static--235 pfb-market-chart-static--236'
    )

    if text == original:
        raise RuntimeError("no changes made to chart partial; expected left/right pad patch")

    write(path, text, "move value chart point axes inward while keeping dot/date/value vertically aligned")

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
        patch_chart_partial()

        hugo = run(["hugo", "-D"])

        chart_partial = read(PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html")
        public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []

        public_sample = ""
        for page in public_transfer_pages[:10]:
            public_sample += read(page)[:10000]

        for page in public_transfer_pages[:20]:
            text = read(page)
            if "pfb-market-chart-static--236" in text:
                idx = text.find("pfb-market-chart-static--236")
                fragments.append((rel(page), text[max(0, idx - 250): idx + 1400].replace("\n", " ")[:1600]))

        checks = {
            "hugo_exit_code": hugo.returncode,
            "partial_left_pad_92": "{{- $leftPad := 92.0 -}}" in chart_partial,
            "partial_right_pad_92": "{{- $rightPad := 92.0 -}}" in chart_partial,
            "partial_keeps_group_axis": 'pfb-market-chart-static__point-group' in chart_partial and 'transform="translate({{ printf "%.2f" $x }} 0)"' in chart_partial,
            "partial_dot_and_label_same_axis": 'cx="0"' in chart_partial and 'x="0"' in chart_partial,
            "public_transfer_pages_found": len(public_transfer_pages),
            "public_has_236_chart": "pfb-market-chart-static--236" in public_sample,
            "public_has_dot_cx_zero": 'cx="0"' in public_sample,
            "public_has_label_x_zero": 'x="0"' in public_sample,
            "observed_236_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["partial_left_pad_92"]
            and checks["partial_right_pad_92"]
            and checks["partial_keeps_group_axis"]
            and checks["partial_dot_and_label_same_axis"]
            and checks["public_transfer_pages_found"] > 0
            and checks["public_has_236_chart"]
            and checks["public_has_dot_cx_zero"]
            and checks["public_has_label_x_zero"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 236 - INSET VALUE CHART POINTS AND LABELS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Keeps 235 vertical axis logic: group translate(X 0), dot cx=0, labels x=0.")
    lines.append("- Changes only chart horizontal padding: left/right pad 48 -> 92.")
    lines.append("- This moves the first and last point+label axes inward so labels do not hug the card edges.")
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
    lines.append("OBSERVED 236 PUBLIC FRAGMENTS")
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
