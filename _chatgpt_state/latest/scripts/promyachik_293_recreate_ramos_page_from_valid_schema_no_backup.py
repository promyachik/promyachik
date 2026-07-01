from pathlib import Path
import json
import datetime
import subprocess
import re

ROOT = Path.cwd()
REPORT = ROOT / "var" / "promyachik_293_recreate_ramos_page_from_valid_schema_no_backup_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)
log = []

def add(s=""):
    log.append(str(s))

def write_report():
    REPORT.write_text("\n".join(log), encoding="utf-8")

add("PROMYACHIK 293 - RECREATE RAMOS PAGE FROM VALID SCHEMA - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {ROOT}")
add("")
add("RULE")
add("- Recreate only Ramos transfer page using the same required field schema as working transfer pages.")
add("- Add/replace Ramos market-value data entry for the shared runtime chart source.")
add("- Do not create backup folder or backup file.")
add("- No push.")
add("- No site opened.")
add("")

ramos = ROOT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
konate = ROOT / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
cucurella = ROOT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"
values_path = ROOT / "data" / "player-market-values.json"
layout = ROOT / "layouts" / "transfers" / "single.html"

for p in [ramos, konate, cucurella, values_path, layout]:
    add(f"exists {p.relative_to(ROOT)}: {p.exists()}")

missing = [str(p.relative_to(ROOT)) for p in [ramos, konate, cucurella, values_path, layout] if not p.exists()]
if missing:
    add("ERROR: missing required files: " + ", ".join(missing))
    write_report()
    print("FAILED")
    raise SystemExit(1)

schema_tokens = [
    "player_image:", "player_id:", "position:", "birth_date:", "nationality:",
    "nationality_flag:", "preferred_foot:", "from_club_id:", "to_club_id:",
    "previous_club_stats:"
]
konate_text = konate.read_text(encoding="utf-8", errors="ignore")
cuc_text = cucurella.read_text(encoding="utf-8", errors="ignore")
add("")
add("WORKING PAGE SCHEMA CHECK")
for token in schema_tokens:
    add(f"Konate has {token} {token in konate_text}")
    add(f"Cucurella has {token} {token in cuc_text}")

# Recreate Ramos content from scratch. No old Ramos fields are reused.
new_ramos = '''---
title: "Гонсалу Рамуш переходит в «Милан»: сумма сделки и профиль игрока"
seo_title: "Гонсалу Рамуш → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Гонсалу Рамуш согласовал переход из Paris Saint-Germain в AC Milan. Детали сделки, профиль игрока, гражданство, рабочая нога и динамика стоимости."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T22:30:00+02:00
draft: false
type: "transfers"
layout: "single"
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
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
player_image_background_removed: false
position: "Нападающий"
position_ru: "Нападающий"
main_position: "CF"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
nationality: "Португалия"
nationality_flag: "images/flags/portugal.svg"
preferred_foot: "Правая"
height: "1.85 м"
from_club_id: 85
from_club_name: "Paris Saint-Germain"
to_club_id: 489
to_club_name: "AC Milan"
from_name: "Paris Saint-Germain"
to_name: "AC Milan"
from_team: "Paris Saint-Germain"
to_team: "AC Milan"
fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
market_value: "€30M"
market_value_display: "€30M"
source_name: "Fabrizio Romano"
source_url: ""
homepage_image: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
concept_art: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
hero_image: "images/homepage/featured/goncalo-ramos-ac-milan-hero.png"
card_image: "images/homepage/featured/goncalo-ramos-ac-milan-card.png"
show_in_top_ticker: true
show_in_footer_ticker: true
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

Гонсалу Рамуш — португальский центральный нападающий. На странице используется та же валидная схема профиля, что и на рабочих страницах Конате и Кукурельи: фото игрока, позиция, дата рождения, возраст, гражданство, флаг, рабочая нога, рыночная стоимость, блок статистики и график динамики стоимости.

## Почему этот трансфер важен для AC Milan

Для AC Milan Рамуш добавляет вариант в центре атаки. Он может играть как основной форвард, открываться под передачи из глубины и завершать атаки в штрафной. Переход также усиливает конкуренцию в атакующей линии и даёт тренерскому штабу больше вариантов под разные матчи.

## Статус сделки

На данный момент страница имеет статус **«СОГЛАСОВАНО»**. Если появится официальное объявление клуба, материал можно обновить без смены адреса страницы.
'''

