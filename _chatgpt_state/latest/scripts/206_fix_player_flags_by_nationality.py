from pathlib import Path
import re
import unicodedata
import shutil
from datetime import datetime

project = Path.cwd()
content_dir = project / "content"
static_flags_dir = project / "static" / "images" / "flags"
docs_dir = project / "docs"
var_dir = project / "var"
backup_dir = project / "_backup_206_fix_player_flags_by_nationality"

docs_dir.mkdir(parents=True, exist_ok=True)
var_dir.mkdir(parents=True, exist_ok=True)
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = var_dir / "profutbik_206_fix_player_flags_by_nationality_report.txt"
rules_path = docs_dir / "PROFUTBIK_TRANSFER_PLAYER_PAGE_RULES.md"

FLAG_IMAGE_KEYS = [
    "country_flag_image",
    "flag_image",
    "player_flag_image",
    "player_country_flag_image",
    "nationality_flag_image",
]

FLAG_EMOJI_KEYS = [
    "country_flag",
    "flag",
    "player_flag",
    "player_country_flag",
    "nationality_flag",
]

COUNTRY_KEYS = [
    "nationality",
    "player_nationality",
    "player_country",
    "country",
]

CODE_KEYS = [
    "country_code",
    "nationality_code",
    "player_country_code",
]

COUNTRY_CODE_TO_NAME = {
    "PT": "Portugal",
    "AR": "Argentina",
    "BR": "Brazil",
    "FR": "France",
    "ES": "Spain",
    "GB": "England",
    "EN": "England",
    "DE": "Germany",
    "IT": "Italy",
    "NL": "Netherlands",
    "BE": "Belgium",
    "TR": "Turkey",
    "RU": "Russia",
    "UA": "Ukraine",
    "HR": "Croatia",
    "UY": "Uruguay",
    "CO": "Colombia",
    "MA": "Morocco",
    "SN": "Senegal",
    "NG": "Nigeria",
    "DK": "Denmark",
    "SE": "Sweden",
    "NO": "Norway",
    "PL": "Poland",
    "CH": "Switzerland",
    "AT": "Austria",
    "CZ": "Czech Republic",
    "RS": "Serbia",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "CM": "Cameroon",
    "CI": "Ivory Coast",
    "EG": "Egypt",
    "US": "United States",
    "MX": "Mexico",
    "JP": "Japan",
    "KR": "South Korea",
}

COUNTRY_NAME_TO_CODE = {v.lower(): k for k, v in COUNTRY_CODE_TO_NAME.items()}
COUNTRY_NAME_TO_CODE.update({
    "portugal": "PT",
    "argentina": "AR",
    "brazil": "BR",
    "brasil": "BR",
    "france": "FR",
    "spain": "ES",
    "england": "GB",
    "germany": "DE",
    "italy": "IT",
    "netherlands": "NL",
    "holland": "NL",
    "belgium": "BE",
    "turkey": "TR",
    "russia": "RU",
    "ukraine": "UA",
    "croatia": "HR",
    "uruguay": "UY",
    "colombia": "CO",
    "morocco": "MA",
    "senegal": "SN",
    "nigeria": "NG",
    "denmark": "DK",
    "sweden": "SE",
    "norway": "NO",
    "poland": "PL",
    "switzerland": "CH",
    "austria": "AT",
    "czech republic": "CZ",
    "serbia": "RS",
    "slovenia": "SI",
    "slovakia": "SK",
    "cameroon": "CM",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "côte d’ivoire": "CI",
    "egypt": "EG",
    "united states": "US",
    "usa": "US",
    "mexico": "MX",
    "japan": "JP",
    "south korea": "KR",
})

COUNTRY_EMOJI = {
    "PT": "🇵🇹",
    "AR": "🇦🇷",
    "BR": "🇧🇷",
    "FR": "🇫🇷",
    "ES": "🇪🇸",
    "GB": "🏴",
    "DE": "🇩🇪",
    "IT": "🇮🇹",
    "NL": "🇳🇱",
    "BE": "🇧🇪",
    "TR": "🇹🇷",
    "RU": "🇷🇺",
    "UA": "🇺🇦",
    "HR": "🇭🇷",
    "UY": "🇺🇾",
    "CO": "🇨🇴",
    "MA": "🇲🇦",
    "SN": "🇸🇳",
    "NG": "🇳🇬",
    "DK": "🇩🇰",
    "SE": "🇸🇪",
    "NO": "🇳🇴",
    "PL": "🇵🇱",
    "CH": "🇨🇭",
    "AT": "🇦🇹",
    "CZ": "🇨🇿",
    "RS": "🇷🇸",
    "SI": "🇸🇮",
    "SK": "🇸🇰",
    "CM": "🇨🇲",
    "CI": "🇨🇮",
    "EG": "🇪🇬",
    "US": "🇺🇸",
    "MX": "🇲🇽",
    "JP": "🇯🇵",
    "KR": "🇰🇷",
}

