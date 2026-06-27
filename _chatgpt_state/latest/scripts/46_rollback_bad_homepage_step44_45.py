from __future__ import annotations

import datetime as dt
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "layouts" / "index.html"
PARTIAL = ROOT / "layouts" / "partials" / "homepage-desktop-hero.html"
CSS = ROOT / "static" / "css" / "homepage-desktop-step1.css"
BACKUPS = ROOT / "var" / "backups"

if not INDEX.exists():
    raise SystemExit(f"ERROR: missing file: {INDEX}")

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
rollback_backup = BACKUPS / f"homepage_step_46_rollback_bad_hero_{stamp}"
rollback_backup.mkdir(parents=True, exist_ok=True)

# Always preserve current broken state before changing anything.
shutil.copy2(INDEX, rollback_backup / "current_layouts_index_before_rollback.html")
if PARTIAL.exists():
    shutil.copy2(PARTIAL, rollback_backup / "current_homepage-desktop-hero.html")
if CSS.exists():
    shutil.copy2(CSS, rollback_backup / "current_homepage-desktop-step1.css")

# Prefer the backup created by step 44, because it was made before the first bad homepage block was inserted.
step44_candidates = sorted(BACKUPS.glob("homepage_step_44_*/layouts_index.html"))
restored_from = None

if step44_candidates:
    restored_from = step44_candidates[-1]
    restored = restored_from.read_text(encoding="utf-8")
else:
    # Fallback: remove only the blocks inserted by step 44/45 from the current index.
    restored = INDEX.read_text(encoding="utf-8")

# Safety cleanup: remove any inserted homepage step blocks if they exist in the restored file.
for start, end in [
    ("<!-- PROFUTBIK_HOMEPAGE_STEP44_START -->", "<!-- PROFUTBIK_HOMEPAGE_STEP44_END -->"),
    ("<!-- PROFUTBIK_HOMEPAGE_STEP45_START -->", "<!-- PROFUTBIK_HOMEPAGE_STEP45_END -->"),
]:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\s*", re.DOTALL)
    restored = pattern.sub("", restored)

INDEX.write_text(restored, encoding="utf-8")

# Remove the wrong partial/CSS from active paths. Copies already saved above.
for path in [PARTIAL, CSS]:
    if path.exists():
        path.unlink()

print("DONE")
print("BAD HOMEPAGE STEP 44/45 ROLLED BACK")
if restored_from:
    print(f"Restored index from: {restored_from}")
else:
    print("No step 44 backup found; removed step 44/45 markers from current index instead.")
print(f"Current broken files saved to: {rollback_backup}")
print("Removed active wrong files:")
print(f"- {PARTIAL}")
print(f"- {CSS}")
