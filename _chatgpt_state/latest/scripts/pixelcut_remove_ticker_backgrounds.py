from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
TRANSFERS_FILE = PROJECT_ROOT / "data" / "transfers.json"
PIXELCUT_URL = "https://api.developer.pixelcut.ai/v1/remove-background"

REQUEST_DELAY_SECONDS = 2
MAX_ATTEMPTS = 2
RATE_LIMIT_WAIT_SECONDS = 65


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


def pixelcut_remove_background(
    api_key: str,
    image_url: str,
) -> str:
    payload = json.dumps(
        {
            "image_url": image_url,
            "format": "png",
            "crop": False,
        }
    ).encode("utf-8")

    request = Request(
        PIXELCUT_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-KEY": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            result = json.load(response)

    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Pixelcut HTTP {error.code}: {body}") from error

    except URLError as error:
        raise RuntimeError(
            f"Ошибка соединения с Pixelcut: {error.reason}"
        ) from error

    result_url = str(result.get("result_url") or "").strip()

    if not result_url:
        raise RuntimeError(
            f"Pixelcut не вернул result_url: {result}"
        )

    return result_url


def call_pixelcut_with_retry(
    api_key: str,
    image_url: str,
) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return pixelcut_remove_background(
                api_key,
                image_url,
            )
        except RuntimeError as error:
            if "HTTP 429" in str(error) and attempt < MAX_ATTEMPTS:
                print("  Достигнут лимит Pixelcut.")
                print(
                    f"  Ожидание {RATE_LIMIT_WAIT_SECONDS} секунд..."
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                continue

            raise

    raise RuntimeError("Не удалось обработать изображение через Pixelcut.")


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
        destination.suffix + ".pixelcut.part"
    )

    try:
        with urlopen(request, timeout=90) as response:
            image_data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"Скачивание результата: HTTP {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "Скачивание результата: ошибка соединения: "
            f"{error.reason}"
        ) from error

    if len(image_data) < 500:
        raise RuntimeError(
            "Pixelcut вернул пустой или повреждённый PNG."
        )

    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(image_data)
    temporary.replace(destination)


def main() -> None:
    load_env()

    pixelcut_key = os.environ.get(
        "PIXELCUT_API_KEY",
        "",
    ).strip()

    if not pixelcut_key:
        print("ОШИБКА: в .env нет PIXELCUT_API_KEY.")
        print()
        print("Добавь в C:\\Users\\Dmitrii\\Promyachik\\.env строку:")
        print("PIXELCUT_API_KEY=твой_ключ_Pixelcut")
        sys.exit(1)

    transfers = load_transfers()

    backup_dir = PROJECT_ROOT / "backups" / "pixelcut"
    backup_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    failed: list[str] = []

    print("Удаление фона через Pixelcut API")
    print(f"Записей: {len(transfers)}")
    print()

    for number, transfer in enumerate(transfers, start=1):
        if not isinstance(transfer, dict):
            continue

        player_name = str(transfer.get("player") or "").strip()
        source_url = str(
            transfer.get("player_image_source_url") or ""
        ).strip()
        local_relative = str(
            transfer.get("player_image") or ""
        ).strip()

        print(f"[{number}/{len(transfers)}] {player_name}")

        if not source_url:
            print("  ОШИБКА: нет player_image_source_url из API-Football.")
            failed.append(player_name or f"запись {number}")
            continue

        if not local_relative:
            print("  ОШИБКА: нет player_image.")
            failed.append(player_name or f"запись {number}")
            continue

        destination = PROJECT_ROOT / "static" / Path(local_relative)

        if not destination.exists():
            print(
                "  ПРЕДУПРЕЖДЕНИЕ: локальный файл не найден, "
                "Pixelcut всё равно обработает URL из API-Football."
            )
        else:
            backup_file = backup_dir / destination.name

            if not backup_file.exists():
                backup_file.write_bytes(destination.read_bytes())

        try:
            result_url = call_pixelcut_with_retry(
                pixelcut_key,
                source_url,
            )

            download_png(
                result_url,
                destination,
            )

            transfer["player_image_background_removed"] = True
            transfer["player_image_processor"] = "Pixelcut"
            transfer["player_image_pixelcut_result_url"] = result_url

            processed += 1

            print(f"  Готово: {local_relative}")

        except RuntimeError as error:
            print(f"  ОШИБКА: {error}")
            failed.append(player_name or f"запись {number}")

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
    print(f"ГОТОВО. Обработано Pixelcut: {processed}")

    if failed:
        print("Не удалось обработать: " + ", ".join(failed))
        sys.exit(2)

    print("Фон удалён у всех фотографий.")
    print("Файлы заменены в static/images/players/api/")
    print("data/transfers.json обновлён.")


if __name__ == "__main__":
    main()