ramos.write_text(new_ramos, encoding="utf-8")
add("")
add("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
add("- recreated from scratch with clean multiline front matter")
add("- no inline market_value_chart, no value_history, no broken old one-line field soup")
add("- keeps Portugal flag / Portuguese nationality / right foot / API-Football photo")

# Add/replace Ramos in shared market values data. This is the runtime source used by the chart system.
try:
    data = json.loads(values_path.read_text(encoding="utf-8"))
except Exception as e:
    add(f"ERROR: cannot parse data/player-market-values.json: {e!r}")
    write_report()
    print("FAILED")
    raise SystemExit(1)

players = data.setdefault("players", [])
players = [p for p in players if str(p.get("player_id", "")) != "41585" and p.get("player") not in ["Гонсалу Рамуш", "Gonçalo Ramos"]]
ramos_chart = {
    "player_id": "41585",
    "player": "Гонсалу Рамуш",
    "aliases": ["Гонсалу Рамуш", "Gonçalo Ramos", "Goncalo Ramos", "G. Ramos"],
    "current_value_million": 30,
    "current_value_label": "€30M",
    "source_url": "https://www.transfermarkt.com/goncalo-ramos/marktwertverlauf/spieler/550550",
    "points": [
        {"date_full": "01.07.2020", "date": "2020", "value_million": 8, "value_label": "€8M", "x": 20.0, "y": 74.08},
        {"date_full": "01.07.2021", "date": "2021", "value_million": 15, "value_label": "€15M", "x": 76.0, "y": 65.40},
        {"date_full": "01.07.2022", "date": "2022", "value_million": 25, "value_label": "€25M", "x": 132.0, "y": 53.00},
        {"date_full": "01.07.2023", "date": "2023", "value_million": 35, "value_label": "€35M", "x": 188.0, "y": 40.60},
        {"date_full": "01.07.2024", "date": "2024", "value_million": 50, "value_label": "€50M", "x": 244.0, "y": 22.00},
        {"date_full": "30.06.2026", "date": "2026", "value_million": 30, "value_label": "€30M", "x": 300.0, "y": 46.80}
    ],
    "path": "M 20 74.08 L 76 65.40 L 132 53.00 L 188 40.60 L 244 22.00 L 300 46.80",
    "area_path": "M 20 74.08 L 76 65.40 L 132 53.00 L 188 40.60 L 244 22.00 L 300 46.80 L 300 110 L 20 110 Z"
}
players.append(ramos_chart)
data["players"] = players
values_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
add("CHANGED: data/player-market-values.json")
add("- replaced/added Ramos runtime chart entry by player_id 41585")

# Clean the transfer template from only known failed Ramos-specific hacks/guards, without touching global successful CSS/JS.
layout_text = layout.read_text(encoding="utf-8", errors="ignore")
old_layout = layout_text
bad_markers = ["PROMYACHIK 287", "PROMYACHIK 288", "PROMYACHIK 289", "PROMYACHIK 290", "PROMYACHIK 291", "PROMYACHIK 292"]
# Remove simple HTML style/script blocks carrying these markers if present.
for marker in bad_markers:
    layout_text = re.sub(r"\s*<style[^>]*>[^<]*" + re.escape(marker) + r".*?</style>\s*", "\n", layout_text, flags=re.S)
    layout_text = re.sub(r"\s*<script[^>]*>[^<]*" + re.escape(marker) + r".*?</script>\s*", "\n", layout_text, flags=re.S)
# Remove empty Ramos-only no-op guard if present.
layout_text = layout_text.replace('{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }} {{ end }} ', '')
if layout_text != old_layout:
    layout.write_text(layout_text, encoding="utf-8")
    add("CHANGED: layouts/transfers/single.html")
    add("- removed known failed Ramos-only hack markers / empty no-op guard")
else:
    add("UNCHANGED: layouts/transfers/single.html")

# Build Hugo.
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
add("")
add("TARGET CHECK")
add("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
add(f"target_html_exists: {target.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_player": "Gonçalo Ramos" in html or "Гонсалу Рамуш" in html,
        "has_portugal_ru": "Португал" in html,
        "has_right_foot_ru": "Правая" in html,
        "has_market_value_30m": "€30M" in html,
        "no_old_portugal_en_profile": "Portugal" not in html,
        "no_old_right_en_profile": "Right" not in html,
        "has_player_market_hint": "player-market" in html or "market-value" in html,
        "has_api_photo_path": "images/players/api/41585.png" in html or "/promyachik/images/players/api/41585.png" in html,
    }
    for k, v in checks.items():
        add(f"{k}: {v}")
    ok = ok and checks["has_player"] and checks["has_portugal_ru"] and checks["has_right_foot_ru"] and checks["has_market_value_30m"] and checks["has_api_photo_path"]

add("")
add(f"VERIFIED_OK: {ok}")
add("NO BACKUP CREATED.")
add("NO PUSH MADE.")
add("NO SITE OPENED.")
add("DONE" if ok else "FAILED")
write_report()
print("DONE" if ok else "FAILED")
print(f"REPORT: {REPORT}")
raise SystemExit(0 if ok else 1)
