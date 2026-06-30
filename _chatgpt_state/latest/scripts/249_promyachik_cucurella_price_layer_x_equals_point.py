
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import re
import sys
import os
import json

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

BACKUPS_ROOT = Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS")
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
FULL_BACKUP_DIR = BACKUPS_ROOT / f"{timestamp}_FULL_BACKUP_BEFORE_249_CUCURELLA_PRICE_LAYER"

SAFETY_BACKUP = PROJECT / f"_backup_promyachik_249_before_cucurella_price_layer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
REPORT = PROJECT / "var" / "promyachik_249_cucurella_price_layer_x_equals_point_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE = PROJECT / "static" / "css" / "style.css"

RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

CSS_START = "/* PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT START */"
CSS_END = "/* PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT END */"

commands = []
changed = []
warnings = []
backup_errors = []

CSS_BLOCK = '''
/* PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT START */

/*
   Страница Marc Cucurella.
   Отдельный слой цен под графиком.
   Каждый label получает тот же X, что и его point.left / point.x / point.x_percent.
   Y у всех labels общий: один нижний ряд под графиком.
   График, линия, точки и логотипы не перерисовываются.
*/

.promyachik-cucurella-price-layer-249 {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    height: 62px !important;
    min-height: 62px !important;
    margin: 10px 0 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    pointer-events: none !important;
    box-sizing: border-box !important;
}

.promyachik-cucurella-price-label-249 {
    position: absolute !important;
    top: 0 !important;
    transform: translateX(-50%) !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    min-width: 72px !important;
    max-width: 120px !important;
    text-align: center !important;
    white-space: nowrap !important;
    line-height: 1.08 !important;
    z-index: 20 !important;
    box-sizing: border-box !important;
}

.promyachik-cucurella-price-label-249__date {
    display: block !important;
    width: 100% !important;
    margin: 0 0 5px !important;
    text-align: center !important;
}

.promyachik-cucurella-price-label-249__value {
    display: block !important;
    width: 100% !important;
    margin: 0 !important;
    text-align: center !important;
}

/* PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT END */
'''

