from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "payload" / "stats-icons-v184" / "goals.png"
DST_DIR = ROOT / "static" / "images" / "stats-icons-v184"
DST = DST_DIR / "goals.png"
PARTIAL = ROOT / "layouts" / "partials" / "transfer-player-stats.html"
BACKUP_DIR = ROOT / "_backup_188_fix_approved_goals_icon_right_edge"
REPORT = ROOT / "_188_fix_approved_goals_icon_right_edge_report.txt"

DST_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if DST.exists():
    shutil.copy2(DST, BACKUP_DIR / f"goals_before_188_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

shutil.copy2(SRC, DST)

partial_changed = False
if PARTIAL.exists():
    html = PARTIAL.read_text(encoding="utf-8")
    shutil.copy2(PARTIAL, BACKUP_DIR / f"transfer-player-stats_before_188_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    # Add/update a cache-busting query only for the goals icon so the browser cannot keep the old cropped image.
    html2 = html.replace('{{ "images/stats-icons-v184/goals.png" | relURL }}?v=187', '{{ "images/stats-icons-v184/goals.png" | relURL }}?v=188')
    html2 = html2.replace('{{ "images/stats-icons-v184/goals.png" | relURL }}?v=186', '{{ "images/stats-icons-v184/goals.png" | relURL }}?v=188')
    html2 = html2.replace('{{ "images/stats-icons-v184/goals.png" | relURL }}', '{{ "images/stats-icons-v184/goals.png" | relURL }}?v=188')
    if html2 != html:
        PARTIAL.write_text(html2, encoding="utf-8")
        partial_changed = True

REPORT.write_text(
    "188_FIX_APPROVED_GOALS_ICON_RIGHT_EDGE\n"
    "Changed: static/images/stats-icons-v184/goals.png\n"
    "Optional partial cache-bust changed: " + str(partial_changed) + "\n"
    "Purpose: keep the approved ball design but give the right edge visible breathing room and force browser refresh.\n",
    encoding="utf-8"
)
print("DONE: 188 approved goals icon right edge fixed")
print("PARTIAL_CACHE_BUST_CHANGED:", partial_changed)
