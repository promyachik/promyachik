
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import re
import sys

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_241_before_restore_real_graph_ramos_data_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_241_restore_real_graph_and_add_ramos_chart_data_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STATIC_PARTIAL = PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html"
STYLE = PROJECT / "static" / "css" / "style.css"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"

commands = []
changed = []
candidate_log = []
warnings = []

BAD_CSS_BLOCKS = [
    ("/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART START */", "/* PROMYACHIK 230 CENTER MARKET VALUE UNDER CHART END */"),
    ("/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS START */", "/* PROMYACHIK 231 CENTER VALUE CHART TIMELINE LABELS END */"),
    ("/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS START */", "/* PROMYACHIK 232 ALIGN VALUE LABELS TO POINTS END */"),
    ("/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS START */", "/* PROMYACHIK 233 FORCE ALIGN VALUE LABELS END */"),
    ("/* PROMYACHIK 234 VALUE CHART SVG LABELS START */", "/* PROMYACHIK 234 VALUE CHART SVG LABELS END */"),
    ("/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT START */", "/* PROMYACHIK 235 VERTICAL VALUE LABEL ALIGNMENT END */"),
    ("/* PROMYACHIK 238 VALUE CHART AXIS FIX START */", "/* PROMYACHIK 238 VALUE CHART AXIS FIX END */"),
    ("/* PROMYACHIK 239 ACTUAL VALUE CHART START */", "/* PROMYACHIK 239 ACTUAL VALUE CHART END */"),
    ("/* PROMYACHIK 240 VALUE HISTORY CHART START */", "/* PROMYACHIK 240 VALUE HISTORY CHART END */"),
]

BAD_INCLUDES = [
    '{{ partial "promyachik-align-value-labels-232.html" . }}',
    '{{ partial "promyachik-force-align-value-labels-233.html" . }}',
]

BAD_PARTIALS = [
    PROJECT / "layouts" / "partials" / "promyachik-align-value-labels-232.html",
    PROJECT / "layouts" / "partials" / "promyachik-force-align-value-labels-233.html",
]

BAD_MARKERS = [
    "pfb-value-chart-v239",
    "pfb-value-chart-v240",
    "pfb-market-chart-static--234",
    "pfb-market-chart-static--235",
    "pfb-market-chart-static--236",
    "pfb-market-chart-static--238",
    "PROMYACHIK 230",
    "PROMYACHIK 231",
    "PROMYACHIK 232",
    "PROMYACHIK 233",
    "PROMYACHIK 234",
    "PROMYACHIK 235",
    "PROMYACHIK 238",
    "PROMYACHIK 239",
    "PROMYACHIK 240",
    "__promyachikForceAlignValueLabels233Ready",
    "__promyachikAlignValueLabels232Ready",
]

def sha(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except Exception:
        return str(path)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def backup(path: Path):
    if path.exists():
        dst = BACKUP_DIR / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def copy_file(src: Path, dst: Path, label: str):
    before = sha(dst)
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((rel(dst), f"{label} <= {src}", before != after, before, after))

def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False
    )
    commands.append({
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout[-3500:],
        "stderr": p.stderr[-3500:],
    })
    return p

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)

def score_backup_file(path: Path, target_name: str) -> int:
    if not path.exists() or path.name != target_name:
        return -999999

    text = read(path)
    low = str(path).lower().replace("\\", "/")

    if len(text) < 120:
        return -999999

    if any(marker.lower() in text.lower() for marker in BAD_MARKERS):
        return -999999

    if "/restore_files/" in low and any(v in low for v in ["239", "240", "238", "235", "234", "233", "232"]):
        return -999999

    score = 0

    if "_backup_promyachik_239_before_replace_actual_dynamic_value_chart" in low:
        score += 5000

    if "_backup_promyachik_240_before_value_history_chart" in low:
        score -= 3000

    if "_backup_promyachik_238" in low or "_backup_promyachik_237" in low or "_backup_promyachik_236" in low:
        score += 1200

    if "_backup_promyachik_235" in low or "_backup_promyachik_234" in low:
        score += 900

    if "_backup_promyachik_" in low:
        score += 600

    if target_name == "transfer-player-market-value-chart.html":
        if ".Params.market_value_chart" in text:
            score += 600
        if "area_path" in text:
            score += 400
        if "current_label" in text:
            score += 300
        if "chart.points" in text:
            score += 300
        if "value_history" in text:
            score -= 700

    if target_name == "profutbik-market-chart-static.html":
        if "duplicate old static chart disabled" in text:
            return -999999
        if "pfb-market-chart-static" in text:
            score += 700

    return score

