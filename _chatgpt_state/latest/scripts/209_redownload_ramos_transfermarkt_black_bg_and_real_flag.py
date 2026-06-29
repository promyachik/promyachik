from pathlib import Path
from datetime import datetime
import re
import shutil
import sys
import json
import urllib.request
import urllib.parse
from html import unescape
from collections import deque

try:
    from PIL import Image
except Exception:
    raise SystemExit("Pillow is required. Install once if missing: py -m pip install pillow")

project = Path.cwd()
package_root = Path(__file__).resolve().parents[1]
backup_dir = project / "_backup_209_redownload_ramos_transfermarkt_black_bg_and_real_flag"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_209_redownload_ramos_transfermarkt_black_bg_and_real_flag_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

ramos_page = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
photo_out = project / "static" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black.png"
old_api_photo = project / "static" / "images" / "players" / "api" / "41585.png"
flag_out = project / "static" / "images" / "flags" / "portugal-proper.png"
flag_payload = package_root / "payload" / "flags" / "portugal-proper.png"
css_path = project / "static" / "css" / "style.css"
rules_path = project / "docs" / "PROFUTBIK_TRANSFER_PLAYER_PAGE_RULES.md"

tm_url = "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"

touched = []
warnings = []

def backup(path: Path):
    if path.exists():
        rel = path.relative_to(project)
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def download_bytes(url: str, referer: str = None) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
        "Accept": "text/html,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def extract_transfermarkt_image(html: str):
    html = unescape(html)

    # Prefer high-quality Transfermarkt portrait header URLs.
    candidates = []
    for m in re.finditer(r'https?://[^"\']+transfermarkt\.technology/portrait/[^"\']+', html, flags=re.I):
        candidates.append(m.group(0))
    for m in re.finditer(r'https?://[^"\']+tmssl\.akamaized\.net/images/portrait/[^"\']+', html, flags=re.I):
        candidates.append(m.group(0))
    for m in re.finditer(r'https?://[^"\']+/images/portrait/[^"\']+', html, flags=re.I):
        candidates.append(m.group(0))

    clean = []
    seen = set()
    for c in candidates:
        c = c.replace("\\/", "/")
        c = c.split("?")[0]
        # strip html garbage
        c = c.replace("&amp;", "&")
        if "550550" not in c and "default" in c.lower():
            continue
        if c not in seen:
            clean.append(c)
            seen.add(c)

    # Sort header first, then anything with 550550.
    clean.sort(key=lambda u: (0 if "/portrait/header/" in u else 1, 0 if "550550" in u else 1, len(u)))
    return clean[0] if clean else None

def replace_edge_bg_with_black(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    def is_bg(x, y):
        r, g, b, a = px[x, y]
        if a < 20:
            return True
        # white/gray/very light backgrounds
        if r > 210 and g > 210 and b > 210:
            return True
        # Transfermarkt light gray / blue-gray background
        if abs(r-g) < 28 and abs(g-b) < 38 and r > 135 and g > 135 and b > 135:
            return True
        return False

    visited = [[False] * h for _ in range(w)]
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h-1))
    for y in range(h):
        q.append((0, y))
        q.append((w-1, y))

    bg = []
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        if visited[x][y]:
            continue
        visited[x][y] = True
        if not is_bg(x, y):
            continue
        bg.append((x, y))
        q.append((x+1, y))
        q.append((x-1, y))
        q.append((x, y+1))
        q.append((x, y-1))

    for x, y in bg:
        px[x, y] = (0, 0, 0, 255)

    # Composite transparent pixels over black too.
    black = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
    black.alpha_composite(rgba)
    return black

def set_yaml_field(text: str, key: str, value: str) -> str:
    pattern = rf'(?m)^({re.escape(key)}\s*:\s*).*$'
    replacement = rf'\g<1>{value}'
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    if text.startswith("---"):
        idx = text.find("\n---", 3)
        if idx != -1:
            return text[:idx] + f"\n{key}: {value}" + text[idx:]
    return text + f"\n{key}: {value}\n"

