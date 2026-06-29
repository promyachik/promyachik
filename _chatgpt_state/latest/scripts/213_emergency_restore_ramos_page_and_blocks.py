from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import urllib.request

project = Path.cwd()
emergency_backup = project / "_backup_213_emergency_restore_ramos_page_and_blocks"
emergency_backup.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_213_emergency_restore_ramos_page_and_blocks_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

LOCAL_URL = "http://localhost:1313/promyachik/transfers/goncalo-ramos-ac-milan/"

targets = {
    "ramos": project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md",
    "transfer_single": project / "layouts" / "transfers" / "single.html",
    "default_single": project / "layouts" / "_default" / "single.html",
    "baseof": project / "layouts" / "_default" / "baseof.html",
    "index_layout": project / "layouts" / "index.html",
    "style_css": project / "static" / "css" / "style.css",
    "stats_partial": project / "layouts" / "partials" / "transfer-player-stats.html",
    "portugal_svg": project / "static" / "images" / "flags" / "portugal.svg",
}

broken_partial = project / "layouts" / "partials" / "ramos-hardfix-v211.html"

bad_tokens = [
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
    "\\nplayer_image:",
]

touched = []
warnings = []
hugo_result = ""
selected = {}

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project))
    except Exception:
        return str(p)

def run_cmd(cmd):
    return subprocess.run(cmd, cwd=project, capture_output=True, text=True)

def read_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_file(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    backup_current(p)
    p.write_text(text, encoding="utf-8", newline="\n")
    if p not in touched:
        touched.append(p)

def backup_current(p: Path):
    if p.exists():
        dst = emergency_backup / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)

def delete_file(p: Path):
    if p.exists():
        backup_current(p)
        p.unlink()
        if p not in touched:
            touched.append(p)

def has_bad(text: str) -> bool:
    return any(tok in text for tok in bad_tokens)

def clean_exact_bad_refs(text: str) -> str:
    original = text

    text = text.replace('{{ partial "ramos-hardfix-v211.html" . }}', "")
    text = text.replace("{{ partial \"ramos-hardfix-v211.html\" . }}", "")

    # Remove exact hardfix style/script blocks only.
    text = re.sub(r'<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*', "", text, flags=re.I | re.S)
    text = re.sub(r'<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*', "", text, flags=re.I | re.S)

    # Remove compact CSS blocks by exact marker only.
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

def git_show(path_rel: str, rev: str):
    p = run_cmd(["git", "show", f"{rev}:{path_rel}"])
    if p.returncode == 0:
        return p.stdout
    return None

def collect_git_candidates(path_rel: str, max_depth=40):
    out = []
    for i in range(max_depth + 1):
        rev = "HEAD" if i == 0 else f"HEAD~{i}"
        txt = git_show(path_rel, rev)
        if txt is not None:
            out.append((f"git:{rev}", txt))
    return out

def collect_backup_candidates(path_rel: str):
    out = []
    for b in sorted(project.glob("_backup_*"), reverse=True):
        p = b / path_rel
        if p.exists() and p.is_file():
            try:
                out.append((f"backup:{b.name}", read_file(p)))
            except Exception:
                pass
    return out

def score_ramos(text: str) -> int:
    s = 0
    if "Gonçalo Ramos" in text: s += 50
    if "Paris Saint-Germain" in text or "Paris Saint Germain" in text: s += 10
    if "AC Milan" in text: s += 10
    if "player_image: /images/players/api/41585.png" in text or 'player_image: "/images/players/api/41585.png"' in text: s += 35
    if "country_flag_image: /images/flags/portugal.svg" in text or 'country_flag_image: "/images/flags/portugal.svg"' in text: s += 35
    if "market_value: €30M" in text or 'market_value: "€30M"' in text: s += 10
    if "transfer-player-stats" in text: s -= 5
    if "\\nplayer_image:" in text: s -= 200
    if has_bad(text): s -= 200
    if "<script" in text and "pfb-ramos" in text: s -= 300
    return s

def score_layout(text: str, needs_stats=False) -> int:
    s = 0
    if has_bad(text): s -= 300
    if "ramos-hardfix-v211" in text: s -= 300
    if needs_stats and "transfer-player-stats.html" in text: s += 80
    if "{{ .Content }}" in text or ".Content" in text: s += 10
    if "transfer" in text.lower(): s += 5
    return s

def choose_candidate(path_rel: str, scorer, fallback_current=True):
    candidates = []
    candidates += collect_backup_candidates(path_rel)
    candidates += collect_git_candidates(path_rel)
    p = project / path_rel
    if fallback_current and p.exists():
        candidates.append(("current-cleaned", clean_exact_bad_refs(read_file(p))))

    if not candidates:
        return None, None, None

    scored = []
    for source, txt in candidates:
        scored.append((scorer(txt), source, txt))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_source, best_text = scored[0]
    return best_source, best_score, clean_exact_bad_refs(best_text)

def restore_portugal_svg():
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
    write_file(targets["portugal_svg"], svg)

def clean_generated_and_css():
    roots = [
        project / "public",
        project / "css",
        project / "transfers" / "goncalo-ramos-ac-milan",
        project / "static" / "css",
    ]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in [".html", ".htm", ".css", ".js", ".json", ".md"]:
                continue
            parts = [x.lower() for x in p.parts]
            if ".git" in parts or emergency_backup.name.lower() in parts:
                continue
            txt = read_file(p)
            new = clean_exact_bad_refs(txt)
            if new != txt:
                write_file(p, new)

