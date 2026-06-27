from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
PAYLOAD = PROJECT / "scripts" / "profutbik_enhancement_payload"

ACTIVE_JS = PROJECT / "static" / "js" / "transfer-player-market-value-chart.js"
ACTIVE_CSS = PROJECT / "static" / "css" / "transfer-player-market-value-chart.css"
TRANSFER_TEMPLATE = PROJECT / "layouts" / "transfers" / "single.html"
STATS_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-stats.html"
PLAYERS_FILE = PROJECT / "data" / "playerdb" / "players.json"
CONFIG_FILE = PROJECT / "data" / "playerdb" / "config.json"
CHART_LOGO_DIR = PROJECT / "static" / "images" / "clubs" / "chart"
EXTRA_CLUBS_FILE = PROJECT / "data" / "clubs" / "extra-clubs.json"

SPECS = [
  {
    "slug": "kylian-mbappe-real-madrid",
    "aliases": [
      "Kylian Mbappé",
      "Kylian Mbappe",
      "Килиан Мбаппе"
    ],
    "from_club_id": 85,
    "from_club_name": "Paris Saint-Germain",
    "season": 2023,
    "season_label": "2023/24"
  },
  {
    "slug": "florian-wirtz-liverpool",
    "aliases": [
      "Florian Wirtz",
      "Флориан Вирц"
    ],
    "from_club_id": 168,
    "from_club_name": "Bayer Leverkusen",
    "season": 2024,
    "season_label": "2024/25"
  },
  {
    "slug": "ibrahima-konate-real-madrid",
    "aliases": [
      "Ibrahima Konaté",
      "Ibrahima Konate",
      "Ибраима Конате"
    ],
    "from_club_id": 40,
    "from_club_name": "Liverpool",
    "season": 2025,
    "season_label": "2025/26"
  },
  {
    "slug": "marc-cucurella-real-madrid",
    "aliases": [
      "Marc Cucurella",
      "Марк Кукурелья"
    ],
    "from_club_id": 49,
    "from_club_name": "Chelsea",
    "season": 2025,
    "season_label": "2025/26"
  },
  {
    "slug": "denzel-dumfries-real-madrid",
    "aliases": [
      "Denzel Dumfries",
      "Дензел Дюмфрис"
    ],
    "from_club_id": 505,
    "from_club_name": "Inter",
    "season": 2025,
    "season_label": "2025/26"
  },
  {
    "slug": "julian-alvarez-barcelona",
    "aliases": [
      "Julián Álvarez",
      "Julian Alvarez",
      "Хулиан Альварес"
    ],
    "from_club_id": 530,
    "from_club_name": "Atlético Madrid",
    "season": 2025,
    "season_label": "2025/26"
  },
  {
    "slug": "elliot-anderson-manchester-city",
    "aliases": [
      "Elliot Anderson",
      "Эллиот Андерсон"
    ],
    "from_club_id": 65,
    "from_club_name": "Nottingham Forest",
    "season": 2025,
    "season_label": "2025/26"
  },
  {
    "slug": "bernardo-silva-real-madrid",
    "aliases": [
      "Bernardo Silva",
      "Бернарду Силва"
    ],
    "from_club_id": 50,
    "from_club_name": "Manchester City",
    "season": 2025,
    "season_label": "2025/26"
  }
]
CLUBS = {
  "monaco": {
    "name": "AS Monaco",
    "short": "ASM",
    "api_id": 91
  },
  "psg": {
    "name": "Paris Saint-Germain",
    "short": "PSG",
    "api_id": 85
  },
  "real-madrid": {
    "name": "Real Madrid",
    "short": "RMA",
    "api_id": 541
  },
  "bayer-leverkusen": {
    "name": "Bayer Leverkusen",
    "short": "B04",
    "api_id": 168
  },
  "liverpool": {
    "name": "Liverpool",
    "short": "LFC",
    "api_id": 40
  },
  "rb-leipzig": {
    "name": "RB Leipzig",
    "short": "RBL",
    "api_id": 173
  },
  "barcelona": {
    "name": "Barcelona",
    "short": "FCB",
    "api_id": 529
  },
  "getafe": {
    "name": "Getafe",
    "short": "GET",
    "api_id": 546
  },
  "brighton": {
    "name": "Brighton & Hove Albion",
    "short": "BHA",
    "api_id": 51
  },
  "sparta-rotterdam": {
    "name": "Sparta Rotterdam",
    "short": "SPA",
    "api_id": None
  },
  "heerenveen": {
    "name": "SC Heerenveen",
    "short": "HEE",
    "api_id": None
  },
  "psv": {
    "name": "PSV Eindhoven",
    "short": "PSV",
    "api_id": 197
  },
  "inter": {
    "name": "Inter",
    "short": "INT",
    "api_id": 505
  },
  "river-plate": {
    "name": "River Plate",
    "short": "CARP",
    "api_id": None
  },
  "manchester-city": {
    "name": "Manchester City",
    "short": "MCI",
    "api_id": 50
  },
  "atletico-madrid": {
    "name": "Atlético Madrid",
    "short": "ATM",
    "api_id": 530
  },
  "newcastle": {
    "name": "Newcastle United",
    "short": "NEW",
    "api_id": 34
  },
  "nottingham-forest": {
    "name": "Nottingham Forest",
    "short": "NFO",
    "api_id": 65
  }
}

