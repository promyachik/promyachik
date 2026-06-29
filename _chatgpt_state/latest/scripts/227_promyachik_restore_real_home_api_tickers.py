
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import json
import re
import sys

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_CANDIDATES = [Path(r"C:\Users\Dmitrii\Promyachik"), Path(r"C:\Users\Dmitrii\promyachik")]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])
RESTORE = PACKAGE_DIR / "restore_files"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_227_before_real_home_api_tickers_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_227_restore_real_home_api_tickers_report.txt"

commands = []
changed = []
warnings = []
home_candidates = []

BAD_TEXT = ["Сайт запускается", "cite", "\\n\\n", "\\nplayer_image", "PROMYACHIK 226", "PROMYACHIK 225"]

def sha(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except Exception:
        return str(path)

def backup(path: Path):
    if path.exists():
        dst = BACKUP_DIR / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            if path.is_dir():
                shutil.copytree(path, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(path, dst)

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def copy_restore(rel_path: str, dst: Path, label: str):
    src = RESTORE / rel_path
    before = sha(dst)
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((rel(dst), label + f" <= {src}", before != after, before, after))

def run(cmd):
    p = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)
    commands.append({"cmd": " ".join(cmd), "returncode": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]})
    return p

def strip_quotes(value: str) -> str:
    value = value.strip()
    if value and value[0:1] in ['"', "'"] and value[-1:] == value[0]:
        value = value[1:-1]
    return value.strip()

def parse_front_matter(path: Path) -> dict:
    text = read(path)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data = {}
    current_key = None
    current_list = None
    for raw_line in text[3:end].strip("\n").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = ""
                current_key = key
                current_list = None
            else:
                data[key] = strip_quotes(value)
                current_key = key
                current_list = None
        elif current_key and line.lstrip().startswith("-"):
            item = strip_quotes(line.lstrip()[1:].strip())
            if current_list is None:
                current_list = []
                data[current_key] = current_list
            current_list.append(item)
    return data

def norm_path(value: str) -> str:
    if not value:
        return ""
    value = str(value).strip().replace("\\", "/")
    if value.startswith("/"):
        value = value[1:]
    return value

def path_exists_static(value: str) -> bool:
    return bool(value) and (PROJECT / "static" / norm_path(value)).exists()

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def safe_int(value):
    try:
        if value in ("", None, "false", "False"):
            return None
        return int(str(value).strip())
    except Exception:
        return None

def first_nonempty(*values):
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if value and value.lower() not in ("false", "none", "null"):
            return value
    return ""

def score_home_candidate(path: Path, text: str) -> int:
    if not text or len(text) < 500:
        return -100000
    if any(token in text for token in BAD_TEXT):
        return -100000
    for token in ["kylian-mbappe-real-madrid-hero.png", "florian-wirtz-liverpool-hero.png", "bernardo-silva-real-madrid-hero.png", "Главный трансфер дня"]:
        if token not in text:
            return -100000
    score = min(len(text) // 100, 400)
    for token, points in [("pf-featured-dot", 600), ("data-featured-index", 600), ("pf-featured", 350), ("data-featured", 250), ("Mbappé", 180), ("Wirtz", 180), ("Bernardo", 180), ("{{", 150), ("relURL", 150)]:
        if token in text:
            score += points
    full = str(path).lower()
    if "66_clean_index_restore_hugo_safe" in full:
        score += 1200
    if "_backup_66" in full or "step66" in full or "package_66" in full:
        score += 900
    if path.name.lower() in ("index.html", "layouts__index.html"):
        score += 250
    if "227_" in full or "226_" in full or "225_" in full:
        score -= 2000
    return score

def find_real_home_candidate():
    roots = [PROJECT, PROJECT / "backups", PROJECT / "payload", PROJECT / "_chatgpt_state"]
    seen = set()
    candidates = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            pstr = str(path)
            if pstr in seen:
                continue
            seen.add(pstr)
            low = pstr.lower()
            if any(skip in low for skip in ["\\public\\", "/public/", "\\resources\\", "/resources/", "\\node_modules\\", "/node_modules/", "\\.git\\", "/.git/", "\\static\\images\\", "/static/images/", "\\var\\", "/var/"]):
                continue
            if path.stat().st_size > 2_000_000:
                continue
            name = path.name.lower()
            if not (name in {"index.html", "layouts__index.html", "66_clean_index_restore_hugo_safe.bat", "66_clean_index_restore_hugo_safe.py"} or name.endswith((".html", ".txt", ".md", ".bat", ".py"))):
                continue
            try:
                text = read(path)
            except Exception:
                continue
            score = score_home_candidate(path, text)
            if score > 0:
                candidates.append((score, path, text, "direct"))
                continue
            if "kylian-mbappe-real-madrid-hero.png" in text and "Главный трансфер дня" in text:
                start = text.find("<!DOCTYPE html")
                end = text.rfind("</html>")
                if start != -1 and end != -1:
                    html = text[start:end + len("</html>")]
                    score = score_home_candidate(path, html)
                    if score > 0:
                        candidates.append((score + 120, path, html, "extracted-html"))
    candidates.sort(key=lambda x: x[0], reverse=True)
    global home_candidates
    home_candidates = [(score, rel(path), kind, len(text)) for score, path, text, kind in candidates[:12]]
    return candidates[0] if candidates else None

def restore_home_from_existing_candidate():
    candidate = find_real_home_candidate()
    if not candidate:
        raise RuntimeError("Не найден настоящий старый layouts/index.html из пакета 66/backup. Новая главная не будет написана заново.")
    score, path, text, kind = candidate
    write(PROJECT / "layouts" / "index.html", text, f"restore real old homepage candidate score={score} kind={kind} source={path}")

def load_club_logos():
    path = PROJECT / "data" / "club-logos.json"
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("clubs"), dict):
        raise RuntimeError("data/club-logos.json отсутствует или сломан. Нельзя ставить выдуманные логотипы.")
    return data["clubs"]

