from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
PLAYERS_FILE = PROJECT_ROOT / "data" / "playerdb" / "players.json"
PRIORITY_FILE = (
    PROJECT_ROOT / "data" / "playerdb" / "pixelcut_priority.json"
)
CUTOUT_DIR = (
    PROJECT_ROOT / "static" / "images" / "players" / "cutout"
)
PIXELCUT_URL = (
    "https://api.developer.pixelcut.ai/v1/remove-background"
)

REQUEST_DELAY_SECONDS = 2
MAX_ATTEMPTS = 2


class PixelcutQuotaReached(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_env() -> None:
    if not ENV_FILE.exists():
        print("ERROR: .env file not found.")
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        print(f"ERROR: invalid JSON: {path}")
        print(error)
        sys.exit(1)

    if not isinstance(data, dict):
        print(f"ERROR: JSON root must be an object: {path}")
        sys.exit(1)

    return data


def save_json(path: Path, data: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_priority_ids() -> list[int]:
    priority_payload = load_json(PRIORITY_FILE)
    raw_items = priority_payload.get("items")

    if not isinstance(raw_items, list):
        print(
            "ERROR: pixelcut_priority.json must contain "
            'an "items" list.'
        )
        sys.exit(1)

    priority_ids: list[int] = []
    seen: set[int] = set()

    for position, raw_item in enumerate(raw_items, start=1):
        raw_id: Any

        if isinstance(raw_item, dict):
            raw_id = raw_item.get("id")
        else:
            raw_id = raw_item

        try:
            player_id = int(raw_id)
        except (TypeError, ValueError):
            print(
                "ERROR: invalid player ID at priority position "
                f"{position}: {raw_item!r}"
            )
            sys.exit(1)

        if player_id in seen:
            continue

        seen.add(player_id)
        priority_ids.append(player_id)

    return priority_ids


def pixelcut_remove_background(
    api_key: str,
    image_url: str,
) -> str:
    body = json.dumps(
        {
            "image_url": image_url,
            "format": "png",
            "crop": False,
        }
    ).encode("utf-8")

    request = Request(
        PIXELCUT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-KEY": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            payload = json.load(response)

    except HTTPError as error:
        response_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        if error.code in (402, 429):
            raise PixelcutQuotaReached(
                f"Pixelcut HTTP {error.code}: {response_body}"
            ) from error

        raise RuntimeError(
            f"Pixelcut HTTP {error.code}: {response_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Pixelcut connection error: {error.reason}"
        ) from error

    result_url = str(payload.get("result_url") or "").strip()

    if not result_url:
        raise RuntimeError(
            "Pixelcut did not return result_url."
        )

    return result_url


def call_with_retry(
    api_key: str,
    image_url: str,
) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return pixelcut_remove_background(
                api_key,
                image_url,
            )

        except PixelcutQuotaReached:
            raise

        except RuntimeError:
            if attempt >= MAX_ATTEMPTS:
                raise

            time.sleep(5)

    raise RuntimeError("Pixelcut request failed.")


def download_png(
    result_url: str,
    destination: Path,
) -> None:
    request = Request(
        result_url,
        headers={"User-Agent": "ProFutbik/1.0"},
        method="GET",
    )

    temporary = destination.with_suffix(
        destination.suffix + ".part"
    )

    try:
        with urlopen(request, timeout=120) as response:
            image_data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"Result download HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Result download error: {error.reason}"
        ) from error

    if len(image_data) < 500:
        raise RuntimeError("Empty Pixelcut PNG.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(image_data)
    temporary.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum priority images to process in this run.",
    )
    args = parser.parse_args()

    if args.limit < 1:
        print("ERROR: limit must be at least 1.")
        sys.exit(1)

    load_env()

    api_key = os.environ.get(
        "PIXELCUT_API_KEY",
        "",
    ).strip()

    if not api_key:
        print("ERROR: PIXELCUT_API_KEY is missing in .env")
        sys.exit(1)

    payload = load_json(PLAYERS_FILE)
    players = payload.get("items") or []

    if not isinstance(players, list):
        print('ERROR: players.json must contain an "items" list.')
        sys.exit(1)

    priority_ids = load_priority_ids()

    players_by_id: dict[int, dict[str, Any]] = {}

    for player in players:
        if not isinstance(player, dict):
            continue

        try:
            player_id = int(player.get("id"))
        except (TypeError, ValueError):
            continue

        players_by_id[player_id] = player

    pending: list[dict[str, Any]] = []
    already_processed: list[int] = []
    missing_players: list[int] = []
    missing_source_url: list[int] = []

    for player_id in priority_ids:
        player = players_by_id.get(player_id)

        if player is None:
            missing_players.append(player_id)
            continue

        if player.get("background_removed"):
            already_processed.append(player_id)
            continue

        if not player.get("photo_source_url"):
            missing_source_url.append(player_id)
            continue

        pending.append(player)

    selected = pending[: args.limit]

    print("Pixelcut priority background removal")
    print(f"Priority IDs: {len(priority_ids)}")
    print(f"Already processed: {len(already_processed)}")
    print(f"Pending priority players: {len(pending)}")
    print(f"This run: {len(selected)}")

    if missing_players:
        print(
            "IDs not found in players.json: "
            + ", ".join(map(str, missing_players))
        )

    if missing_source_url:
        print(
            "IDs without photo_source_url: "
            + ", ".join(map(str, missing_source_url))
        )

    print()

    if not priority_ids:
        print("Priority list is empty.")
        print(
            "Add player IDs to "
            "data/playerdb/pixelcut_priority.json"
        )
        return

    if not selected:
        print("DONE")
        print("No pending priority players to process.")
        return

    processed = 0

    try:
        for number, player in enumerate(selected, start=1):
            player_id = int(player["id"])
            player_name = str(
                player.get("name") or player_id
            )
            team_name = str(
                (player.get("team") or {}).get("name") or "-"
            )

            print(
                f"[{number}/{len(selected)}] "
                f"{player_name} | {team_name} | ID {player_id}"
            )

            result_url = call_with_retry(
                api_key,
                str(player["photo_source_url"]),
            )

            destination = CUTOUT_DIR / f"{player_id}.png"

            download_png(
                result_url,
                destination,
            )

            player["photo_cutout"] = (
                f"images/players/cutout/{player_id}.png"
            )
            player["background_removed"] = True
            player["pixelcut"] = {
                "processed_at": utc_now(),
                "result_url": result_url,
            }

            processed += 1
            payload["generated_at"] = utc_now()
            payload["count"] = len(players)
            payload["items"] = players
            save_json(PLAYERS_FILE, payload)

            print(
                "  Saved: "
                f"images/players/cutout/{player_id}.png"
            )

            if number < len(selected):
                time.sleep(REQUEST_DELAY_SECONDS)

        remaining = len(pending) - processed

        print()
        print("DONE")
        print(f"Processed this run: {processed}")
        print(f"Priority players still pending: {remaining}")

    except PixelcutQuotaReached as error:
        payload["generated_at"] = utc_now()
        payload["count"] = len(players)
        payload["items"] = players
        save_json(PLAYERS_FILE, payload)

        print()
        print(f"PIXELCUT LIMIT: {error}")
        print("Progress was saved.")
        sys.exit(3)

    except RuntimeError as error:
        payload["generated_at"] = utc_now()
        payload["count"] = len(players)
        payload["items"] = players
        save_json(PLAYERS_FILE, payload)

        print()
        print(f"ERROR: {error}")
        print("Progress was saved.")
        sys.exit(2)


if __name__ == "__main__":
    main()