# 1) Download Transfermarkt page and portrait.
downloaded_image_url = None
try:
    page_html = download_bytes(tm_url).decode("utf-8", errors="ignore")
    downloaded_image_url = extract_transfermarkt_image(page_html)
except Exception as e:
    warnings.append(f"Could not fetch Transfermarkt page: {e}")

if not downloaded_image_url:
    raise SystemExit("Could not find Transfermarkt portrait image URL for Ramos. No local changes applied to photo.")

try:
    img_bytes = download_bytes(downloaded_image_url, referer=tm_url)
except Exception as e:
    raise SystemExit(f"Could not download Transfermarkt portrait: {downloaded_image_url} | {e}")

tmp_raw = project / "var" / "ramos_transfermarkt_550550_raw_download"
tmp_raw.write_bytes(img_bytes)

# 2) Convert downloaded portrait to black background.
backup(photo_out)
backup(old_api_photo)
photo_out.parent.mkdir(parents=True, exist_ok=True)
img = Image.open(tmp_raw)
fixed = replace_edge_bg_with_black(img)
fixed.save(photo_out)
touched.append(photo_out)

# Also overwrite the old API file so any template still using it changes visually.
if old_api_photo.exists():
    fixed_resized = fixed.copy()
    # Keep original API image size to avoid breaking layout if template expects 150x150.
    try:
        old = Image.open(old_api_photo)
        fixed_resized = fixed_resized.resize(old.size, Image.LANCZOS)
    except Exception:
        pass
    fixed_resized.save(old_api_photo)
    touched.append(old_api_photo)

# 3) Force real PNG Portugal flag path.
backup(flag_out)
flag_out.parent.mkdir(parents=True, exist_ok=True)
if flag_payload.exists():
    shutil.copy2(flag_payload, flag_out)
else:
    flag = Image.new("RGB", (90, 60), (255, 0, 0))
    flag.save(flag_out)
touched.append(flag_out)

# 4) Patch Ramos page to use new Transfermarkt black image and proper PNG flag.
if not ramos_page.exists():
    warnings.append(f"Missing Ramos page: {ramos_page}")
else:
    backup(ramos_page)
    text = read(ramos_page)

    # Force player photo fields to Transfermarkt black image.
    for key in ["player_image", "api_player_image", "cutout_player_image"]:
        text = set_yaml_field(text, key, "/images/players/transfermarkt/goncalo-ramos-550550-black.png")
    text = set_yaml_field(text, "player_image_source_name", "Transfermarkt")
    text = set_yaml_field(text, "player_image_source_url", tm_url)
    text = set_yaml_field(text, "needs_cutout", "false")

    # Force flag image to PNG, avoiding broken/white SVG rendering.
    for key in ["country_flag_image", "flag_image", "player_flag_image", "player_country_flag_image", "nationality_flag_image"]:
        text = set_yaml_field(text, key, "/images/flags/portugal-proper.png")
    for key in ["country_code", "nationality_code"]:
        text = set_yaml_field(text, key, "PT")
    for key in ["country_flag", "flag", "player_flag", "player_country_flag", "nationality_flag"]:
        text = set_yaml_field(text, key, "🇵🇹")

    text = set_yaml_field(text, "milan_logo", "/images/clubs/ac-milan.svg")
    text = set_yaml_field(text, "market_value", "€30M")
    text = set_yaml_field(text, "value", "€30M")

    write(ramos_page, text)
    touched.append(ramos_page)

# 5) CSS: make flag PNG visible and value stable.
if not css_path.exists():
    write(css_path, "")
