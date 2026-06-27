from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
CLUBS_FILE = PROJECT_ROOT / "data" / "transfer-clubs.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "transfers-api-preview.json"

API_URL = "https://v3.football.api-sports.io/transfers"

# Бесплатный тариф разрешает 10 запросов в минуту.
# Пауза 7 секунд не позволяет превысить этот лимит.
REQUEST_DELAY_SECONDS = 7

# Если API всё же вернёт HTTP 429, ждём сброса минутного лимита.
RATE_LIMIT_WAIT_SECONDS = 65
MAX_ATTEMPTS = 2


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


def api_request(
    api_key: str,
    team_id: int,
) -> dict:
    query = urlencode(
        {
            "team": team_id,
        }
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

    try:
        with urlopen(
            request,
            timeout=30,
        ) as response:
            return json.load(response)

    except HTTPError as error:
        body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"HTTP {error.code}: {body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Ошибка соединения: {error.reason}"
        ) from error


def request_with_retry(
    api_key: str,
    team_id: int,
) -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return api_request(
                api_key,
                team_id,
            )

        except RuntimeError as error:
            error_text = str(error)

            if (
                "HTTP 429" in error_text
                and attempt < MAX_ATTEMPTS
            ):
                print(
                    "  Достигнут минутный лимит API."
                )
                print(
                    f"  Ожидание "
                    f"{RATE_LIMIT_WAIT_SECONDS} секунд..."
                )

                time.sleep(
                    RATE_LIMIT_WAIT_SECONDS
                )
                continue

            raise

    raise RuntimeError(
        "Не удалось получить данные после повторной попытки."
    )


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

    try:
        clubs = json.loads(
            CLUBS_FILE.read_text(
                encoding="utf-8",
            )
        )

    except FileNotFoundError:
        print(
            "ОШИБКА: файл "
            "data/transfer-clubs.json не найден."
        )
        sys.exit(1)

    except json.JSONDecodeError as error:
        print(
            "ОШИБКА JSON в файле "
            "data/transfer-clubs.json"
        )
        print(error)
        sys.exit(1)

    if not isinstance(clubs, list):
        print(
            "ОШИБКА: transfer-clubs.json "
            "должен содержать список клубов."
        )
        sys.exit(1)

    results = []
    failed_clubs = []

    print("ПОЛУЧЕНИЕ ТРАНСФЕРОВ ИЗ API")
    print(f"Количество клубов: {len(clubs)}")
    print(
        "Пауза между запросами: "
        f"{REQUEST_DELAY_SECONDS} секунд"
    )
    print()

    for number, club in enumerate(
        clubs,
        start=1,
    ):
        team_id = club.get("id")
        club_name = club.get(
            "name",
            "Неизвестный клуб",
        )

        if not isinstance(team_id, int):
            print(
                f"[{number}/{len(clubs)}] "
                f"{club_name}: неверный ID"
            )

            failed_clubs.append(
                club_name
            )
            continue

        print(
            f"[{number}/{len(clubs)}] "
            f"{club_name}"
        )

        try:
            payload = request_with_retry(
                api_key,
                team_id,
            )

        except RuntimeError as error:
            print(f"  ОШИБКА: {error}")

            failed_clubs.append(
                club_name
            )

            if number < len(clubs):
                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

            continue

        errors = payload.get("errors")

        if errors:
            print(
                "  ОШИБКА API: "
                f"{errors}"
            )

            failed_clubs.append(
                club_name
            )

            if number < len(clubs):
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

        results.append(
            {
                "club_id": team_id,
                "club_name": club_name,
                "country": club.get(
                    "country",
                    "",
                ),
                "league": club.get(
                    "league",
                    "",
                ),
                "players_count": len(
                    response_items
                ),
                "response": response_items,
            }
        )

        print(
            "  Получено игроков: "
            f"{len(response_items)}"
        )

        if number < len(clubs):
            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("ГОТОВО")
    print(
        "Файл создан: "
        "data/transfers-api-preview.json"
    )
    print(
        "Успешно проверено клубов: "
        f"{len(results)} из {len(clubs)}"
    )

    if failed_clubs:
        print()
        print("Не удалось проверить клубы:")

        for club_name in failed_clubs:
            print(f"- {club_name}")


if __name__ == "__main__":
    main()