from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons" / "goals.png"
DST = ROOT / "static" / "images" / "stats-icons" / "goals.png"
BACKUP_DIR = ROOT / "_backup_171_fix_goals_icon_source"
REPORT = ROOT / "_171_fix_goals_icon_source_report.txt"


def fail(message: str) -> None:
    REPORT.write_text("FAILED\n" + message + "\n", encoding="utf-8")
    raise SystemExit(message)


def main() -> None:
    if not SRC.exists():
        fail(f"Missing payload: {SRC}")
    DST.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if DST.exists():
        shutil.copy2(DST, BACKUP_DIR / f"goals.before_v171_{ts}.png")
    shutil.copy2(SRC, DST)
    REPORT.write_text(
        "DONE_171_FULL_FIX_GOALS_ICON_SOURCE\n"
        f"replaced={DST.relative_to(ROOT)}\n"
        "changed_only=goals_icon_png\n"
        "note=No CSS/layout/JS changes. Current pushed state remains source of truth.\n",
        encoding="utf-8",
    )
    print("DONE_171_FULL_FIX_GOALS_ICON_SOURCE")


if __name__ == "__main__":
    main()
