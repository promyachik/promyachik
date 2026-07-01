from pathlib import Path
import re
import subprocess
import datetime

ROOT = Path.cwd()
REPORT = ROOT / "var" / "promyachik_286_rebuild_ramos_from_working_page_schema_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)
log = []

def add(s=""):
    log.append(str(s))

def fail(msg):
    add("FAILED")
    add("ERROR: " + msg)
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise SystemExit(1)

add("PROMYACHIK 286 - REBUILD RAMOS FROM WORKING PAGE SCHEMA - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {ROOT}")
add("")
add("RULE")
add("- Rebuild only Ramos transfer content against the same working field schema as Konate/Cucurella.")
add("- Add a minimal template guard to prevent the old legacy static chart duplicate on pages that opt out.")
add("- Do not create any backup folder or backup file.")
add("- No push.")
add("- No site opened.")
add("")

ramos = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
konate = ROOT / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
cucurella = ROOT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"
layout = ROOT / "layouts" / "transfers" / "single.html"

for p in [ramos, konate, cucurella, layout]:
    add(f"exists {p.relative_to(ROOT)}: {p.exists()}")
    if not p.exists():
        fail(f"required file missing: {p}")

konate_text = konate.read_text(encoding="utf-8", errors="ignore")
cucurella_text = cucurella.read_text(encoding="utf-8", errors="ignore")
old_ramos_text = ramos.read_text(encoding="utf-8", errors="ignore")
layout_text = layout.read_text(encoding="utf-8", errors="ignore")

schema_tokens = [
    "player_image", "player_id", "position", "birth_date", "nationality", "nationality_flag",
    "preferred_foot", "from_club_id", "to_club_id", "previous_club_stats"
]
add("")
add("WORKING PAGE SCHEMA CHECK")
for token in schema_tokens:
    add(f"Konate has {token}: {token in konate_text}")
    add(f"Cucurella has {token}: {token in cucurella_text}")

bad_tokens_before = ["\\nplayer_image", "country_flag:", "preferred_foot: \"Right\"", "Centre-Forward", "market_value_chart: current_label"]
add("")
add("RAMOS OLD STATE CHECK")
for token in bad_tokens_before:
    add(f"old Ramos contains {token!r}: {token in old_ramos_text}")

new_ramos = r"""---
title: "Gonçalo Ramos переходит в AC Milan из Paris Saint-Germain"
seo_title: "Gonçalo Ramos → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Gonçalo Ramos согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons, источник — Fabrizio Romano."
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
player_id: 41585
player_slug: "goncalo-ramos"
player_image: "images/players/api/41585.png"
api_player_image: "images/players/api/41585.png"
player_image_source_name: "Transfermarkt"
player_image_source_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
player_image_background_removed: false

position: "Нападающий"
main_position: "CF"
shirt_number: "9"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
height: "1.85 м"
nationality: "Португалия"
nationality_flag: "images/flags/portugal.svg"
preferred_foot: "Правая"
market_value: "€30M"
market_value_display: "€30M"
market_value_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"

from_club_id: 85
from_club_name: "Paris Saint-Germain"
from_club_logo: "images/clubs/api/85.png"
to_club_id: 489
to_club_name: "AC Milan"
to_club_logo: "images/clubs/api/489.png"
from: "Paris Saint-Germain"
from_club: "Paris Saint-Germain"
to: "AC Milan"
to_club: "AC Milan"
fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
league: "Serie A"
source_name: "Fabrizio Romano"
source_url: ""

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

# Ramos keeps one working chart and skips the old duplicate static chart.
disable_legacy_static_market_chart: true
market_value_chart:
  current_label: "€30M"
  updated_at: "2026"
  source_name: "Transfermarkt"
  source_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
  line_path: "M 10.00 74.08 L 26.00 65.40 L 42.00 53.00 L 58.00 40.60 L 74.00 22.00 L 90.00 46.80"
  path: "M 10.00 74.08 L 26.00 65.40 L 42.00 53.00 L 58.00 40.60 L 74.00 22.00 L 90.00 46.80"
  area_path: "M 10.00 74.08 L 26.00 65.40 L 42.00 53.00 L 58.00 40.60 L 74.00 22.00 L 90.00 46.80 L 90.00 100 L 10.00 100 Z"
  points:
    - date: "2020"
      date_label: "2020"
      value_label: "€8M"
      value: "€8M"
      value_number: 8
      x: 10.00
      y: 74.08
      left: 10.00
      bottom: 25.92
      x_percent: 10.00
      y_percent: 74.08
      club: "Benfica"
      club_logo: "images/clubs/api/211.png"
      logo: "images/clubs/api/211.png"
      fallback_letter: "B"
    - date: "2021"
      date_label: "2021"
      value_label: "€15M"
      value: "€15M"
      value_number: 15
      x: 26.00
      y: 65.40
      left: 26.00
      bottom: 34.60
      x_percent: 26.00
      y_percent: 65.40
      club: "Benfica"
      club_logo: "images/clubs/api/211.png"
      logo: "images/clubs/api/211.png"
      fallback_letter: "B"
    - date: "2022"
      date_label: "2022"
      value_label: "€25M"
      value: "€25M"
      value_number: 25
      x: 42.00
      y: 53.00
      left: 42.00
      bottom: 47.00
      x_percent: 42.00
      y_percent: 53.00
      club: "Benfica"
      club_logo: "images/clubs/api/211.png"
      logo: "images/clubs/api/211.png"
      fallback_letter: "B"
    - date: "2023"
      date_label: "2023"
      value_label: "€35M"
      value: "€35M"
      value_number: 35
      x: 58.00
      y: 40.60
      left: 58.00
      bottom: 59.40
      x_percent: 58.00
      y_percent: 40.60
      club: "Paris Saint-Germain"
      club_logo: "images/clubs/api/85.png"
      logo: "images/clubs/api/85.png"
      fallback_letter: "P"
    - date: "2024"
      date_label: "2024"
      value_label: "€50M"
      value: "€50M"
      value_number: 50
      x: 74.00
      y: 22.00
      left: 74.00
      bottom: 78.00
      x_percent: 74.00
      y_percent: 22.00
      club: "Paris Saint-Germain"
      club_logo: "images/clubs/api/85.png"
      logo: "images/clubs/api/85.png"
      fallback_letter: "P"
    - date: "2026"
      date_label: "2026"
      value_label: "€30M"
      value: "€30M"
      value_number: 30
      x: 90.00
      y: 46.80
      left: 90.00
      bottom: 53.20
      x_percent: 90.00
      y_percent: 46.80
      club: "AC Milan"
      club_logo: "images/clubs/api/489.png"
      logo: "images/clubs/api/489.png"
      fallback_letter: "M"

homepage_image: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
concept_art: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
hero_image: "images/homepage/featured/goncalo-ramos-ac-milan-hero.png"
card_image: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
show_in_top_ticker: true
show_in_footer_ticker: true
keywords:
  - Gonçalo Ramos
  - AC Milan
  - Paris Saint-Germain
  - PSG
  - Fabrizio Romano
  - трансферы
  - Serie A
---

Gonçalo Ramos готовится перейти из Paris Saint-Germain в AC Milan. По информации Fabrizio Romano, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**.

Для AC Milan это важное усиление состава. Игрок добавляет команде новую опцию в атаке и может быстро стать заметной частью проекта.

## Главные факты о трансфере Рамуша

- **Игрок:** Gonçalo Ramos
- **Предыдущий клуб:** Paris Saint-Germain
- **Новый клуб:** AC Milan
- **Статус:** согласовано
- **Сумма:** €74M + add-ons
- **Позиция:** нападающий
- **Гражданство:** Португалия
- **Рабочая нога:** правая
- **Источник:** Fabrizio Romano

## Профиль игрока

Gonçalo Ramos — португальский центральный нападающий. Его страница приведена к тому же рабочему формату, что и страницы Конате и Кукурельи: фото игрока, гражданство, флаг, позиция, рабочая нога, возраст, рыночная стоимость, динамика стоимости и блок статистики берутся из стандартных полей страницы.

## Почему этот переход важен для AC Milan

Рамуш даёт «Милану» профиль центрального нападающего, который может играть в штрафной, открываться под передачи с флангов и добавлять команде вариант для завершения атак. Его возраст позволяет рассматривать сделку не только как усиление на один сезон, но и как вложение в долгосрочную структуру атаки.

## Что дальше

После официального подтверждения страницу можно будет перевести из статуса «СОГЛАСОВАНО» в «ОФИЦИАЛЬНО» и обновить источник, дату объявления и детали контракта.
"""

