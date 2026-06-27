# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Iterable, List, Optional

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
STATE_ROOT = ROOT / "_chatgpt_state"
LATEST = STATE_ROOT / "latest"
STAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
EXPECTED_REMOTE = "github.com/promyachik/promyachik"

LOG: List[str] = []
ERRORS: List[str] = []

def log(msg: str = "") -> None:
    print(msg, flush=True)
    LOG.append(str(msg))

def fail(msg: str) -> None:
    ERRORS.append(msg)
    log("ERROR: " + msg)

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)

def run(name: str, cmd: List[str], timeout: int = 240, allow_fail: bool = True, print_on_fail: bool = True):
    out = LATEST / "_diagnostics" / f"{name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        res = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        text = f"COMMAND: {' '.join(cmd)}\nFAILED TO RUN: {exc}\n"
        out.write_text(text, encoding="utf-8", errors="replace")
        if print_on_fail:
            log(text)
        if not allow_fail:
            fail(f"{name} could not run")
        return None

    text = "\n".join([
        "COMMAND: " + " ".join(cmd),
        "EXIT_CODE: " + str(res.returncode),
        "\n--- STDOUT ---\n" + (res.stdout or ""),
        "\n--- STDERR ---\n" + (res.stderr or ""),
    ])
    out.write_text(text, encoding="utf-8", errors="replace")

    log(f"{name}: exit {res.returncode}")

    if res.returncode != 0 and print_on_fail:
        log("")
        log(f"--- {name} OUTPUT ---")
        log(text[-5000:])
        log(f"--- END {name} OUTPUT ---")
        log("")

    if res.returncode != 0 and not allow_fail:
        fail(f"{name} failed")
    return res

def git_output(args: List[str]) -> str:
    res = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (res.stdout or "") + (res.stderr or "")

def is_git_repo() -> bool:
    res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, capture_output=True, text=True)
    return res.returncode == 0 and "true" in (res.stdout or "").lower()

def ensure_git_ready() -> None:
    if not is_git_repo():
        fail("This folder is not a Git repository")
        return

    run("git_root", ["git", "rev-parse", "--show-toplevel"])
    run("git_status_start", ["git", "status", "--short"])
    run("git_remote_verbose", ["git", "remote", "-v"])
    run("git_branch_verbose", ["git", "branch", "-vv"])
    run("git_log_last_10", ["git", "log", "--oneline", "-10"])

    # user.name/user.email are needed for commit. Set local defaults only if missing.
    name = git_output(["config", "--get", "user.name"]).strip()
    email = git_output(["config", "--get", "user.email"]).strip()
    if not name:
        run("git_set_user_name", ["git", "config", "user.name", "Dmitrii Ivanov"])
    if not email:
        run("git_set_user_email", ["git", "config", "user.email", "opencart2017z@gmail.com"])

    remotes = git_output(["remote", "-v"]).lower()
    if "origin" not in remotes:
        run("git_add_origin", ["git", "remote", "add", "origin", "https://github.com/promyachik/promyachik.git"])
        remotes = git_output(["remote", "-v"]).lower()

    if EXPECTED_REMOTE not in remotes:
        fail("origin remote is not github.com/promyachik/promyachik")
        log("Current remotes:")
        log(remotes)

def copy_file(src: Path, dest_rel: Optional[str] = None) -> bool:
    if not src.exists() or not src.is_file():
        return False
    if src.stat().st_size > 30 * 1024 * 1024:
        return False
    dest = LATEST / (dest_rel if dest_rel else rel(src))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True

def copy_rglob(base: str, patterns: Iterable[str]) -> int:
    base_path = ROOT / base
    if not base_path.exists():
        return 0
    count = 0
    for pat in patterns:
        for p in base_path.rglob(pat):
            if p.is_file():
                parts = {x.lower() for x in p.relative_to(ROOT).parts}
                if ".git" in parts or "public" in parts or "var" in parts or "_chatgpt_state" in parts:
                    continue
                if copy_file(p):
                    count += 1
    return count