PARTIAL_CALL = '{{ partial "transfer-player-stats.html" . }}'


def normalize(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(character)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def split_front_matter(text: str) -> tuple[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, flags=re.DOTALL)

    if not match:
        raise RuntimeError("No YAML front matter: " + str(text[:80]))

    return match.group(1), text[match.end():]


def replace_yaml_block(front: str, key: str, block: str) -> str:
    lines = front.splitlines()
    output: list[str] = []
    index = 0
    pattern = re.compile(rf"^{re.escape(key)}\s*:", flags=re.IGNORECASE)

    while index < len(lines):
        line = lines[index]

        if not pattern.match(line):
            output.append(line)
            index += 1
            continue

        index += 1

        while index < len(lines):
            next_line = lines[index]

            if (
                next_line
                and not next_line[0].isspace()
                and re.match(r"^[A-Za-z0-9_-]+\s*:", next_line)
            ):
                break

            index += 1

    output.append(block)
    return "\n".join(output)


def scalar(front: str, key: str) -> str | None:
    match = re.search(
        rf"(?mi)^{re.escape(key)}\s*:\s*[\"']?([^\n\"']+)",
        front,
    )
    return match.group(1).strip() if match else None


def stat_block(spec: dict[str, Any], values: dict[str, Any] | None) -> str:
    if values is None:
        values = {
            "matches": "—",
            "goals": "—",
            "assists": "—",
            "minutes": "—",
            "yellow_cards": "—",
            "red_cards": "—",
            "source_note": "Данные будут заполнены после синхронизации API-Football.",
        }

    def q(value: Any) -> str:
        return json.dumps(str(value), ensure_ascii=False)

    label = (
        f"{spec['from_club_name']} · сезон {spec['season_label']}"
    )

    return "\n".join([
        "previous_club_stats:",
        f"  label: {q(label)}",
        f"  matches: {q(values.get('matches', '—'))}",
        f"  goals: {q(values.get('goals', '—'))}",
        f"  assists: {q(values.get('assists', '—'))}",
        f"  minutes: {q(values.get('minutes', '—'))}",
        f"  yellow_cards: {q(values.get('yellow_cards', '—'))}",
        f"  red_cards: {q(values.get('red_cards', '—'))}",
        f"  season: {q(spec['season_label'])}",
        f"  source_note: {q(values.get('source_note', 'API-Football'))}",
    ])


def write_stats_to_page(spec: dict[str, Any], values: dict[str, Any] | None) -> Path:
    page = (
        PROJECT
        / "content"
        / "transfers"
        / spec["slug"]
        / "index.md"
    )

    if not page.exists():
        raise RuntimeError("Transfer page not found: " + str(page))

    text = read_text(page)
    front, body = split_front_matter(text)
    front = replace_yaml_block(
        front,
        "previous_club_stats",
        stat_block(spec, values),
    )

    page.write_text(
        "---\n" + front.strip() + "\n---\n\n" + body.lstrip("\n"),
        encoding="utf-8",
        newline="\n",
    )
    return page


def find_api_key() -> str | None:
    if not CONFIG_FILE.exists():
        return None

    data = json.loads(read_text(CONFIG_FILE))
    wanted = {
        "api_key",
        "api_football_key",
        "x_apisports_key",
        "apisports_key",
        "x_apisports_key",
    }

    def walk(value: Any) -> str | None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).casefold().replace("-", "_")

                if normalized in wanted and isinstance(child, str) and child.strip():
                    return child.strip()

            for child in value.values():
                found = walk(child)
                if found:
                    return found

        if isinstance(value, list):
            for child in value:
                found = walk(child)
                if found:
                    return found

        return None

    return walk(data)


