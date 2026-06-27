from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import sys
import unicodedata
import zlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAYERS_FILE = PROJECT_ROOT / "data" / "playerdb" / "players.json"
PRIORITY_FILE = PROJECT_ROOT / "data" / "playerdb" / "pixelcut_priority.json"
PIXELCUT_SCRIPT = PROJECT_ROOT / "scripts" / "pixelcut_player_database_batch.py"
CUTOUT_DIR = PROJECT_ROOT / "static" / "images" / "players" / "cutout"
TRANSFERS_FILE = PROJECT_ROOT / "data" / "transfers.json"
TRANSFER_TEMPLATE = PROJECT_ROOT / "layouts" / "transfers" / "single.html"
FLAGS_DIR = PROJECT_ROOT / "static" / "images" / "flags"
REPORT_FILE = PROJECT_ROOT / "var" / "current_transfer_batch_report.json"
BUILD_DIR = PROJECT_ROOT / "var" / "current_transfer_batch_build"
BACKUP_ROOT = PROJECT_ROOT / "var" / "current_transfer_batch_backups"

NOW_ISO = datetime.now().astimezone().isoformat(timespec="seconds")


def spec(
    *,
    player: str,
    aliases: list[str],
    accepted_team_ids: list[int],
    slug: str,
    title: str,
    description: str,
    status: str,
    published: str,
    from_club_id: int,
    from_club_name: str,
    to_club_id: int,
    to_club_name: str,
    fee: str,
    position: str,
    birth_date: str,
    age: int,
    nationality: str,
    nationality_flag: str,
    preferred_foot: str,
    source_name: str,
    source_url: str,
    body: str,
) -> dict[str, Any]:
    return locals()


