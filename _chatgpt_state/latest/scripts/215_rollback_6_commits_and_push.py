from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import os
import sys

project = Path.cwd()
backup_dir = project / "_backup_215_rollback_6_commits_and_push"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_215_rollback_6_commits_and_push_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_branch = f"backup-before-rollback-6-{timestamp}"

commands = []
warnings = []

def run(cmd, check=False):
    p = subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False
    )
    commands.append({
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    })
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p

def write_report(extra=None):
    lines = []
    lines.append("PROFUTBIK 215 - ROLLBACK 6 COMMITS AND PUSH")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    if extra:
        lines.extend(extra)
        lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("COMMAND LOG")
    for item in commands:
        lines.append("-" * 70)
        lines.append(f"COMMAND: {item['cmd']}")
        lines.append(f"EXIT_CODE: {item['returncode']}")
        if item["stdout"]:
            lines.append("--- STDOUT ---")
            lines.append(item["stdout"][-5000:])
        if item["stderr"]:
            lines.append("--- STDERR ---")
            lines.append(item["stderr"][-5000:])
    lines.append("")
    lines.append("NO SITE OPENED.")
    lines.append("NO Y/N ASKED.")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

try:
    # 1) Basic git sanity.
    git_root = run(["git", "rev-parse", "--show-toplevel"], check=True).stdout.strip()
    if Path(git_root).resolve() != project.resolve():
        warnings.append(f"Git root is {git_root}, current project is {project}")

    status_before = run(["git", "status", "--short"], check=True).stdout

    current_branch = run(["git", "branch", "--show-current"], check=True).stdout.strip()
    if not current_branch:
        raise RuntimeError("Cannot detect current branch.")

    current_head = run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()
    target_head = run(["git", "rev-parse", "HEAD~6"], check=True).stdout.strip()

    log_before = run(["git", "--no-pager", "log", "--oneline", "-12"], check=True).stdout

    # 2) Save current state to files before changing anything.
    state_dir = backup_dir / "state_before"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "branch.txt").write_text(current_branch + "\n", encoding="utf-8")
    (state_dir / "current_head.txt").write_text(current_head + "\n", encoding="utf-8")
    (state_dir / "target_head_HEAD~6.txt").write_text(target_head + "\n", encoding="utf-8")
    (state_dir / "git_status_before.txt").write_text(status_before, encoding="utf-8")
    (state_dir / "git_log_before.txt").write_text(log_before, encoding="utf-8")

    # 3) Create/push backup branch at current broken HEAD before rollback.
    run(["git", "branch", backup_branch, current_head], check=True)
    # push backup branch; if push fails, stop, because rollback must be recoverable remotely.
    run(["git", "push", "origin", f"{backup_branch}:{backup_branch}"], check=True)

    # 4) Hard reset local branch to HEAD~6.
    run(["git", "reset", "--hard", target_head], check=True)

    # 5) Rebuild Hugo from rolled-back state if available.
    hugo = run(["hugo", "-D"], check=False)
    if hugo.returncode != 0:
        warnings.append("hugo -D returned non-zero after rollback. Rollback still completed locally.")

    # 6) Push rollback to main/current branch.
    # Use force-with-lease to avoid overwriting unexpected remote movement.
    run(["git", "push", "--force-with-lease", "origin", f"HEAD:{current_branch}"], check=True)

    status_after = run(["git", "status", "--short"], check=True).stdout
    log_after = run(["git", "--no-pager", "log", "--oneline", "-8"], check=True).stdout
    new_head = run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()

    extra = []
    extra.append("ROLLBACK RESULT")
    extra.append(f"- Backup branch pushed: {backup_branch}")
    extra.append(f"- Branch rolled back: {current_branch}")
    extra.append(f"- Previous HEAD: {current_head}")
    extra.append(f"- New HEAD: {new_head}")
    extra.append(f"- Target HEAD~6: {target_head}")
    extra.append("")
    extra.append("STATUS AFTER")
    extra.append(status_after if status_after.strip() else "clean")
    extra.append("")
    extra.append("LOG AFTER")
    extra.append(log_after)

    # Also save final state.
    (backup_dir / "state_after").mkdir(exist_ok=True)
    (backup_dir / "state_after" / "new_head.txt").write_text(new_head + "\n", encoding="utf-8")
    (backup_dir / "state_after" / "git_status_after.txt").write_text(status_after, encoding="utf-8")
    (backup_dir / "state_after" / "git_log_after.txt").write_text(log_after, encoding="utf-8")

    write_report(extra)
except Exception as e:
    extra = ["ROLLBACK FAILED", f"- Error: {e}"]
    write_report(extra)
    sys.exit(1)