def club_by_id(clubs, cid):
    if cid is None:
        return None
    return clubs.get(str(cid)) or clubs.get(cid)

def club_name_logo(clubs, cid, *name_candidates, logo_candidates=()):
    club = club_by_id(clubs, cid)
    name = first_nonempty(*name_candidates)
    logo = first_nonempty(*logo_candidates)
    if club:
        name = first_nonempty(club.get("configured_name"), club.get("name"), name)
        logo = first_nonempty(club.get("logo"), logo)
    if cid and not logo and path_exists_static(f"images/clubs/api/{cid}.png"):
        logo = f"images/clubs/api/{cid}.png"
    if logo and path_exists_static(logo):
        return name, norm_path(logo)
    if cid and path_exists_static(f"images/clubs/api/{cid}.png"):
        return name, f"images/clubs/api/{cid}.png"
    return name, norm_path(logo)

def player_image_from_params(params):
    for candidate in [params.get("ticker_player_image"), params.get("cutout_player_image"), params.get("player_image"), params.get("api_player_image"), params.get("homepage_image"), params.get("card_image"), params.get("concept_art")]:
        candidate = norm_path(str(candidate or ""))
        if candidate and path_exists_static(candidate):
            return candidate
    player_id = safe_int(first_nonempty(params.get("player_id"), params.get("api_player_id")))
    if player_id and path_exists_static(f"images/players/api/{player_id}.png"):
        return f"images/players/api/{player_id}.png"
    return ""

def rebuild_transfers_data_from_content():
    clubs = load_club_logos()
    pages = []
    for md in sorted((PROJECT / "content" / "transfers").rglob("index.md")):
        params = parse_front_matter(md)
        if not params:
            continue
        player = first_nonempty(params.get("player"), params.get("player_name"), params.get("title"))
        if not player:
            continue
        slug = md.parent.name
        url = first_nonempty(params.get("url"), f"transfers/{slug}/").strip()
        if url.startswith("/"):
            url = url[1:]
        if not url.endswith("/"):
            url += "/"
        from_id = safe_int(first_nonempty(params.get("from_club_id"), params.get("from_team_id"), params.get("from_api_id"), params.get("source_club_id"), params.get("source_team_id"), params.get("source_api_id"), params.get("old_club_id"), params.get("from_id")))
        to_id = safe_int(first_nonempty(params.get("to_club_id"), params.get("to_team_id"), params.get("to_api_id"), params.get("target_club_id"), params.get("target_team_id"), params.get("target_api_id"), params.get("new_club_id"), params.get("to_id")))
        from_name, from_logo = club_name_logo(clubs, from_id, params.get("from_club_name"), params.get("from_name"), params.get("from_club"), params.get("source_club"), params.get("old_club"), logo_candidates=[params.get("from_club_logo"), params.get("from_team_logo"), params.get("from_logo"), params.get("source_club_logo"), params.get("source_team_logo"), params.get("from_crest")])
        to_name, to_logo = club_name_logo(clubs, to_id, params.get("to_club_name"), params.get("to_name"), params.get("to_club"), params.get("target_club"), params.get("new_club"), logo_candidates=[params.get("to_club_logo"), params.get("to_team_logo"), params.get("to_logo"), params.get("target_club_logo"), params.get("target_team_logo"), params.get("to_crest")])
        player_id = safe_int(first_nonempty(params.get("player_id"), params.get("api_player_id")))
        player_image = player_image_from_params(params)
        pages.append({
            "status": first_nonempty(params.get("status"), "rumour"),
            "status_label": first_nonempty(params.get("status_label"), ""),
            "player": player,
            "player_id": player_id or "",
            "player_image": player_image,
            "player_image_fallback": f"https://media.api-sports.io/football/players/{player_id}.png" if player_id else "",
            "from_club_id": from_id or "",
            "from_club_name": from_name,
            "from_club_logo": from_logo,
            "to_club_id": to_id or "",
            "to_club_name": to_name,
            "to_club_logo": to_logo,
            "from_club": {"id": from_id or "", "name": from_name, "logo": from_logo},
            "to_club": {"id": to_id or "", "name": to_name, "logo": to_logo},
            "fee": first_nonempty(params.get("transfer_fee"), params.get("fee"), params.get("value"), ""),
            "url": url,
            "date": first_nonempty(params.get("date"), params.get("lastmod"), ""),
            "show_in_top_ticker": str(params.get("show_in_top_ticker", "true")).lower() != "false",
            "show_in_footer_ticker": str(params.get("show_in_footer_ticker", "true")).lower() != "false",
        })
    if not pages:
        raise RuntimeError("Не удалось собрать data/transfers.json из content/transfers.")
    pages.sort(key=lambda x: x.get("date", ""), reverse=True)
    write(PROJECT / "data" / "transfers.json", json.dumps(pages, ensure_ascii=False, indent=2) + "\n", "rebuild transfers.json from real content pages + API-Football club-logo map")
    return pages