SPECS: list[dict[str, Any]] = [
    spec(
        player="Ibrahima Konaté",
        aliases=["Ibrahima Konaté", "Ibrahima Konate", "I. Konaté", "I. Konate"],
        accepted_team_ids=[40, 541],
        slug="ibrahima-konate-real-madrid",
        title="Ибраима Конате перешёл в «Реал»: контракт и детали трансфера",
        description="«Реал» официально объявил о переходе Ибраима Конате. Контракт защитника, дата объявления и главные детали трансфера из «Ливерпуля».",
        status="official",
        published="2026-06-18T12:00:00+02:00",
        from_club_id=40,
        from_club_name="Liverpool",
        to_club_id=541,
        to_club_name="Real Madrid",
        fee="Сумма не раскрывается",
        position="Центральный защитник",
        birth_date="25.05.1999",
        age=27,
        nationality="Франция",
        nationality_flag="images/flags/france.svg",
        preferred_foot="Правая",
        source_name="Real Madrid",
        source_url="https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-konate-18-06-2026",
        body='''Ибраима Конате **официально стал игроком мадридского «Реала» 18 июня 2026 года**. Испанский клуб сообщил, что французский центральный защитник подписал соглашение на четыре сезона — до 30 июня 2030 года.

До перехода Конате выступал за «Ливерпуль». В Мадриде защитник должен усилить центр обороны и добавить команде физическую мощь, скорость и опыт матчей высокого уровня.

## Главные факты о трансфере Конате

- **Игрок:** Ибраима Конате
- **Откуда перешёл:** «Ливерпуль»
- **Куда перешёл:** «Реал» Мадрид
- **Дата объявления:** 18 июня 2026 года
- **Контракт:** до 30 июня 2030 года
- **Позиция:** центральный защитник
- **Статус:** официально

## Какой контракт подписал Конате с «Реалом»

Официальное заявление «Реала» подтверждает соглашение на четыре сезона. Финансовые условия перехода клуб в публикации не раскрыл, поэтому указывать неподтверждённую сумму как факт неправильно.

## Зачем «Реалу» понадобился Конате

Конате способен играть в высокой линии обороны, выигрывать силовые единоборства и страховать пространство за спинами партнёров. Его опыт в английском футболе и международных турнирах делает переход важным для обновления оборонительной линии мадридцев.

## Трансфер Конате в «Реал» — официальный или слух

Переход имеет статус **«ОФИЦИАЛЬНО»**. Контракт и срок соглашения подтверждены [официальным сайтом «Реала»](https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-konate-18-06-2026).''',
    ),
    spec(
        player="Marc Cucurella",
        aliases=["Marc Cucurella", "M. Cucurella"],
        accepted_team_ids=[49, 541],
        slug="marc-cucurella-real-madrid",
        title="Марк Кукурелья перешёл в «Реал»: сумма и контракт до 2032 года",
        description="Марк Кукурелья официально перешёл из «Челси» в мадридский «Реал». Сумма сделки, срок контракта и детали трансфера защитника.",
        status="official",
        published="2026-06-15T12:00:00+02:00",
        from_club_id=49,
        from_club_name="Chelsea",
        to_club_id=541,
        to_club_name="Real Madrid",
        fee="€55 млн + €5 млн бонусами",
        position="Левый защитник",
        birth_date="22.07.1998",
        age=27,
        nationality="Испания",
        nationality_flag="images/flags/spain.svg",
        preferred_foot="Левая",
        source_name="Real Madrid",
        source_url="https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-cucurella-15-06-2026",
        body='''Марк Кукурелья **официально перешёл из «Челси» в мадридский «Реал» 15 июня 2026 года**. Испанский клуб объявил, что левый защитник подписал контракт на шесть сезонов — до 30 июня 2032 года.

По информации Фабрицио Романо, пакет сделки составил **55 миллионов евро плюс 5 миллионов возможных бонусов**.

## Главные факты о трансфере Кукурельи

- **Игрок:** Марк Кукурелья
- **Откуда перешёл:** «Челси»
- **Куда перешёл:** «Реал» Мадрид
- **Дата объявления:** 15 июня 2026 года
- **Срок контракта:** до 30 июня 2032 года
- **Сообщаемая сумма:** €55 млн + €5 млн бонусами
- **Статус:** официально

## Почему «Реал» выбрал Кукурелью

Кукурелья способен закрыть весь левый фланг, активно подключаться к атаке и поддерживать высокий темп прессинга. Он также может играть в более узкой роли и помогать команде при выходе из обороны.

## Сколько «Реал» заплатил за Кукурелью

Официальное заявление клубов подтверждает сам переход и шестилетний контракт. Детализацию суммы сообщил Фабрицио Романо: €55 млн гарантированной выплаты и ещё €5 млн в виде бонусов.

## Трансфер Кукурельи — официальный или слух

Переход имеет статус **«ОФИЦИАЛЬНО»** и подтверждён [официальным сайтом «Реала»](https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-cucurella-15-06-2026).''',
    ),
    spec(
        player="Denzel Dumfries",
        aliases=["Denzel Dumfries", "D. Dumfries"],
        accepted_team_ids=[505, 541],
        slug="denzel-dumfries-real-madrid",
        title="Дензел Дюмфрис подписал контракт с «Реалом»: последние детали",
        description="Дензел Дюмфрис прошёл медосмотр и подписал четырёхлетний контракт с «Реалом». Что известно о переходе защитника из «Интера».",
        status="confirmed",
        published="2026-06-09T10:00:00+02:00",
        from_club_id=505,
        from_club_name="Inter",
        to_club_id=541,
        to_club_name="Real Madrid",
        fee="Сумма не раскрывается",
        position="Правый защитник",
        birth_date="18.04.1996",
        age=30,
        nationality="Нидерланды",
        nationality_flag="images/flags/netherlands.svg",
        preferred_foot="Правая",
        source_name="Fabrizio Romano",
        source_url="https://x.com/FabrizioRomano/status/2064229756812636414",
        body='''Дензел Дюмфрис прошёл медицинское обследование и **подписал четырёхлетний контракт с мадридским «Реалом»**, сообщил Фабрицио Романо 9 июня 2026 года.

На момент последнего обновления отдельного официального заявления «Реала» о трансфере на сайте клуба не было, поэтому история получает статус **«ПОДТВЕРЖДЕНО»**, а не «официально».

## Что известно о переходе Дюмфриса

- **Игрок:** Дензел Дюмфрис
- **Текущий клуб в истории:** «Интер»
- **Новый клуб:** «Реал» Мадрид
- **Контракт:** четыре года
- **Медосмотр:** пройден
- **Источник:** Фабрицио Романо
- **Статус:** подтверждено

## Почему Дюмфрис интересен «Реалу»

Нидерландский защитник сочетает скорость, физическую мощь и активную игру в атаке. Он привык действовать по всей правой бровке и способен давать ширину даже при схеме с тремя центральными защитниками.

## Когда трансфер станет официальным

Для статуса «ОФИЦИАЛЬНО» необходимо отдельное заявление клуба. После публикации такого сообщения эта же страница будет обновлена — без создания дубликата.

## Источник информации

Подписание контракта и прохождение медосмотра сообщил [Фабрицио Романо](https://x.com/FabrizioRomano/status/2064229756812636414).''',
    ),
    spec(
        player="Julián Álvarez",
        aliases=["Julián Álvarez", "Julian Alvarez", "J. Álvarez", "J. Alvarez"],
        accepted_team_ids=[530, 529],
        slug="julian-alvarez-barcelona",
        title="«Барселона» сделала предложение по Хулиану Альваресу: что известно",
        description="«Барселона» начала переговоры о трансфере Хулиана Альвареса из «Атлетико». Сумма первого предложения и текущий статус сделки.",
        status="negotiations",
        published="2026-05-29T12:00:00+02:00",
        from_club_id=530,
        from_club_name="Atletico Madrid",
        to_club_id=529,
        to_club_name="Barcelona",
        fee="Предложение €100 млн",
        position="Нападающий",
        birth_date="31.01.2000",
        age=26,
        nationality="Аргентина",
        nationality_flag="images/flags/argentina.svg",
        preferred_foot="Правая",
        source_name="Fabrizio Romano",
        source_url="https://x.com/FabrizioRomano/status/2060298651436535963",
        body='''«Барселона» направила «Атлетико» первое официальное предложение по Хулиану Альваресу на сумму **100 миллионов евро**, сообщил Фабрицио Романо 29 мая 2026 года.

Аргентинский нападающий рассматривает переход в каталонский клуб как приоритетный вариант, однако официального соглашения между клубами пока не объявлено. Поэтому текущий статус истории — **«ПЕРЕГОВОРЫ»**.

## Главные факты по возможному трансферу Альвареса

- **Игрок:** Хулиан Альварес
- **Текущий клуб:** «Атлетико» Мадрид
- **Заинтересованный клуб:** «Барселона»
- **Первое предложение:** €100 млн
- **Позиция игрока:** переход в «Барселону» является приоритетом
- **Статус:** переговоры

## Согласовал ли Альварес контракт с «Барселоной»

На данный момент клубы не публиковали официального сообщения о завершении сделки. Информация касается предложения и переговорного процесса, а не окончательно оформленного трансфера.

## Почему «Барселоне» нужен Альварес

Альварес способен играть центрального нападающего, смещаться в глубину и участвовать в прессинге. Его универсальность позволяет использовать футболиста как основную девятку или как мобильного форварда рядом с другим нападающим.

## Что будет дальше

Эта страница будет обновляться по мере изменения статуса: переговоры, возможное соглашение и официальное объявление. Первое предложение подтвердил [Фабрицио Романо](https://x.com/FabrizioRomano/status/2060298651436535963).''',
    ),
    spec(
        player="Elliot Anderson",
        aliases=["Elliot Anderson", "E. Anderson"],
        accepted_team_ids=[65, 50],
        slug="elliot-anderson-manchester-city",
        title="Эллиот Андерсон переходит в «Манчестер Сити»: сумма сделки",
        description="«Манчестер Сити» согласовал трансфер Эллиота Андерсона из «Ноттингем Форест». Сумма £116 млн, медосмотр и статус сделки.",
        status="agreement",
        published="2026-06-25T23:00:00+02:00",
        from_club_id=65,
        from_club_name="Nottingham Forest",
        to_club_id=50,
        to_club_name="Manchester City",
        fee="£116 млн",
        position="Центральный полузащитник",
        birth_date="06.11.2002",
        age=23,
        nationality="Англия",
        nationality_flag="images/flags/england.svg",
        preferred_foot="Правая",
        source_name="Fabrizio Romano",
        source_url="https://x.com/FabrizioRomano/status/2070259614206017553",
        body='''«Манчестер Сити» и «Ноттингем Форест» **согласовали трансфер Эллиота Андерсона за 116 миллионов фунтов**, сообщил Фабрицио Романо 25 июня 2026 года.

Игрок должен пройти медицинское обследование, после чего клуб сможет завершить формальности и сделать официальное объявление. Текущий статус истории — **«СОГЛАСОВАНО»**.

## Главные факты о трансфере Андерсона

- **Игрок:** Эллиот Андерсон
- **Откуда переходит:** «Ноттингем Форест»
- **Куда переходит:** «Манчестер Сити»
- **Сумма:** £116 млн
- **Медосмотр:** назначен
- **Статус:** согласовано

## Почему «Сити» выбрал Андерсона

Андерсон способен играть в центре поля, продвигать мяч под давлением и выполнять большой объём работы без мяча. Его возраст позволяет рассматривать сделку как долгосрочное усиление полузащиты.

## Трансфер уже официальный?

Нет. Соглашение между клубами достигнуто, но для статуса «ОФИЦИАЛЬНО» нужно клубное объявление после завершения медицинских и контрактных формальностей.

## Источник информации

О достигнутом соглашении и сумме сделки сообщил [Фабрицио Романо](https://x.com/FabrizioRomano/status/2070259614206017553).''',
    ),
    spec(
        player="Bernardo Silva",
        aliases=["Bernardo Silva", "B. Silva"],
        accepted_team_ids=[50, 541],
        slug="bernardo-silva-real-madrid",
        title="Бернарду Силва перешёл в «Реал»: контракт до 2028 года",
        description="«Реал» официально объявил о переходе Бернарду Силвы. Срок контракта, дата трансфера и роль португальского полузащитника.",
        status="official",
        published="2026-06-17T12:00:00+02:00",
        from_club_id=50,
        from_club_name="Manchester City",
        to_club_id=541,
        to_club_name="Real Madrid",
        fee="Сумма не раскрывается",
        position="Атакующий полузащитник",
        birth_date="10.08.1994",
        age=31,
        nationality="Португалия",
        nationality_flag="images/flags/portugal.svg",
        preferred_foot="Левая",
        source_name="Real Madrid",
        source_url="https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-bernardo-silva-17-06-2026",
        body='''Бернарду Силва **официально стал игроком мадридского «Реала» 17 июня 2026 года**. Клуб объявил о контракте на два сезона — до 30 июня 2028 года.

Португальский полузащитник перешёл после длительного периода в «Манчестер Сити», где играл в центре поля и на правом фланге атаки.

## Главные факты о трансфере Бернарду Силвы

- **Игрок:** Бернарду Силва
- **Предыдущий клуб:** «Манчестер Сити»
- **Новый клуб:** «Реал» Мадрид
- **Дата объявления:** 17 июня 2026 года
- **Контракт:** до 30 июня 2028 года
- **Статус:** официально

## Какую роль Бернарду может получить в «Реале»

Бернарду способен играть правее в атаке, в центральной зоне и глубже в полузащите. Его контроль мяча, движение между линиями и опыт больших матчей дают тренерскому штабу несколько тактических вариантов.

## Сколько «Реал» заплатил за Бернарду Силву

В официальном заявлении сумма не указана. Поэтому страница не выдаёт неподтверждённые финансовые оценки за установленный факт.

## Трансфер Бернарду Силвы — официальный или слух

Переход имеет статус **«ОФИЦИАЛЬНО»**. Срок контракта подтверждён [официальным сайтом «Реала»](https://www.realmadrid.com/en-US/news/club/announcements/comunicado-oficial-bernardo-silva-17-06-2026).''',
    ),
]


