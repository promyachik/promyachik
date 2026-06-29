from pathlib import Path
import re
import shutil
from datetime import datetime
from collections import deque

try:
    from PIL import Image
except Exception as e:
    raise SystemExit("Pillow is required for package 208. Install it once with: py -m pip install pillow")

project = Path.cwd()
backup_dir = project / "_backup_208_fix_ramos_photo_black_bg_and_portugal_flag"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_208_fix_ramos_photo_black_bg_and_portugal_flag_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

ramos_page = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
flag_path = project / "static" / "images" / "flags" / "portugal.svg"
css_path = project / "static" / "css" / "style.css"

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

def resolve_site_path(site_path: str):
    s = site_path.strip().strip('"').strip("'")
    if not s:
        return None
    if s.startswith(("http://","https://")):
        return None
    if "?" in s:
        s = s.split("?",1)[0]
    if s.startswith("/promyachik/"):
        s = s[len("/promyachik/"):]
    if s.startswith("/"):
        s = s[1:]
    cands = [project / s, project / "static" / s]
    if not s.startswith("images/"):
        cands.append(project / "static" / "images" / s)
    for c in cands:
        if c.exists():
            return c
    return cands[0]

def extract_photo_paths(page_text: str):
    paths = []
    for key in ["player_image", "api_player_image", "photo", "image"]:
        m = re.search(rf'(?m)^{re.escape(key)}\s*:\s*(.+)$', page_text)
        if m:
            p = m.group(1).strip().strip('"').strip("'")
            local = resolve_site_path(p)
            if local:
                paths.append(local)
    # fallback known path from previous report
    fallback = project / "static" / "images" / "players" / "api" / "41585.png"
    if fallback.exists():
        paths.append(fallback)
    uniq = []
    seen = set()
    for p in paths:
        key = str(p).lower()
        if key not in seen and p.suffix.lower() in [".png",".jpg",".jpeg",".webp"]:
            uniq.append(p)
            seen.add(key)
    return uniq

def replace_white_bg_with_black(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    # Flood-fill from edges through near-white / very light background pixels only.
    def is_bg_pixel(x, y):
        r, g, b, a = px[x, y]
        if a < 30:
            return True
        # near-white / very light gray
        return r > 215 and g > 215 and b > 215

    visited = [[False]*h for _ in range(w)]
    q = deque()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h-1))
    for y in range(h):
        q.append((0, y))
        q.append((w-1, y))

    bg = set()
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        if visited[x][y]:
            continue
        visited[x][y] = True
        if not is_bg_pixel(x, y):
            continue
        bg.add((x, y))
        q.append((x+1, y))
        q.append((x-1, y))
        q.append((x, y+1))
        q.append((x, y-1))

    # Replace detected background with solid black, preserve full opacity.
    for x, y in bg:
        px[x, y] = (0, 0, 0, 255)

    return rgba

# 1) Replace portugal flag with visible SVG.
backup(flag_path)
portugal_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" role="img" aria-label="Portugal flag">
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
write(flag_path, portugal_svg)
touched.append(flag_path)

# 2) Fix Ramos page fields.
if not ramos_page.exists():
    warnings.append(f"Missing page: {ramos_page}")
    page_text = ""
else:
    backup(ramos_page)
    page_text = read(ramos_page)
    for key in [
        "country_flag_image",
        "flag_image",
        "player_flag_image",
        "player_country_flag_image",
        "nationality_flag_image",
    ]:
        page_text = set_yaml_field(page_text, key, "/images/flags/portugal.svg")
    for key in ["country_code", "nationality_code"]:
        page_text = set_yaml_field(page_text, key, "PT")
    for key in ["country_flag", "flag", "player_flag", "player_country_flag", "nationality_flag"]:
        page_text = set_yaml_field(page_text, key, "🇵🇹")
    page_text = set_yaml_field(page_text, "milan_logo", "/images/clubs/ac-milan.svg")
    if re.search(r'(?m)^market_value\s*:\s*(.+)$', page_text) and not re.search(r'(?m)^value\s*:\s*', page_text):
        mv = re.search(r'(?m)^market_value\s*:\s*(.+)$', page_text).group(1).strip()
        page_text = set_yaml_field(page_text, "value", mv)
    if re.search(r'(?m)^value\s*:\s*(.+)$', page_text) and not re.search(r'(?m)^market_value\s*:\s*', page_text):
        val = re.search(r'(?m)^value\s*:\s*(.+)$', page_text).group(1).strip()
        page_text = set_yaml_field(page_text, "market_value", val)
    write(ramos_page, page_text)
    touched.append(ramos_page)

# 3) Fix actual player photo background.
photo_paths = extract_photo_paths(page_text)
for photo in photo_paths:
    if photo.exists():
        backup(photo)
        img = Image.open(photo)
        fixed = replace_white_bg_with_black(img)
        fixed.save(photo)
        touched.append(photo)
    else:
        warnings.append(f"Photo file not found: {photo}")

# 4) Add CSS to stop white placeholder flags and keep value aligned.
if not css_path.exists():
    write(css_path, "")
backup(css_path)
css = read(css_path)
marker = "/* 208 ramos flag visibility and market value alignment */"
css_block = """
/* 208 ramos flag visibility and market value alignment */
body.transfer-page img[src*="/images/flags/"],
body.transfer-page img[src*="images/flags/"] {
  width: 24px !important;
  height: 16px !important;
  min-width: 24px !important;
  max-width: 24px !important;
  min-height: 16px !important;
  max-height: 16px !important;
  display: inline-block !important;
  object-fit: cover !important;
  object-position: center center !important;
  border-radius: 2px !important;
  background: transparent !important;
  filter: none !important;
  opacity: 1 !important;
  mix-blend-mode: normal !important;
  box-shadow: none !important;
  flex: 0 0 24px !important;
  vertical-align: middle !important;
}

body.transfer-page [class*="market"],
body.transfer-page [class*="value"],
body.transfer-page [class*="price"],
body.transfer-page [class*="fee"] {
  white-space: nowrap !important;
  align-items: center !important;
  text-align: left !important;
}
"""
if marker not in css:
    css = css.rstrip() + "\n\n" + css_block.strip() + "\n"
    write(css_path, css)
    touched.append(css_path)

# 5) Report
lines = []
lines.append("PROFUTBIK 208 - FIX RAMOS PHOTO BLACK BG AND PORTUGAL FLAG")
lines.append("=" * 70)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("FIXED")
lines.append("- Player photo background: white/near-white edge background replaced with black.")
lines.append("- Portugal flag asset replaced with visible real SVG.")
lines.append("- Ramos page flag fields forced to portugal.svg and PT.")
lines.append("- Wrong milan_logo fixed to /images/clubs/ac-milan.svg.")
lines.append("- CSS added to keep flags visible and market/value aligned.")
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
