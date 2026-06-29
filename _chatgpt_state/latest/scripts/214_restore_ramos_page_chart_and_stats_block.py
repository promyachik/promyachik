from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import urllib.request

project = Path.cwd()
backup_dir = project / "_backup_214_restore_ramos_page_chart_and_stats_block"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_214_restore_ramos_page_chart_and_stats_block_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

LOCAL_URL = "http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/"

RAMOS_PAGE = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
STATS_PARTIAL = project / "layouts" / "partials" / "transfer-player-stats.html"
TRANSFER_SINGLE = project / "layouts" / "transfers" / "single.html"
BROKEN_PARTIAL = project / "layouts" / "partials" / "ramos-hardfix-v211.html"
PORTUGAL_SVG = project / "static" / "images" / "flags" / "portugal.svg"

touched = []
warnings = []
hugo_result = ""

BAD_MARKERS = [
    "pfb-ramos-v211",
    "ramos-hardfix-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
    "portugal-proper",
    "211 verified Ramos hardfix",
    "210 hard Ramos photo flag value fix",
    "209 final Ramos photo flag value fix",
    "208 ramos flag visibility",
    "207 real fix Ramos flag",
]

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project))
    except Exception:
        return str(p)

def backup(p: Path):
    if p.exists():
        dst = backup_dir / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)

def add_touched(p: Path):
    if p not in touched:
        touched.append(p)

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    backup(p)
    p.write_text(text, encoding="utf-8", newline="\n")
    add_touched(p)

def delete_file(p: Path):
    if p.exists():
        backup(p)
        p.unlink()
        add_touched(p)