FLAG_SVGS: dict[str, str] = {
    "france.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><path fill="#0055a4" d="M0 0h1v2H0z"/><path fill="#fff" d="M1 0h1v2H1z"/><path fill="#ef4135" d="M2 0h1v2H2z"/></svg>''',
    "spain.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><path fill="#aa151b" d="M0 0h3v.5H0zM0 1.5h3V2H0z"/><path fill="#f1bf00" d="M0 .5h3v1H0z"/></svg>''',
    "netherlands.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><path fill="#ae1c28" d="M0 0h3v.667H0z"/><path fill="#fff" d="M0 .667h3v.666H0z"/><path fill="#21468b" d="M0 1.333h3V2H0z"/></svg>''',
    "argentina.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><path fill="#74acdf" d="M0 0h3v.667H0zM0 1.333h3V2H0z"/><path fill="#fff" d="M0 .667h3v.666H0z"/><circle cx="1.5" cy="1" r=".16" fill="#f6b40e"/></svg>''',
    "england.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 5 3"><path fill="#fff" d="M0 0h5v3H0z"/><path fill="#ce1124" d="M2 0h1v3H2zM0 1h5v1H0z"/></svg>''',
    "portugal.svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3 2"><path fill="#046a38" d="M0 0h1.2v2H0z"/><path fill="#da291c" d="M1.2 0H3v2H1.2z"/><circle cx="1.2" cy="1" r=".24" fill="#ffcd00"/></svg>''',
}