def write_ticker_partials_and_css():
    copy_restore("layouts/partials/transfer-ticker.html", PROJECT / "layouts" / "partials" / "transfer-ticker.html", "restore top ticker using API-Football club-logo ids")
    copy_restore("layouts/partials/footer-transfer-ticker.html", PROJECT / "layouts" / "partials" / "footer-transfer-ticker.html", "restore bottom ticker with player photos from API/local paths")
    style = PROJECT / "static" / "css" / "style.css"
    existing = read(style) if style.exists() else ""
    for pattern in [
        r"/\* PROMYACHIK 227 API TICKERS RESTORE START \*/.*?/\* PROMYACHIK 227 API TICKERS RESTORE END \*/",
        r"/\* PROMYACHIK 226 HOME HEADER TICKER RESTORE START \*/.*?/\* PROMYACHIK 226 HOME HEADER TICKER RESTORE END \*/",
        r"/\* PROMYACHIK 225 OLD TESTED TICKER CSS START \*/.*?/\* PROMYACHIK 225 OLD TESTED TICKER CSS END \*/",
    ]:
        existing = re.sub(pattern, "", existing, flags=re.S)
    css = read(RESTORE / "static/css/api-tickers.css")
    write(style, existing.rstrip() + "\n\n" + css.strip() + "\n", "append API ticker CSS only")

def clean_literal_noise_in_templates():
    for rel_path in ["layouts/partials/header.html", "layouts/_default/baseof.html", "layouts/index.html"]:
        path = PROJECT / rel_path
        if not path.exists():
            continue
        text = read(path)
        original = text
        text = re.sub(r"cite[^]*", "", text)
        text = text.replace("\\n\\n", "\n").replace("\\n", "\n")
        if rel_path == "layouts/partials/header.html" and 'partial "transfer-ticker.html"' not in text:
            if re.search(r"</header>", text, flags=re.I):
                text = re.sub(r"(?i)</header>", '</header>\n{{ partial "transfer-ticker.html" . }}', text, count=1)
            else:
                text = text.rstrip() + '\n{{ partial "transfer-ticker.html" . }}\n'
        if text != original:
            write(path, text, "clean literal slash-n/citation garbage")

def find_favicon_asset():
    candidates = []
    for pattern in ["favicon.ico", "favicon.png", "favicon.svg", "images/favicon.ico", "images/favicon.png", "images/favicon.svg", "images/*favicon*.*", "css/profutbik-logo-site.png", "profutbik-logo-site.png"]:
        candidates.extend((PROJECT / "static").glob(pattern))
    candidates = [p for p in candidates if p.is_file()]
    def score(p):
        name = p.name.lower()
        return 100 if name == "favicon.ico" else 95 if name == "favicon.png" else 80 if "favicon" in name else 30 if "logo" in name else 0
    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None

def ensure_favicon_link():
    asset = find_favicon_asset()
    if not asset:
        warnings.append("Favicon asset not found under static/. No invented favicon was created.")
        return
    href = rel(asset).replace("static/", "").lstrip("/")
    ext = asset.suffix.lower()
    mime = "image/x-icon" if ext == ".ico" else "image/png" if ext == ".png" else "image/svg+xml" if ext == ".svg" else ""
    link = f'<link rel="icon" href="{{{{ "{href}" | relURL }}}}"'
    if mime:
        link += f' type="{mime}"'
    link += ">"
    for rel_path in ["layouts/index.html", "layouts/_default/baseof.html"]:
        path = PROJECT / rel_path
        if not path.exists():
            continue
        text = read(path)
        if 'rel="icon"' in text or "rel='icon'" in text:
            continue
        if "</head>" in text:
            write(path, text.replace("</head>", f"    {link}\n</head>", 1), f"restore favicon link to existing asset {href}")

