from pathlib import Path
import subprocess
import datetime
import shutil
import re

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_292_restore_valid_schema_and_rebuild_ramos_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

RAMOS = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
LAYOUT = ROOT / "layouts" / "transfers" / "single.html"
DATA = ROOT / "data" / "player-market-values.json"
BACKUPS = Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS")

log = []
def add(x=""):
    log.append(str(x))

def finish(ok):
    add("DONE" if ok else "FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print("REPORT: " + str(REPORT))
    raise SystemExit(0 if ok else 1)

def stop(msg):
    add("ERROR: " + msg)
    finish(False)

add("PROMYACHIK 292 - RESTORE VALID SCHEMA AND REBUILD RAMOS - NO BACKUP")
add("=" * 100)
add("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
add("Project dir: " + str(ROOT))
add("")
add("RULE")
add("- Do not create a new backup.")
add("- Do not push.")
add("- Do not open site.")
add("- Restore stable global files from the successful 282 backup when available.")
add("- Rebuild only Ramos content into the same page schema as working pages.")
add("- Do not add Ramos-only layout/CSS/JS hacks.")
add("")

if not ROOT.exists():
    stop("project root not found")
if not RAMOS.parent.exists():
    stop("Ramos content folder not found")

backup_dir = None
if BACKUPS.exists():
    candidates = [p for p in BACKUPS.iterdir() if p.is_dir() and "FULL_BACKUP_AFTER_282_PRICE_ROW_UP_ALL_PLAYERS_SUCCESS" in p.name]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        backup_dir = candidates[0]

add("BACKUP 282 SEARCH")
add("backup_root_exists: " + str(BACKUPS.exists()))
add("backup_282_found: " + str(backup_dir is not None))
if backup_dir:
    add("backup_282_used: " + str(backup_dir))

if backup_dir:
    for rel in ["layouts/transfers/single.html", "data/player-market-values.json"]:
        src = backup_dir / rel
        dst = ROOT / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            add("RESTORED FROM 282 BACKUP: " + rel)
        else:
            add("BACKUP FILE MISSING, NOT RESTORED: " + rel)
else:
    add("No 282 backup found. Will do fallback cleanup instead of restore.")

if LAYOUT.exists():
    layout = LAYOUT.read_text(encoding="utf-8", errors="ignore")
    before = layout
    layout = re.sub(r'\s*\{\{\s*if\s+in\s+\.RelPermalink\s+"/transfers/goncalo-ramos-ac-milan/"\s*\}\}\s*<style\s+id="promyachik-ramos-[\s\S]*?</style>\s*\{\{\s*end\s*\}\}\s*', '\n', layout)
    layout = re.sub(r'\s*\{\{\s*if\s+in\s+\.RelPermalink\s+"/transfers/goncalo-ramos-ac-milan/"\s*\}\}\s*\{\{\s*end\s*\}\}\s*', '\n', layout)
    layout = layout.replace('{{ if not (in .RelPermalink "/transfers/goncalo-ramos-ac-milan/") }} {{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }} {{ end }}', '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}')
    if layout != before:
        LAYOUT.write_text(layout, encoding="utf-8")
        add("LAYOUT FALLBACK CLEANUP: changed")
    else:
        add("LAYOUT FALLBACK CLEANUP: no change")
else:
    add("LAYOUT FALLBACK CLEANUP: layout not found")

ramos_content = """---
title: "Гонсалу Рамуш переходит в «Милан»: трансфер из ПСЖ и сумма сделки"
seo_title: "Гонсалу Рамуш → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Гонсалу Рамуш согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons, источник — Fabrizio Romano."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T23:35:00+02:00
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
player_image: "https://media.api-sports.io/football/players/41585.png"
api_player_image: "https://media.api-sports.io/football/players/41585.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
api_photo_missing: false
needs_cutout: false

position: "Нападающий"
position_ru: "Нападающий"
main_position: "CF"
shirt_number: "9"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
height: "1.85 м"
nationality: "Португалия"
player_country: "Португалия"
player_nationality: "Португалия"
nationality_code: "PT"
country_code: "PT"
nationality_flag: "images/flags/portugal.svg"
nationality_flag_image: "images/flags/portugal.svg"
country_flag_image: "images/flags/portugal.svg"
player_flag_image: "images/flags/portugal.svg"
preferred_foot: "Правая"
preferred_foot_ru: "Правая"
working_foot: "Правая"

from_club_id: 85
from_club_name: "Paris Saint-Germain"
from_club_logo: "images/clubs/api/85.png"
from: "Paris Saint-Germain"
from_club: "Paris Saint-Germain"
from_name: "Paris Saint-Germain"
from_logo: "images/clubs/api/85.png"
to_club_id: 489
to_club_name: "AC Milan"
to_club_logo: "images/clubs/api/489.png"
to: "AC Milan"
to_club: "AC Milan"
to_name: "AC Milan"
to_logo: "images/clubs/api/489.png"
league: "Serie A"

fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
source: "Fabrizio Romano"
source_name: "Fabrizio Romano"
source_url: ""
market_value: "€30M"
market_value_display: "€30M"
market_value_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"

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

Gonçalo Ramos готовится перейти из **Paris Saint-Germain** в **AC Milan**. По информации Fabrizio Romano, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**.

Для AC Milan это важное усиление состава. Рамуш добавляет команде вариант центрального нападающего, который может играть в штрафной, завершать атаки после прострелов и открываться между защитниками.

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

Gonçalo Ramos — португальский центральный нападающий. Страница приведена к той же рабочей схеме, что и страницы Конате и Кукурельи: фото игрока, гражданство, флаг, позиция, рабочая нога, возраст, рыночная стоимость, статистика и динамика стоимости берутся из стандартных полей.

## Почему этот переход важен для AC Milan

Рамуш даёт «Милану» профиль форварда, который может действовать в штрафной, бороться за позицию с центральными защитниками и завершать атаки после передач с флангов.
"""
RAMOS.write_text(ramos_content, encoding="utf-8")
add("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
add("- clean multiline YAML")
add("- keeps inline market_value_chart like working transfer pages")
add("- no bad local cutout image")
add("- no one-line front matter")

add("")
add("ASSET CHECK")
for rel in ["static/images/clubs/api/211.png", "static/images/clubs/api/85.png", "static/images/clubs/api/489.png", "static/images/flags/portugal.svg"]:
    add(f"{rel}: {(ROOT / rel).exists()}")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
add("")
add("HUGO")
add("COMMAND: hugo -D")
add("EXIT_CODE: " + str(proc.returncode))
add("--- STDOUT tail ---")
add(proc.stdout[-2500:])
add("--- STDERR tail ---")
add(proc.stderr[-2500:])

target = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
add("")
add("TARGET CHECK")
add("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
add("target_html_exists: " + str(target.exists()))

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_player": ("Gonçalo Ramos" in html or "Гонсалу Рамуш" in html),
        "has_portugal_ru": "Португалия" in html,
        "has_preferred_foot_ru": "Правая" in html,
        "has_market_value_30m": "€30M" in html,
        "has_market_chart": "player-market-chart" in html,
        "has_chart_prices": ("€8M" in html and "€15M" in html and "€30M" in html),
        "no_one_line_frontmatter_leak": "market_value_chart: current_label" not in html,
        "no_bad_ramos_grid_fix_style": "promyachik-ramos-chart-grid-fix" not in html,
    }
    for k, v in checks.items():
        add(f"{k}: {v}")
    ok = ok and all(checks.values())

add("")
add("VERIFIED_OK: " + str(ok))
add("NO BACKUP CREATED.")
add("NO PUSH MADE.")
add("NO SITE OPENED.")
finish(ok)