ramos.write_text(new_ramos, encoding="utf-8")
add("")
add("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
add("- rebuilt full page with clean multi-line front matter")
add("- matched working transfer schema fields used by Konate/Cucurella")
add("- kept Ramos-specific player, clubs, value and chart data")
add("- enabled disable_legacy_static_market_chart to prevent duplicate old chart")

pattern = re.compile(r'\{\{\s*if\s+\.Params\.market_value_chart\s*\}\}\s*\{\{\s*partial\s+"profutbik-market-chart-static\.html"\s+\.\s*\}\}\s*\{\{\s*end\s*\}\}')
replacement = '{{ if and .Params.market_value_chart (not .Params.disable_legacy_static_market_chart) }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}'
layout_new, n = pattern.subn(replacement, layout_text, count=1)
if n:
    layout.write_text(layout_new, encoding="utf-8")
    add("CHANGED: layouts/transfers/single.html")
    add("- added opt-out guard for legacy static market chart duplicate")
else:
    if "disable_legacy_static_market_chart" in layout_text:
        add("UNCHANGED: layouts/transfers/single.html already has disable_legacy_static_market_chart guard")
    else:
        fail("could not find legacy static chart conditional in layouts/transfers/single.html")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
add("")
add("HUGO")
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-2500:])
add("--- STDERR tail ---")
add(proc.stderr[-2500:])
if proc.returncode != 0:
    fail("hugo -D failed")

target = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
if not target.exists():
    fail("target public Ramos HTML was not generated")
html = target.read_text(encoding="utf-8", errors="ignore")

checks = {
    "target_html_exists": target.exists(),
    "has_player": "Gonçalo Ramos" in html,
    "has_position_ru": "Нападающий" in html,
    "has_birth_date": "20.06.2001" in html,
    "has_age": "25 лет" in html,
    "has_nationality_ru": "Португалия" in html,
    "has_preferred_foot_ru": "Правая" in html,
    "has_market_value": "€30M" in html,
    "has_stats_label": "Paris Saint-Germain · сезон 2025/26" in html,
    "legacy_static_title_removed": "ДИНАМИКА СТОИМОСТИ" not in html,
    "no_portugal_english_in_profile": " Portugal" not in html,
    "no_right_english_in_profile": " Right" not in html,
}
add("")
add("TARGET CHECK")
add("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
for k, v in checks.items():
    add(f"{k}: {v}")

ok = all(checks.values())
add("")
add(f"VERIFIED_OK: {ok}")
add("NO BACKUP CREATED.")
add("NO PUSH MADE.")
add("NO SITE OPENED.")
add("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")

print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
