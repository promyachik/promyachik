from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons-v184" / "goals.png"
DST_DIR = ROOT / "static" / "images" / "stats-icons-v184"
DST = DST_DIR / "goals.png"
BACKUP_DIR = ROOT / "_backup_187_fix_goals_icon_right_crop"
REPORT = ROOT / "_187_fix_goals_icon_right_crop_report.txt"

DST_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if DST.exists():
    shutil.copy2(DST, BACKUP_DIR / f"goals_before_187_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

shutil.copy2(SRC, DST)
REPORT.write_text(
    "187_FIX_GOALS_ICON_RIGHT_CROP
"
    "Changed only: static/images/stats-icons-v184/goals.png
"
    "Purpose: keep the approved ball icon but add safer right-side breathing room so it no longer looks cropped.
",
    encoding="utf-8"
)
print("DONE: 187 fixed goals icon copied")
