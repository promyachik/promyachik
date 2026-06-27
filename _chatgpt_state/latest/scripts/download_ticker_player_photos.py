from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
TRANSFERS_FILE = PROJECT_ROOT / "data" / "transfers.json"
PLAYER_IMAGE_DIR = PROJECT_ROOT / "static" / "images" / "players" / "api"

API_ROOT = "https://v3.football.api-sports.io"
SQUADS_API_URL = f"{API_ROOT}/players/squads"
PROFILES_API_URL = f"{API_ROOT}/players/profiles"
PLAYERS_API_URL = f"{API_ROOT}/players"

REQUEST_DELAY_SECONDS = 7
RATE_LIMIT_WAIT_SECONDS = 65
MAX_ATTEMPTS = 2


def load_env() -> None:
    if not ENV_FILE.exists():
        print("ОШИБКА: файл .env не найден.")
        print(f"Ожидался файл: {ENV_FILE}")
        sys.exit(1)

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def load_transfers() -> list[dict[str, Any]]:
    try:
        data = json.loads(TRANSFERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("ОШИБКА: не найден data/transfers.json")
        sys.exit(1)
    except json.JSONDecodeError as error:
        print("ОШИБКА JSON в data/transfers.json")
        print(error)
        sys.exit(1)

    if not isinstance(data, list):
        print("ОШИБКА: data/transfers.json должен содержать JSON-массив.")
        sys.exit(1)

    return data


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)

    without_marks = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        without_marks.lower(),
    ).strip()


def safe_search_query(value: str) -> str:
    return normalize_name(value)


def api_request(
    api_key: str,
    url: str,
    parameters: dict[str, str | int],
) -> dict[str, Any]:
    request = Request(
        f"{url}?{urlencode(parameters)}",
        headers={
            "x-apisports-key": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=40) as response:
            return json.load(response)

    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body}") from error

    except URLError as error:
        raise RuntimeError(
            f"Ошибка соединения: {error.reason}"
        ) from error


