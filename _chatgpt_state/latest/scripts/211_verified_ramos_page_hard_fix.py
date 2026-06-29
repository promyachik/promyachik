
from pathlib import Path
from datetime import datetime
from collections import deque
from html import unescape
import argparse
import subprocess
import shutil
import re
import time
import urllib.request

try:
    from PIL import Image, ImageDraw
except Exception:
    raise SystemExit('Pillow is required. Install once if missing: py -m pip install pillow')

parser = argparse.ArgumentParser()
parser.add_argument('--push', action='store_true')
args = parser.parse_args()

project = Path.cwd()
backup_dir = project / '_backup_211_verified_ramos_page_hard_fix'
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / 'var' / 'profutbik_211_verified_ramos_page_hard_fix_report.txt'
report_path.parent.mkdir(parents=True, exist_ok=True)

LOCAL_URL = 'http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/'
TM_PROFILE = 'https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550'
PLAYER_SITE = '/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png'
FLAG_SITE = '/images/flags/portugal-v211.png'
MARKER = 'pfb-ramos-v211-hardfix'

ramos_page = project / 'content' / 'transfers' / 'goncalo-ramos-ac-milan' / 'index.md'
partial_path = project / 'layouts' / 'partials' / 'ramos-hardfix-v211.html'

photo_targets = [
    project / 'static/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png',
    project / 'static/images/players/transfermarkt/goncalo-ramos-550550-black.png',
    project / 'static/images/players/api/41585.png',
    project / 'public/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png',
    project / 'public/images/players/transfermarkt/goncalo-ramos-550550-black.png',
    project / 'public/images/players/api/41585.png',
    project / 'images/players/transfermarkt/goncalo-ramos-550550-black-v211.png',
    project / 'images/players/transfermarkt/goncalo-ramos-550550-black.png',
    project / 'images/players/api/41585.png',
]
flag_png_targets = [
    project / 'static/images/flags/portugal-v211.png',
    project / 'static/images/flags/portugal-v210.png',
    project / 'static/images/flags/portugal-proper.png',
    project / 'public/images/flags/portugal-v211.png',
    project / 'public/images/flags/portugal-v210.png',
    project / 'images/flags/portugal-v211.png',
    project / 'images/flags/portugal-v210.png',
]
flag_svg_targets = [
    project / 'static/images/flags/portugal.svg',
    project / 'public/images/flags/portugal.svg',
    project / 'images/flags/portugal.svg',
]
source_photo_fallbacks = [
    project / 'static/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png',
    project / 'static/images/players/transfermarkt/goncalo-ramos-550550-black.png',
    project / 'static/images/players/api/41585.png',
    project / 'public/images/players/api/41585.png',
    project / 'images/players/api/41585.png',
]

touched = []
warnings = []
downloaded_portrait_url = ''
hugo_result = ''

def rel(p):
    try:
        return str(p.relative_to(project))
    except Exception:
        return str(p)

def add_touched(p):
    if p not in touched:
        touched.append(p)

def backup(p):
    if p.exists():
        dst = backup_dir / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)

def read_text(p):
    return p.read_text(encoding='utf-8', errors='ignore')