def normalize(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(character)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def player_team_id(player: dict[str, Any]) -> int | None:
    team = player.get("team") or {}
    try:
        return int(team.get("id"))
    except (TypeError, ValueError):
        return None


def player_names(player: dict[str, Any]) -> set[str]:
    names = {
        normalize(player.get("name")),
        normalize(
            f"{player.get('firstname') or ''} {player.get('lastname') or ''}"
        ),
    }
    return {name for name in names if name}


def resolve_player(players: list[dict[str, Any]], item: dict[str, Any]) -> dict[str, Any]:
    aliases = {normalize(alias) for alias in item["aliases"]}
    scored: list[tuple[int, dict[str, Any]]] = []

    for player in players:
        names = player_names(player)
        if not names.intersection(aliases):
            continue

        score = 100
        team_id = player_team_id(player)
        if team_id in item["accepted_team_ids"]:
            score += 20
        if normalize(player.get("name")) == normalize(item["player"]):
            score += 5
        scored.append((score, player))

    if not scored:
        raise RuntimeError(
            f"Игрок не найден в players.json: {item['player']}"
        )

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score = scored[0][0]
    best = [player for score, player in scored if score == best_score]

    if len(best) != 1:
        ids = ", ".join(str(player.get("id")) for player in best)
        raise RuntimeError(
            f"Неоднозначное совпадение для {item['player']}: {ids}"
        )

    return best[0]


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def png_has_real_transparency(path: Path) -> bool:
    try:
        raw = path.read_bytes()
    except OSError:
        return False

    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return False

    offset = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    trns = b""

    while offset + 12 <= len(raw):
        length = struct.unpack(">I", raw[offset:offset + 4])[0]
        chunk_type = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", data
            )
        elif chunk_type == b"IDAT":
            idat.extend(data)
        elif chunk_type == b"tRNS":
            trns = data
        elif chunk_type == b"IEND":
            break

    if color_type == 3:
        return any(alpha < 255 for alpha in trns)
    if color_type == 2:
        return bool(trns)
    if color_type not in (4, 6):
        return False
    if bit_depth != 8 or interlace != 0 or not idat or not width or not height:
        return False

    channels = 2 if color_type == 4 else 4
    stride = width * channels

    try:
        decoded = zlib.decompress(bytes(idat))
    except zlib.error:
        return False

    expected = height * (stride + 1)
    if len(decoded) < expected:
        return False

    previous = bytearray(stride)
    position = 0

    for _ in range(height):
        filter_type = decoded[position]
        position += 1
        scanline = bytearray(decoded[position:position + stride])
        position += stride

        for index in range(stride):
            left = scanline[index - channels] if index >= channels else 0
            up = previous[index]
            up_left = previous[index - channels] if index >= channels else 0

            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 0xFF
            elif filter_type == 2:
                scanline[index] = (scanline[index] + up) & 0xFF
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                scanline[index] = (
                    scanline[index] + paeth(left, up, up_left)
                ) & 0xFF
            elif filter_type != 0:
                return False

        alpha_offset = 1 if color_type == 4 else 3
        if any(scanline[index] < 250 for index in range(alpha_offset, stride, channels)):
            return True

        previous = scanline

    return False


