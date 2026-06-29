from pathlib import Path
import re
import shutil
from datetime import datetime

project = Path.cwd()
backup_dir = project / "_backup_207_real_fix_ramos_flag_and_value_alignment"
backup_dir.mkdir(parents=True, exist_ok=True)

ramos_page = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
flag_path = project / "static" / "images" / "flags" / "portugal.svg"
css_candidates = [
    project / "static" / "css" / "transfer-article.css",
    project / "static" / "css" / "style.css",
]
rules_path = project / "docs" / "PROFUTBIK_TRANSFER_PLAYER_PAGE_RULES.md"
report_path = project / "var" / "profutbik_207_real_fix_ramos_flag_and_value_alignment_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

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

touched = []
warnings = []

# 1) Replace Portugal flag asset with a real visible flag SVG, not a white placeholder.
backup(flag_path)
portugal_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" role="img" aria-label="Portugal flag">
  <rect width="900" height="600" fill="#ff0000"/>
  <rect width="360" height="600" fill="#006600"/>
  <circle cx="360" cy="300" r="92" fill="#ffcc00"/>
  <circle cx="360" cy="300" r="66" fill="#ffffff"/>
  <path d="M320 248h80v86c0 34-18 58-40 70-22-12-40-36-40-70z" fill="#d80000"/>
  <path d="M334 262h52v70c0 22-12 39-26 49-14-10-26-27-26-49z" fill="#ffffff"/>
  <circle cx="347" cy="284" r="7" fill="#003399"/>
  <circle cx="373" cy="284" r="7" fill="#003399"/>
  <circle cx="360" cy="306" r="7" fill="#003399"/>
  <circle cx="347" cy="328" r="7" fill="#003399"/>
  <circle cx="373" cy="328" r="7" fill="#003399"/>
</svg>
"""
write(flag_path, portugal_svg)
touched.append(flag_path)

# 2) Fix Ramos front matter: all flag fields + wrong milan_logo.
if not ramos_page.exists():
    warnings.append(f"Missing Ramos page: {ramos_page}")
else:
    backup(ramos_page)
    text = read(ramos_page)

    def set_yaml_field(src, key, value):
        pattern = rf"(?m)^({re.escape(key)}\s*:\s*).*$"
        replacement = rf"\g<1>{value}"
        if re.search(pattern, src):
            return re.sub(pattern, replacement, src, count=1), True
        # insert before closing front matter
        if src.startswith("---"):
            idx = src.find("\n---", 3)
            if idx != -1:
                return src[:idx] + f"\n{key}: {value}" + src[idx:], True
        return src + f"\n{key}: {value}\n", True

    changes = []
    for key in [
        "country_flag_image",
        "flag_image",
        "player_flag_image",
        "player_country_flag_image",
        "nationality_flag_image",
    ]:
        new_text, _ = set_yaml_field(text, key, "/images/flags/portugal.svg")
        if new_text != text:
            changes.append(key)
            text = new_text

    for key in ["country_code", "nationality_code"]:
        new_text, _ = set_yaml_field(text, key, "PT")
        if new_text != text:
            changes.append(key)
            text = new_text

    for key in ["country_flag", "flag", "player_flag", "player_country_flag", "nationality_flag"]:
        new_text, _ = set_yaml_field(text, key, "🇵🇹")
        if new_text != text:
            changes.append(key)
            text = new_text

    # This was clearly wrong in the report: milan_logo pointed to Argentina flag.
    new_text, _ = set_yaml_field(text, "milan_logo", "/images/clubs/ac-milan.svg")
    if new_text != text:
        changes.append("milan_logo")
        text = new_text

    # Keep value fields explicit for the info block.
    if re.search(r"(?m)^market_value\s*:\s*", text) and not re.search(r"(?m)^value\s*:\s*", text):
        mv = re.search(r"(?m)^market_value\s*:\s*(.+)$", text).group(1).strip()
        new_text, _ = set_yaml_field(text, "value", mv)
        text = new_text
        changes.append("value")
    if re.search(r"(?m)^value\s*:\s*", text) and not re.search(r"(?m)^market_value\s*:\s*", text):
        val = re.search(r"(?m)^value\s*:\s*(.+)$", text).group(1).strip()
        new_text, _ = set_yaml_field(text, "market_value", val)
        text = new_text
        changes.append("market_value")

    write(ramos_page, text)
    touched.append(ramos_page)

# 3) Add a real CSS visual fix for flag rendering and value alignment.
css_file = None
for p in css_candidates:
    if p.exists():
        css_file = p
        break
if css_file is None:
    css_file = project / "static" / "css" / "style.css"
    css_file.parent.mkdir(parents=True, exist_ok=True)
    if not css_file.exists():
        write(css_file, "")

backup(css_file)
css = read(css_file)
marker = "/* 207 real fix Ramos flag and value alignment */"
css_block = r"""
/* 207 real fix Ramos flag and value alignment */
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
  flex: 0 0 24px !important;
  vertical-align: middle !important;
}