def fetch_local():
    try:
        req = urllib.request.Request(LOCAL_URL, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        warnings.append(f"localhost fetch failed: {e}")
        return ""

# 1. Remove broken hardfix partial.
delete_file(broken_partial)

# 2. Restore Ramos markdown from the best clean source.
source, score, text = choose_candidate("content/transfers/goncalo-ramos-ac-milan/index.md", score_ramos)
if text is None or score < 0:
    raise SystemExit("Could not find a clean Ramos page candidate in backups/git history.")
# Ensure the obvious wrong logo field is fixed, but do not inject fields into body.
text = re.sub(r"(?m)^milan_logo\s*:.*$", "milan_logo: /images/clubs/ac-milan.svg", text)
text = re.sub(r"(?m)^player_image\s*:.*$", "player_image: /images/players/api/41585.png", text)
text = re.sub(r"(?m)^api_player_image\s*:.*$", "api_player_image: /images/players/api/41585.png", text)
text = re.sub(r"(?m)^cutout_player_image\s*:.*$", "cutout_player_image: ", text)
text = re.sub(r"(?m)^country_flag_image\s*:.*$", "country_flag_image: /images/flags/portugal.svg", text)
text = re.sub(r"(?m)^flag_image\s*:.*$", "flag_image: /images/flags/portugal.svg", text)
text = re.sub(r"(?m)^player_flag_image\s*:.*$", "player_flag_image: /images/flags/portugal.svg", text)
text = re.sub(r"(?m)^player_country_flag_image\s*:.*$", "player_country_flag_image: /images/flags/portugal.svg", text)
text = re.sub(r"(?m)^nationality_flag_image\s*:.*$", "nationality_flag_image: /images/flags/portugal.svg", text)
write_file(targets["ramos"], text)
selected["ramos"] = f"{source}, score={score}"

# 3. Restore key layouts from clean source so blocks come back.
for key, path_rel, needs_stats in [
    ("transfer_single", "layouts/transfers/single.html", True),
    ("default_single", "layouts/_default/single.html", False),
    ("baseof", "layouts/_default/baseof.html", False),
    ("index_layout", "layouts/index.html", False),
    ("style_css", "static/css/style.css", False),
]:
    p = project / path_rel
    source, score, txt = choose_candidate(path_rel, lambda t, ns=needs_stats: score_layout(t, ns), fallback_current=True)
    if txt is not None and score > -100:
        write_file(p, txt)
        selected[key] = f"{source}, score={score}"
    elif p.exists():
        cleaned = clean_exact_bad_refs(read_file(p))
        write_file(p, cleaned)
        selected[key] = "current-cleaned fallback"

# 4. Restore Portugal flag to a visible normal SVG.
restore_portugal_svg()

# 5. Clean generated/public/css bad references.
clean_generated_and_css()

# 6. Rebuild Hugo if available.
try:
    p = run_cmd(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-2000:]}\nSTDERR tail:\n{p.stderr[-2000:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero.")
except Exception as e:
    hugo_result = f"hugo error: {e}"
    warnings.append(f"hugo -D could not run: {e}")

# 7. Clean again after build.
clean_generated_and_css()

# 8. Verify source files.
source_ramos = read_file(targets["ramos"]) if targets["ramos"].exists() else ""
transfer_single = read_file(targets["transfer_single"]) if targets["transfer_single"].exists() else ""
localhost_html = fetch_local()

bad_in_source = has_bad(source_ramos) or "\\nplayer_image:" in source_ramos
bad_in_layout = "ramos-hardfix-v211" in transfer_single or "pfb-ramos-v211" in transfer_single
stats_include_ok = "transfer-player-stats.html" in transfer_single
literal_fields_on_localhost = "\\nplayer_image:" in localhost_html or "player_image: /images/players" in localhost_html
bad_on_localhost = any(tok in localhost_html for tok in bad_tokens if tok != "\\nplayer_image:") if localhost_html else False

# local can be unavailable; source/layout verification is the important part.
verified = (not bad_in_source) and (not bad_in_layout) and stats_include_ok and (not literal_fields_on_localhost) and (not bad_on_localhost)

lines = []
lines.append("PROFUTBIK 213 - EMERGENCY RESTORE RAMOS PAGE AND BLOCKS")
lines.append("=" * 90)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("SELECTED RESTORE SOURCES")
for k, v in selected.items():
    lines.append(f"- {k}: {v}")
lines.append("")
lines.append("RESTORED")
lines.append("- Ramos markdown restored from clean backup/git candidate.")
lines.append("- Broken v210/v211 Ramos hardfix references removed.")
lines.append("- layouts/partials/ramos-hardfix-v211.html removed if present.")
lines.append("- transfer layout restored with transfer-player-stats.html include.")
lines.append("- CSS cleaned from v207-v211 Ramos hardfix blocks only.")
lines.append("- Portugal flag restored as visible portugal.svg.")
lines.append("")
lines.append("VERIFY")
lines.append(f"- bad_in_ramos_source: {bad_in_source}")
lines.append(f"- bad_in_transfer_layout: {bad_in_layout}")
lines.append(f"- stats_include_ok_in_layouts/transfers/single.html: {stats_include_ok}")
lines.append(f"- localhost_fetched: {bool(localhost_html)}")
lines.append(f"- literal_fields_on_localhost: {literal_fields_on_localhost}")
lines.append(f"- bad_v210_v211_on_localhost: {bad_on_localhost}")
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

write_file(report_path, "\n".join(lines))
print(read_file(report_path))

if not verified:
    raise SystemExit("Emergency restore verification failed. Check report before doing anything else.")
