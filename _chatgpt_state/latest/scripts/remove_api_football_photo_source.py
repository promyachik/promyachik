from pathlib import Path
from datetime import datetime
import shutil
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "layouts" / "transfers" / "single.html"
BACKUP_DIR = ROOT / "var" / "backups"

MARKER = "player-brief__photo-source"
START_MARKER = "{{ with $playerImageSourceName }}"

def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1

def count_with(line: str) -> int:
    # Count Go template "with" openings on this line.
    return len(re.findall(r"{{\s*with\b", line))

def count_end(line: str) -> int:
    # Count Go template end closings on this line.
    return len(re.findall(r"{{\s*end\s*}}", line))

def main() -> int:
    if not TARGET.exists():
        return fail(f"File not found: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    if MARKER not in text:
        print("No player photo source block found. It looks already removed.")
        return 0

    lines = text.splitlines(keepends=True)

    marker_index = None
    for i, line in enumerate(lines):
        if MARKER in line:
            marker_index = i
            break

    if marker_index is None:
        print("No player photo source block found. It looks already removed.")
        return 0

    start_index = None
    for i in range(marker_index, -1, -1):
        if START_MARKER in lines[i]:
            start_index = i
            break

    if start_index is None:
        return fail("Could not find the start of the player photo source block. File was not changed.")

    depth = 0
    end_index_exclusive = None

    for i in range(start_index, len(lines)):
        line = lines[i]
        depth += count_with(line)
        depth -= count_end(line)
        if depth == 0 and i > start_index:
            end_index_exclusive = i + 1
            break

    if end_index_exclusive is None:
        return fail("Could not find the end of the player photo source block. File was not changed.")

    block = "".join(lines[start_index:end_index_exclusive])
    if MARKER not in block:
        return fail("Safety check failed: selected block does not contain player photo source marker. File was not changed.")

    # Save backup before writing.
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"single.html.before_remove_api_football_photo_source_{stamp}.bak"
    shutil.copy2(TARGET, backup_path)

    new_lines = lines[:start_index] + lines[end_index_exclusive:]
    new_text = "".join(new_lines)

    # Normalize excessive blank lines caused by removal, without touching other code.
    new_text = re.sub(r"\n{4,}", "\n\n\n", new_text)

    TARGET.write_text(new_text, encoding="utf-8")

    print(f"Updated: {TARGET}")
    print(f"Backup:  {backup_path}")
    print("Removed only the visible player photo source block under player images.")
    print("Player images and content front matter were not changed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
