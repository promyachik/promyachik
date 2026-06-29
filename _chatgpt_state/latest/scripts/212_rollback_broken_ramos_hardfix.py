from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import urllib.request

project = Path.cwd()
backup_dir = project / "_backup_212_rollback_broken_ramos_hardfix"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_212_rollback_broken_ramos_hardfix_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

LOCAL_URL = "http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/"
RAMOS_PAGE = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
BROKEN_PARTIAL = project / "layouts" / "partials" / "ramos-hardfix-v211.html"

touched = []
warnings = []
hugo_result = ""

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
    p.write_text(text, encoding="utf-8")
    add_touched(p)

def delete_file(p: Path):
    if p.exists():
        backup(p)
        p.unlink()
        add_touched(p)

def fetch_url(url, timeout=4):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        warnings.append(f"Could not fetch {url}: {e}")
        return ""

def run_cmd(cmd):
    return subprocess.run(cmd, cwd=project, capture_output=True, text=True)

def strip_broken_blocks(text: str) -> str:
    original = text

    # Remove partial include line.
    text = text.replace('{{ partial "ramos-hardfix-v211.html" . }}', "")
    text = text.replace("{{ partial \"ramos-hardfix-v211.html\" . }}", "")

    # Remove hardfix style/script by id.
    text = re.sub(r'<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*', "", text, flags=re.I | re.S)
    text = re.sub(r'<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*', "", text, flags=re.I | re.S)

    # Remove generated no-id blocks containing the marker/class.
    text = re.sub(r'<style[^>]*>[^<]*(?:pfb-ramos-v211|211 verified Ramos hardfix|210 hard Ramos photo flag value fix)[\s\S]*?</style>\s*', "", text, flags=re.I)
    text = re.sub(r'<script[^>]*>[\s\S]*?pfb-ramos-v211[\s\S]*?</script>\s*', "", text, flags=re.I)

    # Remove CSS marker blocks appended at the end of CSS files.
    markers = [
        "/* 211 verified Ramos hardfix */",
        "/* 210 hard Ramos photo flag value fix */",
        "/* 209 final Ramos photo flag value fix */",
        "/* 208 ramos flag visibility and market value alignment */",
        "/* 207 real fix Ramos flag and value alignment */",
    ]
    for marker in markers:
        while marker in text:
            start = text.find(marker)
            # stop at next top-level marker or EOF
            nexts = []
            for m in ["\n/* ", "\n</style>", "\n<script", "\n</script>"]:
                idx = text.find(m, start + len(marker))
                if idx != -1:
                    nexts.append(idx)
            end = min(nexts) if nexts else len(text)
            text = text[:start].rstrip() + "\n" + text[end:].lstrip()

    # Remove body class/data artifacts if injected.
    text = text.replace("pfb-ramos-v211-page", "")
    text = text.replace('data-pfb-ramos-v211="1"', "")
    text = text.replace("data-pfb-ramos-v211='1'", "")

    # Replace v210/v211 asset paths back to normal non-hardfix fields.
    replacements = [
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "/images/players/api/41585.png"),
        ("images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "images/players/api/41585.png"),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "/images/players/api/41585.png"),
        ("images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "images/players/api/41585.png"),
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

def set_yaml_field(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^({re.escape(key)}\s*:\s*).*$"
    if re.search(pattern, text):
        return re.sub(pattern, rf"\g<1>{value}", text, count=1)
    if text.startswith("---"):
        idx = text.find("\n---", 3)
        if idx != -1:
            return text[:idx] + f"\n{key}: {value}" + text[idx:]
    return text + f"\n{key}: {value}\n"

def restore_portugal_svg():
    flag = project / "static" / "images" / "flags" / "portugal.svg"
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
    write_text(flag, svg)

def normalize_ramos_front_matter():
    if not RAMOS_PAGE.exists():
        warnings.append(f"Ramos page not found: {rel(RAMOS_PAGE)}")
        return
    text = read_text(RAMOS_PAGE)
    original = text

    text = strip_broken_blocks(text)

    for key in ["player_image", "api_player_image"]:
        text = set_yaml_field(text, key, "/images/players/api/41585.png")
    # Do not force broken cutout image.
    text = set_yaml_field(text, "cutout_player_image", "")
    text = set_yaml_field(text, "player_image_source_name", "API-Football")
    text = set_yaml_field(text, "player_image_source_url", "https://media.api-sports.io/football/players/41585.png")
    text = set_yaml_field(text, "needs_cutout", "True")

    for key in ["country_flag_image", "flag_image", "player_flag_image", "player_country_flag_image", "nationality_flag_image"]:
        text = set_yaml_field(text, key, "/images/flags/portugal.svg")
    for key in ["country_code", "nationality_code"]:
        text = set_yaml_field(text, key, "PT")
    for key in ["country_flag", "flag", "player_flag", "player_country_flag", "nationality_flag"]:
        text = set_yaml_field(text, key, "🇵🇹")

    text = set_yaml_field(text, "milan_logo", "/images/clubs/ac-milan.svg")
    text = set_yaml_field(text, "market_value", "€30M")
    text = set_yaml_field(text, "value", "€30M")

    if text != original:
        write_text(RAMOS_PAGE, text)

def clean_files():
    # Delete broken partial.
    delete_file(BROKEN_PARTIAL)

    # Clean layouts, CSS, generated HTML, markdown/json/js where broken hardfix may exist.
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
            if ".git" in parts or "_backup_212_rollback_broken_ramos_hardfix" in parts:
                continue
            txt = read_text(p)
            new = strip_broken_blocks(txt)
            if new != txt:
                write_text(p, new)

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

before = fetch_url(LOCAL_URL)
clean_files()
normalize_ramos_front_matter()
restore_portugal_svg()
run_hugo()
# clean again after Hugo generated files
clean_files()

after = fetch_url(LOCAL_URL)
bad_markers = ["pfb-ramos-v211", "ramos-hardfix-v211", "goncalo-ramos-550550-black-v211", "portugal-v211"]
marker_after_localhost = any(m in after for m in bad_markers) if after else False

generated_paths = [p for p in [
    project / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html",
    project / "transfers" / "goncalo-ramos-ac-milan" / "index.html",
] if p.exists()]
marker_after_generated = False
for p in generated_paths:
    txt = read_text(p)
    if any(m in txt for m in bad_markers):
        marker_after_generated = True

verified = (not marker_after_localhost) and (not marker_after_generated) and (not BROKEN_PARTIAL.exists())

lines = []
lines.append("PROFUTBIK 212 - ROLLBACK BROKEN RAMOS HARDFIX")
lines.append("=" * 80)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("WHAT WAS REMOVED")
lines.append("- Deleted layouts/partials/ramos-hardfix-v211.html if present.")
lines.append("- Removed partial include from layouts.")
lines.append("- Removed v211 script/style hardfix blocks.")
lines.append("- Removed v210/v211 asset paths from Ramos content/generated files.")
lines.append("- Restored Ramos normal fields to API photo and portugal.svg.")
lines.append("- Kept AC Milan logo field fixed.")
lines.append("")
lines.append("LOCALHOST CHECK")
lines.append(f"- URL: {LOCAL_URL}")
lines.append(f"- before_fetch_ok: {bool(before)}")
lines.append(f"- after_fetch_ok: {bool(after)}")
lines.append(f"- bad_marker_after_localhost: {marker_after_localhost}")
lines.append(f"- bad_marker_after_generated: {marker_after_generated}")
lines.append(f"- broken_partial_exists_after: {BROKEN_PARTIAL.exists()}")
lines.append("")
lines.append("GENERATED HTML CHECKED")
if generated_paths:
    for p in generated_paths:
        lines.append(f"- {rel(p)}")
else:
    lines.append("- none")
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
lines.append(f"ROLLBACK_VERIFIED_OK: {verified}")
lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")

write_text(report_path, "\n".join(lines))
print(read_text(report_path))

if not verified:
    raise SystemExit("Rollback verification failed. Check report.")