def load_players() -> list[dict[str, Any]]:
    if not PLAYERS_FILE.exists():
        return []

    data = json.loads(read_text(PLAYERS_FILE))

    if isinstance(data, dict):
        items = data.get("items", [])
    else:
        items = data

    return [item for item in items if isinstance(item, dict)]


def resolve_player_id(spec: dict[str, Any], page: Path, players: list[dict[str, Any]]) -> int | None:
    front, _body = split_front_matter(read_text(page))
    direct = scalar(front, "player_id")

    if direct:
        try:
            return int(direct)
        except ValueError:
            pass

    aliases = {normalize(alias) for alias in spec["aliases"]}

    for player in players:
        names = {
            normalize(player.get("name")),
            normalize(
                f"{player.get('firstname') or ''} "
                f"{player.get('lastname') or ''}"
            ),
        }

        if aliases.intersection(names):
            try:
                return int(player["id"])
            except (KeyError, TypeError, ValueError):
                return None

    return None


def api_stats(
    api_key: str,
    player_id: int,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode({
        "id": player_id,
        "season": spec["season"],
    })
    url = "https://v3.football.api-sports.io/players?" + query
    request = urllib.request.Request(
        url,
        headers={
            "x-apisports-key": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print("  API warning:", error)
        return None

    if payload.get("errors"):
        print("  API returned errors:", payload.get("errors"))
        return None

    responses = payload.get("response") or []

    if not responses:
        return None

    entries = responses[0].get("statistics") or []
    selected = [
        entry
        for entry in entries
        if int((entry.get("team") or {}).get("id") or 0)
        == int(spec["from_club_id"])
    ]

    if not selected:
        return None

    totals = {
        "matches": 0,
        "goals": 0,
        "assists": 0,
        "minutes": 0,
        "yellow_cards": 0,
        "red_cards": 0,
    }

    for entry in selected:
        games = entry.get("games") or {}
        goals = entry.get("goals") or {}
        cards = entry.get("cards") or {}

        totals["matches"] += int(games.get("appearences") or 0)
        totals["minutes"] += int(games.get("minutes") or 0)
        totals["goals"] += int(goals.get("total") or 0)
        totals["assists"] += int(goals.get("assists") or 0)
        totals["yellow_cards"] += int(cards.get("yellow") or 0)
        totals["red_cards"] += (
            int(cards.get("red") or 0)
            + int(cards.get("yellowred") or 0)
        )

    totals["source_note"] = (
        "Источник статистики: API-Football. "
        "Сумма по доступным турнирам выбранного сезона."
    )
    return totals


def update_stats(best_effort: bool) -> list[Path]:
    changed: list[Path] = []
    players = load_players()
    api_key = find_api_key()

    if not api_key:
        print(
            "API-Football key was not found. "
            "Statistics cards will remain with placeholders."
        )

    for spec in SPECS:
        page = (
            PROJECT
            / "content"
            / "transfers"
            / spec["slug"]
            / "index.md"
        )

        values = None

        if api_key:
            player_id = resolve_player_id(spec, page, players)

            if player_id:
                print(
                    f"Loading statistics: {spec['slug']} "
                    f"(player {player_id}, season {spec['season']})"
                )
                values = api_stats(api_key, player_id, spec)
            else:
                print("  Player ID was not resolved.")

        changed.append(write_stats_to_page(spec, values))

        if values is None and not best_effort and api_key:
            raise RuntimeError(
                "Statistics were not received for " + spec["slug"]
            )

    return changed


def patch_transfer_template() -> None:
    text = read_text(TRANSFER_TEMPLATE)

    if PARTIAL_CALL in text:
        return

    start_marker = "{{ with .Params.previous_club_stats }}"
    end_marker = "{{ $bottomTransfers :="

    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))

    if start < 0 or end < 0:
        raise RuntimeError(
            "The old statistics block was not found "
            "inside layouts/transfers/single.html."
        )

    replacement = "    " + PARTIAL_CALL + "\n\n    "
    updated = text[:start] + replacement + text[end:]

    TRANSFER_TEMPLATE.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )


