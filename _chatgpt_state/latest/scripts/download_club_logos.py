from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "club-logos.json"
)

LOGO_DIRECTORY = (
    PROJECT_ROOT
    / "static"
    / "images"
    / "clubs"
    / "api"
)

API_URL = "https://v3.football.api-sports.io/teams"

# Бесплатному тарифу сейчас доступен максимум сезон 2024.
SEASON = 2024

REQUEST_DELAY_SECONDS = 7
RATE_LIMIT_WAIT_SECONDS = 65
MAX_ATTEMPTS = 2


LEAGUES = [
    {
        "id": 39,
        "name": "Premier League",
        "country": "England",
    },
    {
        "id": 140,
        "name": "La Liga",
        "country": "Spain",
    },
    {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
    },
    {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
    },
    {
        "id": 61,
        "name": "Ligue 1",
        "country": "France",
    },
    {
        "id": 203,
        "name": "Süper Lig",
        "country": "Turkey",
    },
    {
        "id": 94,
        "name": "Primeira Liga",
        "country": "Portugal",
    },
    {
        "id": 235,
        "name": "Российская Премьер-Лига",
        "country": "Russia",
    },
]


EXTRA_TEAMS = [
    {
        "search": "Palmeiras",
        "expected_name": "Palmeiras",
        "country": "Brazil",
        "league": "Дополнительные клубы",
    },
]


def load_env() -> None:
    if not ENV_FILE.exists():
        print("ОШИБКА: файл .env не найден.")
        sys.exit(1)

    for raw_line in ENV_FILE.read_text(
        encoding="utf-8",
    ).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()
        value = value.strip('"')
        value = value.strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def load_existing_data() -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    if not OUTPUT_FILE.exists():
        return {}, {}

    try:
        data = json.loads(
            OUTPUT_FILE.read_text(
                encoding="utf-8",
            )
        )

    except json.JSONDecodeError as error:
        print(
            "ОШИБКА JSON в файле "
            "data/club-logos.json"
        )
        print(error)
        sys.exit(1)

    if not isinstance(data, dict):
        return {}, {}

    clubs = data.get(
        "clubs",
        {},
    )

    leagues = data.get(
        "leagues",
        {},
    )

    if not isinstance(clubs, dict):
        clubs = {}

    if not isinstance(leagues, dict):
        leagues = {}

    return clubs, leagues


def format_api_errors(
    errors: Any,
) -> str:
    if isinstance(errors, dict):
        return "; ".join(
            f"{key}: {value}"
            for key, value in errors.items()
        )

    if isinstance(errors, list):
        return "; ".join(
            str(item)
            for item in errors
        )

    return str(errors)


