from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(os.environ.get("PROFUTBIK_PROJECT_ROOT", r"C:\\Users\\Dmitrii\\Promyachik"))
VERSION = "150_FULL_SAFE_AUTOSYNC_DE_LIGT_DYNAMIC_VALUE"

DE_LIGT_PAGE = PROJECT_ROOT / "content" / "transfers" / "matthijs-de-ligt" / "index.md"
TRANSFERS_FILE = PROJECT_ROOT / "data" / "transfers.json"
CLUB_LOGOS_FILE = PROJECT_ROOT / "data" / "club-logos.json"
TRANSFER_TEMPLATE = PROJECT_ROOT / "layouts" / "transfers" / "single.html"
PARTIAL_SOURCE = PACKAGE_ROOT / "layouts" / "partials" / "profutbik-market-chart-static.html"
PARTIAL_DEST = PROJECT_ROOT / "layouts" / "partials" / "profutbik-market-chart-static.html"
AJAX_LOGO = PROJECT_ROOT / "static" / "images" / "clubs" / "api" / "194.png"
FALLBACK_ABCOUDE = PROJECT_ROOT / "static" / "images" / "clubs" / "fallback" / "fc-abcoude.svg"
TRANSFERMARKT_MARKET_VALUE_URL = (
    "https://www.transfermarkt.com/matthijs-de-ligt/marktwertverlauf/spieler/326031"
)
TRANSFERMARKT_PROFILE_URL = (
    "https://www.transfermarkt.com/matthijs-de-ligt/profil/spieler/326031"
)

MARKET_VALUE_CHART_YAML = """market_value_chart:
  eyebrow: "ДИНАМИКА СТОИМОСТИ"
  title: "Matthijs de Ligt"
  subtitle: "Полная цепочка с молодёжными этапами Ajax, старшими клубами и текущей оценкой. Молодёжные команды Ajax используют основной логотип Ajax, а FC Abcoude получает буквенную заглушку."
  current_value: "€30m"
  source_name: "Transfermarkt"
  source_url: "https://www.transfermarkt.com/matthijs-de-ligt/marktwertverlauf/spieler/326031"
  note: "Оценочная стоимость, не сумма трансфера. Обновлено 03.06.2026."
  points:
    - date_label: "2005–2009"
      value_label: "—"
      value_number: 0
      club: "FC Abcoude"
      tooltip: "FC Abcoude"
      logo: "images/clubs/fallback/fc-abcoude.svg"
      fallback_letter: "A"
      type: "small_youth_club"
    - date_label: "2009–2014"
      value_label: "—"
      value_number: 0
      club: "Ajax Youth"
      tooltip: "Ajax Youth / академия Ajax"
      logo: "images/clubs/api/194.png"
      fallback_letter: "A"
      type: "parent_logo_youth_team"
    - date_label: "2014/15"
      value_label: "—"
      value_number: 0
      club: "Ajax U17"
      tooltip: "Ajax U17 / Аякс до 17"
      logo: "images/clubs/api/194.png"
      fallback_letter: "A"
      type: "parent_logo_youth_team"
    - date_label: "2015/16"
      value_label: "—"
      value_number: 0
      club: "Ajax U19"
      tooltip: "Ajax U19 / Аякс до 19"
      logo: "images/clubs/api/194.png"
      fallback_letter: "A"
      type: "parent_logo_youth_team"
    - date_label: "2016/17"
      value_label: "€0.1m"
      value_number: 0.1
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
"""

FRONTMATTER_UPDATES = {
    "player": "Matthijs de Ligt",
    "player_initials": "MDL",
    "player_id": "532",
    "player_slug": "matthijs-de-ligt",
    "position": "Центральный защитник",
    "birth_date": "12.08.1999",
    "nationality": "Нидерланды",
    "preferred_foot": "Правая",
    "market_value": "30 млн евро",
    "market_value_url": "/players/matthijs-de-ligt/#market-value",
    "from_club_id": "157",
    "from_club_name": "Bayern Munich",
    "to_club_id": "33",
    "to_club_name": "Manchester United",
    "status": "official",
    "fee": "€45.00m",
    "source_name": "Transfermarkt",
    "source_url": TRANSFERMARKT_MARKET_VALUE_URL,
    "source_date": "03.06.2026",
    "player_url": "/players/matthijs-de-ligt/",
}