body.transfer-page .transfer-player-card img[src*="/images/flags/"],
body.transfer-page .transfer-article img[src*="/images/flags/"],
body.transfer-page .player-card img[src*="/images/flags/"] {
  margin-right: 7px !important;
}

body.transfer-page [class*="nationality"],
body.transfer-page [class*="country"],
body.transfer-page [class*="market"],
body.transfer-page [class*="value"] {
  min-width: 0 !important;
  box-sizing: border-box !important;
}

body.transfer-page [class*="market"] *,
body.transfer-page [class*="value"] *,
body.transfer-page [class*="price"] *,
body.transfer-page [class*="fee"] * {
  white-space: nowrap !important;
}

body.transfer-page [class*="market"],
body.transfer-page [class*="value"],
body.transfer-page [class*="price"] {
  align-items: center !important;
  text-align: left !important;
}

body.transfer-page [class*="country"],
body.transfer-page [class*="nationality"] {
  align-items: center !important;
}
"""
if marker not in css:
    css = css.rstrip() + "\n\n" + css_block.strip() + "\n"
    write(css_file, css)
    touched.append(css_file)

# 4) Strengthen rules.
rules_append = """
## 6. Visual identity block fix rule

If the nationality flag is shown as a white placeholder, do not only change front matter. Check the actual SVG/PNG asset and CSS.

Mandatory checks:
- the flag file itself must be a visible country flag, not a white placeholder;
- `img[src*="/images/flags/"]` must not be filtered to white;
- flag image must have fixed size and `object-fit: cover`;
- market value must be `white-space: nowrap`;
- wrong club/logo fields must not point to `/images/flags/`.

For Gonçalo Ramos:
- Portugal flag asset: `/images/flags/portugal.svg`;
- AC Milan logo field must not point to Argentina flag;
- value/market_value should remain `€30M`.
"""
if rules_path.exists():
    backup(rules_path)
    rules = read(rules_path)
else:
    rules = "# ProFutbik / Promyachik — правила страниц игроков и трансферов\n"
if "Visual identity block fix rule" not in rules:
    write(rules_path, rules.rstrip() + "\n\n" + rules_append.strip() + "\n")
    touched.append(rules_path)

# 5) Report.
lines = []
lines.append("PROFUTBIK 207 - REAL FIX RAMOS FLAG AND VALUE ALIGNMENT")
lines.append("=" * 70)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("FIXED")
lines.append("- Replaced Portugal flag asset with a real visible SVG flag.")
lines.append("- Forced Ramos flag fields to /images/flags/portugal.svg.")
lines.append("- Fixed wrong Ramos milan_logo field to /images/clubs/ac-milan.svg.")
lines.append("- Added CSS to stop flags being filtered/placeholder-looking.")
lines.append("- Added CSS to keep market/value text on one line and aligned.")
lines.append("")
lines.append("TOUCHED FILES")
for p in touched:
    try:
        lines.append(f"- {p.relative_to(project)}")
    except Exception:
        lines.append(f"- {p}")
lines.append(f"- {report_path.relative_to(project)}")
lines.append("")
if warnings:
    lines.append("WARNINGS")
    for w in warnings:
        lines.append(f"- {w}")
    lines.append("")
lines.append("CHECK MANUALLY")
lines.append("- Refresh Goncalo Ramos page with Ctrl+F5.")
lines.append("- Check nationality flag: must be Portugal, not white placeholder.")
lines.append("- Check market value: must stay aligned and not slide into citizenship block.")
lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")
lines.append("NO Y/N ASKED.")
write(report_path, "\n".join(lines))
print("\n".join(lines))