def patch_nationality_flag_support(template: str) -> str:
    if "PROFUTBIK_NATIONALITY_FLAG_SUPPORT" in template:
        return template

    start = '''                                    {{ if eq . "Франция" }}'''
    end = '''                                    {{ end }}

                                </span>'''

    start_index = template.find(start)
    if start_index < 0:
        raise RuntimeError("Не найден блок флага Франции в шаблоне.")

    end_index = template.find(end, start_index)
    if end_index < 0:
        raise RuntimeError("Не найден конец блока гражданства в шаблоне.")

    existing = template[start_index:end_index + len("                                    {{ end }}")]
    existing = existing.replace(
        '{{ if eq . "Франция" }}',
        '{{ if eq $nationalityLabel "Франция" }}',
        1,
    ).replace(
        '{{ else if eq . "Германия" }}',
        '{{ else if eq $nationalityLabel "Германия" }}',
        1,
    ).replace(
        '{{ . }}',
        '{{ $nationalityLabel }}',
        1,
    )

    replacement = '''                                    {{/* PROFUTBIK_NATIONALITY_FLAG_SUPPORT */}}
                                    {{ with $page.Params.nationality_flag }}

                                        <img
                                            class="player-brief__flag-svg"
                                            src="{{ . | relURL }}"
                                            alt="Флаг {{ $nationalityLabel }}"
                                            loading="lazy"
                                        >

                                    {{ else }}

''' + existing + '''

                                    {{ end }}'''

    return template[:start_index] + replacement + template[end_index + len("                                    {{ end }}"):]