def collect_state() -> None:
    if LATEST.exists():
        shutil.rmtree(LATEST, ignore_errors=True)
    LATEST.mkdir(parents=True, exist_ok=True)

    info = {
        "created_at": STAMP,
        "project_root": str(ROOT),
        "purpose": "Current local project state for ChatGPT",
        "important": "This folder is overwritten every time by PUSH_STATE_TO_GITHUB.bat",
    }
    (LATEST / "_STATE_INFO.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build current public HTML.
    run("hugo_build", ["hugo"], timeout=240, allow_fail=True)

    # Core source files.
    for f in [
        "hugo.toml",
        "config.toml",
        "config.yaml",
        "config.yml",
        ".gitignore",
        "PUSH_STATE_TO_GITHUB.bat",
        "GET_STATE_FOR_CHATGPT.bat",
    ]:
        copy_file(ROOT / f)

    copy_rglob("layouts", ["*.html", "*.css", "*.js"])
    copy_rglob("content/transfers", ["*.md"])
    copy_rglob("data", ["*.json", "*.toml", "*.yaml", "*.yml"])
    copy_rglob("scripts", ["*.py", "*.bat"])

    # Static source: do not copy all thousands of images, only CSS/JS and focus assets.
    copy_rglob("static/css", ["*.css"])
    copy_file(ROOT / "static" / "header.css")
    for f in [
        "static/images/players/cutout/532.png",
        "static/images/players/api/532.png",
        "static/images/flags/netherlands.svg",
        "static/images/clubs/api/157.png",
        "static/images/clubs/api/33.png",
        "static/images/clubs/bayern-munich.svg",
        "static/images/clubs/manchester-united.svg",
        "static/images/clubs/psg.svg",
        "static/images/clubs/ac-milan.svg",
    ]:
        copy_file(ROOT / f)

    # Rendered HTML is often the most important.
    pub_transfers = ROOT / "public" / "transfers"
    if pub_transfers.exists():
        for p in pub_transfers.rglob("*.html"):
            copy_file(p)

    # Root reports/logs.
    reports = []
    for pat in ["_*.txt", "*.log"]:
        reports.extend([p for p in ROOT.glob(pat) if p.is_file()])
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in reports[:60]:
        copy_file(p, str(Path("_latest_reports") / p.name))

    # File list.
    files = []
    for p in LATEST.rglob("*"):
        if p.is_file():
            try:
                files.append(f"{p.relative_to(LATEST)}\t{p.stat().st_size}")
            except Exception:
                files.append(str(p))
    (LATEST / "_diagnostics" / "state_file_list.txt").parent.mkdir(parents=True, exist_ok=True)
    (LATEST / "_diagnostics" / "state_file_list.txt").write_text("\n".join(sorted(files)), encoding="utf-8", errors="replace")

def commit_and_push() -> None:
    run("git_status_before_add", ["git", "status", "--short"])
    run("git_add_state_force", ["git", "add", "-A", "-f", "_chatgpt_state/latest"], timeout=240, allow_fail=False)
    run("git_add_push_scripts", ["git", "add", "-f", "PUSH_STATE_TO_GITHUB.bat", "scripts/push_state_to_github.py"], timeout=120, allow_fail=True)
    run("git_status_after_add", ["git", "status", "--short"])

    # Detect staged changes.
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged.returncode == 0:
        log("No staged changes. Forcing state timestamp update.")
        marker = LATEST / "_FORCE_UPDATE.txt"
        marker.write_text(f"forced update {STAMP}\n", encoding="utf-8")
        run("git_add_force_marker", ["git", "add", "-f", "_chatgpt_state/latest/_FORCE_UPDATE.txt"], timeout=120, allow_fail=False)

    msg = f"ChatGPT state sync {STAMP}"
    commit = run("git_commit_state", ["git", "commit", "-m", msg], timeout=240, allow_fail=True)
    if commit is not None and commit.returncode != 0:
        combined = ((commit.stdout or "") + "\n" + (commit.stderr or "")).lower()
        if "nothing to commit" in combined:
            log("Nothing to commit, but will still try push.")
        else:
            fail("git commit failed")
            return

    # Push current HEAD to main explicitly.
    push = run("git_push_head_to_main", ["git", "push", "-u", "origin", "HEAD:main"], timeout=300, allow_fail=True, print_on_fail=True)
    if push is None or push.returncode != 0:
        fail("git push failed")
        return

    run("git_ls_remote_main", ["git", "ls-remote", "--heads", "origin", "main"], timeout=120, allow_fail=True)
    run("git_status_final", ["git", "status", "--short"])

def write_final_log() -> None:
    p = LATEST / "_diagnostics" / "push_state_v2_log.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(LOG), encoding="utf-8", errors="replace")
    # Add final log to git as well if possible, but only if we are before push is impossible this may be uncommitted.
    try:
        subprocess.run(["git", "add", "-f", "_chatgpt_state/latest/_diagnostics/push_state_v2_log.txt"], cwd=ROOT, capture_output=True)
    except Exception:
        pass

def main() -> None:
    log("START PUSH_STATE_TO_GITHUB V2")
    log(f"ROOT: {ROOT}")

    collect_state()
    ensure_git_ready()

    if not ERRORS:
        commit_and_push()

    write_final_log()

    if ERRORS:
        log("")
        log("FAILED")
        log("Main error:")
        for e in ERRORS:
            log("- " + e)
        log("")
        log("Copy this window text to ChatGPT.")
        raise SystemExit(2)

    log("")
    log("DONE")
    log("State pushed to GitHub.")
    log("Write in ChatGPT: запушил")

if __name__ == "__main__":
    main()
