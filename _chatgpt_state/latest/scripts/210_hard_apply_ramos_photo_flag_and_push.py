from pathlib import Path
from datetime import datetime
from collections import deque
import argparse
import subprocess
import shutil
import re
import urllib.request
from html import unescape

try:
    from PIL import Image, ImageDraw
except Exception:
    raise SystemExit("Pillow is required. Install once if missing: py -m pip install pillow")

parser = argparse.ArgumentParser()
parser.add_argument("--push", action="store_true")
args = parser.parse_args()

project = Path.cwd()
backup_dir = project / "_backup_210_hard_apply_ramos_photo_flag_and_push"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_210_hard_apply_ramos_photo_flag_and_push_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

ramos_page = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"

tm_profile = "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"

new_photo_site = "/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png"
new_flag_site = "/images/flags/portugal-v210.png"

candidate_source_photo_paths = [
    project / "static" / "images" / "players" / "api" / "41585.png",
    project / "images" / "players" / "api" / "41585.png",
    project / "public" / "images" / "players" / "api" / "41585.png",
    project / "static" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black.png",
    project / "static" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black-v210.png",
]

photo_write_targets = [
    project / "static" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black-v210.png",
    project / "static" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black.png",
    project / "static" / "images" / "players" / "api" / "41585.png",
    project / "public" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black-v210.png",
    project / "public" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black.png",
    project / "public" / "images" / "players" / "api" / "41585.png",
    project / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black-v210.png",
    project / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black.png",
    project / "images" / "players" / "api" / "41585.png",
]

flag_write_targets = [
    project / "static" / "images" / "flags" / "portugal-v210.png",
    project / "static" / "images" / "flags" / "portugal-proper.png",
    project / "public" / "images" / "flags" / "portugal-v210.png",
    project / "public" / "images" / "flags" / "portugal-proper.png",
    project / "images" / "flags" / "portugal-v210.png",
    project / "images" / "flags" / "portugal-proper.png",
]

svg_flag_targets = [
    project / "static" / "images" / "flags" / "portugal.svg",
    project / "public" / "images" / "flags" / "portugal.svg",
    project / "images" / "flags" / "portugal.svg",
]

touched = []
warnings = []
downloaded_portrait_url = None
hugo_result = None

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project))
    except Exception:
        return str(p)

def backup(path: Path):
    if path.exists():
        dst = backup_dir / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(text, encoding="utf-8")
    add_touched(path)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def add_touched(path: Path):
    if path not in touched:
        touched.append(path)

def run_cmd(cmd):
    return subprocess.run(cmd, cwd=project, text=True, capture_output=True)

def download_url(url, referer=None):
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

def find_tm_portrait(html: str):
    html = unescape(html).replace("\\/", "/")
    candidates = []
    patterns = [
        r"https?://[^\"']*transfermarkt\.technology/portrait/[^\"']+",
        r"https?://[^\"']*tmssl\.akamaized\.net/images/portrait/[^\"']+",
        r"https?://[^\"']*/images/portrait/[^\"']+",
    ]
    for pat in patterns:
        candidates += re.findall(pat, html, flags=re.I)
    clean = []
    seen = set()
    for c in candidates:
        c = c.split("?")[0]
        if c in seen:
            continue
        if "default" in c.lower():
            continue
        seen.add(c)
        clean.append(c)
    clean.sort(key=lambda u: (0 if "/portrait/header/" in u else 1, 0 if "550550" in u else 1, len(u)))
    return clean[0] if clean else None

def make_portugal_flag_png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    img = Image.new("RGB", (90, 60), (255, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 36, 60], fill=(0, 102, 0))
    d.ellipse([26, 20, 46, 40], fill=(255, 204, 0))
    d.ellipse([30, 24, 42, 36], fill=(255, 255, 255))
    d.rectangle([33, 26, 39, 35], fill=(210, 0, 0))
    d.ellipse([35, 28, 37, 30], fill=(0, 45, 150))
    d.ellipse([35, 32, 37, 34], fill=(0, 45, 150))
    img.save(path)
    add_touched(path)

