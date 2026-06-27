# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.cwd()
REPORT_LINES: List[str] = []
CRITICAL: List[str] = []
WARNINGS: List[str] = []
ACTIONS: List[str] = []


def norm(value: Any) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower().replace("_", "-").replace(" ", "-").replace("'", "")


def slugify(text: str) -> str:
    s = norm(text)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "transfer"


def log(message: str) -> None:
    print(message, flush=True)
    REPORT_LINES.append(message)


def action(message: str) -> None:
    ACTIONS.append(message)
    log("OK: " + message)


def warn(message: str) -> None:
    WARNINGS.append(message)
    log("WARNING: " + message)


def crit(message: str) -> None:
    CRITICAL.append(message)
    log("CRITICAL: " + message)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warn(f"Cannot read JSON {rel(path)}: {exc}")
        return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def static_abs(value: str) -> Path:
    value = str(value or "").strip().strip('"').strip("'").replace("\\", "/")
    if value.startswith("/promyachik/"):
        value = value[len("/promyachik/"):]
    if value.startswith("/"):
        value = value[1:]
    if value.startswith("static/"):
        return ROOT / value
    return ROOT / "static" / value


def static_url(value: str) -> str:
    value = str(value or "").strip().replace("\\", "/")
    if value.startswith("/promyachik/"):
        value = value[len("/promyachik"):]
    if value.startswith("/"):
        return value
    if value.startswith("static/"):
        return "/" + value[len("static/"):]
    return "/" + value


def static_exists(value: str) -> bool:
    if not value:
        return False
    if str(value).startswith(("http://", "https://", "data:")):
        return True
    return static_abs(value).exists()


