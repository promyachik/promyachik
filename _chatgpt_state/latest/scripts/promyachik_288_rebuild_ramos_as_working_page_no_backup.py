from pathlib import Path
import subprocess
import datetime

root = Path(r"C:\Users\Dmitrii\Promyachik")
report = root / "var" / "promyachik_288_rebuild_ramos_as_working_page_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)
log = []

def add(s=""):
    log.append(str(s))

add("PROMYACHIK 288 - REBUILD RAMOS AS WORKING PAGE - NO BACKUP")
add("=" * 100)
add(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
add(f"Project dir: {root}")
add("")
add("RULE")
add("- Fix only Ramos transfer page and its template guards.")
add("- Rebuild Ramos against the same working field schema as Konate/Cucurella.")
add("- Disable legacy static chart duplicate for Ramos.")
add("- Disable old move-price helper only on Ramos page because it breaks Ramos labels.")
add("- No backup.")
add("- No push.")
add("- No site opened.")
add("")

ramos = root / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
konate = root / "content" / "transfers" / "ibrahima-konate-real-madrid" / "index.md"
cuc = root / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"
layout = root / "layouts" / "transfers" / "single.html"

for p in [ramos, konate, cuc, layout]:
    add(f"exists {p.relative_to(root)}: {p.exists()}")
    if not p.exists():
        report.write_text("\n".join(log), encoding="utf-8")
        print("FAILED")
        print(f"REPORT: {report}")
        raise SystemExit(1)

ramos_text = '''---
title: "Gonçalo Ramos переходит в AC Milan из Paris Saint-Germain"
description: "Gonçalo Ramos согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons, источник — Fabrizio Romano."
date: 2026-06-27T12:00:00+02:00
lastmod: 2026-06-30T22:00:00+02:00
draft: false
type: "transfers"
layout: "single"
slug: "goncalo-ramos-ac-milan"
status: "agreement"
status_label: "СОГЛАСОВАНО"
player: "Gonçalo Ramos"
player_initials: "GR"
player_id: 41585
player_image: "images/players/api/41585.png"
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
position: "Нападающий"
age: 25
age_at_transfer: 25
birth_date: "20.06.2001"
nationality: "Португалия"
nationality_flag: "images/flags/portugal.svg"
preferred_foot: "Правая"
from_club_id: 85
from_club_name: "Paris Saint Germain"
to_club_id: 489
to_club_name: "AC Milan"
fee: "€74M + add-ons"
source_name: "Fabrizio Romano"
source_url: ""
market_value: "€30M"
market_value_display: "€30M"
market_value_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"
disable_legacy_static_market_chart: true
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
  area_path: "M 10.00 74.08 L 26.00 65.40 L 42.00 53.00 L 58.00 40.60 L 74.00 22.00 L 90.00 46.80 L 90.00 100 L 10.00 100 Z"
  path: "M 10.00 74.08 L 26.00 65.40 L 42.00 53.00 L 58.00 40.60 L 74.00 22.00 L 90.00 46.80"
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
      club_logo: "/images/clubs/api/211.png"
      logo: "/images/clubs/api/211.png"
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
      club_logo: "/images/clubs/api/211.png"
      logo: "/images/clubs/api/211.png"
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
      club_logo: "/images/clubs/api/211.png"
      logo: "/images/clubs/api/211.png"
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
      club_logo: "/images/clubs/api/85.png"
      logo: "/images/clubs/api/85.png"
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
      club_logo: "/images/clubs/api/85.png"
      logo: "/images/clubs/api/85.png"
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
      club_logo: "/images/clubs/api/489.png"
      logo: "/images/clubs/api/489.png"
      fallback_letter: "M"
---

Gonçalo Ramos готовится перейти из Paris Saint Germain в AC Milan. По информации Fabrizio Romano, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**.

Для AC Milan это важное усиление состава. Игрок добавляет команде новую опцию в атаке и может быстро стать заметной частью проекта.

## Главные факты о трансфере Рамуша

- **Игрок:** Gonçalo Ramos
- **Предыдущий клуб:** Paris Saint Germain
- **Новый клуб:** AC Milan
- **Статус:** согласовано
- **Сумма:** €74M + add-ons
- **Позиция:** нападающий
- **Гражданство:** Португалия
- **Рабочая нога:** правая
- **Источник:** Fabrizio Romano

## Профиль игрока

Gonçalo Ramos — португальский центральный нападающий. На странице он приведён к тому же рабочему формату, что и Конате и Кукурелья: фото игрока, гражданство, флаг, позиция, рабочая нога, возраст, рыночная стоимость, динамика стоимости и блок статистики берутся из стандартных полей страницы.
'''

ramos.write_text(ramos_text, encoding="utf-8")
add("CHANGED: content/transfers/goncalo-ramos-ac-milan/index.md")
add("- wrote clean multi-line front matter")
add("- Russian profile fields")
add("- kept Ramos market_value_chart for the standard chart partial")
add("- disable_legacy_static_market_chart: true")

layout_text = layout.read_text(encoding="utf-8")
orig_layout = layout_text

legacy_old = '{{ if .Params.market_value_chart }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}'
legacy_new = '{{ if and .Params.market_value_chart (not .Params.disable_legacy_static_market_chart) }} {{ partial "profutbik-market-chart-static.html" . }} {{ end }}'
if legacy_old in layout_text:
    layout_text = layout_text.replace(legacy_old, legacy_new, 1)
    add("CHANGED: layouts/transfers/single.html | legacy static chart guard inserted")
elif legacy_new in layout_text:
    add("OK: layouts/transfers/single.html already has legacy static chart guard")
else:
    add("WARN: exact legacy static chart include not found")

move_partial = '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}'
move_guard = '{{ if not (in .RelPermalink "/transfers/goncalo-ramos-ac-milan/") }} ' + move_partial + ' {{ end }}'
if move_partial in layout_text and move_guard not in layout_text:
    layout_text = layout_text.replace(move_partial, move_guard, 1)
    add("CHANGED: layouts/transfers/single.html | disabled old move-price helper on Ramos only")
elif move_guard in layout_text:
    add("OK: old move-price helper already disabled on Ramos")
else:
    add("WARN: old move-price helper partial not found")

layout_text = layout_text.replace('{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }} {{ end }} ', '')

style_id = 'promyachik-ramos-chart-grid-fix-288'
style_block = '{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }}<style id="promyachik-ramos-chart-grid-fix-288">body.transfer-page .player-market-chart:not(.player-market-chart--manual) .player-market-chart__points{display:grid!important;grid-template-columns:repeat(6,minmax(0,1fr))!important;position:relative!important;left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;transform:none!important;width:100%!important;margin-top:-2px!important;gap:5px!important;}body.transfer-page .player-market-chart:not(.player-market-chart--manual) .player-market-chart__point,body.transfer-page .player-market-chart:not(.player-market-chart--manual) .player-market-chart__point.promyachik-cucurella-price-moved-244{display:grid!important;position:relative!important;left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;transform:none!important;width:auto!important;min-width:0!important;max-width:none!important;text-align:center!important;}body.transfer-page .player-market-chart:not(.player-market-chart--manual) .player-market-chart__point small{display:none!important;}body.transfer-page .player-market-chart:not(.player-market-chart--manual) .player-market-chart__point strong{display:block!important;white-space:nowrap!important;}</style>{{ end }}'
if style_id not in layout_text:
    needle = '{{ partial "transfer-player-market-value-chart.html" . }}'
    if needle in layout_text:
        layout_text = layout_text.replace(needle, style_block + ' ' + needle, 1)
        add("CHANGED: layouts/transfers/single.html | Ramos grid-fix style inserted")
    else:
        add("WARN: chart partial include not found for style insertion")
else:
    add("OK: Ramos grid-fix style already exists")

if layout_text != orig_layout:
    layout.write_text(layout_text, encoding="utf-8")
else:
    add("UNCHANGED: layouts/transfers/single.html")

proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
add("")
add("HUGO")
add("COMMAND: hugo -D")
add(f"EXIT_CODE: {proc.returncode}")
add("--- STDOUT tail ---")
add(proc.stdout[-2200:])
add("--- STDERR tail ---")
add(proc.stderr[-2200:])

target = root / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
add("")
add("TARGET CHECK")
add("target_url: http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/")
add(f"target_html_exists: {target.exists()}")
ok = proc.returncode == 0 and target.exists()
if target.exists():
    html = target.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "has_position_ru": "Нападающий" in html,
        "has_nationality_ru": "Португалия" in html,
        "has_preferred_foot_ru": "Правая" in html,
        "has_market_value": "€30M" in html,
        "legacy_static_title_removed": "ДИНАМИКА СТОИМОСТИ" not in html,
        "no_english_portugal_in_profile": " Portugal" not in html,
        "no_english_right_in_profile": " Right" not in html,
        "has_ramos_grid_fix_style": style_id in html,
        "has_stats_labels": ("МАТЧ" in html or "Матчи" in html or "ГОЛ" in html),
    }
    for k, v in checks.items():
        add(f"{k}: {v}")
    ok = ok and all(v for k, v in checks.items() if k != "has_stats_labels")

add("")
add(f"VERIFIED_OK: {ok}")
add("NO BACKUP CREATED.")
add("NO PUSH MADE.")
add("NO SITE OPENED.")
add("DONE" if ok else "FAILED")
report.write_text("\n".join(log), encoding="utf-8")
print("DONE" if ok else "FAILED")
print(f"REPORT: {report}")
raise SystemExit(0 if ok else 1)