def api_request(
    api_key: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    query = urlencode(
        parameters
    )

    url = f"{API_URL}?{query}"

    request = Request(
        url,
        headers={
            "x-apisports-key": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="GET",
    )

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        try:
            with urlopen(
                request,
                timeout=30,
            ) as response:
                payload = json.load(
                    response
                )

        except HTTPError as error:
            body = error.read().decode(
                "utf-8",
                errors="replace",
            )

            if (
                error.code == 429
                and attempt < MAX_ATTEMPTS
            ):
                print(
                    "  Достигнут минутный лимит API."
                )
                print(
                    "  Ожидание "
                    f"{RATE_LIMIT_WAIT_SECONDS} секунд..."
                )

                time.sleep(
                    RATE_LIMIT_WAIT_SECONDS
                )
                continue

            raise RuntimeError(
                f"HTTP {error.code}: {body}"
            ) from error

        except URLError as error:
            raise RuntimeError(
                "Ошибка соединения: "
                f"{error.reason}"
            ) from error

        if not isinstance(
            payload,
            dict,
        ):
            raise RuntimeError(
                "API вернул неправильный формат."
            )

        errors = payload.get(
            "errors"
        )

        if errors:
            raise RuntimeError(
                "Ошибка API: "
                f"{format_api_errors(errors)}"
            )

        return payload

    raise RuntimeError(
        "Не удалось получить данные."
    )


def download_logo(
    logo_url: str,
    destination: Path,
) -> bool:
    if (
        destination.exists()
        and destination.stat().st_size >= 100
    ):
        return False

    request = Request(
        logo_url,
        headers={
            "User-Agent": "ProFutbik/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(
            request,
            timeout=30,
        ) as response:
            image_data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"логотип: HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "логотип: ошибка соединения: "
            f"{error.reason}"
        ) from error

    if len(image_data) < 100:
        raise RuntimeError(
            "получен пустой или повреждённый логотип"
        )

    temporary_file = destination.with_suffix(
        ".png.part"
    )

    temporary_file.write_bytes(
        image_data
    )

    temporary_file.replace(
        destination
    )

    return True


def save_team(
    clubs: dict[str, Any],
    item: dict[str, Any],
    league_id: int | None,
    league_name: str,
    league_country: str,
    season: int | None,
) -> str:
    team = item.get(
        "team",
        {},
    )

    venue = item.get(
        "venue",
        {},
    )

    if not isinstance(team, dict):
        raise RuntimeError(
            "неправильные данные команды"
        )

    if not isinstance(venue, dict):
        venue = {}

    team_id = team.get(
        "id"
    )

    if not isinstance(team_id, int):
        raise RuntimeError(
            "отсутствует ID команды"
        )

    team_name = str(
        team.get("name")
        or "Неизвестный клуб"
    ).strip()

    logo_url = str(
        team.get("logo")
        or ""
    ).strip()

    if not logo_url:
        raise RuntimeError(
            "API не вернул логотип"
        )

    logo_filename = f"{team_id}.png"

    logo_file = (
        LOGO_DIRECTORY
        / logo_filename
    )

    downloaded = download_logo(
        logo_url,
        logo_file,
    )

    existing = clubs.get(
        str(team_id),
        {},
    )

    if not isinstance(existing, dict):
        existing = {}

    configured_name = str(
        existing.get("configured_name")
        or team_name
    ).strip()

    clubs[str(team_id)] = {
        "id": team_id,
        "name": team_name,
        "configured_name": configured_name,
        "code": team.get("code"),
        "country": (
            team.get("country")
            or league_country
            or ""
        ),
        "league_id": league_id,
        "league": league_name,
        "season": season,
        "founded": team.get("founded"),
        "national": team.get("national"),
        "logo": (
            "images/clubs/api/"
            f"{logo_filename}"
        ),
        "api_logo": logo_url,
        "venue": {
            "id": venue.get("id"),
            "name": venue.get("name"),
            "city": venue.get("city"),
            "capacity": venue.get(
                "capacity"
            ),
        },
    }

    if downloaded:
        return "загружен"

    return "уже сохранён"


def normalize_name(
    value: Any,
) -> str:
    return (
        str(value or "")
        .strip()
        .casefold()
    )


def find_extra_team(
    response_items: list[Any],
    expected_name: str,
    expected_country: str,
) -> dict[str, Any] | None:
    normalized_name = normalize_name(
        expected_name
    )

    normalized_country = normalize_name(
        expected_country
    )

    name_match = None

    for item in response_items:
        if not isinstance(item, dict):
            continue

        team = item.get(
            "team",
            {},
        )

        if not isinstance(team, dict):
            continue

        team_name = normalize_name(
            team.get("name")
        )

        team_country = normalize_name(
            team.get("country")
        )

        if (
            team_name == normalized_name
            and team_country == normalized_country
        ):
            return item

        if team_name == normalized_name:
            name_match = item

    return name_match


def main() -> None:
    load_env()

    api_key = os.environ.get(
        "API_FOOTBALL_KEY",
        "",
    ).strip()

    if not api_key:
        print(
            "ОШИБКА: API_FOOTBALL_KEY "
            "не найден в файле .env"
        )
        sys.exit(1)

    clubs, leagues = load_existing_data()

    LOGO_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    successful_leagues = 0
    downloaded_count = 0
    existing_count = 0
    failed_teams: list[str] = []

    print("ЗАГРУЗКА КЛУБОВ И ЛОГОТИПОВ")
    print(f"Доступный сезон API: {SEASON}")
    print(f"Количество лиг: {len(LEAGUES)}")
    print(
        "Папка логотипов: "
        "static/images/clubs/api/"
    )
    print()

    for league_number, league in enumerate(
        LEAGUES,
        start=1,
    ):
        print(
            f"[Лига {league_number}/"
            f"{len(LEAGUES)}] "
            f"{league['name']} — "
            f"{league['country']}"
        )

        try:
            payload = api_request(
                api_key,
                {
                    "league": league["id"],
                    "season": SEASON,
                },
            )

        except RuntimeError as error:
            print(
                f"  ОШИБКА: {error}"
            )
            print()

            if league_number < len(LEAGUES):
                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

            continue

        response_items = payload.get(
            "response",
            [],
        )

        if not isinstance(
            response_items,
            list,
        ):
            response_items = []

        if not response_items:
            print(
                "  ОШИБКА: API не вернул "
                "команды этой лиги."
            )
            print()

            if league_number < len(LEAGUES):
                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

            continue

        successful_leagues += 1

        leagues[str(league["id"])] = {
            "id": league["id"],
            "name": league["name"],
            "country": league["country"],
            "season": SEASON,
            "teams_count": len(
                response_items
            ),
        }

        print(
            "  Получено команд: "
            f"{len(response_items)}"
        )

        for team_number, item in enumerate(
            response_items,
            start=1,
        ):
            if not isinstance(item, dict):
                continue

            team = item.get(
                "team",
                {},
            )

            if isinstance(team, dict):
                team_name = str(
                    team.get("name")
                    or "Неизвестный клуб"
                ).strip()
            else:
                team_name = "Неизвестный клуб"

            try:
                result = save_team(
                    clubs,
                    item,
                    league["id"],
                    league["name"],
                    league["country"],
                    SEASON,
                )

            except RuntimeError as error:
                failed_teams.append(
                    team_name
                )

                print(
                    f"  [{team_number}/"
                    f"{len(response_items)}] "
                    f"{team_name}: "
                    f"ОШИБКА — {error}"
                )
                continue

            if result == "загружен":
                downloaded_count += 1
            else:
                existing_count += 1

            print(
                f"  [{team_number}/"
                f"{len(response_items)}] "
                f"{team_name}: {result}"
            )

        print()

        if league_number < len(LEAGUES):
            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    if EXTRA_TEAMS:
        time.sleep(
            REQUEST_DELAY_SECONDS
        )

        print("ДОПОЛНИТЕЛЬНЫЕ КЛУБЫ")
        print()

    for extra_number, extra in enumerate(
        EXTRA_TEAMS,
        start=1,
    ):
        print(
            f"[{extra_number}/"
            f"{len(EXTRA_TEAMS)}] "
            f"{extra['expected_name']}"
        )

        try:
            payload = api_request(
                api_key,
                {
                    "search": extra["search"]
                },
            )

        except RuntimeError as error:
            print(
                f"  ОШИБКА: {error}"
            )

            failed_teams.append(
                extra["expected_name"]
            )
            continue

        response_items = payload.get(
            "response",
            [],
        )

        if not isinstance(
            response_items,
            list,
        ):
            response_items = []

        selected = find_extra_team(
            response_items,
            extra["expected_name"],
            extra["country"],
        )

        if selected is None:
            print(
                "  ОШИБКА: клуб не найден."
            )

            failed_teams.append(
                extra["expected_name"]
            )
            continue

        try:
            result = save_team(
                clubs,
                selected,
                None,
                extra["league"],
                extra["country"],
                None,
            )

        except RuntimeError as error:
            print(
                f"  ОШИБКА: {error}"
            )

            failed_teams.append(
                extra["expected_name"]
            )
            continue

        if result == "загружен":
            downloaded_count += 1
        else:
            existing_count += 1

        print(
            f"  {extra['expected_name']}: "
            f"{result}"
        )

    sorted_clubs = dict(
        sorted(
            clubs.items(),
            key=lambda item: int(
                item[0]
            ),
        )
    )

    sorted_leagues = dict(
        sorted(
            leagues.items(),
            key=lambda item: int(
                item[0]
            ),
        )
    )

    output_data = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        ),
        "source_season": SEASON,
        "leagues_count": len(
            sorted_leagues
        ),
        "clubs_count": len(
            sorted_clubs
        ),
        "leagues": sorted_leagues,
        "clubs": sorted_clubs,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output_data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("ГОТОВО")
    print(
        "Успешно обработано лиг: "
        f"{successful_leagues} "
        f"из {len(LEAGUES)}"
    )
    print(
        "Всего клубов в базе: "
        f"{len(sorted_clubs)}"
    )
    print(
        "Новых логотипов загружено: "
        f"{downloaded_count}"
    )
    print(
        "Логотипов уже было: "
        f"{existing_count}"
    )
    print(
        "Карта обновлена: "
        "data/club-logos.json"
    )
    print(
        "Логотипы находятся: "
        "static/images/clubs/api/"
    )

    if failed_teams:
        print()
        print("Не удалось обработать:")

        for team_name in sorted(
            set(failed_teams)
        ):
            print(
                f"- {team_name}"
            )


if __name__ == "__main__":
    main()