def render_page(item: dict[str, Any], player_id: int) -> str:
    initials = "".join(part[0] for part in item["player"].split()[:2]).upper()
    frontmatter = f'''---
title: "{item['title'].replace('"', '\\"')}"
description: "{item['description'].replace('"', '\\"')}"
date: {item['published']}
lastmod: {NOW_ISO}
draft: false
type: "transfers"
layout: "single"

status: "{item['status']}"
player: "{item['player']}"
player_initials: "{initials}"
player_id: {player_id}
player_image: "images/players/cutout/{player_id}.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/{player_id}.png"
player_image_background_removed: true
player_image_processor: "Pixelcut"
position: "{item['position']}"
age: {item['age']}
age_at_transfer: {item['age']}
birth_date: "{item['birth_date']}"
nationality: "{item['nationality']}"
nationality_flag: "{item['nationality_flag']}"
preferred_foot: "{item['preferred_foot']}"

from_club_id: {item['from_club_id']}
from_club_name: "{item['from_club_name']}"
to_club_id: {item['to_club_id']}
to_club_name: "{item['to_club_name']}"

fee: "{item['fee']}"
source_name: "{item['source_name']}"
source_url: "{item['source_url']}"
---

'''
    return frontmatter + item["body"].strip() + "\n"


def backup_paths(paths: list[Path]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    for path in paths:
        if not path.exists():
            continue
        relative = path.resolve().relative_to(PROJECT_ROOT.resolve())
        destination = backup_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, destination)
        else:
            shutil.copy2(path, destination)

    return backup_dir


