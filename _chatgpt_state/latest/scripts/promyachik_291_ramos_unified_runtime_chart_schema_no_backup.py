from pathlib import Path
import subprocess
import datetime
import json
import re

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_291_ramos_unified_runtime_chart_schema_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

RAMOS = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
KONATE = ROOT / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
CUC = ROOT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"
DATA = ROOT / "data" / "player-market-values.json"
LAYOUT = ROOT / "layouts" / "transfers" / "single.html"

log = []
def add(x=""):
    log.append(str(x))

def stop(msg):
    add("ERROR: " + msg)
    add("FAILED")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print("REPORT: " + str(REPORT))
    raise SystemExit(1)

add("PROMYACHIK 291 - RAMOS UNIFIED RUNTIME CHART SCHEMA - NO BACKUP")
add("=" * 100)
add("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
add("Project dir: " + str(ROOT))
add("")
add("RULE")
add("- Do not patch Ramos block-by-block.")
add("- Bring Ramos to the same valid content schema as Konate/Cucurella.")
add("- Put Ramos market graph into data/player-market-values.json, like working runtime charts.")
add("- Remove old inline Ramos market_value_chart from content, because it broke logo paths and duplicated graph logic.")
add("- Remove Ramos-only layout/style hacks from 287/288/289.")
add("- No backup.")
add("- No push.")
add("- No site opened.")
add("")

for p in [RAMOS, KONATE, CUC, DATA, LAYOUT]:
    add(f"exists {p.relative_to(ROOT)}: {p.exists()}")
    if not p.exists():
        stop(f"missing required file: {p}")

kon = KONATE.read_text(encoding="utf-8", errors="ignore")
cuc = CUC.read_text(encoding="utf-8", errors="ignore")
required_schema = [
    "player_image:", "player_id:", "position:", "birth_date:", "nationality:",
    "nationality_flag:", "preferred_foot:", "from_club_id:", "to_club_id:", "previous_club_stats:"
]
add("")
add("WORKING PAGE SCHEMA CHECK")
for token in required_schema:
    add(f"{token} | Konate={token in kon} | Cucurella={token in cuc}")
    if token not in kon or token not in cuc:
        stop("working pages do not contain required schema token: " + token)

ramos_content = '''---
title: "Гонсалу Рамуш переходит в «Милан»: трансфер из ПСЖ и сумма сделки"
description: "Гонсалу Рамуш согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки, профиль игрока, гражданство, рабочая нога, статистика и динамика стоимости."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T22:40:00+02:00
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
player_image: "https://media.api-sports.io/football/players/41585.png"
api_player_image: "https://media.api-sports.io/football/players/41585.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
player_image_background_removed: false
player_image_processor: "none"

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

market_value: "€30M"
market_value_display: "€30M"
market_value_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
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

disable_legacy_static_market_chart: true

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

## Что дальше

После официального подтверждения страницу можно будет перевести из статуса «СОГЛАСОВАНО» в «ОФИЦИАЛЬНО» и обновить источник, дату объявления и детали контракта.
'''

RAMOS.write_text(ramos_content, encoding="utf-8")
add("")
add("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
add("- clean multiline front matter")
add("- no inline market_value_chart/value_history in Ramos content")
add("- keeps Portugal flag and Russian labels")
add("- uses original API-Football photo URL, not bad local cutout")

raw = DATA.read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw)
except Exception as e:
    stop("cannot parse data/player-market-values.json: " + repr(e))

players = data.setdefault("players", [])
players = [p for p in players if str(p.get("player_id", "")) != "41585" and "Gonçalo Ramos" not in p.get("aliases", []) and "Goncalo Ramos" not in p.get("aliases", [])]

ramos_entry = {
    "player_id": "41585",
    "player": "Гонсалу Рамуш",
    "aliases": ["Гонсалу Рамуш", "Gonçalo Ramos", "Goncalo Ramos", "G. Ramos"],
    "current_value_million": 30,
    "source_url": "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550",
    "points": [
        {"date_full": "01.07.2020", "date": "2020", "value_million": 8, "value_label": "€8M", "x": 20.0, "y": 74.08},
        {"date_full": "01.07.2021", "date": "2021", "value_million": 15, "value_label": "€15M", "x": 76.0, "y": 65.40},
        {"date_full": "01.07.2022", "date": "2022", "value_million": 25, "value_label": "€25M", "x": 132.0, "y": 53.00},
        {"date_full": "01.07.2023", "date": "2023", "value_million": 35, "value_label": "€35M", "x": 188.0, "y": 40.60},
        {"date_full": "01.07.2024", "date": "2024", "value_million": 50, "value_label": "€50M", "x": 244.0, "y": 22.00},
        {"date_full": "03.06.2026", "date": "2026", "value_million": 30, "value_label": "€30M", "x": 300.0, "y": 46.80}
    ],
    "current_value_label": "€30M",
    "path": "M 20 74.08 L 76 65.40 L 132 53.00 L 188 40.60 L 244 22.00 L 300 46.80",
    "area_path": "M 20 74.08 L 76 65.40 L 132 53.00 L 188 40.60 L 244 22.00 L 300 46.80 L 300 110 L 20 110 Z"
}
players.append(ramos_entry)
data["players"] = players
DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
add("CHANGED: data/player-market-values.json")
add("- added/updated runtime market chart entry for player_id 41585 Gonçalo Ramos")

layout = LAYOUT.read_text(encoding="utf-8", errors="ignore")
old_layout = layout
for sid in ["promyachik-ramos-chart-grid-fix-287", "promyachik-ramos-chart-grid-fix-288", "promyachik-ramos-chart-grid-fix-289", "promyachik-ramos-chart-grid-fix-290"]:
    pat = re.compile(r'\s*\{\{\s*if\s+in\s+\.RelPermalink\s+"/transfers/goncalo-ramos-ac-milan/"\s*\}\}\s*<style\s+id="' + re.escape(sid) + r'"[\s\S]*?</style>\s*\{\{\s*end\s*\}\}\s*')
    layout, n = pat.subn("\n", layout)
    add(f"remove bad style {sid}: replacements={n}")

bad_guard = '{{ if not (in .RelPermalink "/transfers/goncalo-ramos-ac-milan/") }} {{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }} {{ end }}'
good_helper = '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}'
if bad_guard in layout:
    layout = layout.replace(bad_guard, good_helper)
    add("restored old move-price helper from Ramos-specific guard: yes")
else:
    add("restored old move-price helper from Ramos-specific guard: not needed")

legacy_pat = re.compile(r'\{\{\s*if\s+\.Params\.market_value_chart\s*\}\}\s*\{\{\s*partial\s+"profutbik-market-chart-static\.html"\s+\.\s*\}\}\s*\{\{\s*end\s*\}\}')
legacy_guard = '{{ if and .Params.market_value_chart (not .Params.disable_legacy_static_market_chart) }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}'
layout, n = legacy_pat.subn(legacy_guard, layout, count=1)
add(f"legacy static chart guard replacements: {n}")
if layout != old_layout:
    LAYOUT.write_text(layout, encoding="utf-8")
    add("CHANGED: layouts/transfers/single.html")
else:
    add("UNCHANGED: layouts/transfers/single.html")

proc = subprocess.run(["hugo", "-D"], cwd=ROOT, text=True, capture_output=True)
add("")
add("HUGO")
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-2500:])
add("--- STDERR tail ---")
add(proc.stderr[-2500:])

