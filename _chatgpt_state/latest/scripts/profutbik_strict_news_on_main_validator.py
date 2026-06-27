# -*- coding: utf-8 -*-
from __future__ import annotations

# PROFUTBIK_STDOUT_UTF8_PATCH
try:
    import sys as _pf_sys
    if hasattr(_pf_sys.stdout, 'reconfigure'):
        _pf_sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(_pf_sys.stderr, 'reconfigure'):
        _pf_sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
# /PROFUTBIK_STDOUT_UTF8_PATCH


from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.cwd()
CHECKS: List[Dict[str, Any]] = []
LINES: List[str] = []
BLOCKERS: List[str] = []
WARNINGS: List[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)
    LINES.append(str(msg))


def norm(value: Any) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower().replace("_", "-").replace(" ", "-").replace("'", "")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def check(name: str, ok: bool, details: str = "", blocker: bool = True) -> None:
    status = "OK" if ok else ("BLOCK" if blocker else "WARN")
    row = {"name": name, "status": status, "details": details, "blocker": blocker}
    CHECKS.append(row)
    log(f"{status}: {name}" + (f" — {details}" if details else ""))
    if not ok and blocker:
        BLOCKERS.append(f"{name}: {details}")
    if not ok and not blocker:
        WARNINGS.append(f"{name}: {details}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def static_path(value: str) -> Path:
    value = str(value or "").strip().replace("\\", "/")
    if value.startswith("/promyachik/"):
        value = value[len("/promyachik/"):]
    if value.startswith("/"):
        value = value[1:]
    if value.startswith("static/"):
        return ROOT / value
    return ROOT / "static" / value


def static_exists(value: str) -> bool:
    if not value:
        return False
    if value.startswith(("http://", "https://", "data:")):
        return True
    return static_path(value).exists()


def slugify(value: str) -> str:
    s = norm(value)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "transfer"


def load_playerdb() -> List[Dict[str, Any]]:
    path = ROOT / "data" / "playerdb" / "players.json"
    data = read_json(path)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ["items", "players", "data"]:
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def find_player(player_name: str, player_id: str = "") -> Optional[Dict[str, Any]]:
    players = load_playerdb()
    if player_id:
        for p in players:
            if str(p.get("id") or p.get("player_id") or "") == str(player_id):
                return p

    wanted = norm(player_name)
    parts = [x for x in wanted.split("-") if x]
    best = None
    score_best = 0

    for p in players:
        name = norm(p.get("name") or p.get("player_name") or p.get("full_name") or "")
        score = 100 if name == wanted else 0
        score += sum(20 for part in parts if part and part in name)
        if score > score_best:
            best = p
            score_best = score

    return best if score_best >= 35 else None


def load_clubs() -> Dict[str, Dict[str, Any]]:
    data = read_json(ROOT / "data" / "club-logos.json")
    if isinstance(data, dict) and isinstance(data.get("clubs"), dict):
        return {str(k): v for k, v in data["clubs"].items() if isinstance(v, dict)}
    return {}


def find_club(club_id: str, club_name: str) -> Optional[Dict[str, Any]]:
    clubs = load_clubs()
    if str(club_id) in clubs:
        return clubs[str(club_id)]

    wanted = norm(club_name)
    for club in clubs.values():
        name = norm(club.get("configured_name") or club.get("name") or "")
        if wanted and (wanted == name or wanted in name or name in wanted):
            return club
    return None


def frontmatter(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def image_has_transparency(path: Path) -> Tuple[bool, str]:
    try:
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        alpha = im.getchannel("A")
        extrema = alpha.getextrema()
        if extrema[0] < 250:
            return True, f"alpha_min={extrema[0]}, alpha_max={extrema[1]}"
        return False, f"no meaningful transparency, alpha_min={extrema[0]}, alpha_max={extrema[1]}"
    except Exception as exc:
        return False, f"cannot inspect alpha: {exc}"


def image_likely_white_background(path: Path) -> Tuple[bool, str]:
    try:
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        pts = []
        # Sample border pixels only: white border usually means background remains.
        step_x = max(1, w // 60)
        step_y = max(1, h // 60)
        for x in range(0, w, step_x):
            pts.append(im.getpixel((x, 0)))
            pts.append(im.getpixel((x, h - 1)))
        for y in range(0, h, step_y):
            pts.append(im.getpixel((0, y)))
            pts.append(im.getpixel((w - 1, y)))
        opaque = [p for p in pts if p[3] > 245]
        if not opaque:
            return False, "border mostly transparent"
        white = [p for p in opaque if p[0] > 235 and p[1] > 235 and p[2] > 235]
        ratio = len(white) / max(1, len(opaque))
        return ratio >= 0.55, f"white_border_ratio={ratio:.2f}"
    except Exception as exc:
        return True, f"cannot inspect white background: {exc}"


class HtmlInfo(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs: List[Dict[str, str]] = []
        self.links: List[Dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag.lower() == "img":
            self.imgs.append(d)
        if tag.lower() == "a":
            self.links.append(d)


def run_hugo(out_dir: Path) -> Tuple[bool, str]:
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        res = subprocess.run(["hugo", "--destination", str(out_dir)], cwd=ROOT, capture_output=True, text=True, timeout=120)
    except Exception as exc:
        return False, f"cannot run Hugo: {exc}"

    tail = ""
    if res.stdout:
        tail += "STDOUT:\n" + res.stdout[-3000:] + "\n"
    if res.stderr:
        tail += "STDERR:\n" + res.stderr[-6000:] + "\n"
    return res.returncode == 0, tail


def normalize_rendered_src(src: str) -> Optional[Path]:
    if not src or src.startswith(("http://", "https://", "data:")):
        return None
    s = src.split("?", 1)[0].split("#", 1)[0].replace("\\", "/")
    if s.startswith("/promyachik/"):
        s = s[len("/promyachik"):]
    if s.startswith("/"):
        return ROOT / "static" / s.lstrip("/")
    return ROOT / "static" / s


def fetch_live(slug: str) -> Optional[str]:
    url = f"http://127.0.0.1:1313/promyachik/transfers/{slug}/"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def discover_pixelcut() -> Dict[str, Any]:
    candidates = []
    for pat in [
        "*pixelcut*.bat",
        "**/*pixelcut*.bat",
        "**/*pixelcut*.py",
        "**/*background*remov*.py",
        "**/*cutout*.py",
    ]:
        candidates.extend(ROOT.glob(pat))

    unique = []
    seen = set()
    for p in candidates:
        key = str(p).lower()
        if key not in seen and p.is_file():
            seen.add(key)
            unique.append(p)

    # Do not print secrets. Only detect likely config/env names.
    config_hits = []
    for pat in ["**/*pixelcut*.json", "**/*pixelcut*.env", "**/*.env"]:
        for p in ROOT.glob(pat):
            if p.is_file():
                config_hits.append(p)

    return {
        "scripts": unique[:30],
        "configs": config_hits[:30],
    }


def validate(args) -> int:
    global ROOT
    ROOT = Path(args.root).resolve()

    slug = args.slug
    expected_url_path = f"/promyachik/transfers/{slug}/"
    page_path = ROOT / "content" / "transfers" / slug / "index.md"

    log("PROFUTBIK STRICT NEWS_ON_MAIN VALIDATOR")
    log("=" * 90)
    log(f"Project: {ROOT}")
    log(f"Slug: {slug}")
    log("")

    # 1. Player DB
    player = find_player(args.player, args.player_id)
    check("Игрок найден в playerdb", player is not None, f"{args.player} / id={args.player_id}")
    player_id = str((player or {}).get("id") or args.player_id or "")

    # 2. API raw photo
    api_photo = ""
    if player:
        api_photo = str(player.get("photo_raw") or f"images/players/api/{player_id}.png")
    else:
        api_photo = f"images/players/api/{args.player_id}.png"

    api_photo_path = static_path(api_photo)
    check("API-фото игрока существует", api_photo_path.exists(), rel(api_photo_path))

    # 3. Cutout exists and transparent
    cutout_path = ROOT / "static" / "images" / "players" / "cutout" / f"{player_id}.png"
    check("Cutout-фото существует", cutout_path.exists(), rel(cutout_path))

    if cutout_path.exists():
        transparent, alpha_details = image_has_transparency(cutout_path)
        check("Cutout-фото реально прозрачное", transparent, alpha_details)
        white_bg, white_details = image_likely_white_background(cutout_path)
        check("Cutout-фото не имеет белого фона по краям", not white_bg, white_details)
    elif api_photo_path.exists():
        white_bg, white_details = image_likely_white_background(api_photo_path)
        check("Raw API-фото не должно публиковаться с белым фоном", not white_bg, white_details + " — нужен Pixelcut", blocker=True)

    # 4. Pixelcut integration discoverability
    pix = discover_pixelcut()
    check(
        "Pixelcut/удаление фона найдено в проекте",
        bool(pix["scripts"] or pix["configs"]),
        "scripts=" + ", ".join(rel(p) for p in pix["scripts"][:8]) + ("; configs=" + ", ".join(rel(p) for p in pix["configs"][:5]) if pix["configs"] else ""),
        blocker=False,
    )

    # 5. Country flag
    flag_candidates = [
        ROOT / "static" / "images" / "flags" / f"{args.country_slug}.svg",
        ROOT / "static" / "images" / "flags" / f"{args.country_slug}.png",
        ROOT / "static" / "images" / "flags" / f"{args.country_code.lower()}.svg",
        ROOT / "static" / "images" / "flags" / f"{args.country_code.lower()}.png",
    ]
    existing_flags = [p for p in flag_candidates if p.exists()]
    check("Файл флага страны существует", bool(existing_flags), ", ".join(rel(p) for p in existing_flags) or "not found")

    if existing_flags:
        flag_white, flag_details = image_likely_white_background(existing_flags[0])
        # SVG inspection can fail; do not block on white-background for svg.
        block_flag = existing_flags[0].suffix.lower() != ".svg"
        check("Флаг не выглядит как белая заглушка", (not flag_white) or not block_flag, flag_details, blocker=block_flag)

    # 6. Clubs/logos
    from_club = find_club(args.from_club_id, args.from_club)
    to_club = find_club(args.to_club_id, args.to_club)

    check("Клуб-источник найден в club-logos.json", from_club is not None, f"id={args.from_club_id} name={args.from_club}")
    check("Клуб-получатель найден в club-logos.json", to_club is not None, f"id={args.to_club_id} name={args.to_club}")

    from_logo = (from_club or {}).get("logo") or ""
    to_logo = (to_club or {}).get("logo") or ""
    check("Логотип клуба-источника существует", static_exists(from_logo), f"{from_logo} -> {rel(static_path(from_logo))}")
    check("Логотип клуба-получателя существует", static_exists(to_logo), f"{to_logo} -> {rel(static_path(to_logo))}")

    # 7. Page frontmatter
    fm = frontmatter(page_path)
    check("Страница трансфера существует", page_path.exists(), rel(page_path))
    check("На странице есть player_image/cutout", bool(fm.get("cutout_player_image") or fm.get("player_image")), f"player_image={fm.get('player_image')} cutout={fm.get('cutout_player_image')}")
    check("На странице есть country_flag_image/flag_image", bool(fm.get("country_flag_image") or fm.get("flag_image")), f"country_flag_image={fm.get('country_flag_image')} flag_image={fm.get('flag_image')}")
    check("На странице есть from_club_id/from_club_logo", bool(fm.get("from_club_id") and fm.get("from_club_logo")), f"id={fm.get('from_club_id')} logo={fm.get('from_club_logo')}")
    check("На странице есть to_club_id/to_club_logo", bool(fm.get("to_club_id") and fm.get("to_club_logo")), f"id={fm.get('to_club_id')} logo={fm.get('to_club_logo')}")

    # 8. Hugo/rendered HTML
    out_dir = ROOT / "var" / "strict-news-validator-render"
    hugo_ok, hugo_log = run_hugo(out_dir)
    check("Hugo build проходит", hugo_ok, hugo_log[-1000:])

    built_html = ""
    built_file = None
    if hugo_ok:
        matches = list(out_dir.rglob(f"{slug}/index.html"))
        built_file = matches[0] if matches else None
        check("Готовый HTML страницы найден", built_file is not None, str(built_file or "missing"))
        if built_file:
            built_html = built_file.read_text(encoding="utf-8", errors="replace")

    if built_html:
        parser = HtmlInfo()
        parser.feed(built_html)

        for bad in ["Неизвестный клуб", "НЕИЗВЕСТНЫЙ КЛУБ", "undefined", "null"]:
            check(f"В HTML нет токена {bad}", bad not in built_html, f"token={bad}")

        player_image_expected = f"/promyachik/images/players/cutout/{player_id}.png"
        check("HTML содержит cutout-фото игрока", player_image_expected in built_html, player_image_expected)

        flag_ok_html = (f"/promyachik/images/flags/{args.country_slug}.svg" in built_html) or (f"/promyachik/images/flags/{args.country_code.lower()}.svg" in built_html) or ("/promyachik/images/flags/" in built_html and args.country_slug in built_html)
        check("HTML содержит флаг страны", flag_ok_html, f"country={args.country_slug}/{args.country_code}")

        from_logo_html = f"/promyachik/{from_logo}".replace("//", "/") if from_logo else ""
        to_logo_html = f"/promyachik/{to_logo}".replace("//", "/") if to_logo else ""
        check("HTML содержит логотип клуба-источника", (from_logo and from_logo in built_html) or (from_logo_html and from_logo_html in built_html), from_logo)
        check("HTML содержит логотип клуба-получателя", (to_logo and to_logo in built_html) or (to_logo_html and to_logo_html in built_html), to_logo)

        # Market value/dynamic block: flexible checks by content and logos.
        market_tokens = ["market", "стоимост", "Стоимость", "value", "€"]
        has_market_block = any(t in built_html for t in market_tokens)
        check("HTML содержит блок/данные динамики стоимости", has_market_block, "looking for market/value/стоимость/€ tokens")
        if has_market_block:
            check("Динамика стоимости содержит логотип клуба-источника", from_logo and from_logo in built_html, from_logo)
            check("Динамика стоимости содержит логотип клуба-получателя", to_logo and to_logo in built_html, to_logo)

        expected_href = f"/promyachik/transfers/{slug}/"
        page_link_ok = any((a.get("href") or "") == expected_href for a in parser.links)
        check("HTML содержит правильную ссылку на страницу трансфера", page_link_ok or expected_href in built_html, expected_href)

        # Rendered img src existence
        missing_imgs = []
        for img in parser.imgs:
            src = img.get("src") or ""
            p = normalize_rendered_src(src)
            if p and not p.exists():
                missing_imgs.append(f"{src} -> {rel(p)}")
        check("В готовом HTML нет битых локальных img", not missing_imgs, "; ".join(missing_imgs[:12]))

    # 9. Live server and 404 check
    live_html = fetch_live(slug)
    check("Live Hugo server отдаёт страницу, не 404", live_html is not None and "404" not in live_html[:1000], f"http://127.0.0.1:1313/promyachik/transfers/{slug}/", blocker=False)

    # Write report
    report_dir = ROOT / "var" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = report_dir / f"97_strict_news_on_main_validator_{slug}_{stamp}.txt"

    summary = []
    summary.append("PROFUTBIK STRICT NEWS_ON_MAIN VALIDATOR REPORT")
    summary.append("=" * 90)
    summary.append(f"Project: {ROOT}")
    summary.append(f"Slug: {slug}")
    summary.append(f"Player: {args.player} / {player_id}")
    summary.append("")
    summary.append(f"RESULT: {'PUBLISH BLOCKED' if BLOCKERS else 'PUBLISH OK'}")
    summary.append(f"BLOCKERS: {len(BLOCKERS)}")
    summary.append(f"WARNINGS: {len(WARNINGS)}")
    summary.append("")
    if BLOCKERS:
        summary.append("BLOCKERS")
        summary.append("-" * 90)
        summary.extend(BLOCKERS)
        summary.append("")
    if WARNINGS:
        summary.append("WARNINGS")
        summary.append("-" * 90)
        summary.extend(WARNINGS)
        summary.append("")
    summary.append("FULL CHECK LOG")
    summary.append("-" * 90)
    summary.extend(LINES)

    report.write_text("\n".join(summary), encoding="utf-8")
    print("")
    print("REPORT SAVED:")
    print(report)
    print("")
    print("RESULT:", "PUBLISH BLOCKED" if BLOCKERS else "PUBLISH OK")

    return 2 if BLOCKERS else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--player", required=True)
    p.add_argument("--player-id", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--from-club", required=True)
    p.add_argument("--from-club-id", required=True)
    p.add_argument("--to-club", required=True)
    p.add_argument("--to-club-id", required=True)
    p.add_argument("--country", default="Portugal")
    p.add_argument("--country-slug", default="portugal")
    p.add_argument("--country-code", default="PT")
    return p


if __name__ == "__main__":
    sys.exit(validate(build_parser().parse_args()))