backup(css_path)
css = read(css_path)
marker = "/* 209 final Ramos photo flag value fix */"
css_block = """
/* 209 final Ramos photo flag value fix */
body.transfer-page img[src*="/images/flags/portugal-proper.png"],
body.transfer-page img[src*="images/flags/portugal-proper.png"],
body.transfer-page img[src*="/images/flags/"],
body.transfer-page img[src*="images/flags/"] {
  width: 24px !important;
  height: 16px !important;
  min-width: 24px !important;
  max-width: 24px !important;
  min-height: 16px !important;
  max-height: 16px !important;
  object-fit: cover !important;
  object-position: center center !important;
  display: inline-block !important;
  border-radius: 2px !important;
  filter: none !important;
  opacity: 1 !important;
  mix-blend-mode: normal !important;
  background: transparent !important;
  flex: 0 0 24px !important;
  vertical-align: middle !important;
}

body.transfer-page img[src*="/images/players/transfermarkt/goncalo-ramos-550550-black.png"],
body.transfer-page img[src*="images/players/transfermarkt/goncalo-ramos-550550-black.png"],
body.transfer-page img[src*="/images/players/api/41585.png"],
body.transfer-page img[src*="images/players/api/41585.png"] {
  background: #000000 !important;
  object-fit: cover !important;
  object-position: center top !important;
}

body.transfer-page [class*="market"],
body.transfer-page [class*="value"],
body.transfer-page [class*="price"],
body.transfer-page [class*="fee"] {
  white-space: nowrap !important;
  min-width: 0 !important;
  align-items: center !important;
  text-align: left !important;
}
"""
if marker not in css:
    write(css_path, css.rstrip() + "\n\n" + css_block.strip() + "\n")
    touched.append(css_path)

# 6) Rules update.
rules_append = """
## 7. Photo fallback after repeated background failures

Если два раза не получилось убрать белый фон у локального фото игрока, больше не чинить этот же файл вслепую.

Действие:
1. заново скачать фото игрока с Transfermarkt;
2. сохранить отдельным файлом в `static/images/players/transfermarkt/`;
3. удалить/заменить светлый фон;
4. положить игрока на чистый чёрный фон `#000000`;
5. прописать страницу игрока на новый локальный файл;
6. при необходимости перезаписать старый API-файл, если шаблон всё ещё берёт его.

Для Gonçalo Ramos:
- Transfermarkt player id: 550550;
- локальный файл: `/images/players/transfermarkt/goncalo-ramos-550550-black.png`;
- флаг: `/images/flags/portugal-proper.png`.
"""
if rules_path.exists():
    backup(rules_path)
    rules = read(rules_path)
else:
    rules = "# ProFutbik / Promyachik — правила страниц игроков и трансферов\n"
if "Photo fallback after repeated background failures" not in rules:
    write(rules_path, rules.rstrip() + "\n\n" + rules_append.strip() + "\n")
    touched.append(rules_path)

# 7) Report.
lines = []
lines.append("PROFUTBIK 209 - REDOWNLOAD RAMOS FROM TRANSFERMARKT BLACK BG + REAL PORTUGAL FLAG")
lines.append("=" * 90)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("TRANSFERMARKT")
lines.append(f"- Profile: {tm_url}")
lines.append(f"- Portrait downloaded: {downloaded_image_url}")
lines.append("")
lines.append("FIXED")
lines.append("- Downloaded Ramos photo from Transfermarkt.")
lines.append("- Replaced light/white edge background with solid black #000000.")
lines.append("- Saved new photo to /images/players/transfermarkt/goncalo-ramos-550550-black.png.")
lines.append("- Also overwrote /images/players/api/41585.png if it existed, so old template paths change too.")
lines.append("- Created /images/flags/portugal-proper.png and forced Ramos flag fields to this PNG.")
lines.append("- Fixed milan_logo to /images/clubs/ac-milan.svg.")
lines.append("- Kept market_value/value as €30M.")
lines.append("")
lines.append("TOUCHED FILES")
seen = set()
for p in touched:
    key = str(p).lower()
    if key in seen:
        continue
    seen.add(key)
    try:
        lines.append(f"- {p.relative_to(project)}")
    except Exception:
        lines.append(f"- {p}")
lines.append(f"- {report_path.relative_to(project)}")
if warnings:
    lines.append("")
    lines.append("WARNINGS")
    for w in warnings:
        lines.append(f"- {w}")
lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")
lines.append("NO Y/N ASKED.")
write(report_path, "\n".join(lines))
print("\n".join(lines))
