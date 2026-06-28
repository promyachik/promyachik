from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons-v184" / "matches.png"
DST_DIR = ROOT / "static" / "images" / "stats-icons-v184"
DST = DST_DIR / "matches.png"
BACKUP_DIR = ROOT / "_backup_185_fix_matches_field_icon"
REPORT = ROOT / "_185_fix_matches_field_icon_report.txt"

DST_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if DST.exists():
    shutil.copy2(DST, BACKUP_DIR / f"matches_before_185_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

shutil.copy2(SRC, DST)
REPORT.write_text(
    "185_FIX_MATCHES_FIELD_ICON_FULL\n"
    "Changed only: static/images/stats-icons-v184/matches.png\n"
    "Purpose: replace cropped match icon with a complete football pitch icon on transparent canvas.\n",
    encoding="utf-8"
)
print("DONE: 185 full matches field icon copied")
