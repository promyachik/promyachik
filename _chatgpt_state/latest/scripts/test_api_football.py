from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://v3.football.api-sports.io/status"


def main() -> None:
    api_key = os.environ.get("API_FOOTBALL_KEY", "").strip()

    if not api_key:
        print("ОШИБКА: переменная API_FOOTBALL_KEY не установлена.")
        print("Сначала выполни команду export API_FOOTBALL_KEY='твой_ключ'")
        sys.exit(1)

    request = Request(
        API_URL,
        headers={
            "x-apisports-key": api_key,
            "User-Agent": "ProFutbik/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)

    except HTTPError as error:
        print(f"ОШИБКА API: HTTP {error.code}")
        print(error.read().decode("utf-8", errors="replace"))
        sys.exit(1)

    except URLError as error:
        print(f"ОШИБКА СОЕДИНЕНИЯ: {error.reason}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("ОШИБКА: API вернул ответ, который не является JSON.")
        sys.exit(1)

    errors = data.get("errors")

    if errors:
        print("API вернул ошибку:")
        print(json.dumps(errors, ensure_ascii=False, indent=2))
        sys.exit(1)

    status = data.get("response", {})

    if not isinstance(status, dict):
        print("Получен неожиданный ответ API:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        sys.exit(1)

    account = status.get("account", {})
    subscription = status.get("subscription", {})
    requests_info = status.get("requests", {})

    print("API-FOOTBALL ПОДКЛЮЧЁН УСПЕШНО")
    print()

    if account:
        print(f"Аккаунт: {account.get('firstname', 'не указано')}")

    if subscription:
        print(f"Тариф: {subscription.get('plan', 'не указан')}")
        print(f"Активен: {subscription.get('active', 'не указано')}")

    if requests_info:
        print(
            "Запросы сегодня: "
            f"{requests_info.get('current', '?')} "
            f"из {requests_info.get('limit_day', '?')}"
        )


if __name__ == "__main__":
    main()