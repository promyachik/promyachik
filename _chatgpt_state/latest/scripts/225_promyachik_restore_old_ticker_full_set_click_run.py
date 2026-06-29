
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import json
import re
import sys
import hashlib

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_225_before_old_ticker_full_set_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_225_restore_old_ticker_full_set_report.txt"

RESTORE = PACKAGE_DIR / "restore_files"

TARGETS = [
    PROJECT / "layouts" / "partials" / "transfer-ticker.html",
    PROJECT / "static" / "css" / "transfer-ticker.css",
    PROJECT / "static" / "css" / "style.css",
    PROJECT / "layouts" / "partials" / "header.html",
    PROJECT / "layouts" / "_default" / "baseof.html",
    PROJECT / "layouts" / "index.html",
    PROJECT / "data" / "transfers.json",
    PROJECT / "data" / "club-logos.json",
]

commands = []
changed = []
warnings = []

def sha(path: Path):
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def backup(path: Path):
    if path.exists():
        rel = path.relative_to(PROJECT)
        dst = BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write_text(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((str(path.relative_to(PROJECT)), label, before != after, before, after))

def copy_file(src: Path, dst: Path, label: str):
    before = sha(dst)
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((str(dst.relative_to(PROJECT)), label, before != after, before, after))

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
        "stdout": p.stdout[-3000:],
        "stderr": p.stderr[-3000:],
    })
    return p

def read(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")

def clean_template(path: Path):
    if not path.exists():
        return
    text = read(path)
    original = text

    text = text.replace("\\n\\n", "\n")
    text = text.replace("\\n", "\n")
    text = re.sub(r"cite[^]*", "", text)

    if path.name == "header.html":
        # Remove broken extra footer ticker include if any.
        text = text.replace('{{ partial "footer-transfer-ticker.html" . }}', "")
        if 'partial "transfer-ticker.html"' not in text:
            if re.search(r"</header>", text, re.I):
                text = re.sub(r"(?i)</header>", '</header>\n{{ partial "transfer-ticker.html" . }}', text, count=1)
            else:
                text = text.rstrip() + '\n{{ partial "transfer-ticker.html" . }}\n'

    if text != original:
        write_text(path, text, "clean literal \\n/citation and ensure ticker include")

def load_json_if_possible(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def ensure_transfers_data():
    src = RESTORE / "data" / "transfers.json"
    dst = PROJECT / "data" / "transfers.json"
    current = load_json_if_possible(dst) if dst.exists() else None

    must_restore = (
        not isinstance(current, list)
        or len(current) == 0
        or not any(isinstance(x, dict) and x.get("player") for x in current)
    )

    if must_restore:
        copy_file(src, dst, "restore old working ticker data because data/transfers.json is missing/empty/broken")
    else:
        changed.append((str(dst.relative_to(PROJECT)), "kept existing non-empty transfers data", False, sha(dst), sha(dst)))

    # If transfers.yaml exists and is empty/broken, move it aside so Hugo uses JSON cleanly.
    yaml_path = PROJECT / "data" / "transfers.yaml"
    yml_path = PROJECT / "data" / "transfers.yml"
    for y in [yaml_path, yml_path]:
        if y.exists():
            ytxt = read(y).strip()
            if not ytxt or ytxt in ("[]", "{}"):
                backup(y)
                new_path = y.with_suffix(y.suffix + f".disabled_by_225_{timestamp}")
                y.rename(new_path)
                changed.append((str(y.relative_to(PROJECT)), f"disabled empty {y.name}", True, "exists", "renamed"))

def ensure_club_logos():
    dst = PROJECT / "data" / "club-logos.json"
    current = load_json_if_possible(dst) if dst.exists() else None
    if not isinstance(current, dict) or not isinstance(current.get("clubs"), dict):
        copy_file(RESTORE / "data" / "club-logos-minimal.json", dst, "restore minimal club-logos only because club-logos.json is missing/broken")
    else:
        changed.append((str(dst.relative_to(PROJECT)), "kept existing club-logos.json", False, sha(dst), sha(dst)))

def append_ticker_css_to_style():
    style = PROJECT / "static" / "css" / "style.css"
    css = read(RESTORE / "static" / "css" / "transfer-ticker.css")
    existing = read(style) if style.exists() else ""

    start = "/* PROMYACHIK 225 OLD TESTED TICKER CSS START */"
    end = "/* PROMYACHIK 225 OLD TESTED TICKER CSS END */"

    # Remove previous marker block and the fake 218 block marker if it exists.
    existing = re.sub(
        re.escape(start) + r".*?" + re.escape(end),
        "",
        existing,
        flags=re.S
    )
    existing = re.sub(
        r"/\* 218 restore top bottom transfer tickers \*/.*?(?=/\* \d|\Z)",
        "",
        existing,
        flags=re.S
    )

    new_text = existing.rstrip() + "\n\n" + start + "\n" + css.rstrip() + "\n" + end + "\n"
    write_text(style, new_text, "append old tested pf-ticker CSS to style.css")

def main():
    ok = True
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        ok = False
        lines = [f"ERROR: project folder not found: {PROJECT}"]
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    for t in TARGETS:
        backup(t)

    copy_file(
        RESTORE / "layouts" / "partials" / "transfer-ticker.html",
        PROJECT / "layouts" / "partials" / "transfer-ticker.html",
        "restore old tested interactive ticker partial"
    )

    copy_file(
        RESTORE / "static" / "css" / "transfer-ticker.css",
        PROJECT / "static" / "css" / "transfer-ticker.css",
        "restore old tested ticker css file"
    )

    append_ticker_css_to_style()

    for p in [
        PROJECT / "layouts" / "partials" / "header.html",
        PROJECT / "layouts" / "_default" / "baseof.html",
        PROJECT / "layouts" / "index.html",
    ]:
        clean_template(p)

    ensure_transfers_data()
    ensure_club_logos()

    hugo = run(["hugo", "-D"])

    public_index = PROJECT / "public" / "index.html"
    public_text = read(public_index) if public_index.exists() else ""

    checks = {
        "hugo_exit_code": hugo.returncode,
        "public_index_exists": public_index.exists(),
        "public_has_pf_ticker": "pf-ticker" in public_text,
        "public_has_pf_ticker_item": "pf-ticker__item" in public_text,
        "public_has_literal_slash_n": "\\n" in public_text,
        "transfer_ticker_has_interactive": "pf-ticker--interactive" in read(PROJECT / "layouts" / "partials" / "transfer-ticker.html"),
        "style_css_has_old_ticker_css": "PROMYACHIK 225 OLD TESTED TICKER CSS START" in read(PROJECT / "static" / "css" / "style.css"),
    }

    if hugo.returncode != 0:
        ok = False
    if not checks["public_has_pf_ticker"]:
        ok = False
    if not checks["public_has_pf_ticker_item"]:
        ok = False
    if checks["public_has_literal_slash_n"]:
        ok = False

    lines = []
    lines.append("PROMYACHIK 225 - RESTORE OLD TESTED TICKER FULL SET")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Package dir: {PACKAGE_DIR}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("CHANGED FILES")
    for rel, label, did_change, before, after in changed:
        lines.append(f"- {rel} | {label} | changed={did_change}")
    lines.append("")
    lines.append("CHECKS")
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    lines.append("HUGO")
    lines.append(f"- exit_code: {hugo.returncode}")
    lines.append("--- STDOUT tail ---")
    lines.append(hugo.stdout[-2000:])
    lines.append("--- STDERR tail ---")
    lines.append(hugo.stderr[-2000:])
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands:
        lines.append("-" * 60)
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