def request_with_retry(
    api_key: str,
    url: str,
    parameters: dict[str, str | int],
) -> dict[str, Any]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return api_request(api_key, url, parameters)

        except RuntimeError as error:
            if "HTTP 429" in str(error) and attempt < MAX_ATTEMPTS:
                print("  Достигнут минутный лимит API.")
                print(
                    f"  Ожидание {RATE_LIMIT_WAIT_SECONDS} секунд..."
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                continue

            raise

    raise RuntimeError("Не удалось получить ответ API.")


def name_tokens(value: str) -> list[str]:
    return normalize_name(value).split()


def surname_match_score(
    requested_name: str,
    candidate_name: str,
) -> float:
    requested = name_tokens(requested_name)
    candidate = name_tokens(candidate_name)

    if not requested or not candidate:
        return 0.0

    score = 0.0

    # Обычная фамилия: Mbappe, Alvarez, Olmo, Endrick.
    if requested[-1] == candidate[-1]:
        score += 130.0

    # Составная фамилия: de Ligt.
    if len(requested) >= 2 and len(candidate) >= 2:
        if requested[-2:] == candidate[-2:]:
            score += 160.0

    # API часто пишет имя сокращённо: K. Mbappe / M. de Ligt.
    if requested[-1] == candidate[-1]:
        if requested[0][0] == candidate[0][0]:
            score += 35.0

    return score


def candidate_score(
    requested_name: str,
    candidate: dict[str, Any],
) -> float:
    requested = normalize_name(requested_name)

    candidate_names = [
        str(candidate.get("name") or ""),
        str(candidate.get("firstname") or ""),
        str(candidate.get("lastname") or ""),
    ]

    first_last = " ".join(
        part
        for part in (
            str(candidate.get("firstname") or ""),
            str(candidate.get("lastname") or ""),
        )
        if part
    )

    if first_last:
        candidate_names.append(first_last)

    best = 0.0

    for candidate_name in candidate_names:
        normalized = normalize_name(candidate_name)

        if not normalized:
            continue

        if normalized == requested:
            return 1000.0

        ratio = SequenceMatcher(
            None,
            requested,
            normalized,
        ).ratio()

        score = ratio * 100.0
        score += surname_match_score(
            requested_name,
            candidate_name,
        )

        if requested in normalized or normalized in requested:
            score += 30.0

        best = max(best, score)

    return best


def choose_player(
    requested_name: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not candidates:
        return None

    ranked = sorted(
        candidates,
        key=lambda item: candidate_score(requested_name, item),
        reverse=True,
    )

    winner = ranked[0]
    score = candidate_score(requested_name, winner)

    if score < 85:
        return None

    return winner


def get_profile_candidates(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    response = payload.get("response", [])

    if not isinstance(response, list):
        return []

    candidates: list[dict[str, Any]] = []

    for item in response:
        if not isinstance(item, dict):
            continue

        player = item.get("player")

        if isinstance(player, dict):
            candidates.append(player)
            continue

        if item.get("id") and item.get("name"):
            candidates.append(item)

    return candidates


def get_squad_candidates(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    response = payload.get("response", [])

    if not isinstance(response, list):
        return []

    candidates: list[dict[str, Any]] = []

    for squad in response:
        if not isinstance(squad, dict):
            continue

        players = squad.get("players", [])

        if not isinstance(players, list):
            continue

        for player in players:
            if not isinstance(player, dict):
                continue

            if player.get("id") and player.get("name"):
                candidates.append(player)

    return candidates


def search_queries(player_name: str) -> list[str]:
    normalized = safe_search_query(player_name)
    tokens = normalized.split()

    queries: list[str] = []

    def add(value: str) -> None:
        cleaned = safe_search_query(value)
        if cleaned and cleaned not in queries:
            queries.append(cleaned)

    add(normalized)

    if tokens:
        add(tokens[-1])

    if len(tokens) >= 2:
        add(" ".join(tokens[-2:]))

    # Удачные резервные варианты для текущей ленты.
    manual = {
        "kylian mbappe": ["mbappe"],
        "julian alvarez": ["alvarez"],
        "matthijs de ligt": ["de ligt", "ligt"],
    }

    for value in manual.get(normalized, []):
        add(value)

    return queries


def find_in_team_squads(
    api_key: str,
    player_name: str,
    team_ids: list[int],
) -> dict[str, Any] | None:
    checked: set[int] = set()

    for team_id in team_ids:
        if not team_id or team_id in checked:
            continue

        checked.add(team_id)

        payload = request_with_retry(
            api_key,
            SQUADS_API_URL,
            {"team": team_id},
        )

        candidates = get_squad_candidates(payload)
        selected = choose_player(player_name, candidates)

        if selected:
            return selected

        time.sleep(REQUEST_DELAY_SECONDS)

    return None


def find_by_search(
    api_key: str,
    player_name: str,
) -> dict[str, Any] | None:
    for query in search_queries(player_name):
        payload = request_with_retry(
            api_key,
            PROFILES_API_URL,
            {"search": query},
        )

        errors = payload.get("errors")
        if errors:
            print(
                f"  profiles search '{query}': {errors}"
            )

        selected = choose_player(
            player_name,
            get_profile_candidates(payload),
        )

        if selected:
            return selected

        time.sleep(REQUEST_DELAY_SECONDS)

    for season in (2025, 2024):
        for query in search_queries(player_name):
            payload = request_with_retry(
                api_key,
                PLAYERS_API_URL,
                {
                    "search": query,
                    "season": season,
                },
            )

            selected = choose_player(
                player_name,
                get_profile_candidates(payload),
            )

            if selected:
                return selected

            time.sleep(REQUEST_DELAY_SECONDS)

    return None


def find_player(
    api_key: str,
    player_name: str,
    transfer: dict[str, Any],
) -> dict[str, Any] | None:
    team_ids: list[int] = []

    for field in ("to_club_id", "from_club_id"):
        value = transfer.get(field)

        try:
            team_id = int(value)
        except (TypeError, ValueError):
            continue

        if team_id > 0:
            team_ids.append(team_id)

    # Сначала ищем в составах команд — это надёжнее для сокращённых имён.
    player = find_in_team_squads(
        api_key,
        player_name,
        team_ids,
    )

    if player:
        return player

    # Затем используем поиск без диакритики.
    return find_by_search(
        api_key,
        player_name,
    )


def download_image(
    image_url: str,
    destination: Path,
) -> None:
    request = Request(
        image_url,
        headers={"User-Agent": "ProFutbik/1.0"},
        method="GET",
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part"
    )

    try:
        with urlopen(request, timeout=40) as response:
            image_data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"фотография: HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "фотография: ошибка соединения: "
            f"{error.reason}"
        ) from error

    if len(image_data) < 500:
        raise RuntimeError(
            "API вернул пустое или повреждённое изображение."
        )

    temporary.write_bytes(image_data)
    temporary.replace(destination)


def main() -> None:
    load_env()

    api_key = os.environ.get(
        "API_FOOTBALL_KEY",
        "",
    ).strip()

    if not api_key:
        print(
            "ОШИБКА: в .env нет API_FOOTBALL_KEY."
        )
        sys.exit(1)

    transfers = load_transfers()
    PLAYER_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_dir = (
        PROJECT_ROOT
        / "backups"
        / "api-football"
    )
    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_file = (
        backup_dir
        / "transfers.before-api-photos-v4.json.bak"
    )

    if not backup_file.exists():
        backup_file.write_text(
            TRANSFERS_FILE.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    found = 0
    failed: list[str] = []

    print("Загрузка фотографий игроков из API-Football")
    print(f"Записей: {len(transfers)}")
    print()

    for number, transfer in enumerate(transfers, start=1):
        if not isinstance(transfer, dict):
            continue

        player_name = str(
            transfer.get("player") or ""
        ).strip()

        if not player_name:
            continue

        print(
            f"[{number}/{len(transfers)}] {player_name}"
        )

        try:
            player = find_player(
                api_key,
                player_name,
                transfer,
            )

            if not player:
                print("  ОШИБКА: игрок не найден.")
                failed.append(player_name)
                continue

            player_id = int(player["id"])

            image_url = str(
                player.get("photo")
                or (
                    "https://media.api-sports.io/"
                    "football/players/"
                    f"{player_id}.png"
                )
            ).strip()

            destination = (
                PLAYER_IMAGE_DIR
                / f"{player_id}.png"
            )

            download_image(
                image_url,
                destination,
            )

            local_path = (
                "images/players/api/"
                f"{player_id}.png"
            )

            transfer["player_id"] = player_id
            transfer["player_image"] = local_path
            transfer[
                "player_image_source_name"
            ] = "API-Football"
            transfer[
                "player_image_source_url"
            ] = image_url

            found += 1

            print(
                f"  Сохранено: {local_path}"
            )

        except (
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            print(f"  ОШИБКА: {error}")
            failed.append(player_name)

        if number < len(transfers):
            time.sleep(REQUEST_DELAY_SECONDS)

    TRANSFERS_FILE.write_text(
        json.dumps(
            transfers,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(f"ГОТОВО. Загружено: {found}")

    if failed:
        print(
            "Не удалось загрузить: "
            + ", ".join(failed)
        )
        sys.exit(2)

    print("data/transfers.json обновлён.")
    print(
        "Фотографии сохранены в "
        "static/images/players/api/"
    )


if __name__ == "__main__":
    main()
