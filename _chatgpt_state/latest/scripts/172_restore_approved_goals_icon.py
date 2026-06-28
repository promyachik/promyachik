from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons" / "goals.png"
DST = ROOT / "static" / "images" / "stats-icons" / "goals.png"
BACKUP_DIR = ROOT / "_backup_172_restore_approved_goals_icon"
REPORT = ROOT / "_172_restore_approved_goals_icon_report.txt"


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
        shutil.copy2(DST, BACKUP_DIR / f"goals.before_v172_{ts}.png")

    shutil.copy2(SRC, DST)

    REPORT.write_text(
        "DONE_172_FULL_RESTORE_APPROVED_GOALS_ICON\n"
        f"replaced={DST.relative_to(ROOT)}\n"
        "changed_only=approved_goals_icon_png\n"
        "note=Restores approved goals icon design, only with safe transparent canvas/padding. No CSS/JS/layout changes.\n",
        encoding="utf-8",
    )
    print("DONE_172_FULL_RESTORE_APPROVED_GOALS_ICON")


if __name__ == "__main__":
    main()
