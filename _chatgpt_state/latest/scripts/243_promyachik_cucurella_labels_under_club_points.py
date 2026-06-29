
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_243_before_cucurella_labels_under_points_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_243_cucurella_labels_under_club_points_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE = PROJECT / "static" / "css" / "style.css"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

commands = []
changed = []
candidate_log = []
warnings = []

CSS_START = "/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START */"
CSS_END = "/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END */"

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
    ("/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN START */", "/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN END */"),
    (CSS_START, CSS_END),
]

BAD_MARKERS = [
    "pfb-value-chart-v239",
    "pfb-value-chart-v240",
    "__promyachikCucurellaAlignPriceLabels242Ready",
    "promyachik-cucurella-align-price-labels-242",
    "PROMYACHIK 239",
    "PROMYACHIK 240",
    "PROMYACHIK 242",
]

CSS_BLOCK = '''
/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START */

/*
   Страница Marc Cucurella:
   не трогаем график, линию, точки, логотипы.
   Меняется только нижний ряд подписей.
   Каждая подпись позиционируется через left из той же точки market_value_chart.points.
*/

body.transfer-page .promyachik-cucurella-labels-243 {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    min-height: 58px !important;
    height: 58px !important;
    margin: 8px 0 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}

body.transfer-page .promyachik-cucurella-label-243 {
    position: absolute !important;
    top: 0 !important;
    transform: translateX(-50%) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    min-width: 74px !important;
    max-width: 118px !important;
    text-align: center !important;
    white-space: nowrap !important;
    line-height: 1.08 !important;
    float: none !important;
    box-sizing: border-box !important;
}

body.transfer-page .promyachik-cucurella-label-243__date {
    display: block !important;
    width: 100% !important;
    margin: 0 0 5px !important;
    text-align: center !important;
}

body.transfer-page .promyachik-cucurella-label-243__value {
    display: block !important;
    width: 100% !important;
    margin: 0 !important;
    text-align: center !important;
}

/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END */
'''

CUCURELLA_LABEL_BLOCK = r'''{{ if in .RelPermalink "/transfers/marc-cucurella-real-madrid/" }}
<!-- PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START -->
{{ $promyachikCucCount243 := len $chart.points }}
{{ $promyachikCucDenom243 := sub $promyachikCucCount243 1 }}
{{ if lt $promyachikCucDenom243 1 }}
    {{ $promyachikCucDenom243 = 1 }}
{{ end }}

<div class="promyachik-cucurella-labels-243" aria-label="Подписи стоимости Кукурельи под точками клубов">
    {{ range $promyachikCucIndex243, $promyachikCucPoint243 := $chart.points }}
        {{ $promyachikCucComputedLeft243 := add 10.0 (mul (div (float $promyachikCucIndex243) (float $promyachikCucDenom243)) 80.0) }}
        {{ $promyachikCucLeft243 := default $promyachikCucComputedLeft243 $promyachikCucPoint243.left }}
        {{ with $promyachikCucPoint243.x }}
            {{ $promyachikCucLeft243 = . }}
        {{ end }}
        {{ with $promyachikCucPoint243.x_percent }}
            {{ $promyachikCucLeft243 = . }}
        {{ end }}
        {{ $promyachikCucLeftText243 := printf "%v" $promyachikCucLeft243 }}

        <div
            class="promyachik-cucurella-label-243"
            style="left: {{ $promyachikCucLeftText243 }}{{ if not (in $promyachikCucLeftText243 "%") }}%{{ end }};"
            data-club="{{ default "" $promyachikCucPoint243.club }}"
            data-left="{{ $promyachikCucLeftText243 }}"
        >
            <span class="promyachik-cucurella-label-243__date">
                {{ default $promyachikCucPoint243.date $promyachikCucPoint243.date_label }}
            </span>
            <strong class="promyachik-cucurella-label-243__value">
                {{ $promyachikCucPoint243.value_label }}
            </strong>
        </div>
    {{ end }}
</div>
<!-- PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END -->
{{ else }}
__ORIGINAL_LABEL_BLOCK__
{{ end }}'''

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

def token_iter(text: str):
    token_re = re.compile(r"{{-?\s*(range|with|if)\b[^}]*-?}}|{{-?\s*end\s*-?}}", re.S)
    for m in token_re.finditer(text):
        raw = m.group(0)
        kind_match = re.match(r"{{-?\s*(range|with|if)\b", raw, re.S)
        kind = kind_match.group(1) if kind_match else "end"
        yield m.start(), m.end(), kind, raw

