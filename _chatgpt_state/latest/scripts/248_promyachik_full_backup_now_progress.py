
from pathlib import Path
from datetime import datetime
import shutil
import hashlib
import os
import sys
import subprocess
import json

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

BACKUPS_ROOT = Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS")
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_NAME = f"{timestamp}_FULL_BACKUP_CURRENT_STATE_AFTER_247_ROLLBACK"
BACKUP_DIR = BACKUPS_ROOT / BACKUP_NAME

REPORT = PROJECT / "var" / "promyachik_248_full_backup_now_report.txt"
PROGRESS_IN_BACKUP = BACKUP_DIR / "PROMYACHIK_PROGRESS_CURRENT_STATE.txt"
MANIFEST = BACKUP_DIR / "PROMYACHIK_BACKUP_MANIFEST.json"

EXCLUDE_DIR_NAMES = {
    ".hugo_build.lock",
}

# Full project backup means we do NOT exclude content/layouts/static/data/public/scripts/.git.
# We only avoid copying the external backups folder if someone accidentally placed it inside the project.
EXTERNAL_BACKUP_ROOT_NAME = "Promyachik_BACKUPS"

commands = []
copied_files = 0
copied_dirs = 0
total_bytes = 0
errors = []

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except Exception:
        return str(path)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_cmd(cmd):
    p = subprocess.run(
        cmd,
        cwd=PROJECT if PROJECT.exists() else None,
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

def ignore_func(src, names):
    ignored = []

    for name in names:
        if name == EXTERNAL_BACKUP_ROOT_NAME:
            ignored.append(name)

    return set(ignored)

def count_tree(path: Path):
    files = 0
    dirs = 0
    size = 0

    for root, dirnames, filenames in os.walk(path):
        dirs += len(dirnames)
        for filename in filenames:
            p = Path(root) / filename
            try:
                files += 1
                size += p.stat().st_size
            except OSError:
                pass

    return files, dirs, size

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def detect_state():
    state = {}

    important_paths = [
        "hugo.toml",
        "layouts/transfers/single.html",
        "layouts/partials/transfer-player-market-value-chart.html",
        "layouts/partials/profutbik-market-chart-static.html",
        "static/css/style.css",
        "content/transfers/marc-cucurella-real-madrid/index.md",
        "content/transfers/goncalo-ramos-ac-milan/index.md",
        "data/transfers.json",
    ]

    state["important_files"] = []

    for rp in important_paths:
        p = PROJECT / rp
        item = {"path": rp, "exists": p.exists()}
        if p.exists() and p.is_file():
            item["size"] = p.stat().st_size
            item["sha256"] = sha256_file(p)

            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                item["contains_246"] = "PROMYACHIK 246" in txt or "__promyachikCucurellaForceShift246Ready" in txt
                item["contains_245"] = "PROMYACHIK 245" in txt or "promyachik-cucurella-price-shift-245" in txt
                item["contains_244"] = "PROMYACHIK 244" in txt or "promyachik-cucurella-move-prices" in txt
                item["contains_243"] = "PROMYACHIK 243" in txt or "promyachik-cucurella-label-243" in txt
                item["contains_242"] = "PROMYACHIK 242" in txt or "promyachik-cucurella-align-price" in txt
            except Exception:
                pass

        state["important_files"].append(item)

    transfers_dir = PROJECT / "content" / "transfers"
    if transfers_dir.exists():
        state["transfer_page_count"] = len(list(transfers_dir.glob("*/index.md")))
        state["transfer_pages"] = sorted([p.parent.name for p in transfers_dir.glob("*/index.md")])[:200]
    else:
        state["transfer_page_count"] = 0
        state["transfer_pages"] = []

    public_cuc = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
    if public_cuc.exists():
        txt = public_cuc.read_text(encoding="utf-8", errors="ignore")
        state["public_cucurella_exists"] = True
        state["public_cucurella_contains_246"] = "PROMYACHIK 246" in txt or "__promyachikCucurellaForceShift246Ready" in txt
        state["public_cucurella_contains_245"] = "PROMYACHIK 245" in txt or "promyachik-cucurella-price-shift-245" in txt
    else:
        state["public_cucurella_exists"] = False

    return state

def main():
    global copied_files, copied_dirs, total_bytes

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        msg = f"ERROR: Project not found: {PROJECT}"
        write_text(REPORT, msg)
        print(msg)
        sys.exit(1)

    if BACKUP_DIR.exists():
        msg = f"ERROR: Backup folder already exists: {BACKUP_DIR}"
        write_text(REPORT, msg)
        print(msg)
        sys.exit(1)

    state_before = detect_state()

    # Create full backup.
    try:
        shutil.copytree(PROJECT, BACKUP_DIR, ignore=ignore_func, dirs_exist_ok=False)
    except Exception as e:
        errors.append(str(e))

    if BACKUP_DIR.exists():
        copied_files, copied_dirs, total_bytes = count_tree(BACKUP_DIR)

    # Optional Hugo status only; no project modification beyond report.
    hugo_version = run_cmd(["hugo", "version"])

    manifest = {
        "backup_name": BACKUP_NAME,
        "backup_dir": str(BACKUP_DIR),
        "source_project": str(PROJECT),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "copied_files": copied_files,
        "copied_dirs": copied_dirs,
        "total_bytes": total_bytes,
        "state": state_before,
        "errors": errors,
    }

    if BACKUP_DIR.exists():
        write_text(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))

    progress_lines = []
    progress_lines.append("PROMYACHIK CURRENT PROGRESS / RECOVERY POINT")
    progress_lines.append("=" * 100)
    progress_lines.append(f"Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    progress_lines.append(f"Full backup folder: {BACKUP_DIR}")
    progress_lines.append(f"Source project: {PROJECT}")
    progress_lines.append("")
    progress_lines.append("CURRENT WORK CONTEXT")
    progress_lines.append("- Work is paused after rollback package 247.")
    progress_lines.append("- Main problematic area: Cucurella player value chart bottom price labels.")
    progress_lines.append("- User requirement for next work:")
    progress_lines.append("  1) Work only after exact target block is agreed.")
    progress_lines.append("  2) Make one minimal change at a time.")
    progress_lines.append("  3) After user confirms a step is good, make a FULL project backup.")
    progress_lines.append("  4) Full backup means the whole C:\\Users\\Dmitrii\\Promyachik folder, not one page or one CSS file.")
    progress_lines.append("  5) Do not touch Ramos/Goncalo Ramos page unless user explicitly asks.")
    progress_lines.append("")
    progress_lines.append("IMPORTANT RULE FOR NEXT SESSION")
    progress_lines.append("- Before any new visual fix: inspect the real active HTML/CSS block first.")
    progress_lines.append("- Do not send another fix package until the exact visible element/class/template is identified.")
    progress_lines.append("- If a report says changed files = 0 or VERIFIED_OK = False, stop and diagnose; do not continue guessing.")
    progress_lines.append("")
    progress_lines.append("BACKUP CONTENT")
    progress_lines.append(f"- Copied files: {copied_files}")
    progress_lines.append(f"- Copied folders: {copied_dirs}")
    progress_lines.append(f"- Total bytes: {total_bytes}")
    progress_lines.append("")
    progress_lines.append("KEY FILE STATE")
    for item in state_before.get("important_files", []):
        progress_lines.append(f"- {item.get('path')} | exists={item.get('exists')} | size={item.get('size', '-')}")
        for key in ["contains_242", "contains_243", "contains_244", "contains_245", "contains_246"]:
            if key in item:
                progress_lines.append(f"  {key}: {item[key]}")
    progress_lines.append("")
    progress_lines.append("TRANSFER PAGES")
    progress_lines.append(f"- count: {state_before.get('transfer_page_count')}")
    for slug in state_before.get("transfer_pages", [])[:80]:
        progress_lines.append(f"  - {slug}")
    progress_lines.append("")
    progress_lines.append("HUGO VERSION")
    progress_lines.append(f"- exit_code: {hugo_version.returncode}")
    if hugo_version.stdout:
        progress_lines.append(hugo_version.stdout.strip())
    if hugo_version.stderr:
        progress_lines.append(hugo_version.stderr.strip())
    progress_lines.append("")
    progress_lines.append("RESTORE INSTRUCTION")
    progress_lines.append("- To restore this state, copy the contents of the backup folder back into:")
    progress_lines.append(f"  {PROJECT}")
    progress_lines.append("- Close Hugo window before restoring files.")
    progress_lines.append("")
    if errors:
        progress_lines.append("ERRORS")
        for e in errors:
            progress_lines.append(f"- {e}")

    progress_text = "\n".join(progress_lines)

    if BACKUP_DIR.exists():
        write_text(PROGRESS_IN_BACKUP, progress_text)

    report_lines = []
    report_lines.append("PROMYACHIK 248 - FULL BACKUP NOW + PROGRESS")
    report_lines.append("=" * 100)
    report_lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Project dir: {PROJECT}")
    report_lines.append(f"Backup root: {BACKUPS_ROOT}")
    report_lines.append(f"Full backup folder: {BACKUP_DIR}")
    report_lines.append("")
    report_lines.append("RESULT")
    report_lines.append(f"- backup_exists: {BACKUP_DIR.exists()}")
    report_lines.append(f"- copied_files: {copied_files}")
    report_lines.append(f"- copied_dirs: {copied_dirs}")
    report_lines.append(f"- total_bytes: {total_bytes}")
    report_lines.append(f"- progress_file: {PROGRESS_IN_BACKUP}")
    report_lines.append(f"- manifest_file: {MANIFEST}")
    report_lines.append(f"- errors_count: {len(errors)}")
    report_lines.append("")
    report_lines.append("RULE SAVED")
    report_lines.append("- Full backup after each user-approved step.")
    report_lines.append("- No partial-only backup for approved restore points.")
    report_lines.append("- Stop guessing when a report fails.")
    report_lines.append("")
    report_lines.append("COMMAND LOG")
    for c in commands:
        report_lines.append("-" * 70)
        report_lines.append(f"COMMAND: {c['cmd']}")
        report_lines.append(f"EXIT_CODE: {c['returncode']}")
        if c["stdout"]:
            report_lines.append("--- STDOUT ---")
            report_lines.append(c["stdout"])
        if c["stderr"]:
            report_lines.append("--- STDERR ---")
            report_lines.append(c["stderr"])
    report_lines.append("")
    report_lines.append("NO PUSH MADE.")
    report_lines.append("NO SITE OPENED.")

    write_text(REPORT, "\n".join(report_lines))
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if errors or not BACKUP_DIR.exists() or copied_files <= 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
