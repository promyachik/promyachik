from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons-v184" / "goals.png"
DST_DIR = ROOT / "static" / "images" / "stats-icons-v184"
DST = DST_DIR / "goals.png"
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-stats.html"
BACKUP_DIR = ROOT / "_backup_189_fix_goals_icon_full_right_padding"
REPORT = ROOT / "_189_fix_goals_icon_full_right_padding_report.txt"

DST_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

if DST.exists():
    shutil.copy2(DST, BACKUP_DIR / f"goals_before_189_{stamp}.png")

shutil.copy2(SRC, DST)

partial_changed = False
if PARTIAL.exists():
    old = PARTIAL.read_text(encoding="utf-8")
    (BACKUP_DIR / f"transfer-player-stats_before_189_{stamp}.html").write_text(old, encoding="utf-8")

    # Cache-bust only the goals image. Keep everything else unchanged.
    new = re.sub(
        r'images/stats-icons-v184/goals\.png(?:\?v=\d+)?',
        'images/stats-icons-v184/goals.png?v=189',
        old
    )

    if new != old:
        PARTIAL.write_text(new, encoding="utf-8")
        partial_changed = True

REPORT.write_text(
    "189_FIX_GOALS_ICON_FULL_RIGHT_PADDING\n"
    "Changed: static/images/stats-icons-v184/goals.png\n"
    "Partial cache-bust updated: " + ("yes" if partial_changed else "no") + "\n"
    "Purpose: keep the approved goals icon, reduce the right-edge crop further, and force browser reload via ?v=189.\n",
    encoding="utf-8"
)

print("DONE: 189 approved goals icon with stronger right padding copied")
print("Partial cache-bust updated:", "yes" if partial_changed else "no")