def write_text(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    backup(p)
    p.write_text(text, encoding='utf-8')
    add_touched(p)

def fetch_url(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        warnings.append(f'Could not fetch {url}: {e}')
        return ''

def extract_img_srcs(html):
    return re.findall(r'<img[^>]+src=[\"\']([^\"\']+)[\"\']', html, flags=re.I)

def run_cmd(cmd):
    return subprocess.run(cmd, cwd=project, capture_output=True, text=True)

def download_url(url, referer=None, timeout=20):
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36',
        'Accept':'text/html,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.9,ru;q=0.8',
    }
    if referer:
        headers['Referer'] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def find_tm_portrait(html):
    html = unescape(html).replace('\\/', '/')
    urls = []
    for pat in [
        r'https?://[^\"\']*transfermarkt\\.technology/portrait/[^\"\']+',
        r'https?://[^\"\']*tmssl\\.akamaized\\.net/images/portrait/[^\"\']+',
        r'https?://[^\"\']*/images/portrait/[^\"\']+',
    ]:
        urls += re.findall(pat, html, flags=re.I)
    clean = []
    seen = set()
    for u in urls:
        u = u.split('?')[0]
        if u in seen or 'default' in u.lower():
            continue
        seen.add(u)
        clean.append(u)
    clean.sort(key=lambda u: (0 if '/portrait/header/' in u else 1, 0 if '550550' in u else 1, len(u)))
    return clean[0] if clean else None

def choose_photo():
    global downloaded_portrait_url
    try:
        html = download_url(TM_PROFILE).decode('utf-8', errors='ignore')
        portrait = find_tm_portrait(html)
        if portrait:
            data = download_url(portrait, referer=TM_PROFILE)
            raw = project / 'var' / 'ramos_tm_raw_v211'
            raw.write_bytes(data)
            downloaded_portrait_url = portrait
            return Image.open(raw)
        warnings.append('Transfermarkt portrait URL not found; using local fallback.')
    except Exception as e:
        warnings.append(f'Transfermarkt download failed; using local fallback. Error: {e}')
    for p in source_photo_fallbacks:
        if p.exists():
            warnings.append(f'Local fallback photo used: {rel(p)}')
            return Image.open(p)
    raise RuntimeError('No Transfermarkt photo and no local fallback photo found.')

def replace_edge_light_bg_with_black(img):
    rgba = img.convert('RGBA')
    w, h = rgba.size
    px = rgba.load()
    def is_bg(x, y):
        r, g, b, a = px[x, y]
        if a < 30:
            return True
        if r > 200 and g > 200 and b > 200:
            return True
        if r > 118 and g > 118 and b > 118 and abs(r-g) < 50 and abs(g-b) < 60:
            return True
        mx, mn = max(r,g,b), min(r,g,b)
        if mx > 145 and (mx - mn) < 60:
            return True
        return False
    visited = [[False] * h for _ in range(w)]
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    bg = []
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or visited[x][y]:
            continue
        visited[x][y] = True
        if not is_bg(x, y):
            continue
        bg.append((x, y))
        q.append((x+1, y)); q.append((x-1, y)); q.append((x, y+1)); q.append((x, y-1))
    for x, y in bg:
        px[x, y] = (0, 0, 0, 255)
    black = Image.new('RGBA', rgba.size, (0, 0, 0, 255))
    black.alpha_composite(rgba)
    return black

def save_photo_all(img):
    fixed = replace_edge_light_bg_with_black(img)
    for target in photo_targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        backup(target)
        out = fixed.copy()
        if target.name == '41585.png' and target.exists():
            try:
                old_size = Image.open(target).size
                out = out.resize(old_size, Image.LANCZOS)
            except Exception:
                pass
        out.save(target)
        add_touched(target)

def make_flag_png(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    img = Image.new('RGB', (90, 60), (255, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 36, 60], fill=(0, 102, 0))
    d.ellipse([26, 20, 46, 40], fill=(255, 204, 0))
    d.ellipse([30, 24, 42, 36], fill=(255, 255, 255))
    d.rectangle([33, 26, 39, 35], fill=(210, 0, 0))
    d.ellipse([35, 28, 37, 30], fill=(0, 45, 150))
    d.ellipse([35, 32, 37, 34], fill=(0, 45, 150))
    img.save(path)
    add_touched(path)

def make_flag_svg(path):
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" role="img" aria-label="Portugal flag">
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
'''
    write_text(path, svg)

def set_yaml_field(text, key, value):
    pattern = rf'(?m)^({re.escape(key)}\\s*:\\s*).*$'
    if re.search(pattern, text):
        return re.sub(pattern, rf'\\g<1>{value}', text, count=1)
    if text.startswith('---'):
        idx = text.find('\\n---', 3)
        if idx != -1:
            return text[:idx] + f'\\n{key}: {value}' + text[idx:]
    return text + f'\\n{key}: {value}\\n'

def patch_ramos_front_matter():
    if not ramos_page.exists():
        warnings.append(f'Ramos page not found: {rel(ramos_page)}')
        return
    text = read_text(ramos_page)
    original = text
    for k in ['player_image', 'api_player_image', 'cutout_player_image']:
        text = set_yaml_field(text, k, PLAYER_SITE)
    text = set_yaml_field(text, 'player_image_source_name', 'Transfermarkt')
    text = set_yaml_field(text, 'player_image_source_url', TM_PROFILE)
    text = set_yaml_field(text, 'needs_cutout', 'false')
    for k in ['country_flag_image', 'flag_image', 'player_flag_image', 'player_country_flag_image', 'nationality_flag_image']:
        text = set_yaml_field(text, k, FLAG_SITE)
    for k in ['country_code', 'nationality_code']:
        text = set_yaml_field(text, k, 'PT')
    for k in ['country_flag', 'flag', 'player_flag', 'player_country_flag', 'nationality_flag']:
        text = set_yaml_field(text, k, '🇵🇹')
    text = set_yaml_field(text, 'milan_logo', '/images/clubs/ac-milan.svg')
    text = set_yaml_field(text, 'market_value', '€30M')
    text = set_yaml_field(text, 'value', '€30M')
    if text != original:
        write_text(ramos_page, text)

def make_hardfix_partial():
    partial = '''{{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }}
<style id="pfb-ramos-v211-hardfix-style">
body.pfb-ramos-v211-page img[src*="portugal-v211.png"],body.pfb-ramos-v211-page img[src*="/images/flags/"]{width:24px!important;height:16px!important;min-width:24px!important;max-width:24px!important;min-height:16px!important;max-height:16px!important;object-fit:cover!important;object-position:center center!important;display:inline-block!important;border-radius:2px!important;filter:none!important;opacity:1!important;mix-blend-mode:normal!important;background:transparent!important;flex:0 0 24px!important;vertical-align:middle!important}
body.pfb-ramos-v211-page img[src*="goncalo-ramos-550550-black-v211.png"],body.pfb-ramos-v211-page img[src*="41585.png"],body.pfb-ramos-v211-page img[src*="homepage/featured/goncalo-ramos"]{background:#000!important;object-fit:cover!important;object-position:center top!important}
body.pfb-ramos-v211-page [class*="market"],body.pfb-ramos-v211-page [class*="value"],body.pfb-ramos-v211-page [class*="price"],body.pfb-ramos-v211-page [class*="fee"]{white-space:nowrap!important;min-width:0!important;align-items:center!important;text-align:left!important}
</style>
<script id="pfb-ramos-v211-hardfix">
(function(){function rel(path){var base="{{ "" | relURL }}";if(!base||base==="/")return path;return base.replace(/\\/$/,"")+path;}var player=rel("/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png")+"?v=211";var flag=rel("/images/flags/portugal-v211.png")+"?v=211";function ramos(src){src=String(src||"").toLowerCase();return src.indexOf("41585")!==-1||src.indexOf("goncalo-ramos")!==-1||src.indexOf("gonçalo-ramos")!==-1||src.indexOf("homepage/featured/goncalo-ramos")!==-1;}function isflag(src){src=String(src||"").toLowerCase();return src.indexOf("/images/flags/")!==-1||src.indexOf("images/flags/")!==-1||src.indexOf("flag")!==-1;}function addFlag(){var nodes=document.querySelectorAll("body *");for(var i=0;i<nodes.length;i++){var el=nodes[i];if(!el||el.children.length>6)continue;var txt=(el.textContent||"").trim();if((txt.indexOf("Portugal")!==-1||txt.indexOf("Португал")!==-1)&&!el.querySelector('img[data-pfb-ramos-v211-flag="1"]')){var im=document.createElement("img");im.src=flag;im.alt="Portugal";im.setAttribute("data-pfb-ramos-v211-flag","1");im.style.cssText="width:24px;height:16px;min-width:24px;object-fit:cover;border-radius:2px;display:inline-block;margin-right:7px;vertical-align:middle;filter:none;opacity:1;background:transparent;";el.insertBefore(im,el.firstChild);break;}}}function fix(){if(location.pathname.indexOf("/transfers/goncalo-ramos-ac-milan")===-1)return;document.body.classList.add("pfb-ramos-v211-page");document.documentElement.setAttribute("data-pfb-ramos-v211","1");document.querySelectorAll("img").forEach(function(img){var src=img.getAttribute("src")||"";var alt=(img.getAttribute("alt")||"").toLowerCase();if(ramos(src)||alt.indexOf("gonçalo")!==-1||alt.indexOf("goncalo")!==-1||alt.indexOf("ramos")!==-1){img.setAttribute("src",player);img.setAttribute("data-pfb-ramos-v211-photo","1");img.style.background="#000";img.style.objectFit="cover";img.style.objectPosition="center top";}if(isflag(src)||alt.indexOf("portugal")!==-1||alt.indexOf("португал")!==-1){img.setAttribute("src",flag);img.setAttribute("data-pfb-ramos-v211-flag","1");img.style.width="24px";img.style.height="16px";img.style.minWidth="24px";img.style.objectFit="cover";img.style.filter="none";img.style.opacity="1";}});document.querySelectorAll("*").forEach(function(el){var bg="";try{bg=getComputedStyle(el).backgroundImage||"";}catch(e){}if(ramos(bg)){el.style.backgroundImage="url('"+player+"')";el.style.backgroundColor="#000";el.setAttribute("data-pfb-ramos-v211-bg","1");}});addFlag();}if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",fix);}else{fix();}setTimeout(fix,250);setTimeout(fix,1000);setTimeout(fix,2500);})();
</script>
{{ end }}
'''
    write_text(partial_path, partial)

def inject_partial_into_layouts():
    include = '{{ partial "ramos-hardfix-v211.html" . }}'
    candidates = []
    for rp in ['layouts/transfers/single.html','layouts/_default/single.html','layouts/_default/baseof.html','layouts/index.html']:
        p = project / rp
        if p.exists():
            candidates.append(p)
    layouts = project / 'layouts'
    if layouts.exists():
        for p in layouts.rglob('*.html'):
            if p == partial_path or p in candidates:
                continue
            try:
                txt = read_text(p)
            except Exception:
                continue
            low = txt.lower()
            if 'transfer' in low or '.content' in low or '</body>' in low:
                candidates.append(p)
    patched = []
    for p in candidates:
        txt = read_text(p)
        if include in txt or 'ramos-hardfix-v211' in txt:
            continue
        if '</body>' in txt.lower():
            txt2 = re.sub(r'(?i)</body>', include + '\\n</body>', txt, count=1)
        else:
            txt2 = txt.rstrip() + '\\n' + include + '\\n'
        write_text(p, txt2)
        patched.append(p)
    if not patched:
        raise RuntimeError('No Hugo layout was patched. Could not inject hardfix partial.')
    return patched

def patch_generated_files_directly():
    css_patch = '''
/* 211 verified Ramos hardfix */
body.pfb-ramos-v211-page img[src*="portugal-v211.png"],body.pfb-ramos-v211-page img[src*="/images/flags/"]{width:24px!important;height:16px!important;min-width:24px!important;object-fit:cover!important;filter:none!important;opacity:1!important}
body.pfb-ramos-v211-page img[src*="goncalo-ramos-550550-black-v211.png"],body.pfb-ramos-v211-page img[src*="41585.png"],body.pfb-ramos-v211-page img[src*="homepage/featured/goncalo-ramos"]{background:#000!important;object-fit:cover!important;object-position:center top!important}
body.pfb-ramos-v211-page [class*="market"],body.pfb-ramos-v211-page [class*="value"],body.pfb-ramos-v211-page [class*="price"],body.pfb-ramos-v211-page [class*="fee"]{white-space:nowrap!important;min-width:0!important}
'''
    for css in [project/'static/css/style.css', project/'public/css/style.css', project/'css/style.css']:
        old = read_text(css) if css.exists() else ''
        if '211 verified Ramos hardfix' not in old:
            write_text(css, old.rstrip() + '\\n\\n' + css_patch.strip() + '\\n')
    replacements = [
        ('/images/players/api/41585.png', PLAYER_SITE),
        ('images/players/api/41585.png', PLAYER_SITE.lstrip('/')),
        ('/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png', PLAYER_SITE),
        ('images/players/transfermarkt/goncalo-ramos-550550-black-v210.png', PLAYER_SITE.lstrip('/')),
        ('/images/players/transfermarkt/goncalo-ramos-550550-black.png', PLAYER_SITE),
        ('images/players/transfermarkt/goncalo-ramos-550550-black.png', PLAYER_SITE.lstrip('/')),
        ('/images/flags/portugal.svg', FLAG_SITE),
        ('images/flags/portugal.svg', FLAG_SITE.lstrip('/')),
        ('/images/flags/portugal-v210.png', FLAG_SITE),
        ('images/flags/portugal-v210.png', FLAG_SITE.lstrip('/')),
        ('/images/flags/portugal-proper.png', FLAG_SITE),
        ('images/flags/portugal-proper.png', FLAG_SITE.lstrip('/')),
    ]
    for base in [project/'public', project]:
        if not base.exists():
            continue
        for f in base.rglob('*'):
            if not f.is_file():
                continue
            parts = [x.lower() for x in f.parts]
            if '.git' in parts or '_backup_211_verified_ramos_page_hard_fix' in parts:
                continue
            if f.suffix.lower() not in ['.html','.htm','.md','.css','.js','.json']:
                continue
            try:
                txt = read_text(f)
            except Exception:
                continue
            low = txt.lower()
            if not any(x in low for x in ['goncalo','gonçalo','ramos','41585.png','portugal-v210','portugal.svg']):
                continue
            new = txt
            for old, rep in replacements:
                new = new.replace(old, rep)
            if f.suffix.lower() in ['.html','.htm'] and 'goncalo-ramos-ac-milan' in low and MARKER not in new:
                inj = read_text(partial_path)
                inj = re.sub(r'\\{\\{.*?\\}\\}', '', inj, flags=re.S).strip()
                if '</body>' in new.lower():
                    new = re.sub(r'(?i)</body>', inj + '\\n</body>', new, count=1)
                else:
                    new += '\\n' + inj
            if new != txt:
                write_text(f, new)

def run_hugo():
    global hugo_result
    try:
        p = run_cmd(['hugo', '-D'])
        hugo_result = f'returncode={p.returncode}\\nSTDOUT tail:\\n{p.stdout[-2000:]}\\nSTDERR tail:\\n{p.stderr[-2000:]}'
        if p.returncode != 0:
            warnings.append('hugo -D returned non-zero; direct patch still continues.')
    except Exception as e:
        hugo_result = f'hugo error: {e}'
        warnings.append(f'hugo -D could not run: {e}')

def copy_public_to_root_if_needed():
    mapping = [
        (project/'public/transfers/goncalo-ramos-ac-milan/index.html', project/'transfers/goncalo-ramos-ac-milan/index.html'),
        (project/'public/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png', project/'images/players/transfermarkt/goncalo-ramos-550550-black-v211.png'),
        (project/'public/images/players/api/41585.png', project/'images/players/api/41585.png'),
        (project/'public/images/flags/portugal-v211.png', project/'images/flags/portugal-v211.png'),
        (project/'public/css/style.css', project/'css/style.css'),
    ]
    for src, dst in mapping:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            backup(dst)
            shutil.copy2(src, dst)
            add_touched(dst)

def verify_black_image(path):
    if not path.exists():
        return False, 'missing'
    try:
        img = Image.open(path).convert('RGBA')
        w,h = img.size
        samples = [img.getpixel((0,0)), img.getpixel((w-1,0)), img.getpixel((0,h-1)), img.getpixel((w-1,h-1)), img.getpixel((w//2,0)), img.getpixel((w//2,h-1))]
        near_white = sum(1 for r,g,b,a in samples if a > 220 and r > 220 and g > 220 and b > 220)
        near_black = sum(1 for r,g,b,a in samples if a > 220 and r < 35 and g < 35 and b < 35)
        return near_black >= 2 and near_white == 0, f'size={w}x{h}, near_black={near_black}, near_white={near_white}, samples={samples}'
    except Exception as e:
        return False, str(e)

def verify_flag(path):
    if not path.exists():
        return False, 'missing'
    try:
        img = Image.open(path).convert('RGB')
        colors = img.getcolors(maxcolors=1000000) or []
        red = sum(c for c,(r,g,b) in colors if r > 180 and g < 80 and b < 80)
        green = sum(c for c,(r,g,b) in colors if g > 90 and r < 80 and b < 80)
        return red > 100 and green > 100, f'red_pixels={red}, green_pixels={green}, size={img.size}'
    except Exception as e:
        return False, str(e)

before_html = fetch_url(LOCAL_URL, timeout=4)
before_imgs = extract_img_srcs(before_html) if before_html else []

for p in flag_png_targets:
    make_flag_png(p)
for p in flag_svg_targets:
    make_flag_svg(p)

photo = choose_photo()
save_photo_all(photo)
patch_ramos_front_matter()
make_hardfix_partial()
patched_layouts = inject_partial_into_layouts()
run_hugo()
patch_generated_files_directly()
copy_public_to_root_if_needed()

time.sleep(1.5)
after_html = fetch_url(LOCAL_URL, timeout=5)
after_imgs = extract_img_srcs(after_html) if after_html else []

generated_html_paths = [p for p in [project/'public/transfers/goncalo-ramos-ac-milan/index.html', project/'transfers/goncalo-ramos-ac-milan/index.html'] if p.exists()]
marker_in_localhost = MARKER in after_html if after_html else False
marker_in_generated = any(MARKER in read_text(p) for p in generated_html_paths)
black_ok, black_info = verify_black_image(project/'static/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png')
flag_ok, flag_info = verify_flag(project/'static/images/flags/portugal-v211.png')
verified = (marker_in_localhost or marker_in_generated) and black_ok and flag_ok

lines = []
lines.append('PROFUTBIK 211 - VERIFIED RAMOS PAGE HARD FIX')
lines.append('='*80)
lines.append(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
lines.append(f'Project: {project}')
lines.append('')
lines.append('LOCAL PAGE')
lines.append(f'- URL checked: {LOCAL_URL}')
lines.append(f'- before_fetch_ok: {bool(before_html)}')
lines.append(f'- after_fetch_ok: {bool(after_html)}')
lines.append(f'- marker_in_localhost_after: {marker_in_localhost}')
lines.append(f'- marker_in_generated_html: {marker_in_generated}')
lines.append('')
lines.append('IMAGE SRC BEFORE')
lines += [f'- {src}' for src in before_imgs[:50]] or ['- none / localhost not fetched']
lines.append('')
lines.append('IMAGE SRC AFTER')
lines += [f'- {src}' for src in after_imgs[:50]] or ['- none / localhost not fetched']
lines.append('')
lines.append('PHOTO VERIFY')
lines.append('- static image: static/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png')
lines.append(f'- black_ok: {black_ok}')
lines.append(f'- details: {black_info}')
lines.append(f'- Transfermarkt profile: {TM_PROFILE}')
lines.append(f'- portrait used: {downloaded_portrait_url or "local fallback"}')
lines.append('')
lines.append('FLAG VERIFY')
lines.append('- static flag: static/images/flags/portugal-v211.png')
lines.append(f'- flag_ok: {flag_ok}')
lines.append(f'- details: {flag_info}')
lines.append('')
lines.append('PATCHED LAYOUTS')
lines += [f'- {rel(p)}' for p in patched_layouts]
lines.append('')
lines.append('GENERATED HTML CHECKED')
lines += [f'- {rel(p)}' for p in generated_html_paths] or ['- none']
lines.append('')
lines.append('HUGO RESULT')
lines.append(hugo_result)
lines.append('')
lines.append('TOUCHED FILES')
seen = set()
for p in touched:
    s = rel(p)
    if s not in seen:
        seen.add(s)
        lines.append(f'- {s}')
lines.append(f'- {rel(report_path)}')
lines.append('')
if warnings:
    lines.append('WARNINGS')
    for w in warnings:
        lines.append(f'- {w}')
    lines.append('')
lines.append(f'VERIFIED_OK: {verified}')
lines.append('')
lines.append('NO SITE OPENED.')
lines.append('NO Y/N ASKED.')
write_text(report_path, '\n'.join(lines))

if not verified:
    print(read_text(report_path))
    raise SystemExit('Verification failed. No push will be made.')

if args.push:
    files = []
    for p in touched + [report_path]:
        if p.exists():
            try:
                files.append(str(p.relative_to(project)))
            except Exception:
                pass
    unique = []
    seen = set()
    for f in files:
        if f not in seen:
            unique.append(f)
            seen.add(f)
    git_lines = []
    try:
        add = run_cmd(['git', 'add', '--'] + unique)
        git_lines.append(f'git add returncode: {add.returncode}')
        if add.stdout: git_lines.append('git add stdout:\\n' + add.stdout)
        if add.stderr: git_lines.append('git add stderr:\\n' + add.stderr)
        status = run_cmd(['git', 'status', '--short'])
        git_lines.append('git status --short after add:\\n' + status.stdout)
        if status.stdout.strip():
            commit = run_cmd(['git', 'commit', '-m', 'Verified Ramos photo flag hardfix'])
            git_lines.append(f'git commit returncode: {commit.returncode}')
            if commit.stdout: git_lines.append('git commit stdout:\\n' + commit.stdout)
            if commit.stderr: git_lines.append('git commit stderr:\\n' + commit.stderr)
            if commit.returncode == 0:
                push = run_cmd(['git', 'push'])
                git_lines.append(f'git push returncode: {push.returncode}')
                if push.stdout: git_lines.append('git push stdout:\\n' + push.stdout)
                if push.stderr: git_lines.append('git push stderr:\\n' + push.stderr)
            else:
                git_lines.append('push skipped because commit failed')
        else:
            git_lines.append('No git changes to commit after staging exact touched files.')
    except Exception as e:
        git_lines.append(f'GIT ERROR: {e}')
    report = read_text(report_path)
    report += '\\n\\nGIT RESULT\\n' + '-'*60 + '\\n' + '\\n'.join(git_lines) + '\\n'
    write_text(report_path, report)
    print(report)
else:
    print(read_text(report_path))