FLAG_ALIAS_TO_SLUG = {
    "portugal": "portugal",
    "argentina": "argentina",
    "brazil": "brazil",
    "brasil": "brazil",
    "france": "france",
    "spain": "spain",
    "england": "england",
    "germany": "germany",
    "italy": "italy",
    "netherlands": "netherlands",
    "holland": "netherlands",
    "belgium": "belgium",
    "turkey": "turkey",
    "russia": "russia",
    "ukraine": "ukraine",
    "croatia": "croatia",
    "uruguay": "uruguay",
    "colombia": "colombia",
    "morocco": "morocco",
    "senegal": "senegal",
    "nigeria": "nigeria",
    "denmark": "denmark",
    "sweden": "sweden",
    "norway": "norway",
    "poland": "poland",
    "switzerland": "switzerland",
    "austria": "austria",
    "czech republic": "czech-republic",
    "serbia": "serbia",
    "slovenia": "slovenia",
    "slovakia": "slovakia",
    "cameroon": "cameroon",
    "ivory coast": "ivory-coast",
    "cote d'ivoire": "ivory-coast",
    "côte d’ivoire": "ivory-coast",
    "egypt": "egypt",
    "united states": "united-states",
    "usa": "united-states",
    "mexico": "mexico",
    "japan": "japan",
    "south korea": "south-korea",
}

PLACEHOLDER_WORDS = [
    "placeholder", "default", "unknown", "empty", "blank", "white",
    "no-flag", "noflag", "flag-placeholder", "stub", "заглуш"
]

def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = value.replace("’", "'")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")

def normalize_country(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    upper = raw.upper()
    if upper in COUNTRY_CODE_TO_NAME:
        raw = COUNTRY_CODE_TO_NAME[upper]
    return slugify(raw)

def code_for_country(country_slug: str) -> str:
    if not country_slug:
        return ""
    for alias, slug in FLAG_ALIAS_TO_SLUG.items():
        if slug == country_slug and alias in COUNTRY_NAME_TO_CODE:
            return COUNTRY_NAME_TO_CODE[alias]
    pretty = country_slug.replace("-", " ")
    return COUNTRY_NAME_TO_CODE.get(pretty.lower(), "")

def clean_value(v: str) -> str:
    v = (v or "").strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        v = v[1:-1]
    return v.strip()

def is_placeholder_path(v: str) -> bool:
    s = (v or "").lower().strip()
    if not s:
        return True
    if s in ["false", "true", "api-football"]:
        return True
    return any(w in s for w in PLACEHOLDER_WORDS)

def resolve_site_path(site_path: str):
    s = clean_value(site_path)
    if not s or s.startswith(("http://", "https://")):
        return None
    if "?" in s:
        s = s.split("?", 1)[0]
    if s.startswith("/promyachik/"):
        s = s[len("/promyachik/"):]
    if s.startswith("/"):
        s = s[1:]
    candidates = [
        project / s,
        project / "static" / s,
    ]
    if not s.startswith("images/"):
        candidates.append(project / "static" / "images" / s)
    for c in candidates:
        if c.exists():
            return c
    return None

def is_valid_flag_path(v: str) -> bool:
    if is_placeholder_path(v):
        return False
    s = clean_value(v)
    if "/images/flags/" not in s.replace("\\", "/").lower():
        return False
    return resolve_site_path(s) is not None

def site_path_from_static(path: Path) -> str:
    try:
        rel = path.relative_to(project / "static").as_posix()
        return "/" + rel
    except Exception:
        return path.as_posix()

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, text: str):
    p.write_text(text, encoding="utf-8")

def parse_front_matter(text: str):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return "---", text[3:end], text[end+4:]
    if text.startswith("+++"):
        end = text.find("\n+++", 3)
        if end != -1:
            return "+++", text[3:end], text[end+4:]
    return None, None, text

def fm_to_pairs(fm_text: str):
    pairs = []
    for line in fm_text.splitlines():
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+)(\s*:\s*)(.*?)(\s*)$", line)
        if m:
            pairs.append({
                "line": line,
                "key": m.group(2),
                "value": clean_value(m.group(4)),
                "prefix": m.group(1),
                "sep": m.group(3),
                "suffix": m.group(5),
                "matched": True,
            })
        else:
            pairs.append({"line": line, "matched": False})
    return pairs

