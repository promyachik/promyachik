
from pathlib import Path
import datetime
import re
from urllib.request import urlopen
from urllib.error import URLError

ROOT = Path(r"C:\Users\Dmitrii\Promyachik")
REPORT = ROOT / "var" / "promyachik_270_locate_real_cucurella_graph_source_no_changes_report.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)

TARGET_URL = "http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/"
TARGET_PUBLIC = ROOT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

SEARCH_DIRS = ["layouts", "content", "static", "assets", "data", "public"]
EXTS = {".html", ".htm", ".md", ".css", ".js", ".json", ".toml", ".yaml", ".yml", ".txt", ".xml", ".svg"}
SKIP_PARTS = {".git", "node_modules", "resources", "_backup", "backups", "Promyachik_BACKUPS"}
TOKENS = [
    "marc-cucurella-real-madrid",
    "Marc Cucurella",
    "Cucurella",
    "Кукурель",
    "market_value_chart",
    "player-market",
    "market-value",
    "value_label",
    "chart.points",
    "club_logo",
    "ДИНАМИКА",
    "€20",
    "€25",
    "€30",
    "€40",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
    "promyachik-cucurella",
]

def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"__READ_ERROR__ {e}"

def snippet(text, pos, radius=220):
    a = max(0, pos-radius)
    b = min(len(text), pos+radius)
    s = text[a:b].replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s

log = []
log.append("PROMYACHIK 270 - LOCATE REAL CUCURELLA GRAPH SOURCE - NO CHANGES")
log.append("="*100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {ROOT}")
log.append("RULE")
log.append("- This script DOES NOT modify files.")
log.append("- No backup.")
log.append("- No push.")
log.append("- No site opened.")
log.append("- Goal: find the exact file/source that renders the visible Cucurella chart year above price.")
log.append("")

# Live page check
log.append("LIVE TARGET PAGE")
log.append(f"url: {TARGET_URL}")
try:
    live = urlopen(TARGET_URL, timeout=8).read().decode("utf-8", errors="ignore")
    log.append(f"live_fetch_ok: True")
    log.append(f"live_length: {len(live)}")
    for token in ["player-market", "market-value", "ДИНАМИКА", "€20", "€25", "2021", "2022", "2023", "2024", "2025"]:
        log.append(f"live_count {token}: {live.count(token)}")
    log.append("live_fragments_around_euro:")
    euros = [m.start() for m in re.finditer("€", live)]
    for p in euros[:15]:
        log.append("  " + snippet(live, p))
except Exception as e:
    log.append(f"live_fetch_ok: False")
    log.append(f"live_error: {repr(e)}")
log.append("")

# Public target check
log.append("PUBLIC TARGET HTML")
log.append(f"path: {TARGET_PUBLIC}")
log.append(f"exists: {TARGET_PUBLIC.exists()}")
if TARGET_PUBLIC.exists():
    public = read_text(TARGET_PUBLIC)
    log.append(f"public_length: {len(public)}")
    for token in ["player-market", "market-value", "ДИНАМИКА", "€20", "€25", "2021", "2022", "2023", "2024", "2025"]:
        log.append(f"public_count {token}: {public.count(token)}")
    log.append("public_fragments_around_euro:")
    euros = [m.start() for m in re.finditer("€", public)]
    for p in euros[:15]:
        log.append("  " + snippet(public, p))
log.append("")

# Project-wide source search
log.append("SOURCE SEARCH")
hits = []
for d in SEARCH_DIRS:
    base = ROOT / d
    if not base.exists():
        log.append(f"dir_missing: {d}")
        continue
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts_lower = {p.lower() for p in rel.parts}
        if any(skip.lower() in parts_lower for skip in SKIP_PARTS):
            continue
        if path.suffix.lower() not in EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        matched = []
        for token in TOKENS:
            c = text.count(token)
            if c:
                matched.append((token, c))
        if matched:
            score = sum(c for _, c in matched)
            # boost likely source files
            rels = str(rel).replace('\\', '/')
            if any(x in rels for x in ["transfer-player-market-value-chart", "marc-cucurella-real-madrid", "player", "chart"]):
                score += 1000
            hits.append((score, rel, matched, text))

hits.sort(key=lambda x: (-x[0], str(x[1])))
log.append(f"files_with_hits: {len(hits)}")
for idx, (score, rel, matched, text) in enumerate(hits[:80], 1):
    log.append("")
    log.append(f"HIT {idx}: {rel}")
    log.append(f"score: {score}")
    log.append("tokens: " + ", ".join(f"{t}={c}" for t,c in matched[:20]))
    # print useful snippets around top priority tokens
    for token in ["player-market", "market-value", "market_value_chart", "value_label", "€20", "2021", "promyachik-cucurella", "marc-cucurella-real-madrid"]:
        pos = text.find(token)
        if pos != -1:
            log.append(f"snippet around {token}: {snippet(text, pos)}")
            break

log.append("")
log.append("DONE")
REPORT.write_text("\n".join(log), encoding="utf-8")
print("DONE")
print(f"REPORT: {REPORT}")
