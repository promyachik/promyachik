from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re
import shutil
import sys

VERSION = "152_FULL_RESTORE_APPROVED_MARKET_CHART_LAST5"
PROJECT = Path(os.environ.get("PROFUTBIK_PROJECT_ROOT", r"C:\Users\Dmitrii\Promyachik"))
if not PROJECT.exists():
    PROJECT = Path(__file__).resolve().parents[1]

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_152_restore_approved_market_chart_last5_{TIMESTAMP}"
REPORT = PROJECT / f"_152_restore_approved_market_chart_last5_report_{TIMESTAMP}.txt"

MARKER_START = "<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_START -->"
MARKER_END = "<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_END -->"

DE_LIGT_PAGE = PROJECT / "content" / "transfers" / "matthijs-de-ligt" / "index.md"
TRANSFERS_JSON = PROJECT / "data" / "transfers.json"

BAD_LAYOUT_FILES = [
    PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html",
    PROJECT / "layouts" / "transfers" / "single.html",
]

REFERENCE_SLUGS = [
    "marc-cucurella",
    "cucurella",
    "bernardo-silva",
    "denzel-dumfries",
    "dumfries",
]

DE_LIGT_MARKET_VALUE_CHART = '''market_value_chart:
  eyebrow: "ДИНАМИКА СТОИМОСТИ"
  title: "Matthijs de Ligt"
  subtitle: "Последние 5 команд в истории игрока. Молодёжная команда Ajax использует основной логотип Ajax, при наведении показывается точное название команды."
  current_value: "€30m"
  source_name: "Transfermarkt"
  source_url: "https://www.transfermarkt.com/matthijs-de-ligt/marktwertverlauf/spieler/326031"
  note: "Показаны только последние 5 команд. Полная ранняя история может храниться в данных, но не перегружает график."
  points:
    - date_label: "2016/17"
      value_label: "—"
      value_number: 0
      club: "Ajax U21"
      tooltip: "Ajax U21 / Аякс до 21"
      logo: "images/clubs/api/194.png"
      fallback_letter: "A"
      type: "parent_logo_youth_team"
    - date_label: "18.07.2019"
      value_label: "€75m"
      value_number: 75
      club: "Ajax"
      tooltip: "Ajax"
      logo: "images/clubs/api/194.png"
      fallback_letter: "A"
      type: "senior_club"
    - date_label: "19.07.2022"
      value_label: "€70m"
      value_number: 70
      club: "Juventus"
      tooltip: "Juventus"
      logo: "images/clubs/api/496.png"
      fallback_letter: "J"
      type: "senior_club"
    - date_label: "13.08.2024"
      value_label: "€65m"
      value_number: 65
      club: "Bayern"
      tooltip: "Bayern Munich"
      logo: "images/clubs/api/157.png"
      fallback_letter: "B"
      type: "senior_club"
    - date_label: "03.06.2026"
      value_label: "€30m"
      value_number: 30
      club: "Man United"
      tooltip: "Manchester United"
      logo: "images/clubs/api/33.png"
      fallback_letter: "M"
      type: "senior_club"
'''

FRONTMATTER_PATCHES = {
    "player": "Matthijs de Ligt",
    "market_value": "30 млн евро",
    "source_name": "Transfermarkt",
    "source_url": "https://www.transfermarkt.com/matthijs-de-ligt/marktwertverlauf/spieler/326031",
    "source_date": "03.06.2026",
}


def log(lines: list[str], message: str) -> None:
    print(message)
    lines.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def backup_file(path: Path, lines: list[str]) -> None:
    if not path.exists():
        return
    try:
        rel = path.relative_to(PROJECT)
    except ValueError:
        rel = Path(path.name)
    dst = BACKUP_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    log(lines, f"BACKUP {rel}")


def remove_151_injection(path: Path, lines: list[str]) -> None:
    if not path.exists():
        return
    text = read_text(path)
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    if start == -1 or end == -1 or end <= start:
        return
    backup_file(path, lines)
    end += len(MARKER_END)
    new_text = text[:start].rstrip() + "\n" + text[end:].lstrip("\r\n")
    write_text(path, new_text)
    log(lines, f"REMOVED_151_INJECTION {path.relative_to(PROJECT)}")


def find_reference_pages(lines: list[str]) -> list[Path]:
    base = PROJECT / "content" / "transfers"
    found: list[Path] = []
    for slug in REFERENCE_SLUGS:
        candidates = [
            base / slug / "index.md",
            base / f"{slug}.md",
        ]
        for p in candidates:
            if p.exists() and p not in found:
                found.append(p)
    # Fallback broad search only inside transfer pages.
    for p in base.glob("**/index.md") if base.exists() else []:
        low = str(p).lower()
        if any(key in low for key in ["cucurella", "bernardo", "dumfries"]):
            if p not in found:
                found.append(p)
    for p in found:
        log(lines, f"REFERENCE_FOUND {p.relative_to(PROJECT)}")
    if not found:
        log(lines, "WARNING_REFERENCE_PAGES_NOT_FOUND")
    return found