def run_cmd(cmd):
    return subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def fetch_local():
    try:
        req = urllib.request.Request(LOCAL_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        warnings.append(f"localhost fetch failed: {e}")
        return ""

def clean_bad_hardfix(text: str) -> str:
    text = text.replace('{{ partial "ramos-hardfix-v211.html" . }}', "")
    text = text.replace("{{ partial \"ramos-hardfix-v211.html\" . }}", "")

    text = re.sub(r'<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*', "", text, flags=re.I | re.S)
    text = re.sub(r'<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*', "", text, flags=re.I | re.S)

    css_markers = [
        "/* 211 verified Ramos hardfix */",
        "/* 210 hard Ramos photo flag value fix */",
        "/* 209 final Ramos photo flag value fix */",
        "/* 208 ramos flag visibility and market value alignment */",
        "/* 207 real fix Ramos flag and value alignment */",
    ]
    for marker in css_markers:
        while marker in text:
            start = text.find(marker)
            next_marker = text.find("\n/* ", start + len(marker))
            end = next_marker if next_marker != -1 else len(text)
            text = text[:start].rstrip() + "\n" + text[end:].lstrip()

    replacements = [
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "/images/players/api/41585.png"),
        ("images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "images/players/api/41585.png"),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "/images/players/api/41585.png"),
        ("images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "images/players/api/41585.png"),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black.png", "/images/players/api/41585.png"),
        ("images/players/transfermarkt/goncalo-ramos-550550-black.png", "images/players/api/41585.png"),
        ("/images/flags/portugal-v211.png", "/images/flags/portugal.svg"),
        ("images/flags/portugal-v211.png", "images/flags/portugal.svg"),
        ("/images/flags/portugal-v210.png", "/images/flags/portugal.svg"),
        ("images/flags/portugal-v210.png", "images/flags/portugal.svg"),
        ("/images/flags/portugal-proper.png", "/images/flags/portugal.svg"),
        ("images/flags/portugal-proper.png", "images/flags/portugal.svg"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def clean_files_from_hardfix():
    delete_file(BROKEN_PARTIAL)
    roots = [
        project / "layouts",
        project / "static" / "css",
        project / "public",
        project / "css",
        project / "transfers" / "goncalo-ramos-ac-milan",
    ]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in [".html", ".htm", ".css", ".js", ".json", ".md"]:
                continue
            parts = [x.lower() for x in p.parts]
            if ".git" in parts or backup_dir.name.lower() in parts:
                continue
            old = read_text(p)
            new = clean_bad_hardfix(old)
            if new != old:
                write_text(p, new)

def write_portugal_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" role="img" aria-label="Portugal flag">
<rect width="900" height="600" fill="#FF0000"/>
<rect width="360" height="600" fill="#006600"/>
<g transform="translate(360 300)">
<circle r="92" fill="#FFCC00"/>
<circle r="66" fill="#FFFFFF"/>
<path d="M-40 -52H40V34c0 34-18 58-40 70-22-12-40-36-40-70Z" fill="#D40000"/>
<path d="M-26 -38H26V32c0 22-12 39-26 49-14-10-26-27-26-49Z" fill="#FFFFFF"/>
<circle cx="-13" cy="-16" r="7" fill="#003399"/>
<circle cx="13" cy="-16" r="7" fill="#003399"/>
<circle cx="0" cy="6" r="7" fill="#003399"/>
<circle cx="-13" cy="28" r="7" fill="#003399"/>
<circle cx="13" cy="28" r="7" fill="#003399"/>
</g>
</svg>
"""
    write_text(PORTUGAL_SVG, svg)

def write_clean_ramos_page():
    # Valid multiline YAML. Keeps market_value_chart and removes the literal body garbage.
    text = """---
title: "Gonçalo Ramos переходит в AC Milan из Paris Saint-Germain"
seo_title: "Gonçalo Ramos → AC Milan: трансфер из ПСЖ, сумма €74M + add-ons"
description: "Gonçalo Ramos согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons, источник — Fabrizio Romano."
date: 2026-06-27
draft: false
type: "transfers"
slug: "goncalo-ramos-ac-milan"
url: "/transfers/goncalo-ramos-ac-milan/"
permalink: "/transfers/goncalo-ramos-ac-milan/"
href: "/transfers/goncalo-ramos-ac-milan/"
link: "/transfers/goncalo-ramos-ac-milan/"
page_url: "/transfers/goncalo-ramos-ac-milan/"

player: "Gonçalo Ramos"
player_name: "Gonçalo Ramos"
full_name: "Gonçalo Matias Ramos"
player_slug: "goncalo-ramos"
player_id: 41585
api_player_id: 41585
shirt_number: 9

from: "Paris Saint Germain"
from_name: "Paris Saint-Germain"
from_club: "Paris Saint Germain"
from_club_name: "Paris Saint Germain"
from_team: "Paris Saint-Germain"
old_club: "Paris Saint-Germain"
club_from: "Paris Saint-Germain"
source_club: "Paris Saint-Germain"

to: "AC Milan"
to_name: "AC Milan"
to_club: "AC Milan"
to_club_name: "AC Milan"
to_team: "AC Milan"
new_club: "AC Milan"
club_to: "AC Milan"
target_club: "AC Milan"

from_id: 85
from_club_id: 85
from_team_id: 85
from_api_id: 85
old_club_id: 85
to_id: 489
to_club_id: 489
to_team_id: 489
to_api_id: 489
new_club_id: 489

from_logo: "/images/clubs/api/85.png"
from_club_logo: "/images/clubs/api/85.png"
from_team_logo: "/images/clubs/psg.svg"
from_club_badge: "/images/clubs/psg.svg"
from_badge: "/images/clubs/psg.svg"
old_club_logo: "/images/clubs/psg.svg"
club_from_logo: "/images/clubs/psg.svg"
from_crest: "/images/clubs/psg.svg"
source_club_logo: "/images/clubs/psg.svg"
psg_logo: "/images/clubs/chart/psg.svg"

to_logo: "/images/clubs/api/489.png"
to_club_logo: "/images/clubs/api/489.png"
to_team_logo: "/images/clubs/ac-milan.svg"
to_club_badge: "/images/clubs/ac-milan.svg"
to_badge: "/images/clubs/ac-milan.svg"
new_club_logo: "/images/clubs/ac-milan.svg"
club_to_logo: "/images/clubs/ac-milan.svg"
to_crest: "/images/clubs/ac-milan.svg"
target_club_logo: "/images/clubs/ac-milan.svg"
milan_logo: "/images/clubs/ac-milan.svg"

status: "agreement"
status_label: "СОГЛАСОВАНО"
fee: "€74M + add-ons"
amount: "€74M + add-ons"
transfer_fee: "€74M + add-ons"
source: "Fabrizio Romano"
source_name: "Fabrizio Romano"
source_url: ""

homepage_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
concept_art: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"
hero_image: "/images/homepage/featured/goncalo-ramos-ac-milan-hero.png"
card_image: "/images/homepage/featured/goncalo-ramos-ac-milan-card.png"

player_image: "/images/players/api/41585.png"
api_player_image: "/images/players/api/41585.png"
cutout_player_image: ""
api_photo_missing: false
player_image_source_name: "API-Football"
player_image_source_url: "https://media.api-sports.io/football/players/41585.png"
needs_cutout: true

nationality: "Portugal"
country: "Portugal"
player_country: "Portugal"
player_nationality: "Portugal"
country_code: "PT"
nationality_code: "PT"
country_flag: "🇵🇹"
flag: "🇵🇹"
player_flag: "🇵🇹"
player_country_flag: "🇵🇹"
nationality_flag: "🇵🇹"
country_flag_image: "/images/flags/portugal.svg"
flag_image: "/images/flags/portugal.svg"
player_flag_image: "/images/flags/portugal.svg"
player_country_flag_image: "/images/flags/portugal.svg"
nationality_flag_image: "/images/flags/portugal.svg"

position: "Centre-Forward"
position_ru: "Нападающий"
main_position: "CF"
foot: "right"
foot_ru: "Правая"
preferred_foot: "Right"
preferred_foot_ru: "Правая"
dominant_foot: "Right"
working_foot: "Правая"
height: "1.85 м"
birth_date: "20.06.2001"
age: 25
league: "Serie A"

market_value: "€30M"
value: "€30M"
market_value_chart:
  eyebrow: "ДИНАМИКА СТОИМОСТИ"
  title: "Gonçalo Ramos"
  subtitle: "Рыночная стоимость по годам"
  current_label: "€30M"
  current_value: "€30M"
  source_name: "Transfermarkt"
  source_url: "https://www.transfermarkt.com/goncalo-ramos/marktwertverlauf/spieler/550550"
  note: "Оценочная стоимость, не сумма трансфера."
  points:
    - date: "2020"
      date_label: "2020"
      value_label: "€8M"
      value_number: 8
      club: "Benfica"
      logo: "/images/clubs/benfica.svg"
      fallback_letter: "B"
      tooltip: "Benfica · €8M"
    - date: "2021"
      date_label: "2021"
      value_label: "€15M"
      value_number: 15
      club: "Benfica"
      logo: "/images/clubs/benfica.svg"
      fallback_letter: "B"
      tooltip: "Benfica · €15M"
    - date: "2022"
      date_label: "2022"
      value_label: "€25M"
      value_number: 25
      club: "Benfica"
      logo: "/images/clubs/benfica.svg"
      fallback_letter: "B"
      tooltip: "Benfica · €25M"
    - date: "2023"
      date_label: "2023"
      value_label: "€35M"
      value_number: 35
      club: "Paris Saint-Germain"
      logo: "/images/clubs/psg.svg"
      fallback_letter: "P"
      tooltip: "PSG · €35M"
    - date: "2024"
      date_label: "2024"
      value_label: "€50M"
      value_number: 50
      club: "Paris Saint-Germain"
      logo: "/images/clubs/psg.svg"
      fallback_letter: "P"
      tooltip: "PSG · €50M"
    - date: "2026"
      date_label: "2026"
      value_label: "€30M"
      value_number: 30
      club: "AC Milan"
      logo: "/images/clubs/ac-milan.svg"
      fallback_letter: "M"
      tooltip: "AC Milan · €30M"

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
  - "Gonçalo Ramos"
  - "AC Milan"
  - "Paris Saint-Germain"
  - "PSG"
  - "Fabrizio Romano"
  - "трансферы"
  - "Serie A"

show_in_top_ticker: true
show_in_footer_ticker: true
---

## Gonçalo Ramos → AC Milan

Gonçalo Ramos готовится перейти из Paris Saint Germain в AC Milan. По информации Fabrizio Romano, клубы согласовали сделку, а сумма перехода составляет **€74M + add-ons**.

Для AC Milan это важное усиление состава. Игрок добавляет команде новую опцию в атаке и может быстро стать заметной частью проекта.

### Детали трансфера

- Игрок: **Gonçalo Ramos**
- Откуда: **Paris Saint Germain**
- Куда: **AC Milan**
- Статус: **СОГЛАСОВАНО**
- Сумма: **€74M + add-ons**
- Источник: **Fabrizio Romano**

### Профиль игрока

Gonçalo Ramos — португальский центральный нападающий. Рабочая нога — правая, рост — 1.85 м. На странице сохранены стандартные поля для карточки игрока: страна, флаг, позиция, рабочая нога, рост, рыночная стоимость и динамика стоимости.
"""
    write_text(RAMOS_PAGE, text)

def detect_icon_file(tokens):
    icon_dir = project / "static" / "images" / "stats-icons-v184"
    if not icon_dir.exists():
        return None
    files = [p for p in icon_dir.iterdir() if p.is_file()]
    for want in tokens:
        for p in files:
            if p.name.lower() == want.lower():
                return p.name
    for p in files:
        stem = p.stem.lower()
        if any(token.lower() in stem for token in tokens):
            return p.name
    return None

def write_stats_partial():
    icon_matches = detect_icon_file(["matches.png", "match.png", "games", "appearances", "matches"]) or "matches.png"
    icon_goals = detect_icon_file(["goals.png", "goal.png", "goals", "goal"]) or "goals.png"
    icon_assists = detect_icon_file(["assists.png", "assist.png", "assists", "assist"]) or "assists.png"
    icon_yellow = detect_icon_file(["yellow-card.png", "yellow_card.png", "yellow.png", "yellow"]) or "yellow-card.png"
    icon_red = detect_icon_file(["red-card.png", "red_card.png", "red.png", "red"]) or "red-card.png"

    partial = f"""{{{{ if not .Params.hide_stats_block }}}}
<section id="pfb-stats-v184" class="transfer-stats pfb-stats-v184 transfer-stats--under-market-chart" aria-label="Player statistics">
  <style>
    /* 214 restore approved icon-only stats block */
    body.transfer-page #pfb-stats-v184.transfer-stats.pfb-stats-v184,
    #pfb-stats-v184.transfer-stats.pfb-stats-v184 {{
      padding: 0 !important;
      border: 0 !important;
      border-radius: 0 !important;
      background: transparent !important;
      background-image: none !important;
      box-shadow: none !important;
      outline: 0 !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
      margin-top: 18px !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__grid {{
      display: grid !important;
      gap: 10px !important;
      justify-items: center !important;
      align-items: center !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__row {{
      display: grid !important;
      gap: 10px !important;
      justify-items: center !important;
      align-items: center !important;
      width: 100% !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__row--top {{
      grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__row--bottom {{
      grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
      width: 66% !important;
      margin: 0 auto !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__card {{
      position: relative !important;
      width: calc(100% - 9px) !important;
      min-width: 0 !important;
      min-height: calc(100% - 4px) !important;
      aspect-ratio: 1 / 1 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-sizing: border-box !important;
      justify-self: center !important;
      align-self: center !important;
      border: 1px solid rgba(212, 175, 55, 0.34) !important;
      border-radius: 16px !important;
      background: radial-gradient(circle at 50% 30%, rgba(212,175,55,.12), rgba(12,15,20,.96) 60%) !important;
      box-shadow: inset 0 0 18px rgba(212,175,55,.06), 0 8px 22px rgba(0,0,0,.26) !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__icon {{
      width: 54% !important;
      height: 54% !important;
      object-fit: contain !important;
      display: block !important;
      filter: drop-shadow(0 0 7px rgba(212,175,55,.35)) !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__tooltip {{
      position: absolute !important;
      left: 50% !important;
      bottom: calc(100% + 8px) !important;
      transform: translateX(-50%) translateY(4px) !important;
      opacity: 0 !important;
      pointer-events: none !important;
      white-space: nowrap !important;
      padding: 8px 10px !important;
      border-radius: 10px !important;
      border: 1px solid rgba(212,175,55,.42) !important;
      background: rgba(8,10,14,.96) !important;
      color: #f4d875 !important;
      font-size: 12px !important;
      font-weight: 800 !important;
      letter-spacing: .02em !important;
      transition: opacity .14s ease, transform .14s ease !important;
      z-index: 20 !important;
    }}
    #pfb-stats-v184 .pfb-stats-v184__card:hover .pfb-stats-v184__tooltip {{
      opacity: 1 !important;
      transform: translateX(-50%) translateY(0) !important;
    }}
  </style>
  <div class="pfb-stats-v184__grid">
    <div class="pfb-stats-v184__row pfb-stats-v184__row--top">
      <div class="pfb-stats-v184__card" aria-label="Матчи">
        <img class="pfb-stats-v184__icon" src="{{{{ "images/stats-icons-v184/{icon_matches}" | relURL }}}}" alt="">
        <span class="pfb-stats-v184__tooltip">Матчи</span>
      </div>
      <div class="pfb-stats-v184__card" aria-label="Голы">
        <img class="pfb-stats-v184__icon" src="{{{{ "images/stats-icons-v184/{icon_goals}" | relURL }}}}" alt="">
        <span class="pfb-stats-v184__tooltip">Голы</span>
      </div>
      <div class="pfb-stats-v184__card" aria-label="Ассисты">
        <img class="pfb-stats-v184__icon" src="{{{{ "images/stats-icons-v184/{icon_assists}" | relURL }}}}" alt="">
        <span class="pfb-stats-v184__tooltip">Ассисты</span>
      </div>
    </div>
    <div class="pfb-stats-v184__row pfb-stats-v184__row--bottom">
      <div class="pfb-stats-v184__card" aria-label="Жёлтые карточки">
        <img class="pfb-stats-v184__icon" src="{{{{ "images/stats-icons-v184/{icon_yellow}" | relURL }}}}" alt="">
        <span class="pfb-stats-v184__tooltip">Жёлтые карточки</span>
      </div>
      <div class="pfb-stats-v184__card" aria-label="Красные карточки">
        <img class="pfb-stats-v184__icon" src="{{{{ "images/stats-icons-v184/{icon_red}" | relURL }}}}" alt="">
        <span class="pfb-stats-v184__tooltip">Красные карточки</span>
      </div>
    </div>
  </div>
</section>
{{{{ end }}}}
"""
    write_text(STATS_PARTIAL, partial)

def ensure_layout_has_chart_and_stats():
    if not TRANSFER_SINGLE.exists():
        warnings.append(f"Missing layout: {rel(TRANSFER_SINGLE)}")
        return
    text = read_text(TRANSFER_SINGLE)
    original = text
    text = clean_bad_hardfix(text)
    if 'partial "transfer-player-market-value-chart.html"' not in text:
        text += '\n{{ partial "transfer-player-market-value-chart.html" . }}\n'
    if 'partial "profutbik-market-chart-static.html"' not in text:
        text += '\n{{ if .Params.market_value_chart }}{{ partial "profutbik-market-chart-static.html" . }}{{ end }}\n'
    if 'partial "transfer-player-stats.html"' not in text:
        text += '\n{{ partial "transfer-player-stats.html" . }}\n'
    if text != original:
        write_text(TRANSFER_SINGLE, text)

def run_hugo():
    global hugo_result
    try:
        p = run_cmd(["hugo", "-D"])
        hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-2000:]}\nSTDERR tail:\n{p.stderr[-2000:]}"
        if p.returncode != 0:
            warnings.append("hugo -D returned non-zero.")
    except Exception as e:
        hugo_result = f"hugo error: {e}"
        warnings.append(f"hugo -D could not run: {e}")

before = fetch_local()
clean_files_from_hardfix()
write_clean_ramos_page()
write_portugal_svg()
write_stats_partial()
ensure_layout_has_chart_and_stats()
run_hugo()
clean_files_from_hardfix()

after = fetch_local()

public_html_path = project / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
generated = read_text(public_html_path) if public_html_path.exists() else ""

source = read_text(RAMOS_PAGE) if RAMOS_PAGE.exists() else ""
partial_text = read_text(STATS_PARTIAL) if STATS_PARTIAL.exists() else ""
layout_text = read_text(TRANSFER_SINGLE) if TRANSFER_SINGLE.exists() else ""

bad_source = "\\nplayer_image:" in source or any(x in source for x in BAD_MARKERS)
bad_generated = "\\nplayer_image:" in generated or any(x in generated for x in BAD_MARKERS)
bad_after = ("\\nplayer_image:" in after or any(x in after for x in BAD_MARKERS)) if after else False

yaml_ok = source.startswith("---\n") and "\n---\n" in source[4:]
chart_source_ok = "market_value_chart:" in source and "value_number:" in source
stats_partial_ok = "pfb-stats-v184" in partial_text and "previous_club_stats" not in partial_text
layout_ok = 'transfer-player-stats.html' in layout_text and 'transfer-player-market-value-chart.html' in layout_text
generated_stats_ok = "pfb-stats-v184" in generated if generated else False
generated_chart_ok = ("ДИНАМИКА СТОИМОСТИ" in generated or "Рыночная стоимость по годам" in generated) if generated else False

verified = yaml_ok and chart_source_ok and stats_partial_ok and layout_ok and not bad_source and not bad_generated

lines = []
lines.append("PROFUTBIK 214 - RESTORE RAMOS PAGE CHART AND STATS BLOCK")
lines.append("=" * 90)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("FIXED")
lines.append("- Rewrote Ramos page as valid multiline YAML front matter.")
lines.append("- Removed literal body garbage like \\nplayer_image / api_player_image / flag fields.")
lines.append("- Restored market_value_chart data for the dynamic value chart.")
lines.append("- Restored transfer-player-stats.html as approved icon-only block, not the broken previous_club_stats-only text partial.")
lines.append("- Removed v210/v211 hardfix leftovers.")
lines.append("- Rebuilt Hugo.")
lines.append("")
lines.append("VERIFY")
lines.append(f"- yaml_ok: {yaml_ok}")
lines.append(f"- chart_source_ok: {chart_source_ok}")
lines.append(f"- stats_partial_ok: {stats_partial_ok}")
lines.append(f"- layout_ok: {layout_ok}")
lines.append(f"- generated_stats_ok: {generated_stats_ok}")
lines.append(f"- generated_chart_ok: {generated_chart_ok}")
lines.append(f"- bad_source: {bad_source}")
lines.append(f"- bad_generated: {bad_generated}")
lines.append(f"- localhost_fetched: {bool(after)}")
lines.append(f"- bad_after_localhost: {bad_after}")
lines.append(f"- VERIFIED_OK: {verified}")
lines.append("")
lines.append("HUGO RESULT")
lines.append(hugo_result)
lines.append("")
lines.append("TOUCHED FILES")
seen = set()
for p in touched:
    s = rel(p)
    if s not in seen:
        seen.add(s)
        lines.append(f"- {s}")
lines.append(f"- {rel(report_path)}")
lines.append("")
if warnings:
    lines.append("WARNINGS")
    for w in warnings:
        lines.append(f"- {w}")
    lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")

write_text(report_path, "\n".join(lines))
print(read_text(report_path))

if not verified:
    raise SystemExit("Restore verification failed. Check report.")