def make_portugal_flag_svg(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
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
    write_text(path, svg)

def edge_bg_to_black(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    def is_bg(x, y):
        r, g, b, a = px[x, y]
        if a < 30:
            return True
        if r > 200 and g > 200 and b > 200:
            return True
        if r > 120 and g > 120 and b > 120 and abs(r-g) < 45 and abs(g-b) < 55:
            return True
        mx, mn = max(r,g,b), min(r,g,b)
        if mx > 150 and (mx - mn) < 55:
            return True
        return False

    visited = [[False] * h for _ in range(w)]
    q = deque()
    for x in range(w):
        q.append((x,0))
        q.append((x,h-1))
    for y in range(h):
        q.append((0,y))
        q.append((w-1,y))

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
        bg.append((x,y))
        q.append((x+1,y))
        q.append((x-1,y))
        q.append((x,y+1))
        q.append((x,y-1))

    for x, y in bg:
        px[x,y] = (0,0,0,255)

    black = Image.new("RGBA", rgba.size, (0,0,0,255))
    black.alpha_composite(rgba)
    return black

def choose_photo_image():
    global downloaded_portrait_url
    try:
        html = download_url(tm_profile).decode("utf-8", errors="ignore")
        portrait = find_tm_portrait(html)
        if portrait:
            data = download_url(portrait, referer=tm_profile)
            raw_path = project / "var" / "ramos_tm_550550_raw_v210"
            raw_path.write_bytes(data)
            downloaded_portrait_url = portrait
            return Image.open(raw_path)
        warnings.append("Transfermarkt portrait URL was not found.")
    except Exception as e:
        warnings.append(f"Transfermarkt download failed: {e}")

    for p in candidate_source_photo_paths:
        if p.exists():
            warnings.append(f"Used local fallback photo: {rel(p)}")
            return Image.open(p)

    raise RuntimeError("No Transfermarkt portrait and no local Ramos photo fallback found.")

def save_photo_to_all_targets(img: Image.Image):
    fixed = edge_bg_to_black(img)
    for target in photo_write_targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        backup(target)
        out = fixed.copy()
        if target.name == "41585.png" and target.exists():
            try:
                old_size = Image.open(target).size
                out = out.resize(old_size, Image.LANCZOS)
            except Exception:
                pass
        out.save(target)
        add_touched(target)

def set_yaml_field(text, key, value):
    pattern = rf"(?m)^({re.escape(key)}\s*:\s*).*$"
    if re.search(pattern, text):
        return re.sub(pattern, rf"\g<1>{value}", text, count=1)
    if text.startswith("---"):
        idx = text.find("\n---", 3)
        if idx != -1:
            return text[:idx] + f"\n{key}: {value}" + text[idx:]
    return text + f"\n{key}: {value}\n"

def patch_ramos_markdown():
    if not ramos_page.exists():
        warnings.append(f"Ramos markdown not found: {rel(ramos_page)}")
        return
    text = read_text(ramos_page)
    original = text
    for k in ["player_image", "api_player_image", "cutout_player_image"]:
        text = set_yaml_field(text, k, new_photo_site)
    text = set_yaml_field(text, "player_image_source_name", "Transfermarkt")
    text = set_yaml_field(text, "player_image_source_url", tm_profile)
    text = set_yaml_field(text, "needs_cutout", "false")

    for k in ["country_flag_image", "flag_image", "player_flag_image", "player_country_flag_image", "nationality_flag_image"]:
        text = set_yaml_field(text, k, new_flag_site)
    for k in ["country_code", "nationality_code"]:
        text = set_yaml_field(text, k, "PT")
    for k in ["country_flag", "flag", "player_flag", "player_country_flag", "nationality_flag"]:
        text = set_yaml_field(text, k, "🇵🇹")
    text = set_yaml_field(text, "milan_logo", "/images/clubs/ac-milan.svg")
    text = set_yaml_field(text, "market_value", "€30M")
    text = set_yaml_field(text, "value", "€30M")
    if text != original:
        write_text(ramos_page, text)

def patch_text_file(path: Path, replacements):
    try:
        text = read_text(path)
    except Exception:
        return
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        write_text(path, text)

def patch_generated_html_and_css():
    replacements = [
        ("/images/players/api/41585.png", new_photo_site),
        ("images/players/api/41585.png", new_photo_site.lstrip("/")),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black.png", new_photo_site),
        ("images/players/transfermarkt/goncalo-ramos-550550-black.png", new_photo_site.lstrip("/")),
        ("/images/flags/portugal.svg", new_flag_site),
        ("images/flags/portugal.svg", new_flag_site.lstrip("/")),
        ("/images/flags/portugal-proper.png", new_flag_site),
        ("images/flags/portugal-proper.png", new_flag_site.lstrip("/")),
    ]

    for base in [project / "public", project]:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            parts = {part.lower() for part in p.parts}
            if ".git" in parts or "_backup_210_hard_apply_ramos_photo_flag_and_push" in parts:
                continue
            if p.suffix.lower() in [".html", ".htm", ".md", ".css", ".js", ".json"]:
                try:
                    s = read_text(p)
                except Exception:
                    continue
                lower = s.lower()
                if any(token in lower for token in ["goncalo", "gonçalo", "ramos", "41585.png", "portugal.svg", "portugal-proper.png"]):
                    patch_text_file(p, replacements)

    css_block = f"""
/* 210 hard Ramos photo flag value fix */
body.transfer-page img[src*="goncalo-ramos-550550-black-v210.png"],
body.transfer-page img[src*="/images/players/api/41585.png"] {{
  background: #000000 !important;
  object-fit: cover !important;
  object-position: center top !important;
}}

body.transfer-page img[src*="portugal-v210.png"],
body.transfer-page img[src*="/images/flags/"] {{
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
}}

body.transfer-page [class*="market"],
body.transfer-page [class*="value"],
body.transfer-page [class*="price"],
body.transfer-page [class*="fee"] {{
  white-space: nowrap !important;
  min-width: 0 !important;
  align-items: center !important;
  text-align: left !important;
}}
"""
    for css_dir in [project / "static" / "css", project / "public" / "css", project / "css"]:
        css_dir.mkdir(parents=True, exist_ok=True)
        css_path = css_dir / "style.css"
        if not css_path.exists():
            css_path.write_text("", encoding="utf-8")
        css = read_text(css_path)
        if "210 hard Ramos photo flag value fix" not in css:
            write_text(css_path, css.rstrip() + "\n\n" + css_block.strip() + "\n")

def copy_public_ramos_to_root():
    src_page = project / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
    dst_page = project / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
    if src_page.exists():
        dst_page.parent.mkdir(parents=True, exist_ok=True)
        backup(dst_page)
        shutil.copy2(src_page, dst_page)
        add_touched(dst_page)

    for src in [
        project / "public" / "images" / "players" / "transfermarkt" / "goncalo-ramos-550550-black-v210.png",
        project / "public" / "images" / "players" / "api" / "41585.png",
        project / "public" / "images" / "flags" / "portugal-v210.png",
        project / "public" / "css" / "style.css",
    ]:
        if src.exists():
            dst = project / src.relative_to(project / "public")
            dst.parent.mkdir(parents=True, exist_ok=True)
            backup(dst)
            shutil.copy2(src, dst)
            add_touched(dst)

for p in flag_write_targets:
    make_portugal_flag_png(p)
for p in svg_flag_targets:
    make_portugal_flag_svg(p)

img = choose_photo_image()
save_photo_to_all_targets(img)

patch_ramos_markdown()

try:
    p = run_cmd(["hugo", "-D"])
    hugo_result = {"returncode": p.returncode, "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-2000:]}
    if p.returncode != 0:
        warnings.append("hugo -D failed; direct file patch still applied.")
except Exception as e:
    hugo_result = {"error": str(e)}
    warnings.append(f"hugo -D could not run: {e}")

patch_generated_html_and_css()
copy_public_ramos_to_root()

rules_path = project / "docs" / "PROFUTBIK_TRANSFER_PLAYER_PAGE_RULES.md"
rule_add = f"""
## 8. Hard-publish check after player visual fix

For a player visual fix, do not only patch `content/` or `static/`.

Mandatory layers to update/check:
- `content/transfers/<player>/index.md`;
- `static/images/...`;
- `public/images/...` if generated files exist;
- root `images/...` if GitHub Pages is publishing from repo root;
- generated `public/transfers/<player>/index.html`;
- root `transfers/<player>/index.html` if repo-root publishing exists;
- CSS in `static/css`, `public/css`, and root `css` if those folders exist.

For Gonçalo Ramos v210:
- player photo: `{new_photo_site}`;
- Portugal flag: `{new_flag_site}`;
"""
if rules_path.exists():
    rules = read_text(rules_path)
else:
    rules = "# ProFutbik / Promyachik — правила страниц игроков и трансферов\n"
if "Hard-publish check after player visual fix" not in rules:
    write_text(rules_path, rules.rstrip() + "\n\n" + rule_add.strip() + "\n")

lines = []
lines.append("PROFUTBIK 210 - HARD APPLY RAMOS PHOTO FLAG AND PUSH EXACT FILES")
lines.append("=" * 90)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("FIXED VISUAL PATHS")
lines.append(f"- New player photo path: {new_photo_site}")
lines.append(f"- New Portugal flag path: {new_flag_site}")
lines.append("- Old API photo 41585.png overwritten in static/public/root when those folders exist.")
lines.append("- Generated HTML/CSS layers patched after Hugo build if present.")
lines.append("")
lines.append("TRANSFERMARKT")
lines.append(f"- Profile: {tm_profile}")
lines.append(f"- Portrait used: {downloaded_portrait_url or 'local fallback'}")
lines.append("")
lines.append("HUGO BUILD")
lines.append(str(hugo_result))
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
lines.append("NO Y/N ASKED.")
write_text(report_path, "\n".join(lines))

if args.push:
    files_to_stage = []
    for p in touched + [report_path]:
        if p.exists():
            try:
                files_to_stage.append(str(p.relative_to(project)))
            except Exception:
                pass
    unique = []
    seen = set()
    for f in files_to_stage:
        if f not in seen:
            unique.append(f)
            seen.add(f)

    git_lines = []
    try:
        if unique:
            add = run_cmd(["git", "add", "--"] + unique)
            git_lines.append("git add returncode: " + str(add.returncode))
            if add.stdout: git_lines.append("git add stdout:\n" + add.stdout)
            if add.stderr: git_lines.append("git add stderr:\n" + add.stderr)

        status = run_cmd(["git", "status", "--short"])
        git_lines.append("git status --short after add:\n" + status.stdout)

        if status.stdout.strip():
            commit = run_cmd(["git", "commit", "-m", "Fix Goncalo Ramos photo and Portugal flag"])
            git_lines.append("git commit returncode: " + str(commit.returncode))
            if commit.stdout: git_lines.append("git commit stdout:\n" + commit.stdout)
            if commit.stderr: git_lines.append("git commit stderr:\n" + commit.stderr)

            if commit.returncode == 0:
                push = run_cmd(["git", "push"])
                git_lines.append("git push returncode: " + str(push.returncode))
                if push.stdout: git_lines.append("git push stdout:\n" + push.stdout)
                if push.stderr: git_lines.append("git push stderr:\n" + push.stderr)
            else:
                git_lines.append("git push skipped because commit failed.")
        else:
            git_lines.append("No git changes to commit after staging exact files.")
    except Exception as e:
        git_lines.append("GIT ERROR: " + str(e))

    report = read_text(report_path)
    report += "\n\nGIT PUSH RESULT\n" + "-" * 60 + "\n" + "\n".join(git_lines) + "\n"
    write_text(report_path, report)
    print(report)
else:
    print(read_text(report_path))