def find_matching_end(text: str, start_token_end: int):
    depth = 1
    for s, e, kind, raw in token_iter(text[start_token_end:]):
        abs_e = start_token_end + e

        if kind in ["range", "with", "if"]:
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return abs_e

    return -1

def find_label_range_block(text: str):
    starts = []
    range_re = re.compile(r"{{-?\s*range\b[^}]*\$chart\.points[^}]*-?}}", re.S)

    for m in range_re.finditer(text):
        end = find_matching_end(text, m.end())
        if end == -1:
            continue

        block = text[m.start():end]
        if "value_label" in block and ".date" in block and "club_logo" not in block:
            starts.append((m.start(), end, block))

    if not starts:
        for m in range_re.finditer(text):
            end = find_matching_end(text, m.end())
            if end == -1:
                continue
            block = text[m.start():end]
            if "value_label" in block:
                starts.append((m.start(), end, block))

    if not starts:
        raise RuntimeError("Не нашёл в transfer-player-market-value-chart.html нижний range $chart.points с .date и .value_label.")

    return starts[-1]

def score_backup(path: Path) -> int:
    if not path.exists() or path.name != "transfer-player-market-value-chart.html":
        return -999999

    text = read(path)
    low = str(path).lower().replace("\\", "/")

    if len(text) < 120:
        return -999999

    if "/public/" in low or "/resources/" in low or "/.git/" in low or "/var/" in low:
        return -999999

    if any(marker in text for marker in BAD_MARKERS):
        return -999999

    if "/restore_files/" in low and any(v in low for v in ["239", "240", "242", "243"]):
        return -999999

    score = 0

    if "_backup_promyachik_239_before_replace_actual_dynamic_value_chart" in low:
        score += 5000

    if "_backup_promyachik_240_before_value_history_chart" in low:
        score -= 2000

    if "_backup_promyachik_" in low:
        score += 500

    if ".Params.market_value_chart" in text:
        score += 500

    if "chart.points" in text:
        score += 300

    if "area_path" in text:
        score += 250

    if "value_history" in text:
        score -= 400

    return score

def restore_original_chart_if_needed():
    if not DYNAMIC_PARTIAL.exists():
        raise RuntimeError(f"missing {DYNAMIC_PARTIAL}")

    current = read(DYNAMIC_PARTIAL)

    if "pfb-value-chart-v239" not in current and "pfb-value-chart-v240" not in current and "value_history" not in current:
        candidate_log.append("dynamic partial already looks original; no restore needed")
        return "not needed", 0

    candidates = []
    for path in PROJECT.rglob("transfer-player-market-value-chart.html"):
        try:
            score = score_backup(path)
        except Exception:
            continue

        if score > 0:
            candidates.append((score, path, sha(path), path.stat().st_size))

    candidates.sort(key=lambda item: item[0], reverse=True)

    for score, path, digest, size in candidates[:12]:
        candidate_log.append(f"score={score} | size={size} | sha={digest} | {path}")

    if not candidates:
        raise RuntimeError("Нужно восстановить старый график, но backup transfer-player-market-value-chart.html не найден.")

    score, source, _, _ = candidates[0]
    copy_file(source, DYNAMIC_PARTIAL, f"restore original chart partial before 239/240 replacement score={score}")
    return str(source), score

def patch_cucurella_label_block():
    text = read(DYNAMIC_PARTIAL)

    text = re.sub(
        r"{{\s*if\s+in\s+\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*}}"
        r".*?PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END.*?"
        r"{{\s*else\s*}}(.*?){{\s*end\s*}}",
        lambda m: m.group(1),
        text,
        flags=re.S,
    )

    start, end, original_block = find_label_range_block(text)

    replacement = CUCURELLA_LABEL_BLOCK.replace("__ORIGINAL_LABEL_BLOCK__", original_block)

    text = text[:start] + replacement + text[end:]

    write(DYNAMIC_PARTIAL, text, "patch only the bottom label range: Cucurella labels use the same X as club points")

def cleanup_style():
    if not STYLE.exists():
        raise RuntimeError(f"missing {STYLE}")

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "remove failed label/chart CSS blocks and add Cucurella label CSS")

