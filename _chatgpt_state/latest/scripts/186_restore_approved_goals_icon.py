from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons-v184" / "goals.png"
DST_DIR = ROOT / "static" / "images" / "stats-icons-v184"
DST = DST_DIR / "goals.png"
BACKUP_DIR = ROOT / "_backup_186_restore_approved_goals_icon"
REPORT = ROOT / "_186_restore_approved_goals_icon_report.txt"

DST_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if DST.exists():
    shutil.copy2(DST, BACKUP_DIR / f"goals_before_186_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

shutil.copy2(SRC, DST)
REPORT.write_text(
    "186_RESTORE_APPROVED_GOALS_ICON\n"
    "Changed only: static/images/stats-icons-v184/goals.png\n"
    "Purpose: restore the previously approved goals icon in the stats block.\n",
    encoding="utf-8"
)
print("DONE: 186 approved goals icon copied")
