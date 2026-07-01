from pathlib import Path
import subprocess
import datetime
import sys

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
CONTENT = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
REPORT = ROOT / "var" / "promyachik_285_fix_ramos_content_format_like_konate_cucurella_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 285 - FIX GONCALO RAMOS CONTENT FORMAT LIKE KONATE/CUCURELLA - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("")
log.append("RULE")
log.append("- Fix only Goncalo Ramos transfer content file.")
log.append("- Make front matter normal multiline YAML like Konate/Cucurella.")
log.append("- Restore player profile fields: citizenship, flag, foot, market value, stats, chart.")
log.append("- Do not touch CSS.")
log.append("- Do not touch JS.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

if not CONTENT.exists():
    log.append(f"ERROR: content file not found: {CONTENT}")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    sys.exit(1)

new_text = '''---
title: "Гонсалу Рамуш переходит в AC Milan из Paris Saint-Germain"
seo_title: "Гонсалу Рамуш → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Гонсалу Рамуш согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons, источник — Fabrizio Romano."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T21:45:00+02:00
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
shirt_number: "9"
player_id: 41585
player_slug: "goncalo-ramos"
player_image: "images/players/transfermarkt/goncalo-ramos-550550-black-v210.png"
api_player_image: "images/players/transfermarkt/goncalo-ramos-550550-black-v210.png"
cutout_player_image: "images/players/transfermarkt/goncalo-ramos-550550-black-v210.png"
player_image_source_name: "Transfermarkt"
player_image_source_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
player_image_background_removed: true
player_image_processor: "manual-black-background"
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
nationality_code: "PT"
country_code: "PT"
nationality_flag: "images/flags/portugal-v210.png"
country_flag_image: "images/flags/portugal-v210.png"
flag_image: "images/flags/portugal-v210.png"
player_flag_image: "images/flags/portugal-v210.png"
player_country_flag_image: "images/flags/portugal-v210.png"
nationality_flag_image: "images/flags/portugal-v210.png"
preferred_foot: "Правая"
preferred_foot_ru: "Правая"
dominant_foot: "Правая"
working_foot: "Правая"
height: "1.85 м"
from: "Paris Saint-Germain"
from_club: "Paris Saint-Germain"
from_team: "Paris Saint-Germain"
from_club_id: 85
from_club_name: "Paris Saint-Germain"
from_team_id: 85
from_logo: "images/clubs/api/85.png"
from_club_logo: "images/clubs/api/85.png"
to: "AC Milan"
to_club: "AC Milan"
to_team: "AC Milan"
to_club_id: 489
to_club_name: "AC Milan"
to_team_id: 489
to_logo: "images/clubs/api/489.png"
to_club_logo: "images/clubs/api/489.png"
fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
source: "Fabrizio Romano"
source_name: "Fabrizio Romano"
source_url: "https://x.com/FabrizioRomano"
market_value: "€30M"
market_value_display: "€30M"
market_value_url: "https://www.transfermarkt.com/goncalo-ramos/marktwertverlauf/spieler/550550"
league: "Serie A"
url: "/transfers/goncalo-ramos-ac-milan/"
link: "/transfers/goncalo-ramos-ac-milan/"
href: "/transfers/goncalo-ramos-ac-milan/"
permalink: "/transfers/goncalo-ramos-ac-milan/"
page_url: "/transfers/goncalo-ramos-ac-milan/"
homepage_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
concept_art: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
hero_image: "/images/homepage/featured/goncalo-ramos-ac-milan-hero.png"
card_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
show_in_top_ticker: true
show_in_footer_ticker: true
needs_cutout: false
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
  source_url: "https://www.transfermarkt.com/goncalo-ramos/marktwertverlauf/spieler/550550"
  line_path: "M 20 95 L 76 83 L 132 67 L 188 51 L 244 26 L 300 59"
  path: "M 20 95 L 76 83 L 132 67 L 188 51 L 244 26 L 300 59"
  area_path: "M 20 95 L 76 83 L 132 67 L 188 51 L 244 26 L 300 59 L 300 110 L 20 110 Z"
  points:
    - date: "2020"
      date_full: "2020"
      value_million: 8
      value_label: "€8M"
      x: 20
      y: 95
      club: "Benfica"
      club_logo: "images/clubs/chart/benfica.svg"
    - date: "2021"
      date_full: "2021"
      value_million: 15
      value_label: "€15M"
      x: 76
      y: 83
      club: "Benfica"
      club_logo: "images/clubs/chart/benfica.svg"
    - date: "2022"
      date_full: "2022"
      value_million: 25
      value_label: "€25M"
      x: 132
      y: 67
      club: "Benfica"
      club_logo: "images/clubs/chart/benfica.svg"
    - date: "2023"
      date_full: "2023"
      value_million: 35
      value_label: "€35M"
      x: 188
      y: 51
      club: "Benfica / PSG"
      club_logo: "images/clubs/chart/psg.svg"
    - date: "2024"
      date_full: "2024"
      value_million: 50
      value_label: "€50M"
      x: 244
      y: 26
      club: "Paris Saint-Germain"
      club_logo: "images/clubs/chart/psg.svg"
    - date: "2026"
      date_full: "2026"
      value_million: 30
      value_label: "€30M"
      x: 300
      y: 59
      club: "AC Milan"
      club_logo: "images/clubs/ac-milan.svg"
keywords:
  - Gonçalo Ramos
  - AC Milan
  - Paris Saint-Germain
  - PSG
  - Fabrizio Romano
  - трансферы
  - Serie A
---

Гонсалу Рамуш готовится перейти из Paris Saint-Germain в AC Milan. По информации Фабрицио Романо, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**.

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

Гонсалу Рамуш — португальский центральный нападающий. Его профиль на странице приведён к тому же рабочему формату, что у Конате и Кукурельи: фото игрока, гражданство, флаг, позиция, рабочая нога, возраст, рыночная стоимость, динамика стоимости и блок статистики берутся из стандартных полей страницы.

## Что Рамуш может дать AC Milan

Рамуш полезен в штрафной, умеет открываться между центральными защитниками и завершать атаки после передач с флангов. Для AC Milan это вариант усиления центральной зоны атаки и конкуренции за место основного форварда.

## Статус трансфера

На текущий момент страница использует статус **«СОГЛАСОВАНО»**. После официального объявления статус можно будет обновить без смены адреса страницы.
'''

old = CONTENT.read_text(encoding="utf-8", errors="ignore")
CONTENT.write_text(new_text, encoding="utf-8")
log.append(f"CHANGED: {CONTENT}")
log.append(f"old_length: {len(old)}")
log.append(f"new_length: {len(new_text)}")

checks = {
    "has_multiline_front_matter_start": new_text.startswith('---\n'),
    "has_multiline_front_matter_end": "\n---\n\n" in new_text,
    "has_nationality_portugal_ru": 'nationality: "Португалия"' in new_text,
    "has_preferred_foot_ru": 'preferred_foot: "Правая"' in new_text,
    "has_market_value_chart": "market_value_chart:" in new_text,
    "has_previous_club_stats": "previous_club_stats:" in new_text,
    "has_player_image": "player_image:" in new_text,
}
log.append("")
log.append("CONTENT CHECKS")
for k, v in checks.items():
    log.append(f"{k}: {v}")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2500:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2500:])

target = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
log.append(f"target_public_html_exists: {target.exists()}")
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    for token in ["Португалия", "Правая", "€30M", "player-market-chart", "transfer-player-stats", "Gonçalo Ramos"]:
        log.append(f"target_contains_{token}: {token in html}")

ok = proc.returncode == 0 and target.exists() and all(checks.values())
log.append("")
log.append(f"VERIFIED_OK: {ok}")
log.append("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
sys.exit(0 if ok else 1)
