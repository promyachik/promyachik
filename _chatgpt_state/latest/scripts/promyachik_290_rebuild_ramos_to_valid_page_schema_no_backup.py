from pathlib import Path
import subprocess
import datetime
import re

root = Path(r"C:\Users\Dmitrii\Promyachik")
report = root / "var" / "promyachik_290_rebuild_ramos_to_valid_page_schema_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)

ramos = root / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
konate = root / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
cucurella = root / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"
layout = root / "layouts" / "transfers" / "single.html"

log = []
log.append("PROMYACHIK 290 - REBUILD RAMOS TO VALID PAGE SCHEMA - NO BACKUP")
log.append("=" * 100)
log.append("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
log.append("Project dir: " + str(root))
log.append("")
log.append("RULE")
log.append("- Rebuild only Ramos content to the same minimal valid field schema as working transfer pages.")
log.append("- Remove Ramos inline market_value_chart so the page uses the same runtime chart system as working pages.")
log.append("- Guard legacy static chart duplicate in the transfer template.")
log.append("- Guard old 244 move-price helper away from Ramos page only.")
log.append("- Do not create any backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

for p in [ramos, konate, cucurella, layout]:
    log.append(f"exists {p.relative_to(root)}: {p.exists()}")
if not all(p.exists() for p in [ramos, konate, cucurella, layout]):
    log.append("ERROR: required file missing. Stopped before changes.")
    report.write_text("\n".join(log), encoding="utf-8")
    raise SystemExit(1)

konate_text = konate.read_text(encoding="utf-8", errors="ignore")
cuc_text = cucurella.read_text(encoding="utf-8", errors="ignore")
required = ["player_image:", "player_id:", "position:", "birth_date:", "nationality:", "nationality_flag:", "preferred_foot:", "from_club_id:", "to_club_id:", "previous_club_stats:"]
log.append("")
log.append("VALID PAGE SCHEMA CHECK")
valid_schema = True
for key in required:
    kh = key in konate_text
    ch = key in cuc_text
    log.append(f"{key} | Konate={kh} | Cucurella={ch}")
    valid_schema = valid_schema and kh and ch
if not valid_schema:
    log.append("ERROR: working page schema check failed. Stopped before changes.")
    report.write_text("\n".join(log), encoding="utf-8")
    raise SystemExit(1)

ramos_body = """---
title: "Гонсалу Рамуш переходит в «Милан»: детали трансфера из ПСЖ"
description: "Гонсалу Рамуш готовится перейти из Paris Saint-Germain в AC Milan. Сумма сделки, статус, профиль игрока и роль форварда в новой команде."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T22:10:00+02:00
draft: false
type: "transfers"
layout: "single"
status: "agreement"
player: "Gonçalo Ramos"
player_initials: "GR"
player_id: 41585
player_image: "https://media.api-sports.io/football/players/41585.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
player_image_background_removed: false
player_image_processor: "none"
position: "Нападающий"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
nationality: "Португалия"
nationality_flag: "images/flags/portugal.svg"
preferred_foot: "Правая"
from_club_id: 85
from_club_name: "Paris Saint-Germain"
to_club_id: 489
to_club_name: "AC Milan"
fee: "€74M + add-ons"
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
---
Гонсалу Рамуш готовится перейти из **Paris Saint-Germain** в **AC Milan**.

По информации Фабрицио Романо, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**. Для «Милана» это важное усиление атаки: Рамуш может играть центрального нападающего, открываться в штрафной и завершать атаки после прострелов и передач с флангов.

## Главные факты о трансфере Рамуша

- **Игрок:** Гонсалу Рамуш
- **Предыдущий клуб:** Paris Saint-Germain
- **Новый клуб:** AC Milan
- **Статус:** согласовано
- **Сумма:** €74M + add-ons
- **Позиция:** нападающий
- **Гражданство:** Португалия
- **Рабочая нога:** правая

## Профиль игрока

Гонсалу Рамуш — португальский центральный нападающий. На странице используется та же рабочая схема карточки, что и у Конате и Кукурельи: фото игрока, позиция, дата рождения, возраст, гражданство, флаг, рабочая нога, рыночная стоимость, статистика и динамика стоимости.

## Что Рамуш может дать «Милану»

Рамуш добавляет команде вариант классического форварда для игры в штрафной. Он может открываться между центральными защитниками, атаковать ближнюю штангу, завершать быстрые атаки и давить на защитников без мяча.

## Статус трансфера

На текущем этапе статус страницы — **согласовано**. Если клубы официально объявят переход, страницу можно будет обновить без изменения адреса.
"""

ramos.write_text(ramos_body, encoding="utf-8")
log.append("")
log.append("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
log.append("- rebuilt clean multiline front matter")
log.append("- removed inline market_value_chart and value_history from Ramos content")
log.append("- kept Portugal flag and Russian profile labels")
log.append("- switched player image to original API-Football URL, not local cutout")

layout_text = layout.read_text(encoding="utf-8", errors="ignore")
old_layout = layout_text

layout_text = layout_text.replace(
    '{{ if .Params.market_value_chart }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}',
    '{{ if and .Params.market_value_chart (not .Params.disable_legacy_static_market_chart) }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}'
)
layout_text = layout_text.replace(
    '{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }} {{ end }} {{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}',
    '{{ if not (in .RelPermalink "/transfers/goncalo-ramos-ac-milan/") }} {{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }} {{ end }}'
)
helper = '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}'
guarded = '{{ if not (in .RelPermalink "/transfers/goncalo-ramos-ac-milan/") }} {{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }} {{ end }}'
if helper in layout_text and guarded not in layout_text:
    layout_text = layout_text.replace(helper, guarded, 1)

if layout_text != old_layout:
    layout.write_text(layout_text, encoding="utf-8")
    log.append("CHANGED: layouts/transfers/single.html")
    log.append("- guarded legacy static chart duplicate")
    log.append("- guarded old 244 price helper away from Ramos only")
else:
    log.append("UNCHANGED: layouts/transfers/single.html | target guards already present or pattern not found")

proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
log.append("")
log.append("HUGO")
log.append("COMMAND: hugo -D")
log.append(f"EXIT_CODE: {proc.returncode}")
log.append("--- STDOUT tail ---")
log.append(proc.stdout[-2000:])
log.append("--- STDERR tail ---")
log.append(proc.stderr[-2000:])

target = root / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
log.append("")
log.append("TARGET CHECK")
log.append("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
log.append(f"target_html_exists: {target.exists()}")

ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_player_name": ("Gonçalo Ramos" in html or "Гонсалу Рамуш" in html),
        "has_portugal_ru": "Португалия" in html,
        "has_preferred_foot_ru": "Правая" in html,
        "has_market_value_30m": "€30M" in html,
        "no_english_portugal_profile_value": "Portugal" not in html,
        "no_english_right_profile_value": "Right" not in html,
        "no_legacy_static_title": "ДИНАМИКА СТОИМОСТИ" not in html,
        "no_inline_market_chart_values_from_content": "€8M" not in html and "€15M" not in html and "€25M" not in html,
        "has_runtime_chart_script": "transfer-player-market-value-chart.js" in html,
        "has_api_player_photo": "https://media.api-sports.io/football/players/41585.png" in html,
    }
    for k, v in checks.items():
        log.append(f"{k}: {v}")
    ok = ok and all(checks.values())

log.append("")
log.append(f"VERIFIED_OK: {ok}")
log.append("NO BACKUP CREATED.")
log.append("NO PUSH MADE.")
log.append("NO SITE OPENED.")
log.append("DONE" if ok else "FAILED")

report.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print("REPORT: " + str(report))
raise SystemExit(0 if ok else 1)