DEFAULT_PAGE_BODY = """
## Matthijs de Ligt — переход в Manchester United

Matthijs de Ligt перешёл из Bayern Munich в Manchester United. На странице используется обновлённая динамика рыночной стоимости: от ранних клубов и молодёжных команд Ajax до Juventus, Bayern и Manchester United.

## История стоимости

Блок динамики показывает оценочную рыночную стоимость игрока, а не сумму трансфера. Для молодёжных команд Ajax используется основной логотип Ajax, а для FC Abcoude используется буквенная заглушка.
""".lstrip()


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def backup(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    relative = path.relative_to(PROJECT_ROOT)
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    print(f"BACKUP: {relative} -> {target.relative_to(PROJECT_ROOT)}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path):
    return json.loads(read_text(path))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download_ajax_logo() -> None:
    AJAX_LOGO.parent.mkdir(parents=True, exist_ok=True)

    if AJAX_LOGO.exists() and AJAX_LOGO.stat().st_size > 100:
        print("OK: Ajax logo already exists")
        return

    url = "https://media.api-sports.io/football/teams/194.png"
    request = Request(url, headers={"User-Agent": "ProFutbik/1.0"})

    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()

    except (HTTPError, URLError, TimeoutError) as error:
        print(f"WARNING: Ajax logo download failed: {error}")
        print("WARNING: chart will use Ajax fallback letter until API logo is loaded.")
        return

    if len(payload) < 100:
        print("WARNING: Ajax logo response is too small; skipped.")
        return

    AJAX_LOGO.write_bytes(payload)
    print("OK: Ajax logo saved to static/images/clubs/api/194.png")


def create_abcoude_fallback() -> None:
    FALLBACK_ABCOUDE.parent.mkdir(parents=True, exist_ok=True)
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="FC Abcoude">
  <circle cx="48" cy="48" r="45" fill="#08090d" stroke="#e3bf58" stroke-width="4"/>
  <circle cx="48" cy="48" r="34" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="2"/>
  <text x="48" y="59" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="900" fill="#f2d26d">A</text>
</svg>
"""
    write_text(FALLBACK_ABCOUDE, svg)
    print("OK: FC Abcoude fallback logo saved")


def update_club_logos(backup_root: Path) -> None:
    if not CLUB_LOGOS_FILE.exists():
        print("WARNING: data/club-logos.json not found; skipped.")
        return

    backup(CLUB_LOGOS_FILE, backup_root)
    data = load_json(CLUB_LOGOS_FILE)

    leagues = data.setdefault("leagues", {})
    leagues.setdefault(
        "88",
        {
            "id": 88,
            "name": "Eredivisie",
            "country": "Netherlands",
            "season": 2024,
            "teams_count": None,
            "note": "Added for De Ligt history; full Eredivisie import should be loaded through API-Football later.",
        },
    )

    clubs = data.setdefault("clubs", {})
    clubs["194"] = {
        "id": 194,
        "name": "Ajax",
        "configured_name": "Ajax",
        "code": "AJA",
        "country": "Netherlands",
        "league_id": 88,
        "league": "Eredivisie",
        "season": 2024,
        "founded": 1900,
        "national": False,
        "logo": "images/clubs/api/194.png",
        "api_logo": "https://media.api-sports.io/football/teams/194.png",
        "youth_logo_rule": "Ajax Youth / Ajax U17 / Ajax U19 / Ajax U21 use the main Ajax logo; tooltip keeps the exact youth team name.",
    }

    save_json(CLUB_LOGOS_FILE, data)
    print("OK: data/club-logos.json updated with Eredivisie/Ajax")


def update_transfers_json(backup_root: Path) -> None:
    if not TRANSFERS_FILE.exists():
        print("WARNING: data/transfers.json not found; skipped.")
        return

    backup(TRANSFERS_FILE, backup_root)
    data = load_json(TRANSFERS_FILE)
    if not isinstance(data, list):
        fail("data/transfers.json must be a list")

    updated = False
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("player") == "Matthijs de Ligt":
            item.update(
                {
                    "status": "official",
                    "from_club_id": 157,
                    "from_club_name": "Bayern Munich",
                    "to_club_id": 33,
                    "to_club_name": "Manchester United",
                    "fee": "€45.00m",
                    "url": "transfers/matthijs-de-ligt/",
                    "market_value": "€30m",
                    "market_value_updated": "2026-06-03",
                    "market_value_source_name": "Transfermarkt",
                    "market_value_source_url": TRANSFERMARKT_MARKET_VALUE_URL,
                }
            )
            updated = True
            break

    if not updated:
        data.append(
            {
                "status": "official",
                "player": "Matthijs de Ligt",
                "from_club_id": 157,
                "from_club_name": "Bayern Munich",
                "to_club_id": 33,
                "to_club_name": "Manchester United",
                "fee": "€45.00m",
                "url": "transfers/matthijs-de-ligt/",
                "player_image": "images/players/api/532.png",
                "player_id": 532,
                "player_image_source_name": "API-Football",
                "player_image_source_url": "https://media.api-sports.io/football/players/532.png",
                "market_value": "€30m",
                "market_value_updated": "2026-06-03",
                "market_value_source_name": "Transfermarkt",
                "market_value_source_url": TRANSFERMARKT_MARKET_VALUE_URL,
            }
        )

    save_json(TRANSFERS_FILE, data)
    print("OK: data/transfers.json updated for De Ligt")


def split_front_matter(content: str) -> tuple[str, str]:
    if not content.startswith("---\n"):
        return "", content
    marker = content.find("\n---", 4)
    if marker == -1:
        return "", content
    fm = content[4:marker]
    body = content[marker + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    return fm, body


def quote_yaml(value: str) -> str:
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def remove_yaml_block(fm: str, key: str) -> str:
    pattern = re.compile(
        rf"^({re.escape(key)}:\n(?:^[ \t].*\n|^\s*$\n?)*)",
        flags=re.MULTILINE,
    )
    return pattern.sub("", fm)


def set_scalar(fm: str, key: str, value: str) -> str:
    replacement = f"{key}: {quote_yaml(value)}"
    pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", flags=re.MULTILINE)
    if pattern.search(fm):
        return pattern.sub(replacement, fm, count=1)
    if fm.strip():
        return fm.rstrip() + "\n" + replacement + "\n"
    return replacement + "\n"


def clean_wrong_value_history(body: str) -> str:
    body = re.sub(
        r"\n*<section[^>]+class=\"[^\"]*transfer-value-history[^\"]*\"[\s\S]*?</section>\s*",
        "\n\n",
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def update_de_ligt_page(backup_root: Path) -> None:
    backup(DE_LIGT_PAGE, backup_root)

    if DE_LIGT_PAGE.exists():
        original = read_text(DE_LIGT_PAGE)
        fm, body = split_front_matter(original)
    else:
        fm, body = "", DEFAULT_PAGE_BODY

    for key in ("market_value_chart", "transfer_value_history", "value_history"):
        fm = remove_yaml_block(fm, key)

    for key, value in FRONTMATTER_UPDATES.items():
        fm = set_scalar(fm, key, value)

    fm = fm.rstrip() + "\n\n" + MARKET_VALUE_CHART_YAML.rstrip() + "\n"
    body = clean_wrong_value_history(body or DEFAULT_PAGE_BODY)

    if "## История стоимости" not in body:
        body = body.rstrip() + "\n\n## История стоимости\n\nБлок динамики показывает оценочную рыночную стоимость игрока, а не сумму трансфера.\n"

    write_text(DE_LIGT_PAGE, f"---\n{fm}---\n\n{body}")
    print("OK: De Ligt page front matter updated")


def patch_transfer_template(backup_root: Path) -> None:
    if not TRANSFER_TEMPLATE.exists():
        print("WARNING: layouts/transfers/single.html not found; skipped template patch.")
        return

    content = read_text(TRANSFER_TEMPLATE)
    marker = '{{ partial "profutbik-market-chart-static.html" . }}'
    if marker in content:
        print("OK: transfer template already contains market chart partial")
        return

    backup(TRANSFER_TEMPLATE, backup_root)

    insert = """

                {{ if .Params.market_value_chart }}
                    {{ partial "profutbik-market-chart-static.html" . }}
                {{ end }}
"""

    candidates = [
        "\n            </section>\n\n</aside>",
        "\n            </section>\n\n        </aside>",
    ]

    patched = None
    for candidate in candidates:
        if candidate in content:
            patched = content.replace(candidate, insert + candidate, 1)
            break

    if patched is None:
        # Safe fallback: place chart before previous_club_stats block if the exact player-brief closing area changed.
        fallback = "\n    {{ with .Params.previous_club_stats }}"
        if fallback not in content:
            fail("Cannot find a safe insertion point for market chart partial in layouts/transfers/single.html")
        patched = content.replace(fallback, "\n    {{ if .Params.market_value_chart }}\n        {{ partial \"profutbik-market-chart-static.html\" . }}\n    {{ end }}\n" + fallback, 1)

    write_text(TRANSFER_TEMPLATE, patched)
    print("OK: layouts/transfers/single.html patched with market chart partial")


def validate_and_copy_partial(backup_root: Path) -> None:
    if not PARTIAL_SOURCE.exists():
        fail("Package file layouts/partials/profutbik-market-chart-static.html is missing")

    if PARTIAL_DEST.exists():
        try:
            same = PARTIAL_DEST.read_bytes() == PARTIAL_SOURCE.read_bytes()
        except OSError:
            same = False
        if same:
            print("OK: market chart partial already up to date")
        else:
            backup(PARTIAL_DEST, backup_root)
            shutil.copy2(PARTIAL_SOURCE, PARTIAL_DEST)
            print("OK: market chart partial replaced in project")
    else:
        PARTIAL_DEST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PARTIAL_SOURCE, PARTIAL_DEST)
        print("OK: market chart partial copied to project")


def main() -> None:
    if not (PROJECT_ROOT / "hugo.toml").exists():
        fail(f"Hugo project not found at {PROJECT_ROOT}. Check PROFUTBIK_PROJECT_ROOT in the BAT file.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = PROJECT_ROOT / "backups" / f"{VERSION}_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    print(f"PACKAGE: {PACKAGE_ROOT}")
    print(f"PROJECT: {PROJECT_ROOT}")
    print(f"BACKUP: {backup_root.relative_to(PROJECT_ROOT)}")

    validate_and_copy_partial(backup_root)
    download_ajax_logo()
    create_abcoude_fallback()
    update_club_logos(backup_root)
    update_transfers_json(backup_root)
    update_de_ligt_page(backup_root)
    patch_transfer_template(backup_root)

    print("OK: De Ligt dynamic market value chart updated.")
    print("OK: Ticker, Ramos, Endrick, favicon, and old graph JS/CSS were not edited by this script.")
if __name__ == "__main__":
    main()