def get_field(pairs, key):
    key_l = key.lower()
    for item in pairs:
        if item.get("matched") and item["key"].lower() == key_l:
            return item["value"]
    return ""

def set_field(pairs, key, value):
    key_l = key.lower()
    value = str(value)
    for item in pairs:
        if item.get("matched") and item["key"].lower() == key_l:
            if item["value"] != value:
                item["value"] = value
                item["line"] = f'{item["prefix"]}{item["key"]}{item["sep"]}{value}{item["suffix"]}'
                return True
            return False
    pairs.append({
        "line": f"{key}: {value}",
        "key": key,
        "value": value,
        "prefix": "",
        "sep": ": ",
        "suffix": "",
        "matched": True,
        "added": True,
    })
    return True

def pairs_to_fm(pairs):
    return "\n".join(item["line"] for item in pairs)

def page_country_slug(pairs):
    for k in COUNTRY_KEYS:
        v = get_field(pairs, k)
        if v:
            return normalize_country(v)
    for k in CODE_KEYS:
        v = get_field(pairs, k)
        if v:
            return normalize_country(v)
    return ""

def page_country_code(pairs, country_slug):
    for k in CODE_KEYS:
        v = get_field(pairs, k).strip().upper()
        if v in COUNTRY_CODE_TO_NAME:
            return v
    return code_for_country(country_slug)

def collect_flag_files():
    m = {}
    if static_flags_dir.exists():
        for p in static_flags_dir.iterdir():
            if p.is_file() and p.suffix.lower() in [".svg", ".png", ".webp", ".jpg", ".jpeg"]:
                m[slugify(p.stem)] = site_path_from_static(p)
    return m

def best_flag_for_country(country_slug, country_to_existing_flag, flag_files):
    if not country_slug:
        return ""
    if country_slug in country_to_existing_flag:
        return country_to_existing_flag[country_slug]
    canonical = FLAG_ALIAS_TO_SLUG.get(country_slug, country_slug)
    if canonical in flag_files:
        return flag_files[canonical]
    if country_slug in flag_files:
        return flag_files[country_slug]
    return ""

def backup_file(path: Path):
    rel = path.relative_to(project)
    out = backup_dir / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() and path.exists():
        shutil.copy2(path, out)

pages = []
if content_dir.exists():
    for p in content_dir.rglob("*.md"):
        text = read_text(p)
        kind, fm_text, body = parse_front_matter(text)
        if kind and ("transfers" in str(p).lower() or any(t in text.lower() for t in ["player:", "player_name:", "transfer_fee:", "market_value:"])):
            pages.append((p, text, kind, fm_text, body))

flag_files = collect_flag_files()

country_to_existing_flag = {}
for p, text, kind, fm_text, body in pages:
    pairs = fm_to_pairs(fm_text)
    cslug = page_country_slug(pairs)
    if not cslug:
        continue
    for key in FLAG_IMAGE_KEYS:
        v = get_field(pairs, key)
        if is_valid_flag_path(v):
            country_to_existing_flag.setdefault(cslug, clean_value(v))
            break

changed_pages = []
fixed_flags = []
warnings = []
suspicious_logo_fields = []
market_syncs = []

for p, text, kind, fm_text, body in pages:
    pairs = fm_to_pairs(fm_text)
    cslug = page_country_slug(pairs)
    if not cslug:
        warnings.append(f"{p.relative_to(project)}: no nationality/country field found")
        continue

    desired_flag = best_flag_for_country(cslug, country_to_existing_flag, flag_files)
    if not desired_flag:
        warnings.append(f"{p.relative_to(project)}: no flag asset found for country slug '{cslug}'")
        continue

    code = page_country_code(pairs, cslug)
    emoji = COUNTRY_EMOJI.get(code, "")

    page_changes = []

    for key in FLAG_IMAGE_KEYS:
        old = get_field(pairs, key)
        if clean_value(old) != desired_flag:
            set_field(pairs, key, desired_flag)
            page_changes.append(f"{key}: {old or '<missing>'} -> {desired_flag}")

    if code:
        for key in ["country_code", "nationality_code"]:
            old = get_field(pairs, key)
            if clean_value(old).upper() != code:
                set_field(pairs, key, code)
                page_changes.append(f"{key}: {old or '<missing>'} -> {code}")

    if emoji:
        for key in FLAG_EMOJI_KEYS:
            old = get_field(pairs, key)
            if clean_value(old) != emoji:
                set_field(pairs, key, emoji)
                page_changes.append(f"{key}: {old or '<missing>'} -> {emoji}")

    market_value = get_field(pairs, "market_value")
    value = get_field(pairs, "value")
    if market_value and not value:
        set_field(pairs, "value", market_value)
        page_changes.append(f"value: <missing> -> {market_value}")
        market_syncs.append(f"{p.relative_to(project)}: value filled from market_value")
    elif value and not market_value:
        set_field(pairs, "market_value", value)
        page_changes.append(f"market_value: <missing> -> {value}")
        market_syncs.append(f"{p.relative_to(project)}: market_value filled from value")

    for item in pairs:
        if item.get("matched"):
            k = item["key"].lower()
            v = item["value"].replace("\\", "/").lower()
            if (k.endswith("_logo") or k.endswith("_badge") or k.endswith("_crest")) and "/images/flags/" in v:
                suspicious_logo_fields.append(f"{p.relative_to(project)}: {item['key']} -> {item['value']}")

    if page_changes:
        backup_file(p)
        new_fm = pairs_to_fm(pairs)
        new_text = f"{kind}\n{new_fm}\n{kind}{body}"
        write_text(p, new_text)
        changed_pages.append(p)
        fixed_flags.append((p, cslug, desired_flag, page_changes))

