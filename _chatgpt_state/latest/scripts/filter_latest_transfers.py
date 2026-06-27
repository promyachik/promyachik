from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "transfers-api-preview.json"
)

CLUBS_FILE = (
    PROJECT_ROOT
    / "data"
    / "transfer-clubs.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "transfers-filtered-preview.json"
)

DAYS_LIMIT = 30

EXCLUDED_TYPES = {
    "return from loan",
    "retired",
    "retirement",
    "raise",
}

UNKNOWN_TYPES = {
    "",
    "-",
    "n/a",
    "transfer",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

    except FileNotFoundError:
        print(
            f"ОШИБКА: файл не найден: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )
        sys.exit(1)

    except json.JSONDecodeError as error:
        print(
            f"ОШИБКА JSON в файле: "
            f"{path.relative_to(PROJECT_ROOT)}"
        )
        print(error)
        sys.exit(1)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return unescape(
        str(value).strip()
    )


def parse_transfer_date(
    value: Any,
) -> date | None:
    text = clean_text(value)

    if not text:
        return None

    try:
        return datetime.strptime(
            text,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return None


def normalize_type(
    value: Any,
) -> str:
    return clean_text(value).lower()


def format_fee(
    raw_type: str,
) -> str:
    normalized = raw_type.lower()

    if normalized in {
        "free",
        "free agent",
        "€ free",
    }:
        return "Свободный агент"

    if normalized == "loan":
        return "Аренда"

    if normalized in UNKNOWN_TYPES:
        return "Сумма не разглашается"

    return raw_type


def build_slug(
    player_id: Any,
    transfer_date: date,
) -> str:
    safe_player_id = clean_text(
        player_id
    ) or "unknown"

    return (
        "transfers/"
        f"api-{safe_player_id}-"
        f"{transfer_date.isoformat()}/"
    )


def main() -> None:
    raw_clubs = load_json(
        CLUBS_FILE
    )

    raw_api_data = load_json(
        SOURCE_FILE
    )

    if not isinstance(
        raw_clubs,
        list,
    ):
        print(
            "ОШИБКА: transfer-clubs.json "
            "должен содержать список."
        )
        sys.exit(1)

    if not isinstance(
        raw_api_data,
        list,
    ):
        print(
            "ОШИБКА: transfers-api-preview.json "
            "должен содержать список."
        )
        sys.exit(1)

    monitored_club_ids = {
        club.get("id")
        for club in raw_clubs
        if isinstance(
            club.get("id"),
            int,
        )
    }

    today = date.today()
    date_from = (
        today
        - timedelta(
            days=DAYS_LIMIT - 1,
        )
    )

    filtered_transfers = []
    seen_transfers = set()

    scanned_players = 0
    scanned_transfer_records = 0
    skipped_old = 0
    skipped_type = 0
    skipped_duplicate = 0
    skipped_invalid = 0
    skipped_unrelated = 0

    for club_block in raw_api_data:
        if not isinstance(
            club_block,
            dict,
        ):
            continue

        players = club_block.get(
            "response",
            [],
        )

        if not isinstance(
            players,
            list,
        ):
            continue

        for player_item in players:
            if not isinstance(
                player_item,
                dict,
            ):
                continue

            scanned_players += 1

            player = player_item.get(
                "player",
                {},
            )

            if not isinstance(
                player,
                dict,
            ):
                player = {}

            player_id = player.get("id")
            player_name = clean_text(
                player.get("name")
            )

            api_update = clean_text(
                player_item.get("update")
            )

            transfers = player_item.get(
                "transfers",
                [],
            )

            if not isinstance(
                transfers,
                list,
            ):
                continue

            for transfer in transfers:
                scanned_transfer_records += 1

                if not isinstance(
                    transfer,
                    dict,
                ):
                    skipped_invalid += 1
                    continue

                transfer_date = (
                    parse_transfer_date(
                        transfer.get("date")
                    )
                )

                if transfer_date is None:
                    skipped_invalid += 1
                    continue

                if not (
                    date_from
                    <= transfer_date
                    <= today
                ):
                    skipped_old += 1
                    continue

                raw_type = clean_text(
                    transfer.get("type")
                )

                normalized_type = (
                    normalize_type(
                        raw_type
                    )
                )

                if (
                    normalized_type
                    in EXCLUDED_TYPES
                ):
                    skipped_type += 1
                    continue

                teams = transfer.get(
                    "teams",
                    {},
                )

                if not isinstance(
                    teams,
                    dict,
                ):
                    skipped_invalid += 1
                    continue

                team_in = teams.get(
                    "in",
                    {},
                )

                team_out = teams.get(
                    "out",
                    {},
                )

                if not isinstance(
                    team_in,
                    dict,
                ):
                    team_in = {}

                if not isinstance(
                    team_out,
                    dict,
                ):
                    team_out = {}

                in_id = team_in.get("id")
                out_id = team_out.get("id")

                in_name = clean_text(
                    team_in.get("name")
                )

                out_name = clean_text(
                    team_out.get("name")
                )

                in_logo = clean_text(
                    team_in.get("logo")
                )

                out_logo = clean_text(
                    team_out.get("logo")
                )

                if (
                    not player_name
                    or not in_name
                    or not out_name
                ):
                    skipped_invalid += 1
                    continue

                if (
                    in_id is not None
                    and out_id is not None
                    and in_id == out_id
                ):
                    skipped_invalid += 1
                    continue

                if (
                    in_id
                    not in monitored_club_ids
                    and out_id
                    not in monitored_club_ids
                ):
                    skipped_unrelated += 1
                    continue

                duplicate_key = (
                    player_id,
                    transfer_date.isoformat(),
                    out_id,
                    in_id,
                    normalized_type,
                )

                if (
                    duplicate_key
                    in seen_transfers
                ):
                    skipped_duplicate += 1
                    continue

                seen_transfers.add(
                    duplicate_key
                )

                filtered_transfers.append(
                    {
                        "date": (
                            transfer_date
                            .isoformat()
                        ),
                        "status": "official",
                        "player_id": player_id,
                        "player": player_name,
                        "from_club": {
                            "id": out_id,
                            "name": out_name,
                            "logo": out_logo,
                        },
                        "to_club": {
                            "id": in_id,
                            "name": in_name,
                            "logo": in_logo,
                        },
                        "fee": format_fee(
                            raw_type
                        ),
                        "raw_type": (
                            raw_type
                            or "N/A"
                        ),
                        "api_update": (
                            api_update
                        ),
                        "url": build_slug(
                            player_id,
                            transfer_date,
                        ),
                    }
                )

    filtered_transfers.sort(
        key=lambda item: (
            item["date"],
            item["api_update"],
            item["player"],
        ),
        reverse=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            filtered_transfers,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("ФИЛЬТРАЦИЯ ЗАВЕРШЕНА")
    print()
    print(
        "Период: "
        f"{date_from.strftime('%d.%m.%Y')} "
        f"— {today.strftime('%d.%m.%Y')}"
    )
    print(
        "Проверено игроков: "
        f"{scanned_players}"
    )
    print(
        "Проверено записей: "
        f"{scanned_transfer_records}"
    )
    print(
        "Оставлено трансферов: "
        f"{len(filtered_transfers)}"
    )
    print(
        "Удалено старых записей: "
        f"{skipped_old}"
    )
    print(
        "Удалено возвратов и "
        "служебных типов: "
        f"{skipped_type}"
    )
    print(
        "Удалено дублей: "
        f"{skipped_duplicate}"
    )
    print(
        "Удалено некорректных записей: "
        f"{skipped_invalid}"
    )
    print(
        "Удалено нерелевантных записей: "
        f"{skipped_unrelated}"
    )
    print()
    print(
        "Файл создан: "
        "data/transfers-filtered-preview.json"
    )


if __name__ == "__main__":
    main()