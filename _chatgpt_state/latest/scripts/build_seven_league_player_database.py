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
CONFIG_FILE = PROJECT_ROOT / "data" / "playerdb" / "config.json"
LEAGUES_FILE = PROJECT_ROOT / "data" / "playerdb" / "leagues.json"
TEAMS_FILE = PROJECT_ROOT / "data" / "playerdb" / "teams.json"
PLAYERS_FILE = PROJECT_ROOT / "data" / "playerdb" / "players.json"
PROGRESS_FILE = PROJECT_ROOT / "var" / "playerdb" / "progress.json"
RAW_IMAGE_DIR = PROJECT_ROOT / "static" / "images" / "players" / "api"

API_ROOT = "https://v3.football.api-sports.io"
REQUEST_DELAY_SECONDS = 7
RATE_LIMIT_WAIT_SECONDS = 65
MAX_ATTEMPTS = 2


class QuotaReached(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_env() -> None:
    if not ENV_FILE.exists():
        print("ERROR: .env file not found.")
        print(f"Expected: {ENV_FILE}")
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


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"ERROR: invalid JSON: {path}")
        print(error)
        sys.exit(1)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def api_request(
    api_key: str,
    endpoint: str,
    parameters: dict[str, str | int],
) -> tuple[dict[str, Any], dict[str, str]]:
    request = Request(
        f"{API_ROOT}/{endpoint}?{urlencode(parameters)}",
        headers={
            "x-apisports-key": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)
            headers = {
                key.lower(): value
                for key, value in response.headers.items()
            }
            return payload, headers

    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        if error.code == 429:
            raise QuotaReached(f"HTTP 429: {body}") from error

        raise RuntimeError(f"HTTP {error.code}: {body}") from error

    except URLError as error:
        raise RuntimeError(
            f"Connection error: {error.reason}"
        ) from error


def inspect_api_errors(payload: dict[str, Any]) -> None:
    errors = payload.get("errors")

    if not errors:
        return

    text = json.dumps(errors, ensure_ascii=False).lower()

    quota_markers = (
        "request",
        "limit",
        "quota",
        "rate",
        "too many",
    )

    if any(marker in text for marker in quota_markers):
        raise QuotaReached(
            json.dumps(errors, ensure_ascii=False)
        )

    raise RuntimeError(
        "API error: "
        + json.dumps(errors, ensure_ascii=False)
    )


def request_with_retry(
    api_key: str,
    endpoint: str,
    parameters: dict[str, str | int],
) -> tuple[dict[str, Any], dict[str, str]]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            payload, headers = api_request(
                api_key,
                endpoint,
                parameters,
            )
            inspect_api_errors(payload)
            return payload, headers

        except QuotaReached:
            raise

        except RuntimeError:
            if attempt >= MAX_ATTEMPTS:
                raise

            time.sleep(5)

    raise RuntimeError("API request failed.")


def request_remaining(headers: dict[str, str]) -> str:
    for key in (
        "x-ratelimit-requests-remaining",
        "x-ratelimit-remaining",
    ):
        if key in headers:
            return headers[key]

    return "unknown"



def league_teams(
    api_key: str,
    league_id: int,
    season: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    payload, headers = request_with_retry(
        api_key,
        "teams",
        {
            "league": league_id,
            "season": season,
        },
    )

    response = payload.get("response") or []

    teams: list[dict[str, Any]] = []

    for item in response:
        if not isinstance(item, dict):
            continue

        team = item.get("team") or {}
        venue = item.get("venue") or {}

        if not team.get("id"):
            continue

        teams.append(
            {
                "id": int(team["id"]),
                "name": team.get("name"),
                "code": team.get("code"),
                "country": team.get("country"),
                "founded": team.get("founded"),
                "national": team.get("national"),
                "logo": team.get("logo"),
                "venue": venue,
            }
        )

    return teams, headers


def squad_players(
    api_key: str,
    team_id: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    payload, headers = request_with_retry(
        api_key,
        "players/squads",
        {"team": team_id},
    )

    response = payload.get("response") or []

    players: list[dict[str, Any]] = []

    for squad in response:
        if not isinstance(squad, dict):
            continue

        for player in squad.get("players") or []:
            if not isinstance(player, dict) or not player.get("id"):
                continue

            players.append(player)

    return players, headers


def download_photo(
    photo_url: str,
    destination: Path,
) -> None:
    if destination.exists() and destination.stat().st_size > 500:
        return

    request = Request(
        photo_url,
        headers={"User-Agent": "ProFutbik/1.0"},
        method="GET",
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part"
    )

    try:
        with urlopen(request, timeout=60) as response:
            image_data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"Photo HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Photo connection error: {error.reason}"
        ) from error

    if len(image_data) < 500:
        raise RuntimeError("Empty player photo.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(image_data)
    temporary.replace(destination)


def player_record(
    raw: dict[str, Any],
    team: dict[str, Any],
    league: dict[str, Any],
    season: int,
) -> dict[str, Any]:
    player_id = int(raw["id"])
    photo_url = str(
        raw.get("photo")
        or (
            "https://media.api-sports.io/"
            f"football/players/{player_id}.png"
        )
    )

    return {
        "id": player_id,
        "name": raw.get("name"),
        "firstname": raw.get("firstname"),
        "lastname": raw.get("lastname"),
        "age": raw.get("age"),
        "number": raw.get("number"),
        "position": raw.get("position"),
        "photo_source": "API-Football",
        "photo_source_url": photo_url,
        "photo_raw": f"images/players/api/{player_id}.png",
        "photo_cutout": None,
        "background_removed": False,
        "team": {
            "id": team["id"],
            "name": team["name"],
            "logo": team.get("logo"),
        },
        "league": {
            "id": league["id"],
            "name": league["name"],
            "country": league["country"],
            "season": season,
        },
        "updated_at": utc_now(),
    }


def save_databases(
    league_records: list[dict[str, Any]],
    team_records: list[dict[str, Any]],
    players_by_id: dict[str, dict[str, Any]],
    progress: dict[str, Any],
) -> None:
    save_json(
        LEAGUES_FILE,
        {
            "generated_at": utc_now(),
            "items": sorted(
                league_records,
                key=lambda item: item["id"],
            ),
        },
    )

    save_json(
        TEAMS_FILE,
        {
            "generated_at": utc_now(),
            "count": len(team_records),
            "items": sorted(
                team_records,
                key=lambda item: (
                    item["league"]["name"],
                    item["name"],
                ),
            ),
        },
    )

    players = sorted(
        players_by_id.values(),
        key=lambda item: (
            item["league"]["name"],
            item["team"]["name"],
            item.get("name") or "",
        ),
    )

    save_json(
        PLAYERS_FILE,
        {
            "generated_at": utc_now(),
            "count": len(players),
            "items": players,
        },
    )

    save_json(PROGRESS_FILE, progress)


def main() -> None:
    load_env()

    api_key = os.environ.get(
        "API_FOOTBALL_KEY",
        "",
    ).strip()

    if not api_key:
        print("ERROR: API_FOOTBALL_KEY is missing in .env")
        sys.exit(1)

    config = load_json(CONFIG_FILE, {})
    leagues = config.get("leagues") or []

    if not leagues:
        print("ERROR: no leagues in data/playerdb/config.json")
        sys.exit(1)

    selection = config.get("selection") or {}
    selected_team_ids = {
        int(value)
        for value in selection.get("team_ids") or []
    }

    progress = load_json(
        PROGRESS_FILE,
        {
            "version": 1,
            "completed_team_ids": [],
            "failed_team_ids": [],
            "last_run_at": None,
        },
    )

    completed = {
        int(value)
        for value in progress.get("completed_team_ids") or []
    }

    existing_players_payload = load_json(
        PLAYERS_FILE,
        {"items": []},
    )

    players_by_id = {
        str(item["id"]): item
        for item in existing_players_payload.get("items") or []
        if isinstance(item, dict) and item.get("id")
    }

    league_records: list[dict[str, Any]] = []
    team_records: list[dict[str, Any]] = []

    print("ProFutbik player database")
    print("Leagues: 7")
    print("Free plan mode: team lists use season 2024; squads use players/squads.")
    print("The script is resume-safe.")
    print()

    try:
        for league_number, league in enumerate(leagues, start=1):
            league_id = int(league["id"])
            league_name = str(league["name"])

            print(
                f"[LEAGUE {league_number}/{len(leagues)}] "
                f"{league_name}"
            )

            season = int(
                league.get("free_plan_season")
                or config.get("free_plan_season")
                or 2024
            )

            print(
                f"  Free-plan reference season: {season}"
            )

            teams, headers = league_teams(
                api_key,
                league_id,
                season,
            )
            print(
                f"  Teams found: {len(teams)}; "
                f"requests remaining: {request_remaining(headers)}"
            )

            league_record = {
                "id": league_id,
                "name": league_name,
                "country": league.get("country"),
                "reference_season": season,
                "squad_source": "players/squads current response",
                "team_count": len(teams),
            }
            league_records.append(league_record)

            for team in teams:
                if selected_team_ids and team["id"] not in selected_team_ids:
                    continue

                team_record = {
                    **team,
                    "league": {
                        "id": league_id,
                        "name": league_name,
                        "country": league.get("country"),
                        "reference_season": season,
                        "squad_source": "players/squads current response",
                    },
                }
                team_records.append(team_record)

            save_databases(
                league_records,
                team_records,
                players_by_id,
                progress,
            )

            for team_index, team in enumerate(teams, start=1):
                team_id = int(team["id"])

                if selected_team_ids and team_id not in selected_team_ids:
                    continue

                if team_id in completed:
                    print(
                        f"  [SKIP] {team['name']} already completed."
                    )
                    continue

                print(
                    f"  [TEAM {team_index}/{len(teams)}] "
                    f"{team['name']}"
                )

                time.sleep(REQUEST_DELAY_SECONDS)

                squad, headers = squad_players(
                    api_key,
                    team_id,
                )

                saved_photos = 0

                for raw_player in squad:
                    record = player_record(
                        raw_player,
                        team,
                        league,
                        season,
                    )

                    player_id = record["id"]
                    photo_url = record["photo_source_url"]
                    destination = (
                        RAW_IMAGE_DIR / f"{player_id}.png"
                    )

                    try:
                        download_photo(
                            photo_url,
                            destination,
                        )
                        saved_photos += 1
                    except RuntimeError as error:
                        record["photo_error"] = str(error)

                    existing = players_by_id.get(
                        str(player_id)
                    )

                    if (
                        existing
                        and existing.get("background_removed")
                    ):
                        record["photo_cutout"] = existing.get(
                            "photo_cutout"
                        )
                        record["background_removed"] = True
                        record["pixelcut"] = existing.get(
                            "pixelcut"
                        )

                    players_by_id[str(player_id)] = record

                completed.add(team_id)
                progress["completed_team_ids"] = sorted(completed)
                progress["last_run_at"] = utc_now()
                progress["last_team"] = {
                    "id": team_id,
                    "name": team["name"],
                    "league": league_name,
                }

                save_databases(
                    league_records,
                    team_records,
                    players_by_id,
                    progress,
                )

                print(
                    f"    Players: {len(squad)}; "
                    f"photos: {saved_photos}; "
                    f"requests remaining: {request_remaining(headers)}"
                )

        progress["finished_at"] = utc_now()
        save_databases(
            league_records,
            team_records,
            players_by_id,
            progress,
        )

        print()
        print("DONE")
        print(f"Teams completed: {len(completed)}")
        print(f"Players in database: {len(players_by_id)}")
        print(
            "Run 02_pixelcut_next_50_players.bat "
            "to remove backgrounds in batches."
        )

    except QuotaReached as error:
        progress["last_run_at"] = utc_now()
        progress["stopped_reason"] = str(error)

        save_databases(
            league_records,
            team_records,
            players_by_id,
            progress,
        )

        print()
        print("API LIMIT REACHED.")
        print("Progress was saved.")
        print(
            "Run this BAT again after the API quota resets."
        )
        sys.exit(3)

    except RuntimeError as error:
        progress["last_run_at"] = utc_now()
        progress["stopped_reason"] = str(error)

        save_databases(
            league_records,
            team_records,
            players_by_id,
            progress,
        )

        print()
        print(f"ERROR: {error}")
        print("Progress was saved.")
        sys.exit(2)


if __name__ == "__main__":
    main()