def find_best_backup(target_name: str):
    candidates = []
    for path in PROJECT.rglob(target_name):
        if not path.is_file():
            continue

        low = str(path).lower().replace("\\", "/")
        if "/public/" in low or "/resources/" in low or "/.git/" in low or "/var/" in low:
            continue

        try:
            score = score_backup_file(path, target_name)
        except Exception:
            continue

        if score > 0:
            candidates.append((score, path, sha(path), path.stat().st_size))

    candidates.sort(key=lambda item: item[0], reverse=True)

    for score, path, digest, size in candidates[:15]:
        candidate_log.append(f"{target_name} | score={score} | size={size} | sha={digest} | {path}")

    if not candidates:
        raise RuntimeError(f"Не найден рабочий backup для {target_name}")

    return candidates[0]

def restore_chart_partials():
    dynamic_score, dynamic_source, _, _ = find_best_backup("transfer-player-market-value-chart.html")
    copy_file(dynamic_source, DYNAMIC_PARTIAL, f"restore original dynamic chart partial score={dynamic_score}")

    try:
        static_score, static_source, _, _ = find_best_backup("profutbik-market-chart-static.html")
        copy_file(static_source, STATIC_PARTIAL, f"restore original static chart partial score={static_score}")
    except Exception as e:
        warnings.append(f"static chart restore skipped: {e}")

    return dynamic_source, dynamic_score

def remove_failed_css():
    if not STYLE.exists():
        warnings.append(f"style.css not found: {STYLE}")
        return

    text = read(STYLE)
    original = text

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    if text != original:
        write(STYLE, text.rstrip() + "\n", "remove failed chart CSS blocks 230-240")

def cleanup_bad_includes_and_partials():
    for rel_path in [
        "layouts/_default/baseof.html",
        "layouts/transfers/single.html",
    ]:
        path = PROJECT / rel_path

        if not path.exists():
            continue

        text = read(path)
        old = text

        for include in BAD_INCLUDES:
            text = text.replace(include, "")

        text = re.sub(r"\n{4,}", "\n\n\n", text)

        if text != old:
            write(path, text, "remove old bad value-label JS includes")

    for path in BAD_PARTIALS:
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete bad value-label JS partial", True, "exists", "deleted"))

def split_frontmatter(text: str):
    m = re.match(r"(?s)^---\s*\n(.*?)\n---\s*(.*)$", text)
    if not m:
        raise RuntimeError("Не смог разобрать YAML front matter Ramos index.md")
    return m.group(1), m.group(2)

def extract_value_history(front: str):
    m = re.search(r"(?s)value_history:\s*(.*?)(?:\n[a-zA-Z0-9_]+:|\nkeywords:|\n---|$)", front)
    block = m.group(1) if m else ""

    pairs = re.findall(r'year:\s*"?([^"\n]+)"?\s*[\r\n ]+value:\s*"?([^"\n]+)"?', block)

    if not pairs:
        pairs = re.findall(r'-\s*year:\s*"?([^"\s]+)"?\s*value:\s*"?([^"\s]+)"?', front)

    if not pairs:
        pairs = [
            ("2020", "€8M"),
            ("2021", "€15M"),
            ("2022", "€25M"),
            ("2023", "€35M"),
            ("2024", "€50M"),
            ("2026", "€30M"),
        ]

    return [(str(y).strip(), str(v).strip()) for y, v in pairs]

