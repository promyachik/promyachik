from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import shutil
import sys

VERSION = "153_FULL_ROLLBACK_152_RESTORE_MARKET_CHART"
PROJECT = Path(os.environ.get("PROFUTBIK_PROJECT_ROOT", r"C:\Users\Dmitrii\Promyachik"))
if not PROJECT.exists():
    PROJECT = Path(__file__).resolve().parents[1]

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
SAFETY_BACKUP = PROJECT / f"_backup_153_before_rollback_152_{TS}"
REPORT = PROJECT / f"_153_rollback_152_restore_market_chart_report_{TS}.txt"

RESTORE_FILES = [
    Path("layouts/transfers/single.html"),
    Path("layouts/partials/profutbik-market-chart-static.html"),
    Path("content/transfers/matthijs-de-ligt/index.md"),
    Path("data/transfers.json"),
]

BACKUP_PATTERNS = [
    "_backup_152_restore_approved_market_chart_last5_*",
    "backups/152_FULL_RESTORE_APPROVED_MARKET_CHART_LAST5_*",
    "backups/152_full_restore_approved_market_chart_last5_*",
]


def log(lines: list[str], msg: str) -> None:
    print(msg)
    lines.append(msg)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def safe_backup_current(rel: Path, lines: list[str]) -> None:
    src = PROJECT / rel
    if src.exists():
        dst = SAFETY_BACKUP / rel
        copy_file(src, dst)
        log(lines, f"SAFETY_BACKUP {rel.as_posix()}")


def find_backup_dirs(lines: list[str]) -> list[Path]:
    dirs: list[Path] = []
    for pattern in BACKUP_PATTERNS:
        dirs.extend([p for p in PROJECT.glob(pattern) if p.is_dir()])
    unique = sorted(set(dirs), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in unique[:10]:
        log(lines, f"CANDIDATE_BACKUP {p.relative_to(PROJECT)}")
    return unique


def has_restore_files(root: Path) -> bool:
    return any((root / rel).exists() for rel in RESTORE_FILES)


def restore_from_backup(root: Path, lines: list[str]) -> int:
    restored = 0
    for rel in RESTORE_FILES:
        src = root / rel
        dst = PROJECT / rel
        if not src.exists():
            log(lines, f"SKIP_NOT_IN_BACKUP {rel.as_posix()}")
            continue
        safe_backup_current(rel, lines)
        copy_file(src, dst)
        log(lines, f"RESTORED {rel.as_posix()} FROM {root.relative_to(PROJECT)}")
        restored += 1
    return restored


def main() -> int:
    lines: list[str] = []
    log(lines, f"VERSION {VERSION}")
    log(lines, f"PROJECT {PROJECT}")
    if not PROJECT.exists():
        log(lines, "ERROR_PROJECT_NOT_FOUND")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    backups = [p for p in find_backup_dirs(lines) if has_restore_files(p)]
    if not backups:
        log(lines, "ERROR_NO_152_BACKUP_FOUND")
        log(lines, "ACTION_REQUIRED_FIND_BACKUP_152_OR_SEND_FILES")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"REPORT {REPORT}")
        return 1

    selected = backups[0]
    log(lines, f"SELECTED_BACKUP {selected.relative_to(PROJECT)}")
    restored = restore_from_backup(selected, lines)

    if restored == 0:
        log(lines, "ERROR_NOTHING_RESTORED")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"REPORT {REPORT}")
        return 1

    log(lines, f"RESTORED_COUNT {restored}")
    log(lines, "RESULT_ROLLBACK_152_DONE")
    log(lines, "NEXT_CHECK_MARKET_CHART_VISIBLE_BEFORE_ANY_NEW_PATCH")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"REPORT {REPORT}")
    print("DONE_153_FULL_ROLLBACK_152_RESTORE_MARKET_CHART")
    return 0


if __name__ == "__main__":
    sys.exit(main())