def verify(pages):
    checks = {}
    ok = True
    public_home = PROJECT / "public" / "index.html"
    public_text = read(public_home) if public_home.exists() else ""
    checks["public_index_exists"] = public_home.exists()
    checks["public_index_not_placeholder"] = "Сайт запускается" not in public_text
    checks["public_no_literal_slash_n"] = "\\n" not in public_text
    checks["home_has_step66_featured_dots_or_slider"] = ("pf-featured-dot" in public_text or "data-featured-index" in public_text or "home-slider" in public_text)
    checks["home_has_concept_art_paths"] = all(token in public_text for token in ["kylian-mbappe-real-madrid-hero.png", "florian-wirtz-liverpool-hero.png", "bernardo-silva-real-madrid-hero.png"])
    data_text = read(PROJECT / "data" / "transfers.json")
    checks["data_has_api_club_ids"] = '"from_club_id"' in data_text and '"to_club_id"' in data_text
    checks["data_has_player_images"] = '"player_image"' in data_text and ("images/players/api/" in data_text or "images/homepage/featured/" in data_text)
    checks["data_urls_not_generic_transfers_only"] = '"url": "transfers/"' not in data_text
    checks["public_has_api_club_logos"] = "images/clubs/api/" in public_text
    checks["public_has_top_ticker_items"] = "pf-ticker__item" in public_text
    checks["public_has_bottom_player_photos"] = "bottom-transfer-strip-v3__photo" in public_text and ("images/players/api/" in public_text or "media.api-sports.io/football/players/" in public_text or "images/homepage/featured/" in public_text)
    checks["public_has_favicon_link"] = 'rel="icon"' in public_text or "rel='icon'" in public_text
    for key, value in checks.items():
        if key != "public_has_favicon_link" and not value:
            ok = False
    missing_pages = []
    for item in pages:
        url = str(item.get("url", "")).strip("/")
        if url and not (PROJECT / "public" / url / "index.html").exists():
            missing_pages.append(url)
    checks["missing_public_pages_for_ticker_urls"] = missing_pages
    if missing_pages:
        ok = False
    return ok, checks

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for rel_path in ["layouts/index.html", "layouts/partials/header.html", "layouts/_default/baseof.html", "layouts/partials/transfer-ticker.html", "layouts/partials/footer-transfer-ticker.html", "data/transfers.json", "static/css/style.css"]:
        backup(PROJECT / rel_path)
    ok = True
    error_text = ""
    hugo = None
    checks = {}
    try:
        restore_home_from_existing_candidate()
        clean_literal_noise_in_templates()
        pages = rebuild_transfers_data_from_content()
        write_ticker_partials_and_css()
        ensure_favicon_link()
        hugo = run(["hugo", "-D"])
        ok, checks = verify(pages)
        if hugo.returncode != 0:
            ok = False
    except Exception as e:
        ok = False
        error_text = str(e)
    changed_count = sum(1 for _, _, did, _, _ in changed if did)
    lines = []
    lines.append("PROMYACHIK 227 - RESTORE REAL HOME + API LOGOS/PHOTOS IN TICKERS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Package dir: {PACKAGE_DIR}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Homepage was restored only from an existing local package-66/backup candidate.")
    lines.append("- No generated replacement homepage was written.")
    lines.append("- Ticker data was rebuilt from real content/transfers pages.")
    lines.append("- Club logos come from data/club-logos.json API-Football mapping.")
    lines.append("- Player photos come from existing local/API player image paths.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("HOME CANDIDATES")
    if home_candidates:
        for score, path, kind, length in home_candidates:
            lines.append(f"- score={score}; kind={kind}; len={length}; path={path}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHANGED FILES")
    for rel_path, label, did, before, after in changed:
        lines.append(f"- {rel_path} | {label} | changed={did}")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    if error_text:
        lines.append("ERROR")
        lines.append(error_text)
        lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("HUGO")
    if hugo is None:
        lines.append("- not run")
    else:
        lines.append(f"- exit_code: {hugo.returncode}")
        lines.append("--- STDOUT tail ---")
        lines.append(hugo.stdout[-2500:])
        lines.append("--- STDERR tail ---")
        lines.append(hugo.stderr[-2500:])
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands:
        lines.append("-" * 70)
        lines.append(f"COMMAND: {c['cmd']}")
        lines.append(f"EXIT_CODE: {c['returncode']}")
        if c["stdout"]:
            lines.append("--- STDOUT ---")
            lines.append(c["stdout"])
        if c["stderr"]:
            lines.append("--- STDERR ---")
            lines.append(c["stderr"])
    lines.append("")
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
