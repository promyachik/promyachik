
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import hashlib
import sys

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

SOURCE = PACKAGE_DIR / "restore_files" / "transfer-ticker.html"
TARGET = PROJECT / "layouts" / "partials" / "transfer-ticker.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_224_before_old_ticker_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_224_restore_old_ticker_click_run_report.txt"

commands = []

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

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

def main():
    lines = []
    lines.append("PROMYACHIK 224 - RESTORE OLD TESTED TRANSFER TICKER")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Package dir: {PACKAGE_DIR}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")

    ok = True

    if not SOURCE.exists():
        ok = False
        lines.append(f"ERROR: source file not found: {SOURCE}")
    if not PROJECT.exists():
        ok = False
        lines.append(f"ERROR: project folder not found: {PROJECT}")

    if ok:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        REPORT.parent.mkdir(parents=True, exist_ok=True)

        source_bytes = SOURCE.read_bytes()
        old_bytes = TARGET.read_bytes() if TARGET.exists() else b""
        old_hash = sha256_bytes(old_bytes) if old_bytes else "MISSING"
        new_hash = sha256_bytes(source_bytes)

        if TARGET.exists():
            backup_target = BACKUP_DIR / "layouts" / "partials" / "transfer-ticker.html"
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(TARGET, backup_target)
            lines.append(f"Backup created: {backup_target}")
        else:
            lines.append("Old target file did not exist.")

        shutil.copy2(SOURCE, TARGET)

        final_bytes = TARGET.read_bytes()
        final_hash = sha256_bytes(final_bytes)
        changed = old_hash != final_hash

        lines.append("")
        lines.append("CHANGED FILE")
        lines.append(f"- {TARGET}")
        lines.append("")
        lines.append("HASH CHECK")
        lines.append(f"- old_hash: {old_hash}")
        lines.append(f"- source_hash: {new_hash}")
        lines.append(f"- final_hash: {final_hash}")
        lines.append(f"- copied_ok: {final_hash == new_hash}")
        lines.append(f"- changed_from_before: {changed}")
        lines.append("")

        target_text = read_text(TARGET)
        first_lines = "\n".join(target_text.splitlines()[:6])
        lines.append("TARGET FIRST LINES")
        lines.append(first_lines)
        lines.append("")

        header = PROJECT / "layouts" / "partials" / "header.html"
        style = PROJECT / "static" / "css" / "style.css"
        data_file = PROJECT / "data" / "transfers.yaml"
        data_file_json = PROJECT / "data" / "transfers.json"

        header_text = read_text(header) if header.exists() else ""
        style_text = read_text(style) if style.exists() else ""

        header_include_ok = 'partial "transfer-ticker.html"' in header_text
        css_pf_ticker_ok = "pf-ticker" in style_text
        data_ok = data_file.exists() or data_file_json.exists()

        lines.append("VISIBILITY CHECKS")
        lines.append(f"- header exists: {header.exists()}")
        lines.append(f"- header includes transfer-ticker partial: {header_include_ok}")
        lines.append(f"- style.css exists: {style.exists()}")
        lines.append(f"- style.css contains pf-ticker CSS: {css_pf_ticker_ok}")
        lines.append(f"- data/transfers.yaml or data/transfers.json exists: {data_ok}")
        lines.append("")

        # Build Hugo. This is a check/build only; no push, no browser opening.
        hugo = run(["hugo", "-D"])
        lines.append("HUGO")
        lines.append(f"- exit_code: {hugo.returncode}")
        lines.append("--- STDOUT tail ---")
        lines.append(hugo.stdout[-2000:])
        lines.append("--- STDERR tail ---")
        lines.append(hugo.stderr[-2000:])
        lines.append("")

        public_index = PROJECT / "public" / "index.html"
        public_ticker_ok = False
        if public_index.exists():
            public_text = read_text(public_index)
            public_ticker_ok = "pf-ticker" in public_text

        lines.append("PUBLIC CHECK")
        lines.append(f"- public/index.html exists: {public_index.exists()}")
        lines.append(f"- public/index.html contains pf-ticker: {public_ticker_ok}")
        lines.append("")

        if final_hash != new_hash:
            ok = False
            lines.append("ERROR: target file hash does not match source.")
        if hugo.returncode != 0:
            ok = False
            lines.append("ERROR: hugo -D failed.")

        lines.append("")
        lines.append("IMPORTANT")
        lines.append("- This package changed only layouts/partials/transfer-ticker.html.")
        lines.append("- It did not change homepage, header, baseof, CSS, Ramos page, stats, or chart.")
        lines.append("- If public/index.html still does not contain pf-ticker, the next missing file is header/baseof/home layout, not this ticker file.")
        lines.append("- If public/index.html contains pf-ticker but it is not visible/moving, the next missing file is static/css/style.css pf-ticker CSS.")
        lines.append("")
        lines.append("NO SITE OPENED.")
        lines.append("NO PUSH MADE.")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
