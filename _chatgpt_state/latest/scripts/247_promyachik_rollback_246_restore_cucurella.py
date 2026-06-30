
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
SAFETY_BACKUP = PROJECT / f"_backup_promyachik_247_before_rollback_246_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_247_rollback_246_restore_cucurella_report.txt"

RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

TARGETS = [
    "layouts/transfers/single.html",
    "layouts/_default/baseof.html",
    "static/css/style.css",
    "public/transfers/marc-cucurella-real-madrid/index.html",
]

MARKER_START = "<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT START -->"
MARKER_END = "<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT END -->"
CSS_START = "/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT START */"
CSS_END = "/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT END */"

BAD_246_STRINGS = [
    "__promyachikCucurellaForceShift246Ready",
    "promyachik-cucurella-force-price-246",
    "promyachik-cucurella-force-shifted-246",
    "data-promyachik-cucurella-force-shift-246",
    "PROMYACHIK 246 CUCURELLA FORCE",
]

commands = []
changed = []
warnings = []
restore_log = []

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

def backup_current(path: Path):
    if path.exists():
        dst = SAFETY_BACKUP / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup_current(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def copy_restore(src: Path, dst: Path, label: str):
    before = sha(dst)
    backup_current(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((rel(dst), f"{label} <= {src}", before != after, before, after))

def run_cmd(cmd):
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

def strip_between(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)

def find_latest_246_backup():
    backups = sorted(
        [p for p in PROJECT.glob("_backup_promyachik_246_before_force_shift_cucurella_price_right_*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if backups:
        return backups[0]
    return None

def restore_from_246_backup(backup_dir: Path):
    restored = 0

    for rel_target in TARGETS:
        src = backup_dir / rel_target
        dst = PROJECT / rel_target

        if src.exists():
            copy_restore(src, dst, "restore from pre-246 backup")
            restore_log.append(f"restored {rel_target} from {src}")
            restored += 1
        else:
            restore_log.append(f"backup missing {rel_target}")

    return restored

def remove_246_markers_fallback():
    # Fallback cleanup if backup is incomplete.
    paths = [
        PROJECT / "layouts" / "transfers" / "single.html",
        PROJECT / "layouts" / "_default" / "baseof.html",
        PROJECT / "static" / "css" / "style.css",
        PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html",
    ]

    for path in paths:
        if not path.exists():
            continue

        text = read(path)
        old = text

        text = strip_between(text, MARKER_START, MARKER_END)
        text = strip_between(text, CSS_START, CSS_END)

        if text != old:
            write(path, text.rstrip() + "\n", "fallback remove 246 markers/scripts/css")

def restore_deleted_old_partials_if_available(backup_dir: Path | None):
    # Only restore these if they existed in the pre-246 backup. This is to restore exactly previous state.
    if backup_dir is None:
        return

    for rel_target in [
        "layouts/partials/promyachik-cucurella-align-price-labels-242.html",
        "layouts/partials/promyachik-cucurella-move-prices-to-club-x-244.html",
    ]:
        src = backup_dir / rel_target
        dst = PROJECT / rel_target
        if src.exists():
            copy_restore(src, dst, "restore previously existing partial from pre-246 backup")
            restore_log.append(f"restored old partial {rel_target}")

def collect_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in BAD_246_STRINGS + ["pfb-market-chart", "market-chart", "€"]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 400):idx + 900].replace("\n", " ")[:1300]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    SAFETY_BACKUP.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ramos_before = sha(RAMOS_PAGE)
    cucurella_before = sha(CUCURELLA_PAGE)

    ok = True
    error_text = ""
    hugo = None
    backup_dir = None
    restored_count = 0
    fragments = []
    checks = {}

    try:
        backup_dir = find_latest_246_backup()

        if backup_dir:
            restored_count = restore_from_246_backup(backup_dir)
            restore_deleted_old_partials_if_available(backup_dir)
        else:
            warnings.append("pre-246 backup not found; using marker cleanup fallback")

        remove_246_markers_fallback()

        hugo = run_cmd(["hugo", "-D"])

        # After Hugo rebuild, ensure public page has no 246 marker.
        remove_246_markers_fallback()

        single_text = read(PROJECT / "layouts" / "transfers" / "single.html") if (PROJECT / "layouts" / "transfers" / "single.html").exists() else ""
        style_text = read(PROJECT / "static" / "css" / "style.css") if (PROJECT / "static" / "css" / "style.css").exists() else ""
        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""
        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_ramos_text = read(public_ramos) if public_ramos.exists() else ""

        ramos_after = sha(RAMOS_PAGE)
        cucurella_after = sha(CUCURELLA_PAGE)

        fragments = collect_fragments()

        checks = {
            "hugo_exit_code": hugo.returncode,
            "pre_246_backup_found": str(backup_dir) if backup_dir else "",
            "restored_files_from_backup_count": restored_count,
            "ramos_content_untouched": ramos_before == ramos_after,
            "cucurella_content_untouched": cucurella_before == cucurella_after,
            "single_has_no_246": all(s not in single_text for s in BAD_246_STRINGS),
            "style_has_no_246": all(s not in style_text for s in BAD_246_STRINGS) and CSS_START not in style_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_cucurella_has_no_246": all(s not in public_text for s in BAD_246_STRINGS),
            "public_ramos_has_no_246": all(s not in public_ramos_text for s in BAD_246_STRINGS),
            "observed_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["single_has_no_246"]
            and checks["style_has_no_246"]
            and checks["public_cucurella_exists"]
            and checks["public_cucurella_has_no_246"]
            and checks["public_ramos_has_no_246"]
        )

    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 247 - ROLLBACK 246 RESTORE CUCURELLA")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Remove 246 completely.")
    lines.append("- Restore files from the backup created before 246, when available.")
    lines.append("- Do not touch Ramos content.")
    lines.append("- Do not touch Cucurella content.")
    lines.append("- Run Hugo after restore.")
    lines.append("")
    lines.append("BACKUPS")
    lines.append(f"- safety backup before rollback: {SAFETY_BACKUP}")
    lines.append(f"- pre-246 backup used: {backup_dir if backup_dir else 'NOT FOUND'}")
    lines.append("")
    lines.append("RESTORE LOG")
    if restore_log:
        for item in restore_log:
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
    lines.append("OBSERVED PUBLIC FRAGMENTS")
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