def walk_json(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_json(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_json(v)


def copy_payload_assets() -> None:
    src_root = ROOT / "payload" / "static"
    if not src_root.exists():
        return
    for src in src_root.rglob("*"):
        if src.is_file():
            dst = ROOT / "static" / src.relative_to(src_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            action(f"Copied asset {rel(dst)}")


def parse_frontmatter(path: Path) -> Tuple[str, str]:
    if not path.exists():
        return "", ""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def set_fm_key(front: str, key: str, value: Any) -> str:
    value = "" if value is None else str(value)
    safe = value.replace("\\", "\\\\").replace('"', '\\"')
    line = f'{key}: "{safe}"'
    pattern = re.compile(rf'(?m)^{re.escape(key)}\s*:\s*.*$')
    if pattern.search(front):
        return pattern.sub(line, front)
    return front.rstrip() + "\n" + line + "\n"


def remove_fm_key(front: str, key: str) -> str:
    return re.sub(rf'(?m)^{re.escape(key)}\s*:\s*.*\n?', "", front)


def load_player_db() -> List[Dict[str, Any]]:
    path = ROOT / "data" / "playerdb" / "players.json"
    data = read_json(path)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return [x for x in data["items"] if isinstance(x, dict)]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def find_player(player_name: str, player_id: Optional[int]) -> Optional[Dict[str, Any]]:
    players = load_player_db()
    if player_id:
        for p in players:
            if str(p.get("id")) == str(player_id):
                return p

    wanted = norm(player_name)
    parts = [x for x in wanted.split("-") if x]
    best = None
    best_score = 0

    for p in players:
        name = norm(p.get("name") or p.get("player_name") or "")
        score = 100 if name == wanted else 0
        score += sum(20 for part in parts if part and part in name)
        if score > best_score:
            best = p
            best_score = score

    return best if best_score >= 35 else None


def load_clubs() -> Dict[str, Dict[str, Any]]:
    path = ROOT / "data" / "club-logos.json"
    data = read_json(path)
    if isinstance(data, dict) and isinstance(data.get("clubs"), dict):
        return {str(k): v for k, v in data["clubs"].items() if isinstance(v, dict)}
    return {}


def find_club(club_id: int, club_name: str) -> Optional[Dict[str, Any]]:
    clubs = load_clubs()
    if str(club_id) in clubs:
        return clubs[str(club_id)]

    wanted = norm(club_name)
    for _, club in clubs.items():
        name = norm(club.get("configured_name") or club.get("name") or "")
        if wanted and (wanted == name or wanted in name or name in wanted):
            return club
    return None


def ensure_club_logo(club: Dict[str, Any]) -> str:
    logo = club.get("logo") or ""
    if not logo:
        crit(f"Club {club.get('name')} has no logo in data/club-logos.json")
        return ""

    url = static_url(logo)
    path = static_abs(url)
    if path.exists():
        action(f"Club logo exists: {rel(path)}")
        return url

    warn(f"Club logo file missing; generated visible fallback at {rel(path)}")
    try:
        from PIL import Image, ImageDraw, ImageFont
        path.parent.mkdir(parents=True, exist_ok=True)
        im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        label = (club.get("short_name") or club.get("name") or "CLB")[:3].upper()
        d.ellipse((5, 5, 123, 123), fill=(12, 18, 28, 255), outline=(229, 180, 58, 255), width=7)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
        except Exception:
            font = None
        if font:
            box = d.textbbox((0, 0), label, font=font)
            x = (128 - (box[2] - box[0])) / 2
            y = (128 - (box[3] - box[1])) / 2
        else:
            x, y = 34, 50
        d.text((x, y), label, fill=(255, 255, 255, 255), font=font)
        im.save(path)
        return url
    except Exception as exc:
        crit(f"Cannot create fallback club logo {rel(path)}: {exc}")
        return ""


def ensure_flag(country: str, country_code: str) -> str:
    flag_dir = ROOT / "static" / "images" / "flags"
    candidates = [
        flag_dir / f"{slugify(country)}.svg",
        flag_dir / f"{slugify(country)}.png",
        flag_dir / f"{country_code.lower()}.svg",
        flag_dir / f"{country_code.lower()}.png",
    ]

    for p in candidates:
        if p.exists():
            action(f"Country flag exists: {rel(p)}")
            return "/" + str(p.relative_to(ROOT / "static")).replace("\\", "/")

    if norm(country) == "portugal" or country_code.upper() == "PT":
        p = flag_dir / "portugal.svg"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600">'
            '<rect width="360" height="600" fill="#046A38"/>'
            '<rect x="360" width="540" height="600" fill="#DA291C"/>'
            '<circle cx="360" cy="300" r="105" fill="#FFCD00"/>'
            '<circle cx="360" cy="300" r="72" fill="#fff"/>'
            '</svg>',
            encoding="utf-8",
        )
        warn(f"Country flag missing; generated fallback {rel(p)}")
        return "/images/flags/portugal.svg"

    crit(f"Country flag missing for {country}")
    return ""


def enqueue_cutout(player: Dict[str, Any], api_photo: str) -> None:
    player_id = str(player.get("id") or "")
    queue_path = ROOT / "data" / "image-processing" / "background-removal-queue.json"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue = read_json(queue_path)
    if not isinstance(queue, list):
        queue = []

    already = any(isinstance(x, dict) and str(x.get("player_id")) == player_id for x in queue)
    if already:
        action(f"Cutout task already queued for player {player_id}")
        return

    queue.append({
        "player_id": player_id,
        "player_name": player.get("name") or "",
        "source_image": api_photo,
        "target_image": f"images/players/cutout/{player_id}.png",
        "status": "queued",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "reason": "NEWS_ON_MAIN requires transparent/cutout player photo",
    })
    write_json(queue_path, queue)
    action(f"Cutout task queued: {rel(queue_path)}")


def resolve_player_images(player: Dict[str, Any], allow_api_fallback: bool) -> Dict[str, Any]:
    player_id = str(player.get("id") or "")
    result = {"player_id": player_id, "api_photo": "", "cutout_photo": "", "page_photo": "", "needs_cutout": False}

    if not player_id:
        crit("Player has no API-Football ID")
        return result

    raw = player.get("photo_raw") or f"images/players/api/{player_id}.png"
    api_url = static_url(raw)
    api_path = static_abs(api_url)
    if not api_path.exists():
        crit(f"API player photo missing: {rel(api_path)}")
        return result

    result["api_photo"] = api_url
    action(f"API player photo exists: {rel(api_path)}")

    cutout_path = ROOT / "static" / "images" / "players" / "cutout" / f"{player_id}.png"
    if cutout_path.exists():
        result["cutout_photo"] = "/" + str(cutout_path.relative_to(ROOT / "static")).replace("\\", "/")
        result["page_photo"] = result["cutout_photo"]
        action(f"Cutout player photo exists: {rel(cutout_path)}")
    else:
        result["needs_cutout"] = True
        enqueue_cutout(player, api_url)
        if allow_api_fallback:
            result["page_photo"] = api_url
            warn("Cutout missing; using raw API photo because TEST mode allows fallback")
        else:
            crit(f"Cutout missing: {rel(cutout_path)}. Publish blocked until background removal is done.")

    return result


def status_label(status: str) -> str:
    return {
        "rumour": "СЛУХ",
        "negotiations": "ПЕРЕГОВОРЫ",
        "agreement": "СОГЛАСОВАНО",
        "confirmed": "ПОДТВЕРЖДЕНО",
        "official": "ОФИЦИАЛЬНО",
    }.get(status, "ТРАНСФЕР")


def make_item(args, player: Dict[str, Any], from_club: Dict[str, Any], to_club: Dict[str, Any], images: Dict[str, Any], flag_url: str) -> Dict[str, Any]:
    from_logo = ensure_club_logo(from_club)
    to_logo = ensure_club_logo(to_club)
    transfer_url = f"/transfers/{args.slug}/"
    from_name = from_club.get("configured_name") or from_club.get("name") or args.from_club
    to_name = to_club.get("configured_name") or to_club.get("name") or args.to_club
    country = args.country or player.get("nationality") or player.get("country") or ""

    return {
        "slug": args.slug,
        "url": transfer_url,
        "link": transfer_url,
        "href": transfer_url,
        "permalink": transfer_url,
        "page_url": transfer_url,

        "player": player.get("name") or args.player,
        "player_name": player.get("name") or args.player,
        "player_id": str(player.get("id") or ""),
        "api_player_id": str(player.get("id") or ""),

        "player_image": images.get("page_photo") or "",
        "api_player_image": images.get("api_photo") or "",
        "cutout_player_image": images.get("cutout_photo") or "",
        "player_image_source_name": "API-Football",
        "player_image_source_url": player.get("photo_source_url") or f"https://media.api-sports.io/football/players/{player.get('id')}.png",

        "from_club_id": str(from_club.get("id") or args.from_club_id),
        "from_club_name": from_name,
        "from_club_logo": from_logo,
        "from": from_name,
        "from_club": from_name,
        "from_logo": from_logo,

        "to_club_id": str(to_club.get("id") or args.to_club_id),
        "to_club_name": to_name,
        "to_club_logo": to_logo,
        "to": to_name,
        "to_club": to_name,
        "to_logo": to_logo,

        "status": args.status,
        "status_label": status_label(args.status),
        "fee": args.fee,
        "amount": args.fee,
        "transfer_fee": args.fee,
        "source": args.source_name,
        "source_name": args.source_name,
        "source_url": args.source_url or "",

        "country": country,
        "nationality": country,
        "country_flag": args.country_flag,
        "flag": args.country_flag,
        "country_flag_image": flag_url,

        "position": args.position,
        "position_ru": args.position_ru,
        "main_position": args.main_position,
        "foot": args.foot,
        "foot_ru": args.foot_ru,
        "height": args.height,
        "birth_date": args.birth_date,
        "age": args.age,
        "market_value": args.market_value,
        "league": args.league,

        "homepage_image": args.homepage_image,
        "concept_art": args.homepage_image,
        "hero_image": args.hero_image,
        "card_image": args.homepage_image,

        "show_in_top_ticker": True,
        "show_in_footer_ticker": args.show_in_footer_ticker,
        "needs_cutout": bool(images.get("needs_cutout")),
    }


def remove_dangerous_data_folder() -> None:
    bad = ROOT / "data" / "transfers"
    if not bad.exists():
        return
    for p in bad.glob("*.json"):
        p.unlink()
        warn(f"Removed dangerous data/transfers JSON: {rel(p)}")
    try:
        if not any(bad.iterdir()):
            bad.rmdir()
            action("Removed empty data/transfers folder")
    except Exception:
        pass


def upsert_transfers_json(item: Dict[str, Any], position: int) -> None:
    path = ROOT / "data" / "transfers.json"
    data = read_json(path)
    if data is None:
        data = []

    def merge(old):
        if isinstance(old, dict):
            old.update(item)
            return old
        return dict(item)

    if isinstance(data, list):
        rows, found = [], False
        for old in data:
            if isinstance(old, dict) and old.get("slug") == item["slug"]:
                rows.append(merge(old))
                found = True
            else:
                rows.append(old)
        if not found:
            rows.insert(max(0, min(position - 1, len(rows))), item)
        write_json(path, rows)
        action(f"Updated data/transfers.json: {item['slug']}")
    elif isinstance(data, dict) and isinstance(data.get("transfers"), list):
        rows, found = [], False
        for old in data["transfers"]:
            if isinstance(old, dict) and old.get("slug") == item["slug"]:
                rows.append(merge(old))
                found = True
            else:
                rows.append(old)
        if not found:
            rows.insert(max(0, min(position - 1, len(rows))), item)
        data["transfers"] = rows
        write_json(path, data)
        action(f"Updated data/transfers.json.transfers: {item['slug']}")
    else:
        crit("data/transfers.json has unsupported structure")


def default_body(item: Dict[str, Any]) -> str:
    player = item["player_name"]
    from_club = item["from_club_name"]
    to_club = item["to_club_name"]
    return f"""## {player} → {to_club}

{player} готовится перейти из {from_club} в {to_club}. По информации {item.get("source_name")}, клубы согласовали сделку, а сумма перехода составляет **{item.get("fee")}**.

Для {to_club} это важное усиление состава. Игрок добавляет команде новую опцию в атаке и может быстро стать заметной частью проекта.

### Детали трансфера

- Игрок: **{player}**
- Откуда: **{from_club}**
- Куда: **{to_club}**
- Статус: **{item.get("status_label")}**
- Сумма: **{item.get("fee")}**
- Источник: **{item.get("source_name")}**

### Профиль игрока

{player} — {item.get("position_ru")} сборной {item.get("country")}. Рабочая нога — {item.get("foot_ru")}, рост — {item.get("height")}. На странице сохранены стандартные поля для карточки игрока: страна, флаг, позиция, рабочая нога, рост, рыночная стоимость и динамика стоимости.
"""


def write_page(item: Dict[str, Any], args) -> None:
    page = ROOT / "content" / "transfers" / item["slug"] / "index.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    front, _ = parse_frontmatter(page)

    # Remove earlier dedicated layout hack.
    front = remove_fm_key(front, "layout")

    for key, value in item.items():
        if isinstance(value, (str, int, float, bool)):
            front = set_fm_key(front, key, value)

    front = set_fm_key(front, "title", args.title)
    front = set_fm_key(front, "seo_title", args.seo_title or args.title)
    front = set_fm_key(front, "description", args.description)
    front = set_fm_key(front, "date", args.date)
    front = set_fm_key(front, "draft", "false")
    front = set_fm_key(front, "type", "transfers")

    body = args.body or default_body(item)
    page.write_text("---\n" + front.strip() + "\n---\n\n" + body.strip() + "\n", encoding="utf-8")
    action(f"Transfer page written: {rel(page)}")


def patch_homepage_slider(item: Dict[str, Any]) -> None:
    index = ROOT / "layouts" / "index.html"
    if not index.exists():
        warn("layouts/index.html not found; homepage slider patch skipped")
        return

    text = index.read_text(encoding="utf-8", errors="replace")
    original = text
    slug = item["slug"]
    var = re.sub(r"[^a-z0-9]+", "", slugify(item["player_name"]))
    url_var = "$" + var + "URL"
    hero_var = "$" + var + "Hero"

    if url_var not in text:
        insertion = '{{ ' + url_var + ' := "transfers/' + slug + '/" | relURL }}'
        matches = list(re.finditer(r'\{\{\s*\$[a-zA-Z0-9]+URL\s*:=\s*"transfers/[^"]+"\s*\|\s*relURL\s*\}\}', text))
        if matches:
            pos = matches[-1].end()
            text = text[:pos] + "\n" + insertion + text[pos:]
        else:
            text = insertion + "\n" + text

    if hero_var not in text:
        hero = str(item.get("hero_image") or "").lstrip("/")
        insertion = '{{ ' + hero_var + ' := "' + hero + '" | relURL }}'
        matches = list(re.finditer(r'\{\{\s*\$[a-zA-Z0-9]+Hero\s*:=\s*"images/homepage/featured/[^"]+"\s*\|\s*relURL\s*\}\}', text))
        if matches:
            pos = matches[-1].end()
            text = text[:pos] + "\n" + insertion + text[pos:]
        else:
            text = insertion + "\n" + text

    # If JS transfer array exists and slug isn't in it, add item before closing bracket.
    if "window.PF_FEATURED_TRANSFERS" in text and slug not in text:
        obj_lines = [
            "{",
            f'                name: "{item["player_name"]}",',
            '                link: "{{ ' + url_var + ' }}",',
            '                heroImage: "{{ ' + hero_var + ' }}",',
            f'                alt: "{item["player_name"]} — трансфер {item["to_club_name"]}"',
            "            }",
        ]
        obj = "\n".join(obj_lines)
        pattern = re.compile(r'(window\.PF_FEATURED_TRANSFERS\s*=\s*\[)(.*?)(\s*\];)', re.S)
        m = pattern.search(text)
        if m:
            arr = m.group(2).strip()
            new_arr = arr.rstrip()
            if new_arr and not new_arr.endswith(","):
                new_arr += ","
            new_arr += "\n            " + obj
            text = text[:m.start(2)] + "\n            " + new_arr + "\n        " + text[m.end(2):]
            action("Homepage PF_FEATURED_TRANSFERS patched")
        else:
            warn("PF_FEATURED_TRANSFERS exists but could not be parsed")

    if text != original:
        index.write_text(text, encoding="utf-8")
        action("layouts/index.html updated")
    else:
        action("Homepage slider already contains transfer or no patch needed")


class ImgParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag.lower() == "img":
            self.imgs.append(data)
        if tag.lower() == "a":
            self.links.append(data)


def run_hugo_check(item: Dict[str, Any]) -> None:
    build_dir = ROOT / "var" / "auto-news-main-render-check"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(["hugo", "--destination", str(build_dir)], cwd=ROOT, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        warn("Hugo not found in PATH; render check skipped")
        return
    except subprocess.TimeoutExpired:
        crit("Hugo render check timed out")
        return
    except Exception as exc:
        crit(f"Hugo render check failed to start: {exc}")
        return

    if result.returncode != 0:
        crit("Hugo build failed")
        if result.stderr:
            REPORT_LINES.append(result.stderr[-5000:])
        return

    action("Hugo build passed")

    rendered = list(build_dir.rglob(f"{item['slug']}/index.html"))
    if not rendered:
        crit(f"Rendered page not found: {item['slug']}/index.html")
        return

    html = rendered[0].read_text(encoding="utf-8", errors="replace")
    for token in ["Неизвестный клуб", "НЕИЗВЕСТНЫЙ КЛУБ", "Неизвестная страна", "undefined", "null"]:
        if token in html:
            crit(f"Rendered page contains bad token: {token}")

    if item["player_name"] not in html:
        crit("Rendered page does not contain player name")

    for key in ["from_club_logo", "to_club_logo", "player_image", "homepage_image", "country_flag_image"]:
        value = item.get(key) or ""
        if value and not static_exists(value):
            crit(f"Missing static image for {key}: {value}")

    parser = ImgParser()
    parser.feed(html)
    for img in parser.imgs:
        src = (img.get("src") or "").strip()
        if not src or src.startswith(("http://", "https://", "data:")):
            continue
        clean = src.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("/promyachik/"):
            clean = clean[len("/promyachik"):]
        if clean.startswith("/"):
            p = ROOT / "static" / clean.lstrip("/")
        else:
            p = ROOT / "static" / clean
        if not p.exists():
            crit(f"Rendered img source missing: {src}")

    expected = f"/transfers/{item['slug']}/"
    for key in ["url", "link", "href", "permalink", "page_url"]:
        if item.get(key) != expected:
            crit(f"Wrong transfer URL field {key}: {item.get(key)} expected {expected}")

    if not CRITICAL:
        action("Rendered page passed checks")


def write_report(slug: str) -> Path:
    reports = ROOT / "var" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / f"91_auto_news_on_main_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    lines = [
        "PROFUTBIK AUTO NEWS_ON_MAIN REPORT",
        "=" * 80,
        f"Project: {ROOT}",
        f"Slug: {slug}",
        "",
        f"CRITICAL: {len(CRITICAL)}",
        f"WARNINGS: {len(WARNINGS)}",
        f"ACTIONS: {len(ACTIONS)}",
        "",
    ]

    if CRITICAL:
        lines += ["CRITICAL", "-" * 80] + CRITICAL + [""]
    if WARNINGS:
        lines += ["WARNINGS", "-" * 80] + WARNINGS + [""]
    if ACTIONS:
        lines += ["ACTIONS", "-" * 80] + ACTIONS + [""]

    lines += ["FULL LOG", "-" * 80] + REPORT_LINES
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def run(args) -> int:
    global ROOT
    ROOT = Path(args.root).resolve()

    log("START: ProFutbik auto NEWS_ON_MAIN pipeline")
    log(f"Project: {ROOT}")
    log(f"Player: {args.player}")

    copy_payload_assets()
    remove_dangerous_data_folder()

    player = find_player(args.player, args.player_id)
    if not player:
        crit(f"Player not found in data/playerdb/players.json: {args.player}")
        report = write_report(args.slug)
        log(f"REPORT: {report}")
        return 2
    action(f"Player found in playerdb: id={player.get('id')} name={player.get('name')}")

    from_club = find_club(args.from_club_id, args.from_club)
    to_club = find_club(args.to_club_id, args.to_club)
    if not from_club:
        crit(f"From club not found in data/club-logos.json: id={args.from_club_id} name={args.from_club}")
    else:
        action(f"From club found: id={from_club.get('id')} name={from_club.get('configured_name') or from_club.get('name')}")
    if not to_club:
        crit(f"To club not found in data/club-logos.json: id={args.to_club_id} name={args.to_club}")
    else:
        action(f"To club found: id={to_club.get('id')} name={to_club.get('configured_name') or to_club.get('name')}")

    if not from_club or not to_club:
        report = write_report(args.slug)
        log(f"REPORT: {report}")
        return 2

    images = resolve_player_images(player, args.allow_api_photo_fallback)
    flag_url = ensure_flag(args.country, args.country_code)
    item = make_item(args, player, from_club, to_club, images, flag_url)

    write_page(item, args)
    upsert_transfers_json(item, args.homepage_position)
    patch_homepage_slider(item)
    run_hugo_check(item)

    report = write_report(item["slug"])
    log(f"REPORT: {report}")

    if CRITICAL:
        log("PUBLISH BLOCKED")
        return 2

    if WARNINGS:
        log("PUBLISH OK WITH WARNINGS")
        return 0

    log("PUBLISH OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--player", required=True)
    p.add_argument("--player-id", type=int, default=None)
    p.add_argument("--from-club", required=True)
    p.add_argument("--from-club-id", type=int, required=True)
    p.add_argument("--to-club", required=True)
    p.add_argument("--to-club-id", type=int, required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--seo-title", default="")
    p.add_argument("--description", required=True)
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p.add_argument("--status", default="agreement")
    p.add_argument("--fee", required=True)
    p.add_argument("--source-name", required=True)
    p.add_argument("--source-url", default="")
    p.add_argument("--country", default="Portugal")
    p.add_argument("--country-code", default="PT")
    p.add_argument("--country-flag", default="🇵🇹")
    p.add_argument("--position", default="Centre-Forward")
    p.add_argument("--position-ru", default="Нападающий")
    p.add_argument("--main-position", default="CF")
    p.add_argument("--foot", default="right")
    p.add_argument("--foot-ru", default="Правая")
    p.add_argument("--height", default="1.85 м")
    p.add_argument("--birth-date", default="20.06.2001")
    p.add_argument("--age", default="25")
    p.add_argument("--market-value", default="€30M")
    p.add_argument("--league", default="Serie A")
    p.add_argument("--homepage-image", default="/images/homepage/featured/goncalo-ramos-ac-milan-card.png")
    p.add_argument("--hero-image", default="/images/homepage/featured/goncalo-ramos-ac-milan-hero.png")
    p.add_argument("--homepage-position", type=int, default=4)
    p.add_argument("--show-in-footer-ticker", action="store_true")
    p.add_argument("--allow-api-photo-fallback", action="store_true")
    p.add_argument("--body", default="")
    return p


if __name__ == "__main__":
    sys.exit(run(build_parser().parse_args()))