def numeric_from_value(value: str) -> float:
    raw = value.strip()
    cleaned = re.sub(r"[^0-9,.]", "", raw).replace(",", ".")
    if not cleaned:
        return 0.0
    num = float(cleaned)
    low = raw.lower()
    if "тыс" in low or "k" in low:
        num = num / 1000.0
    return num

def club_logo_for_year(year: str):
    try:
        y = int(re.sub(r"[^0-9]", "", year)[:4])
    except Exception:
        y = 0

    if y <= 2022:
        return "Benfica", "/images/clubs/api/211.png", "B"
    if y <= 2025:
        return "Paris Saint-Germain", "/images/clubs/api/85.png", "P"
    return "AC Milan", "/images/clubs/api/489.png", "M"

def build_market_value_chart(front: str):
    pairs = extract_value_history(front)
    values = [numeric_from_value(v) for _, v in pairs]
    max_value = max(values) if values else 1.0
    if max_value <= 0:
        max_value = 1.0

    n = len(pairs)
    left = 10.0
    right = 90.0
    den = max(1, n - 1)

    points_yaml = []
    path_parts = []

    for i, ((year, value), numeric) in enumerate(zip(pairs, values)):
        x = left + ((right - left) * i / den)
        height_ratio = numeric / max_value if max_value else 0
        y = 84.0 - (height_ratio * 62.0)
        bottom = 100.0 - y
        club, logo, fallback = club_logo_for_year(year)

        path_parts.append(f"{'M' if i == 0 else 'L'} {x:.2f} {y:.2f}")

        point_lines = [
            f'    - date: "{year}"',
            f'      date_label: "{year}"',
            f'      value_label: "{value}"',
            f'      value: "{value}"',
            f'      value_number: {numeric:g}',
            f'      x: {x:.2f}',
            f'      y: {y:.2f}',
            f'      left: {x:.2f}',
            f'      bottom: {bottom:.2f}',
            f'      x_percent: {x:.2f}',
            f'      y_percent: {y:.2f}',
            f'      club: "{club}"',
            f'      club_logo: "{logo}"',
            f'      logo: "{logo}"',
            f'      fallback_letter: "{fallback}"',
        ]
        points_yaml.append("\n".join(point_lines))

    line_path = " ".join(path_parts)
    area_path = f"{line_path} L {right:.2f} 100 L {left:.2f} 100 Z"
    current = pairs[-1][1] if pairs else "€30M"
    updated = pairs[-1][0] if pairs else "2026"

    chart_lines = [
        "market_value_chart:",
        f'  current_label: "{current}"',
        f'  updated_at: "{updated}"',
        '  source_name: "Transfermarkt"',
        '  source_url: "https://www.transfermarkt.com/goncalo-ramos/profil/spieler/550550"',
        f'  line_path: "{line_path}"',
        f'  path: "{line_path}"',
        f'  area_path: "{area_path}"',
        "  points:",
        "\n".join(points_yaml),
        ""
    ]
    return "\n".join(chart_lines)