rules_append = """
## 5. Player identity block — обязательная проверка

После блока статистики у любого нового игрока всегда проверяется информационный блок игрока:

- гражданство;
- флаг гражданства;
- рыночная стоимость;
- позиция;
- возраст;
- клубы;
- визуальное выравнивание значений.

Флаг нельзя оставлять белой заглушкой.  
Если у игрока нет флага, но у другого игрока с такой же страной флаг уже есть, использовать тот же файл флага.

Пример:
- Bernardo Silva — Portugal → `/images/flags/portugal.svg`;
- Gonçalo Ramos — Portugal → должен получить тот же `/images/flags/portugal.svg`.

Для новых игроков все common-поля флага должны быть синхронизированы:

```text
country_flag_image
flag_image
player_flag_image
player_country_flag_image
nationality_flag_image
```

Если поле `market_value` или `value` отсутствует, но второе есть, значения нужно синхронизировать.  
Если цена визуально съезжает в блок гражданства, сначала проверить флаг/placeholder и только потом править CSS.
"""

if rules_path.exists():
    rules_text = read_text(rules_path)
else:
    rules_text = "# ProFutbik / Promyachik — правила страниц игроков и трансферов\n"
if "Player identity block — обязательная проверка" not in rules_text:
    if rules_path.exists():
        backup_file(rules_path)
    write_text(rules_path, rules_text.rstrip() + "\n\n" + rules_append.strip() + "\n")
    rules_changed = True
else:
    rules_changed = False

lines = []
lines.append("PROFUTBIK 206 - FIX PLAYER FLAGS BY NATIONALITY")
lines.append("=" * 70)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("WHAT THIS PACKAGE DID")
lines.append("- Normalized player nationality flag fields across transfer/player pages.")
lines.append("- Used existing valid flag from players with the same country when available.")
lines.append("- Fallback: static/images/flags/<country>.svg/png when available.")
lines.append("- Synchronized value/market_value only when one was missing.")
lines.append("- Updated player identity block rule in docs.")
lines.append("")
lines.append("CHANGED PAGES")
if fixed_flags:
    for p, cslug, flag, changes in fixed_flags:
        lines.append(f"- {p.relative_to(project)} | country={cslug} | flag={flag}")
        for ch in changes:
            lines.append(f"  * {ch}")
else:
    lines.append("- No page front matter changes were needed.")
lines.append("")
lines.append("SUSPICIOUS CLUB LOGO/BADGE/CREST FIELDS POINTING TO FLAGS")
if suspicious_logo_fields:
    for s in suspicious_logo_fields:
        lines.append(f"- {s}")
else:
    lines.append("- None found.")
lines.append("")
lines.append("MARKET VALUE SYNC")
if market_syncs:
    for s in market_syncs:
        lines.append(f"- {s}")
else:
    lines.append("- No missing market_value/value fields needed sync.")
lines.append("")
lines.append("WARNINGS")
if warnings:
    for w in warnings:
        lines.append(f"- {w}")
else:
    lines.append("- No warnings.")
lines.append("")
lines.append("TOUCHED FILES")
for p in changed_pages:
    lines.append(f"- {p.relative_to(project)}")
if rules_changed:
    lines.append(f"- {rules_path.relative_to(project)}")
lines.append(f"- {report_path.relative_to(project)}")
lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")
lines.append("NO Y/N ASKED.")

write_text(report_path, "\n".join(lines))
print("\n".join(lines))