def remove_242_partial_include_if_present():
    partial = PROJECT / "layouts" / "partials" / "promyachik-cucurella-align-price-labels-242.html"
    if partial.exists():
        backup(partial)
        partial.unlink()
        changed.append((rel(partial), "delete old 242 JS label align partial", True, "exists", "deleted"))

    single = PROJECT / "layouts" / "transfers" / "single.html"
    include = '{{ partial "promyachik-cucurella-align-price-labels-242.html" . }}'
    if single.exists():
        text = read(single)
        old = text
        text = text.replace(include, "")
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        if text != old:
            write(single, text, "remove old 242 JS include")

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in [
        "PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START",
        "promyachik-cucurella-label-243",
        "data-club=\"Barcelona",
        "€5",
        "€",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 500): idx + 1600].replace("\n", " ")[:1900]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ramos_before = sha(RAMOS_PAGE)
    cucurella_before = sha(CUCURELLA_PAGE)

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []
    restored_source = ""
    restored_score = 0

    try:
        restored_source, restored_score = restore_original_chart_if_needed()
        patch_cucurella_label_block()
        cleanup_style()
        remove_242_partial_include_if_present()

        hugo = run(["hugo", "-D"])

        dynamic_text = read(DYNAMIC_PARTIAL)
        style_text = read(STYLE)
        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""
        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_ramos_text = read(public_ramos) if public_ramos.exists() else ""

        fragments = collect_public_fragments()

        ramos_after = sha(RAMOS_PAGE)
        cucurella_after = sha(CUCURELLA_PAGE)

        checks = {
            "hugo_exit_code": hugo.returncode,
            "ramos_content_untouched": ramos_before == ramos_after,
            "cucurella_content_untouched": cucurella_before == cucurella_after,
            "restored_source": restored_source,
            "restored_score": restored_score,
            "dynamic_partial_has_243_cucurella_conditional": "PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START" in dynamic_text,
            "dynamic_partial_keeps_original_else_block": "__ORIGINAL_LABEL_BLOCK__" not in dynamic_text and "{{ else }}" in dynamic_text,
            "dynamic_partial_no_v239_v240": "pfb-value-chart-v239" not in dynamic_text and "pfb-value-chart-v240" not in dynamic_text,
            "style_has_243_css": CSS_START in style_text and CSS_END in style_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_cucurella_has_243_labels": "promyachik-cucurella-label-243" in public_text,
            "public_cucurella_has_no_242_js": "__promyachikCucurellaAlignPriceLabels242Ready" not in public_text,
            "public_cucurella_no_v239_v240": "pfb-value-chart-v239" not in public_text and "pfb-value-chart-v240" not in public_text,
            "public_ramos_has_no_243_marker": "promyachik-cucurella-label-243" not in public_ramos_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["dynamic_partial_has_243_cucurella_conditional"]
            and checks["dynamic_partial_no_v239_v240"]
            and checks["style_has_243_css"]
            and checks["public_cucurella_exists"]
            and checks["public_cucurella_has_243_labels"]
            and checks["public_cucurella_has_no_242_js"]
            and checks["public_cucurella_no_v239_v240"]
            and checks["public_ramos_has_no_243_marker"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 243 - CUCURELLA LABELS UNDER CLUB POINTS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Work target: Cucurella chart label row.")
    lines.append("- Do not touch Ramos content.")
    lines.append("- Do not touch Cucurella content data.")
    lines.append("- Do not redraw graph/line/dots/logos.")
    lines.append("- Only replace the bottom label range for Cucurella page.")
    lines.append("- For Cucurella labels: each label left uses the same point.left / point.x / point.x_percent coordinate as the club point.")
    lines.append("- Non-Cucurella pages keep the original label block through the else branch.")
    lines.append("")
    lines.append("EXPLAINED GEOMETRY")
    lines.append("- Barcelona point coordinate = point.left / point.x.")
    lines.append("- Barcelona label style = left: same coordinate; transform translateX(-50%).")
    lines.append("- Therefore Barcelona price/year sits vertically under the Barcelona point.")
    lines.append("- The same loop is used for all 5 Cucurella clubs, left to right.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("RESTORE")
    lines.append(f"- restored_source: {restored_source}")
    lines.append(f"- restored_score: {restored_score}")
    lines.append("")
    lines.append("CANDIDATES")
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
    lines.append("OBSERVED CUCURELLA PUBLIC FRAGMENTS")
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
    lines.append("NO RAMOS CONTENT CHANGE.")
    lines.append("NO CUCURELLA CONTENT CHANGE.")
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