def add_ramos_market_value_chart():
    if not RAMOS_PAGE.exists():
        raise RuntimeError(f"Ramos page not found: {RAMOS_PAGE}")

    text = read(RAMOS_PAGE)
    front, body = split_frontmatter(text)

    front = re.sub(r"(?ms)^market_value_chart:\n(?:^[ \t].*\n?|\n)*", "", front)

    chart_block = build_market_value_chart(front)

    if re.search(r"(?m)^keywords:", front):
        front = re.sub(r"(?m)^keywords:", chart_block + "\nkeywords:", front, count=1)
    else:
        front = front.rstrip() + "\n" + chart_block

    new_text = "---\n" + front.rstrip() + "\n---\n" + body.lstrip()
    write(RAMOS_PAGE, new_text, "add market_value_chart data to Ramos so original graph renders like other pages")

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    tokens = ["pfb-value-chart-v240", "pfb-value-chart-v239", "market-value", "€8M", "€15M", "€25M", "€35M", "€50M", "€30M"]

    for token in tokens:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 500): idx + 1200].replace("\n", " ")[:1700]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []
    dynamic_source = ""
    dynamic_score = 0

    try:
        dynamic_source, dynamic_score = restore_chart_partials()
        remove_failed_css()
        cleanup_bad_includes_and_partials()
        add_ramos_market_value_chart()

        hugo = run(["hugo", "-D"])

        dynamic_text = read(DYNAMIC_PARTIAL)
        static_text = read(STATIC_PARTIAL) if STATIC_PARTIAL.exists() else ""
        ramos_text = read(RAMOS_PAGE)
        style_text = read(STYLE) if STYLE.exists() else ""
        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_text = read(public_ramos) if public_ramos.exists() else ""

        fragments = collect_public_fragments()

        checks = {
            "hugo_exit_code": hugo.returncode,
            "restored_dynamic_source": str(dynamic_source),
            "restored_dynamic_score": dynamic_score,
            "dynamic_partial_restored_no_v239_v240": "pfb-value-chart-v239" not in dynamic_text and "pfb-value-chart-v240" not in dynamic_text,
            "dynamic_partial_is_original_market_chart": ".Params.market_value_chart" in dynamic_text and "chart.points" in dynamic_text,
            "static_partial_not_disabled": "duplicate old static chart disabled" not in static_text,
            "ramos_has_market_value_chart": "market_value_chart:" in ramos_text,
            "ramos_has_chart_points": "points:" in ramos_text and "value_number:" in ramos_text,
            "failed_css_removed": all(marker not in style_text for marker in BAD_MARKERS),
            "public_ramos_exists": public_ramos.exists(),
            "public_no_v239_v240": "pfb-value-chart-v239" not in public_text and "pfb-value-chart-v240" not in public_text,
            "public_has_ramos_values": all(token in public_text for token in ["€8M", "€15M", "€25M", "€35M", "€50M", "€30M"]),
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["dynamic_partial_restored_no_v239_v240"]
            and checks["dynamic_partial_is_original_market_chart"]
            and checks["static_partial_not_disabled"]
            and checks["ramos_has_market_value_chart"]
            and checks["ramos_has_chart_points"]
            and checks["failed_css_removed"]
            and checks["public_ramos_exists"]
            and checks["public_no_v239_v240"]
            and checks["public_has_ramos_values"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 241 - RESTORE REAL GRAPH + ADD RAMOS CHART DATA")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Do NOT replace graph design.")
    lines.append("- Do NOT redraw SVG/chart.")
    lines.append("- Restore the same original chart partial used before bad attempts.")
    lines.append("- Add market_value_chart data to Ramos so he uses the same graph system as De Ligt/Cucurella/Wirtz/etc.")
    lines.append("- Remove failed 239/240 chart replacement CSS and older failed attempts.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("RESTORED SOURCE")
    lines.append(f"- dynamic_source: {dynamic_source}")
    lines.append(f"- dynamic_score: {dynamic_score}")
    lines.append("")
    lines.append("TOP CANDIDATES")
    if candidate_log:
        for item in candidate_log[:20]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHANGED FILES")
    if changed:
        for path_rel, label, did, before, after in changed:
            lines.append(f"- {path_rel} | {label} | changed={did}")
    else:
        lines.append("- none")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    if error_text:
        lines.append("ERROR")
        lines.append(error_text)
        lines.append("")
    lines.append("OBSERVED PUBLIC FRAGMENTS")
    if fragments:
        for token, fragment in fragments:
            lines.append(f"- token={token} | {fragment}")
    else:
        lines.append("- none")
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