def restore_approved_layouts(lines: list[str]) -> None:
    """Undo the custom De Ligt chart partial if an older approved backup exists.

    Priority is backup created before 148 applied its custom partial. If that does not
    exist, the script only removes the 151 runtime limiter and leaves current approved
    files alone.
    """
    backup_roots: list[Path] = []
    patterns = [
        "backups/148_FULL_AUTOSYNC_DE_LIGT_DYNAMIC_VALUE_*",
        "backups/150_FULL_SAFE_AUTOSYNC_DE_LIGT_DYNAMIC_VALUE_*",
        "_backup_148*",
        "_backup_150*",
    ]
    for pat in patterns:
        backup_roots.extend([p for p in PROJECT.glob(pat) if p.is_dir()])

    # Prefer 148 backups because they should contain the version before custom 148 partial.
    def rank(path: Path):
        s = str(path).lower()
        pri = 0 if "148_full_autosync" in s else 1
        return (pri, path.stat().st_mtime)

    backup_roots = sorted(set(backup_roots), key=rank)

    restored_any = False
    for file_path in BAD_LAYOUT_FILES:
        restored = False
        rel = file_path.relative_to(PROJECT)
        for root in backup_roots:
            source = root / rel
            if source.exists():
                current = read_text(file_path) if file_path.exists() else ""
                source_text = read_text(source)
                # Do not restore a backup that already contains the manual custom class.
                if "player-market-chart--manual" in source_text and "148" not in str(root):
                    continue
                if current != source_text:
                    backup_file(file_path, lines)
                    write_text(file_path, source_text)
                    log(lines, f"RESTORED_APPROVED_LAYOUT {rel} FROM {root.relative_to(PROJECT)}")
                else:
                    log(lines, f"LAYOUT_ALREADY_APPROVED {rel}")
                restored = True
                restored_any = True
                break
        if not restored:
            log(lines, f"NO_APPROVED_BACKUP_FOUND_FOR {rel}")
            remove_151_injection(file_path, lines)
    if not restored_any:
        log(lines, "NO_LAYOUT_RESTORE_DONE_ONLY_SAFE_CLEANUP")


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return "", text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def patch_simple_key(fm: str, key: str, value: str) -> str:
    value_q = '"' + value.replace('"', '\\"') + '"'
    pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", re.M)
    if pattern.search(fm):
        return pattern.sub(f"{key}: {value_q}", fm, count=1)
    return fm.rstrip() + f"\n{key}: {value_q}\n"


def replace_yaml_block(fm: str, key: str, block: str) -> str:
    lines = fm.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:\s*$", line):
            start = i
            break
    if start is None:
        return fm.rstrip() + "\n" + block.rstrip() + "\n"

    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if line.strip() == "":
            continue
        if not line.startswith((" ", "\t", "-")) and re.match(r"^[A-Za-z0-9_\-]+:\s*", line):
            end = j
            break
    new_lines = lines[:start] + block.rstrip().splitlines() + lines[end:]
    return "\n".join(new_lines).rstrip() + "\n"


def update_de_ligt_page(lines: list[str]) -> None:
    if not DE_LIGT_PAGE.exists():
        log(lines, "ERROR_DE_LIGT_PAGE_NOT_FOUND")
        return
    backup_file(DE_LIGT_PAGE, lines)
    text = read_text(DE_LIGT_PAGE)
    fm, body = split_frontmatter(text)
    if not fm:
        fm = "title: \"Matthijs de Ligt\"\n"
        body = text
    for key, value in FRONTMATTER_PATCHES.items():
        fm = patch_simple_key(fm, key, value)
    fm = replace_yaml_block(fm, "market_value_chart", DE_LIGT_MARKET_VALUE_CHART)
    write_text(DE_LIGT_PAGE, "---\n" + fm.strip() + "\n---\n\n" + body.lstrip())
    log(lines, "UPDATED_DE_LIGT_PAGE_LAST5_WITH_APPROVED_MARKET_CHART_PARAMS")


def update_transfers_json(lines: list[str]) -> None:
    if not TRANSFERS_JSON.exists():
        log(lines, "SKIP_TRANSFERS_JSON_NOT_FOUND")
        return
    import json
    try:
        data = json.loads(read_text(TRANSFERS_JSON))
    except Exception as exc:
        log(lines, f"SKIP_TRANSFERS_JSON_PARSE_ERROR {exc}")
        return
    backup_file(TRANSFERS_JSON, lines)

    changed = False
    def is_deligt(item: dict) -> bool:
        blob = " ".join(str(item.get(k, "")) for k in ["player", "player_name", "title", "slug", "url", "href"]).lower()
        return "de ligt" in blob or "matthijs-de-ligt" in blob

    items = data if isinstance(data, list) else data.get("transfers", []) if isinstance(data, dict) else []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and is_deligt(item):
                for key in ["url", "href", "link", "page_url"]:
                    if key in item:
                        item[key] = "transfers/matthijs-de-ligt/"
                if "url" not in item and "href" not in item and "link" not in item:
                    item["url"] = "transfers/matthijs-de-ligt/"
                for key in ["market_value", "value", "price"]:
                    if key in item:
                        item[key] = "€30m"
                changed = True

    if changed:
        TRANSFERS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log(lines, "UPDATED_TRANSFERS_JSON_DE_LIGT_LINK_VALUE")
    else:
        log(lines, "NO_DE_LIGT_ENTRY_FOUND_IN_TRANSFERS_JSON")


def main() -> int:
    lines: list[str] = []
    log(lines, f"VERSION {VERSION}")
    log(lines, f"PROJECT {PROJECT}")
    if not PROJECT.exists():
        log(lines, "ERROR_PROJECT_NOT_FOUND")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    find_reference_pages(lines)
    restore_approved_layouts(lines)
    update_de_ligt_page(lines)
    update_transfers_json(lines)

    log(lines, "RULE_APPROVED_BASE_CUCURELLA_BERNARDO_DUMFRIES")
    log(lines, "RULE_SHOW_ONLY_LAST_5_TEAMS_VISUALLY")
    log(lines, "DO_NOT_TOUCH_TICKERS_RAMOS_ENDRICK_FAVICON_VAR")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"REPORT {REPORT}")
    print("DONE_152_FULL_RESTORE_APPROVED_MARKET_CHART_LAST5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
