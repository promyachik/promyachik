from pathlib import Path
import subprocess
import datetime
import re
import sys

PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = PROJECT / "var" / "promyachik_284_fix_goncalo_ramos_page_like_konate_cucurella_no_backup_report.txt"
TARGET = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
PUBLIC_TARGET = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"

REPORT.parent.mkdir(parents=True, exist_ok=True)
log = []

def add(line=""):
    log.append(str(line))

def finish(ok: bool):
    add("")
    add("DONE" if ok else "FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(0 if ok else 1)

add("PROMYACHIK 284 - FIX GONCALO RAMOS PAGE LIKE KONATE/CUCURELLA - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {PROJECT}")
add("")
add("RULE")
add("- Fix broken Goncalo Ramos transfer page structure.")
add("- Make profile blocks use the same field names/format as Konate and Cucurella.")
add("- Remove broken escaped literal lines from markdown body.")
add("- Do not create any backup folder or backup file.")
add("- No push.")
add("- No site opened.")
add("- Edit only content/transfers/goncalo-ramos-ac-milan/index.md")
add("")

if not TARGET.exists():
    add(f"ERROR: target file not found: {TARGET}")
    finish(False)

old_text = TARGET.read_text(encoding="utf-8", errors="ignore")
add(f"old_length: {len(old_text)}")
add(f"old_contains_escaped_player_image_tail: {'\\\\nplayer_image:' in old_text or '\\nplayer_image:' in old_text}")
add(f"old_contains_needs_cutout_true: {'needs_cutout: True' in old_text}")

front_matter = '''---
title: "Гонсалу Рамуш переходит в «Милан»: детали сделки с ПСЖ"
seo_title: "Гонсалу Рамуш → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Гонсалу Рамуш согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки, профиль игрока, гражданство, рабочая нога, стоимость и динамика стоимости."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T21:30:00+02:00
draft: false
type: "transfers"
layout: "single"
slug: "goncalo-ramos-ac-milan"
status: "agreement"
status_label: "СОГЛАСОВАНО"

player: "Gonçalo Ramos"
player_name: "Gonçalo Ramos"
full_name: "Gonçalo Matias Ramos"
player_initials: "GR"
player_id: 41585
api_player_id: 41585
player_slug: "goncalo-ramos"
shirt_number: "9"
player_image: "images/players/api/41585.png"
api_player_image: "images/players/api/41585.png"
cutout_player_image: "images/players/api/41585.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
api_photo_missing: false
needs_cutout: false

position: "Нападающий"
position_ru: "Нападающий"
main_position: "CF"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
nationality: "Португалия"
country: "Португалия"
player_country: "Португалия"
player_nationality: "Португалия"
country_code: "PT"
nationality_code: "PT"
nationality_flag: "images/flags/portugal.svg"
country_flag: "images/flags/portugal.svg"
flag: "images/flags/portugal.svg"
player_flag: "images/flags/portugal.svg"
player_country_flag: "images/flags/portugal.svg"
country_flag_image: "images/flags/portugal.svg"
flag_image: "images/flags/portugal.svg"
player_flag_image: "images/flags/portugal.svg"
player_country_flag_image: "images/flags/portugal.svg"
nationality_flag_image: "images/flags/portugal.svg"
preferred_foot: "Правая"
preferred_foot_ru: "Правая"
dominant_foot: "Правая"
working_foot: "Правая"
foot: "Правая"
foot_ru: "Правая"
height: "1.85 м"

from_club_id: 85
from_team_id: 85
from_id: 85
from_api_id: 85
old_club_id: 85
from_club_name: "Paris Saint-Germain"
from_team: "Paris Saint-Germain"
from_name: "Paris Saint-Germain"
from: "Paris Saint-Germain"
from_club: "Paris Saint-Germain"
old_club: "Paris Saint-Germain"
club_from: "Paris Saint-Germain"
source_club: "Paris Saint-Germain"
from_logo: "images/clubs/api/85.png"
from_club_logo: "images/clubs/api/85.png"
from_team_logo: "images/clubs/api/85.png"
from_crest: "images/clubs/api/85.png"
source_club_logo: "images/clubs/api/85.png"

# AC Milan API-Football id in the current local club database.
to_club_id: 489
to_team_id: 489
to_id: 489
to_api_id: 489
new_club_id: 489
to_club_name: "AC Milan"
to_team: "AC Milan"
to_name: "AC Milan"
to: "AC Milan"
to_club: "AC Milan"
new_club: "AC Milan"
club_to: "AC Milan"
target_club: "AC Milan"
to_logo: "images/clubs/api/489.png"
to_club_logo: "images/clubs/api/489.png"
to_team_logo: "images/clubs/api/489.png"
to_crest: "images/clubs/api/489.png"
target_club_logo: "images/clubs/api/489.png"
milan_logo: "images/clubs/api/489.png"

fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
source: "Fabrizio Romano"
source_name: "Fabrizio Romano"
source_url: ""
league: "Serie A"
market_value: "€30M"
market_value_display: "€30M"
value: "€30M"
market_value_url: "/players/goncalo-ramos/#market-value"
url: "/transfers/goncalo-ramos-ac-milan/"
link: "/transfers/goncalo-ramos-ac-milan/"
href: "/transfers/goncalo-ramos-ac-milan/"
permalink: "/transfers/goncalo-ramos-ac-milan/"
page_url: "/transfers/goncalo-ramos-ac-milan/"
show_in_top_ticker: true
show_in_footer_ticker: true

homepage_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
concept_art: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
hero_image: "/images/homepage/featured/goncalo-ramos-ac-milan-hero.png"
card_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"

previous_club_stats:
  label: "Paris Saint-Germain · сезон 2025/26"
  matches: "—"
  goals: "—"
  assists: "—"
  minutes: "—"
  yellow_cards: "—"
  red_cards: "—"
  season: "2025/26"
  source_note: "Данные будут заполнены после синхронизации API-Football."

market_value_chart:
  current_label: "€30M"
  updated_at: "2026"
  source_name: "Transfermarkt"
  source_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
  line_path: "M 8 82 L 24 68 L 40 52 L 56 38 L 72 18 L 88 48"
  area_path: "M 8 82 L 24 68 L 40 52 L 56 38 L 72 18 L 88 48 L 88 92 L 8 92 Z"
  points:
    - date: "2020"
      date_full: "2020"
      value_million: 8
      value_label: "€8M"
      x: 8
      y: 82
      club: "Benfica"
      club_logo: "/images/clubs/chart/benfica.svg"
    - date: "2021"
      date_full: "2021"
      value_million: 15
      value_label: "€15M"
      x: 24
      y: 68
      club: "Benfica"
      club_logo: "/images/clubs/chart/benfica.svg"
    - date: "2022"
      date_full: "2022"
      value_million: 25
      value_label: "€25M"
      x: 40
      y: 52
      club: "Benfica"
      club_logo: "/images/clubs/chart/benfica.svg"
    - date: "2023"
      date_full: "2023"
      value_million: 35
      value_label: "€35M"
      x: 56
      y: 38
      club: "Paris Saint-Germain"
      club_logo: "/images/clubs/api/85.png"
    - date: "2024"
      date_full: "2024"
      value_million: 50
      value_label: "€50M"
      x: 72
      y: 18
      club: "Paris Saint-Germain"
      club_logo: "/images/clubs/api/85.png"
    - date: "2026"
      date_full: "2026"
      value_million: 30
      value_label: "€30M"
      x: 88
      y: 48
      club: "Paris Saint-Germain"
      club_logo: "/images/clubs/api/85.png"

value_history:
  - year: "2020"
    value: "€8M"
  - year: "2021"
    value: "€15M"
  - year: "2022"
    value: "€25M"
  - year: "2023"
    value: "€35M"
  - year: "2024"
    value: "€50M"
  - year: "2026"
    value: "€30M"

keywords:
  - Gonçalo Ramos
  - Гонсалу Рамуш
  - AC Milan
  - Paris Saint-Germain
  - PSG
  - Fabrizio Romano
  - трансферы
  - Serie A
---
'''

body = '''
Гонсалу Рамуш готовится перейти из Paris Saint-Germain в AC Milan.

По информации Fabrizio Romano, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**. Для AC Milan это важное усиление атаки: португальский форвард добавляет команде новую опцию в штрафной и может быстро стать заметной частью проекта.

## Главные факты о трансфере Рамуша

- **Игрок:** Гонсалу Рамуш
- **Предыдущий клуб:** Paris Saint-Germain
- **Новый клуб:** AC Milan
- **Статус:** согласовано
- **Сумма:** €74M + add-ons
- **Позиция:** нападающий
- **Гражданство:** Португалия
- **Рабочая нога:** правая
- **Источник:** Fabrizio Romano

## Профиль игрока

Гонсалу Рамуш — португальский центральный нападающий. Его профиль на странице теперь приведён к тому же формату, что и у Конате и Кукурельи: фото игрока, гражданство, флаг, позиция, рабочая нога, возраст, рыночная стоимость, динамика стоимости и блок статистики берутся из стандартных полей страницы.

## Почему этот переход важен для AC Milan

Рамуш даёт «Милану» вариант классического форварда, который может играть в штрафной, открываться под передачи с флангов и завершать атаки первым касанием. Для команды это усиление глубины атаки и дополнительная конкуренция в линии нападения.

## Что дальше

После официального подтверждения страницу можно будет перевести из статуса «СОГЛАСОВАНО» в «ОФИЦИАЛЬНО» и обновить источник. Статистика по новому клубу пока не выдумывается: если актуальных данных нет, в блоке статистики используются прочерки.
'''.lstrip()

new_text = front_matter + body

# Safety checks before write.
required_tokens = [
    'layout: "single"',
    'player: "Gonçalo Ramos"',
    'position: "Нападающий"',
    'nationality: "Португалия"',
    'preferred_foot: "Правая"',
    'market_value: "€30M"',
    'previous_club_stats:',
    'market_value_chart:',
    'value_label: "€30M"',
]
missing = [t for t in required_tokens if t not in new_text]
if missing:
    add("ERROR: new content failed internal required token check")
    for t in missing:
        add(f"missing: {t}")
    finish(False)

TARGET.write_text(new_text, encoding="utf-8")
add(f"CHANGED: {TARGET}")
add(f"new_length: {len(new_text)}")
add("removed_broken_escaped_tail: yes")

proc = subprocess.run(["hugo", "-D"], cwd=PROJECT, capture_output=True, text=True, encoding="utf-8", errors="ignore")
add("")
add("HUGO")
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-2500:])
add("--- STDERR tail ---")
add(proc.stderr[-2500:])

add("")
add("TARGET CHECK")
add(f"target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
add(f"target_public_html_exists: {PUBLIC_TARGET.exists()}")

html_ok = False
checks = {}
if PUBLIC_TARGET.exists():
    html = PUBLIC_TARGET.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_player_name": "Gonçalo Ramos" in html or "Гонсалу Рамуш" in html,
        "has_birth_block": "Дата рождения" in html and "20.06.2001" in html,
        "has_age_block": "Возраст" in html and "25" in html,
        "has_nationality_block": "Гражданство" in html and "Португал" in html,
        "has_foot_block": "Рабочая нога" in html and "Правая" in html,
        "has_market_value_block": "Рыночная стоимость" in html and "€30M" in html,
        "has_stats_block": "МАТЧ" in html and "ГОЛ" in html,
        "has_chart_block": "player-market-chart" in html,
        "no_escaped_player_image_tail": "\\nplayer_image:" not in html and "player_image:" not in html,
    }
    for k, v in checks.items():
        add(f"{k}: {v}")
    html_ok = all(checks.values())
else:
    add("ERROR: target public html not found after hugo build")

ok = proc.returncode == 0 and html_ok
add(f"VERIFIED_OK: {ok}")
finish(ok)