target = ROOT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
public_data = ROOT / "public" / "data" / "player-market-values.json"
public_js = ROOT / "public" / "js" / "transfer-player-market-value-chart.js"
add("")
add("TARGET CHECK")
add("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
add(f"target_html_exists: {target.exists()}")
add(f"public_data_exists: {public_data.exists()}")
add(f"public_js_exists: {public_js.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_player": ("Gonçalo Ramos" in html or "Гонсалу Рамуш" in html),
        "has_portugal_ru": "Португалия" in html,
        "has_preferred_foot_ru": "Правая" in html,
        "has_market_value_30m": "€30M" in html,
        "has_runtime_chart_script": "transfer-player-market-value-chart.js" in html,
        "no_inline_old_value_history": "value_history" not in html,
        "no_bad_ramos_grid_fix_style": "promyachik-ramos-chart-grid-fix" not in html,
        "no_broken_portugal_english_profile": "Portugal" not in html,
        "no_broken_right_english_profile": "Right" not in html,
    }
    for k,v in checks.items():
        add(f"{k}: {v}")
    ok = ok and all(checks.values())

if public_data.exists():
    pdata = public_data.read_text(encoding="utf-8", errors="ignore")
    add(f"public_data_has_ramos_id_41585: {'41585' in pdata}")
    add(f"public_data_has_ramos_name: {'Gonçalo Ramos' in pdata or 'Гонсалу Рамуш' in pdata}")
    ok = ok and ('41585' in pdata) and ('Gonçalo Ramos' in pdata or 'Гонсалу Рамуш' in pdata)
else:
    ok = False

add("")
add(f"VERIFIED_OK: {ok}")
add("NO BACKUP CREATED.")
add("NO PUSH MADE.")
add("NO SITE OPENED.")
add("DONE" if ok else "FAILED")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print("REPORT: " + str(REPORT))
raise SystemExit(0 if ok else 1)