def copy_payload() -> None:
    mapping = [
        (
            PAYLOAD / "static" / "js" / "transfer-player-market-value-chart.js",
            ACTIVE_JS,
        ),
        (
            PAYLOAD / "static" / "css" / "transfer-player-market-value-chart.css",
            ACTIVE_CSS,
        ),
        (
            PAYLOAD / "layouts" / "partials" / "transfer-player-stats.html",
            STATS_PARTIAL,
        ),
        (
            PAYLOAD / "data" / "clubs" / "extra-clubs.json",
            EXTRA_CLUBS_FILE,
        ),
    ]

    for source, target in mapping:
        if not source.exists():
            raise RuntimeError("Payload file missing: " + str(source))

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    source_logos = PAYLOAD / "static" / "images" / "clubs" / "chart"
    CHART_LOGO_DIR.mkdir(parents=True, exist_ok=True)

    for source in source_logos.glob("*.svg"):
        shutil.copy2(source, CHART_LOGO_DIR / source.name)


def local_logo_candidates(api_id: int) -> list[Path]:
    roots = [
        PROJECT / "static" / "images" / "clubs",
        PROJECT / "static" / "images" / "teams",
    ]
    candidates: list[Path] = []

    for root in roots:
        if not root.exists():
            continue

        for extension in (".png", ".webp", ".jpg", ".jpeg", ".svg"):
            candidates.extend(root.rglob(f"{api_id}{extension}"))
            candidates.extend(root.rglob(f"*{api_id}*{extension}"))

    return [
        item
        for item in candidates
        if "chart" not in {part.casefold() for part in item.parts}
    ]


