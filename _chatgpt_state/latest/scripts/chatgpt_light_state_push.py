# -*- coding: utf-8 -*-
"""
Create a small ChatGPT-readable project snapshot and optionally push ONLY that snapshot.
No backups are created. Real project files are not modified, except _chatgpt_state/latest.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "_chatgpt_state" / "latest"
REPORTS = STATE / "_latest_reports"
DIAG = STATE / "_diagnostics"

MAX_REPORTS = 40

SKIP_DIR_NAMES = {
    ".git", ".github", "public", "resources", "node_modules", "__pycache__",
    "_backup", "backups", "backup", "PROMYACHIK_BACKUPS",
}

SKIP_FILE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".svg",
    ".zip", ".7z", ".rar", ".mp4", ".mov", ".avi", ".pdf",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run(cmd: list[str], check: bool = False) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, shell=False)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def copy_file(src: Path, dst: Path, copied: list[str]) -> None:
    if not src.exists() or not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append(rel(src))


def copy_tree_text(src_dir: Path, dst_dir: Path, copied: list[str], *, include_suffixes: set[str] | None = None) -> None:
    if not src_dir.exists():
        return
    for src in src_dir.rglob("*"):
        if not src.is_file():
            continue
        parts_lower = {p.lower() for p in src.relative_to(src_dir).parts}
        if any(skip.lower() in parts_lower for skip in SKIP_DIR_NAMES):
            continue
        if src.suffix.lower() in SKIP_FILE_SUFFIXES:
            continue
        if include_suffixes is not None and src.suffix.lower() not in include_suffixes:
            continue
        dst = dst_dir / src.relative_to(src_dir)
        copy_file(src, dst, copied)


def copy_public_transfer_html(copied: list[str]) -> None:
    src_root = ROOT / "public" / "transfers"
    dst_root = STATE / "public" / "transfers"
    if not src_root.exists():
        return
    for src in src_root.rglob("index.html"):
        dst = dst_root / src.relative_to(src_root)
        copy_file(src, dst, copied)


def copy_latest_reports(copied: list[str]) -> None:
    src_var = ROOT / "var"
    REPORTS.mkdir(parents=True, exist_ok=True)
    candidates: list[Path] = []
    if src_var.exists():
        for p in src_var.glob("promyachik_*_report.txt"):
            if p.is_file():
                candidates.append(p)
        for p in src_var.glob("*_report.txt"):
            if p.is_file() and p not in candidates:
                candidates.append(p)
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_REPORTS]
    for src in candidates:
        copy_file(src, REPORTS / src.name, copied)


def write_state_info(copied: list[str]) -> None:
    code, head, _ = run(["git", "rev-parse", "--short", "HEAD"])
    git_head = head if code == 0 else "unknown"
    code, status, _ = run(["git", "status", "--short"])
    state_files = [str(p.relative_to(STATE).as_posix()) for p in STATE.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in STATE.rglob("*") if p.is_file())

    info = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_dir": str(ROOT),
        "git_head_short": git_head,
        "purpose": "Small ChatGPT-readable state snapshot. No backups. Heavy images/public database intentionally skipped.",
        "copied_source_files_count": len(copied),
        "state_files_count": len(state_files),
        "state_total_bytes": total_bytes,
        "state_total_mb": round(total_bytes / 1024 / 1024, 3),
        "copied_source_files": copied,
        "git_status_short_before_commit": status.splitlines() if status else [],
        "included": [
            "hugo.toml",
            "layouts/** text files",
            "static/css/** css",
            "static/js/** js",
            "content/transfers/** markdown/text",
            "selected data text/json, excluding data/playerdb",
            "public/transfers/**/index.html only",
            f"latest {MAX_REPORTS} var/*_report.txt reports",
        ],
        "excluded_heavy": [
            "static/images/**",
            "public images/assets except transfer index.html",
            "data/playerdb/**",
            "ZIP/backups/media files",
        ],
    }
    (STATE / "_STATE_INFO.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = [
        "CHATGPT LIGHT STATE SNAPSHOT",
        "=" * 80,
        f"Time: {info['created_at']}",
        f"Project dir: {info['project_dir']}",
        f"Git HEAD: {info['git_head_short']}",
        f"State files: {info['state_files_count']}",
        f"State size: {info['state_total_mb']} MB",
        "",
        "NO BACKUP CREATED.",
        "Heavy folders intentionally skipped: static/images, full public assets, data/playerdb, backups, zips.",
        "",
        "Git status before commit:",
        status or "clean / no output",
        "",
        "Copied source files:",
        *copied,
    ]
    (REPORTS / "_LIGHT_STATE_PUSH_INFO.txt").write_text("\n".join(summary), encoding="utf-8")


def main() -> int:
    if not (ROOT / ".git").exists():
        print("ERROR: This script must be inside the Git project root: C:\\Users\\Dmitrii\\Promyachik")
        return 1

    if STATE.exists():
        shutil.rmtree(STATE)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DIAG.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    copy_file(ROOT / "hugo.toml", STATE / "hugo.toml", copied)
    copy_file(ROOT / ".gitignore", STATE / ".gitignore", copied)

    copy_tree_text(ROOT / "layouts", STATE / "layouts", copied)
    copy_tree_text(ROOT / "content" / "transfers", STATE / "content" / "transfers", copied, include_suffixes={".md", ".html", ".toml", ".yaml", ".yml", ".json"})
    copy_tree_text(ROOT / "static" / "css", STATE / "static" / "css", copied, include_suffixes={".css"})
    copy_tree_text(ROOT / "static" / "js", STATE / "static" / "js", copied, include_suffixes={".js"})

    # Light data only. The player database is large and is skipped.
    for data_sub in ["transfers", "clubs", "chart", "market", "players"]:
        copy_tree_text(ROOT / "data" / data_sub, STATE / "data" / data_sub, copied, include_suffixes={".json", ".toml", ".yaml", ".yml", ".csv", ".txt"})

    copy_public_transfer_html(copied)
    copy_latest_reports(copied)
    write_state_info(copied)

    print("DONE")
    print("LIGHT CHATGPT STATE CREATED")
    print(f"STATE: {STATE}")
    print("NO BACKUP CREATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