NEW_LABEL_BLOCK = r'''{{ if in $.RelPermalink "/transfers/marc-cucurella-real-madrid/" }}
<!-- PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT START -->
{{ $promyachikCucPointCount249 := len $chart.points }}
{{ $promyachikCucDenom249 := sub $promyachikCucPointCount249 1 }}
{{ if lt $promyachikCucDenom249 1 }}
    {{ $promyachikCucDenom249 = 1 }}
{{ end }}

<div class="promyachik-cucurella-price-layer-249" aria-label="Стоимость игрока под точками клубов">
    {{ range $promyachikCucIndex249, $promyachikCucPoint249 := $chart.points }}
        {{ $promyachikCucComputedLeft249 := add 10.0 (mul (div (float $promyachikCucIndex249) (float $promyachikCucDenom249)) 80.0) }}
        {{ $promyachikCucLeft249 := $promyachikCucComputedLeft249 }}

        {{ with $promyachikCucPoint249.left }}
            {{ $promyachikCucLeft249 = . }}
        {{ end }}

        {{ with $promyachikCucPoint249.x }}
            {{ $promyachikCucLeft249 = . }}
        {{ end }}

        {{ with $promyachikCucPoint249.x_percent }}
            {{ $promyachikCucLeft249 = . }}
        {{ end }}

        {{ $promyachikCucLeftText249 := printf "%v" $promyachikCucLeft249 }}

        <div
            class="promyachik-cucurella-price-label-249"
            style="left: {{ $promyachikCucLeftText249 }}{{ if not (in $promyachikCucLeftText249 "%") }}%{{ end }};"
            data-point-index="{{ $promyachikCucIndex249 }}"
            data-point-club="{{ default "" $promyachikCucPoint249.club }}"
            data-point-left="{{ $promyachikCucLeftText249 }}"
        >
            <span class="promyachik-cucurella-price-label-249__date">
                {{ default $promyachikCucPoint249.date $promyachikCucPoint249.date_label }}
            </span>
            <strong class="promyachik-cucurella-price-label-249__value">
                {{ $promyachikCucPoint249.value_label }}
            </strong>
        </div>
    {{ end }}
</div>
<!-- PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT END -->
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

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup_current(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def backup_current(path: Path):
    if path.exists():
        dst = SAFETY_BACKUP / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def run_cmd(cmd):
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

def ignore_backup(src, names):
    ignored = []
    for name in names:
        if name == "Promyachik_BACKUPS":
            ignored.append(name)
    return set(ignored)

def count_tree(path: Path):
    files = 0
    dirs = 0
    size = 0
    for root, dirnames, filenames in os.walk(path):
        dirs += len(dirnames)
        for fn in filenames:
            p = Path(root) / fn
            try:
                files += 1
                size += p.stat().st_size
            except OSError:
                pass
    return files, dirs, size

def create_full_backup_before_change():
    BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
    if FULL_BACKUP_DIR.exists():
        raise RuntimeError(f"Full backup folder already exists: {FULL_BACKUP_DIR}")

    try:
        shutil.copytree(PROJECT, FULL_BACKUP_DIR, ignore=ignore_backup, dirs_exist_ok=False)
    except Exception as e:
        backup_errors.append(str(e))
        raise

    files, dirs, size = count_tree(FULL_BACKUP_DIR)
    manifest = {
        "backup_kind": "FULL_BACKUP_BEFORE_249_CUCURELLA_PRICE_LAYER",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_project": str(PROJECT),
        "backup_dir": str(FULL_BACKUP_DIR),
        "files": files,
        "dirs": dirs,
        "bytes": size,
    }
    (FULL_BACKUP_DIR / "PROMYACHIK_BACKUP_249_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return files, dirs, size

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

def find_bottom_price_range_block(text: str):
    starts = []
    range_re = re.compile(r"{{-?\s*range\b[^}]*\$chart\.points[^}]*-?}}", re.S)

    for m in range_re.finditer(text):
        end = find_matching_end(text, m.end())
        if end == -1:
            continue
        block = text[m.start():end]

        score = 0
        if "value_label" in block:
            score += 100
        if ".date" in block or "date_label" in block:
            score += 80
        if "club_logo" in block:
            score -= 80
        if "area_path" in block:
            score -= 80

        if score >= 100:
            starts.append((score, m.start(), end, block))

    if not starts:
        raise RuntimeError("Не найден нижний блок цен: range $chart.points с .date/.value_label.")

    starts.sort(key=lambda x: (x[0], x[1]), reverse=True)
    _, start, end, block = starts[0]
    return start, end, block

def patch_dynamic_partial():
    if not DYNAMIC_PARTIAL.exists():
        raise RuntimeError(f"Не найден файл: {DYNAMIC_PARTIAL}")

    text = read(DYNAMIC_PARTIAL)

    if "PROMYACHIK 249 CUCURELLA PRICE LAYER X EQUALS POINT START" in text:
        warnings.append("249 already present in dynamic partial; leaving existing block")
        return

    start, end, original_block = find_bottom_price_range_block(text)

    replacement = NEW_LABEL_BLOCK.replace("__ORIGINAL_LABEL_BLOCK__", original_block)

    text = text[:start] + replacement + text[end:]
    write(DYNAMIC_PARTIAL, text, "replace Cucurella bottom prices with separate layer; each price X equals point X")

def patch_style():
    if not STYLE.exists():
        raise RuntimeError(f"Не найден CSS: {STYLE}")

    text = read(STYLE)
    text = strip_block(text, CSS_START, CSS_END)
    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "add CSS for Cucurella separate price layer")

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
    if not public_path.exists():
        return fragments

    text = read(public_path)
    for token in [
        "promyachik-cucurella-price-layer-249",
        "promyachik-cucurella-price-label-249",
        "data-point-left",
        "PROMYACHIK 249 CUCURELLA PRICE LAYER",
        "€",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 500):idx + 1600].replace("\n", " ")[:2100]))
    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    SAFETY_BACKUP.mkdir(parents=True, exist_ok=True)

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
    full_backup_stats = (0, 0, 0)

    try:
        full_backup_stats = create_full_backup_before_change()

        patch_dynamic_partial()
        patch_style()

        hugo = run_cmd(["hugo", "-D"])

        partial_text = read(DYNAMIC_PARTIAL)
        style_text = read(STYLE)
        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""
        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_ramos_text = read(public_ramos) if public_ramos.exists() else ""

        ramos_after = sha(RAMOS_PAGE)
        cucurella_after = sha(CUCURELLA_PAGE)

        fragments = collect_public_fragments()

        checks = {
            "hugo_exit_code": hugo.returncode,
            "full_backup_before_change_exists": FULL_BACKUP_DIR.exists(),
            "full_backup_files": full_backup_stats[0],
            "full_backup_dirs": full_backup_stats[1],
            "full_backup_bytes": full_backup_stats[2],
            "ramos_content_untouched": ramos_before == ramos_after,
            "cucurella_content_untouched": cucurella_before == cucurella_after,
            "partial_has_249_layer": "promyachik-cucurella-price-layer-249" in partial_text,
            "partial_has_original_else_for_other_pages": "{{ else }}" in partial_text and "__ORIGINAL_LABEL_BLOCK__" not in partial_text,
            "style_has_249_css": CSS_START in style_text and CSS_END in style_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_cucurella_has_249_layer": "promyachik-cucurella-price-layer-249" in public_text,
            "public_cucurella_has_price_labels": "promyachik-cucurella-price-label-249" in public_text,
            "public_ramos_has_no_249_layer": "promyachik-cucurella-price-layer-249" not in public_ramos_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["full_backup_before_change_exists"]
            and checks["full_backup_files"] > 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["partial_has_249_layer"]
            and checks["style_has_249_css"]
            and checks["public_cucurella_exists"]
            and checks["public_cucurella_has_249_layer"]
            and checks["public_cucurella_has_price_labels"]
            and checks["public_ramos_has_no_249_layer"]
        )

    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 249 - CUCURELLA PRICE LAYER X EQUALS POINT")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Create a separate price layer under the chart.")
    lines.append("- Each price gets its own block.")
    lines.append("- Each price block left/X equals the corresponding chart point left/x/x_percent.")
    lines.append("- Y is common for all prices: one bottom row under the chart.")
    lines.append("- Only Cucurella page receives the new layer.")
    lines.append("- Other pages keep the original label block through the else branch.")
    lines.append("- Ramos content is not touched.")
    lines.append("- Cucurella content is not touched.")
    lines.append("- No push.")
    lines.append("- No site opened.")
    lines.append("")
    lines.append("FULL BACKUP BEFORE CHANGE")
    lines.append(f"- folder: {FULL_BACKUP_DIR}")
    lines.append(f"- files: {full_backup_stats[0]}")
    lines.append(f"- dirs: {full_backup_stats[1]}")
    lines.append(f"- bytes: {full_backup_stats[2]}")
    lines.append("")
    lines.append("SAFETY BACKUP OF CHANGED FILES")
    lines.append(f"- folder: {SAFETY_BACKUP}")
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
    if backup_errors:
        lines.append("BACKUP ERRORS")
        for err in backup_errors:
            lines.append(f"- {err}")
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
    lines.append("NO PUSH MADE.")
    lines.append("NO SITE OPENED.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