def prepare_logos() -> None:
    for slug, club in CLUBS.items():
        api_id = club.get("api_id")

        if not api_id:
            print("Fallback logo kept:", club["name"])
            continue

        existing = [
            path
            for extension in (".png", ".webp", ".jpg", ".jpeg", ".svg")
            if (path := CHART_LOGO_DIR / f"{slug}{extension}").exists()
            and extension != ".svg"
        ]

        if existing:
            continue

        candidates = local_logo_candidates(int(api_id))

        if candidates:
            source = candidates[0]
            target = CHART_LOGO_DIR / f"{slug}{source.suffix.lower()}"
            shutil.copy2(source, target)
            print("Local club logo copied:", club["name"])
            continue

        url = f"https://media.api-sports.io/football/teams/{api_id}.png"
        target = CHART_LOGO_DIR / f"{slug}.png"

        try:
            urllib.request.urlretrieve(url, target)
            print("Club logo downloaded:", club["name"])
        except Exception:
            if target.exists():
                target.unlink()
            print("Fallback logo kept:", club["name"])


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError("Hugo was not found in PATH.")

    with tempfile.TemporaryDirectory(
        prefix="profutbik_club_timeline_"
    ) as temporary:
        destination = Path(temporary)

        result = subprocess.run(
            [
                hugo,
                "--minify",
                "--destination",
                str(destination),
                "--baseURL",
                "http://127.0.0.1:1313/promyachik/",
            ],
            cwd=PROJECT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Hugo build failed with code " + str(result.returncode)
            )

        built_js = (
            destination
            / "js"
            / "transfer-player-market-value-chart.js"
        )

        if not built_js.exists():
            raise RuntimeError("Built chart JavaScript was not found.")

        js_text = read_text(built_js)

        required_js = [
            "26-club-timeline-modal",
            "player-market-chart__club-button",
            "club-logo-modal",
            "real-madrid",
            "sparta-rotterdam",
        ]

        forbidden_js = [
            "ДИНАМИКА СТОИМОСТИ",
            "player-market-chart__current",
            "player-market-chart__source",
            ">Transfermarkt<",
        ]

        missing = [item for item in required_js if item not in js_text]
        forbidden = [item for item in forbidden_js if item in js_text]

        if missing:
            raise RuntimeError(
                "Built JavaScript is missing: " + ", ".join(missing)
            )

        if forbidden:
            raise RuntimeError(
                "Removed chart elements are still present: "
                + ", ".join(forbidden)
            )

        for spec in SPECS:
            page = (
                destination
                / "transfers"
                / spec["slug"]
                / "index.html"
            )

            if not page.exists():
                raise RuntimeError("Built page missing: " + str(page))

            html = read_text(page)

            for marker in (
                "transfer-player-market-value-chart.js",
                "transfer-player-stats",
                "Матчи",
                "Голы",
                "Голевые передачи",
                "Минуты",
            ):
                if marker not in html:
                    raise RuntimeError(
                        spec["slug"] + " is missing: " + marker
                    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats-only", action="store_true")
    parser.add_argument("--strict-stats", action="store_true")
    args = parser.parse_args()

    if args.stats_only:
        try:
            update_stats(best_effort=not args.strict_stats)
            print()
            print("DONE")
            print("TRANSFER PLAYER STATISTICS UPDATED")
            return 0
        except Exception as error:
            print()
            print("ERROR:", error)
            return 1

    required = [
        PAYLOAD,
        TRANSFER_TEMPLATE,
    ]

    for path in required:
        if not path.exists():
            print("ERROR: required path not found:")
            print(path)
            return 1

    tracked = [
        ACTIVE_JS,
        ACTIVE_CSS,
        TRANSFER_TEMPLATE,
        STATS_PARTIAL,
        EXTRA_CLUBS_FILE,
    ]

    for spec in SPECS:
        tracked.append(
            PROJECT
            / "content"
            / "transfers"
            / spec["slug"]
            / "index.md"
        )

    originals: dict[Path, bytes | None] = {
        path: path.read_bytes() if path.exists() else None
        for path in tracked
    }

    try:
        print()
        print(
            "STEP 1 OF 5: installing club logos, "
            "click modal and clean chart..."
        )
        copy_payload()
        prepare_logos()

        print(
            "STEP 2 OF 5: connecting the unified "
            "statistics partial..."
        )
        patch_transfer_template()

        print(
            "STEP 3 OF 5: creating statistics blocks "
            "for all eight players..."
        )
        update_stats(best_effort=True)

        print(
            "STEP 4 OF 5: checking that the old "
            "chart heading and source button are gone..."
        )

        source_js = read_text(ACTIVE_JS)

        if "ДИНАМИКА СТОИМОСТИ" in source_js:
            raise RuntimeError(
                "Old chart heading is still present."
            )

        if "player-market-chart__source" in source_js:
            raise RuntimeError(
                "Old Transfermarkt button is still present."
            )

        print(
            "STEP 5 OF 5: building a clean temporary "
            "Hugo copy..."
        )
        validate_build()

        print()
        print("DONE")
        print("CLUB LOGOS ADDED ABOVE EVERY POINT")
        print("CLICK-TO-ENLARGE CLUB MODAL READY")
        print("STATISTICS BLOCK READY ON 8 PLAYER PAGES")
        print("CHART TITLE, CURRENT VALUE AND SOURCE BUTTON REMOVED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR:", error)
        print("Restoring all modified project files...")

        for path, content in originals.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("Previous project state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