def restore_paths(backup_dir: Path, generated_page_dirs: list[Path]) -> None:
    for page_dir in generated_page_dirs:
        if page_dir.exists():
            shutil.rmtree(page_dir)

    for source in backup_dir.rglob("*"):
        if source.is_dir():
            continue
        relative = source.relative_to(backup_dir)
        destination = PROJECT_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_hugo_validation() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    command = [
        "hugo",
        "--minify",
        "--destination",
        str(BUILD_DIR),
        "--baseURL",
        "http://127.0.0.1:1313/promyachik/",
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Проверка Hugo завершилась ошибкой:\n"
            + result.stdout
            + "\n"
            + result.stderr
        )


def main() -> None:
    required = [PLAYERS_FILE, PRIORITY_FILE, PIXELCUT_SCRIPT, TRANSFERS_FILE, TRANSFER_TEMPLATE]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Не найдены обязательные файлы:\n" + "\n".join(missing))

    payload = read_json(PLAYERS_FILE)
    players = payload.get("items") or []
    if not isinstance(players, list):
        raise RuntimeError('players.json не содержит список "items".')

    resolved: dict[str, dict[str, Any]] = {}
    print("Проверка игроков в локальной базе:")
    for item in SPECS:
        player = resolve_player(players, item)
        player_id = int(player["id"])
        resolved[item["player"]] = player
        team = player.get("team") or {}
        print(
            f"  OK: {item['player']} -> ID {player_id} | "
            f"{team.get('name') or '-'}"
        )

    old_priority = PRIORITY_FILE.read_bytes()
    pending_ids: list[int] = []

    for item in SPECS:
        player = resolved[item["player"]]
        player_id = int(player["id"])
        cutout = CUTOUT_DIR / f"{player_id}.png"

        if png_has_real_transparency(cutout):
            player["photo_cutout"] = f"images/players/cutout/{player_id}.png"
            player["background_removed"] = True
            continue

        player["photo_cutout"] = None
        player["background_removed"] = False
        player.pop("pixelcut", None)
        if cutout.exists():
            cutout.unlink()
        pending_ids.append(player_id)

    payload["items"] = players
    payload["count"] = len(players)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_json(PLAYERS_FILE, payload)

    try:
        if pending_ids:
            write_json(
                PRIORITY_FILE,
                {
                    "description": "Current ProFutbik transfer batch: verified transparent cutouts only.",
                    "items": pending_ids,
                },
            )
            print()
            print("Pixelcut: удаление фона для ID:", ", ".join(map(str, pending_ids)))
            result = subprocess.run(
                [sys.executable, str(PIXELCUT_SCRIPT), "--limit", str(len(pending_ids))],
                cwd=PROJECT_ROOT,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Pixelcut завершился с кодом {result.returncode}."
                )
        else:
            print("Pixelcut: все шесть прозрачных фотографий уже готовы.")
    finally:
        PRIORITY_FILE.write_bytes(old_priority)

    payload = read_json(PLAYERS_FILE)
    players_by_id = {
        int(player["id"]): player
        for player in payload.get("items") or []
        if isinstance(player, dict) and player.get("id") is not None
    }

    invalid: list[str] = []
    for item in SPECS:
        player_id = int(resolved[item["player"]]["id"])
        cutout = CUTOUT_DIR / f"{player_id}.png"
        record = players_by_id.get(player_id) or {}
        if not png_has_real_transparency(cutout):
            invalid.append(f"{item['player']}: нет реальной прозрачности ({cutout})")
        elif not record.get("background_removed"):
            invalid.append(f"{item['player']}: players.json не подтверждает обработку")

    if invalid:
        raise RuntimeError(
            "Проверка прозрачности не пройдена:\n" + "\n".join(invalid)
        )

    page_dirs = [PROJECT_ROOT / "content" / "transfers" / item["slug"] for item in SPECS]
    backup_dir = backup_paths([TRANSFERS_FILE, TRANSFER_TEMPLATE, *page_dirs])

    try:
        FLAGS_DIR.mkdir(parents=True, exist_ok=True)
        for filename, svg in FLAG_SVGS.items():
            (FLAGS_DIR / filename).write_text(svg + "\n", encoding="utf-8")

        template = TRANSFER_TEMPLATE.read_text(encoding="utf-8-sig")
        TRANSFER_TEMPLATE.write_text(
            patch_nationality_flag_support(template),
            encoding="utf-8",
        )

        current_transfers = read_json(TRANSFERS_FILE)
        if not isinstance(current_transfers, list):
            raise RuntimeError("data/transfers.json должен содержать список.")

        target_names = {normalize(item["player"]) for item in SPECS}
        preserved = [
            entry
            for entry in current_transfers
            if normalize(entry.get("player")) not in target_names
        ]

        new_entries: list[dict[str, Any]] = []
        report_items: list[dict[str, Any]] = []

        for item in SPECS:
            player_id = int(resolved[item["player"]]["id"])
            page_dir = PROJECT_ROOT / "content" / "transfers" / item["slug"]
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.md").write_text(
                render_page(item, player_id),
                encoding="utf-8",
            )

            new_entries.append(
                {
                    "status": item["status"],
                    "player": item["player"],
                    "from_club_id": item["from_club_id"],
                    "from_club_name": item["from_club_name"],
                    "to_club_id": item["to_club_id"],
                    "to_club_name": item["to_club_name"],
                    "fee": item["fee"],
                    "url": f"transfers/{item['slug']}/",
                    "player_image": f"images/players/cutout/{player_id}.png",
                    "player_id": player_id,
                    "player_image_source_name": "API-Football",
                    "player_image_source_url": f"https://media.api-sports.io/football/players/{player_id}.png",
                    "player_image_background_removed": True,
                    "player_image_processor": "Pixelcut",
                }
            )

            report_items.append(
                {
                    "player": item["player"],
                    "player_id": player_id,
                    "status": item["status"],
                    "page": f"content/transfers/{item['slug']}/index.md",
                    "url": f"http://127.0.0.1:1313/promyachik/transfers/{item['slug']}/",
                    "cutout": f"static/images/players/cutout/{player_id}.png",
                }
            )

        write_json(TRANSFERS_FILE, new_entries + preserved)
        run_hugo_validation()

        report = {
            "generated_at": NOW_ISO,
            "backup": str(backup_dir),
            "count": len(report_items),
            "items": report_items,
        }
        write_json(REPORT_FILE, report)

    except Exception:
        restore_paths(backup_dir, page_dirs)
        raise

    print()
    print("DONE")
    print("Создано страниц:", len(SPECS))
    for item in SPECS:
        print(
            "  http://127.0.0.1:1313/promyachik/transfers/"
            + item["slug"]
            + "/"
        )
    print()
    print("Бегущая строка обновлена теми же ID и cutout-файлами.")
    print("Проверка Hugo пройдена без ошибок.")
    print("Отчёт:", REPORT_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("ERROR:", error)
        sys.exit(1)
