
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_237_before_restore_working_value_chart_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_237_restore_working_value_chart_from_backup_report.txt"

TARGET_PARTIAL = PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html"
STYLE = PROJECT / "static" / "css" / "style.css"

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
]

BAD_INCLUDES = [
    '{{ partial "promyachik-align-value-labels-232.html" . }}',
    '{{ partial "promyachik-force-align-value-labels-233.html" . }}',
]

BAD_PARTIALS = [
    PROJECT / "layouts" / "partials" / "promyachik-align-value-labels-232.html",
    PROJECT / "layouts" / "partials" / "promyachik-force-align-value-labels-233.html",
]

BAD_CONTENT_TOKENS = [
    "PROMYACHIK 232",
    "PROMYACHIK 233",
    "PROMYACHIK 234",
    "PROMYACHIK 235",
    "PROMYACHIK 236",
    "__promyachikAlignValueLabels232Ready",
    "__promyachikForceAlignValueLabels233Ready",
    "pfb-market-chart-static--234",
    "pfb-market-chart-static--235",
    "pfb-market-chart-static--236",
    "pfb-market-chart-static__point-group",
    "transform=\"translate({{ printf \"%.2f\" $x }} 0)\"",
    "circle cx=\"0\"",
    "text x=\"0\"",
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

def score_candidate(path: Path, text: str) -> int:
    low_path = str(path).lower().replace("\\", "/")
    name = path.name.lower()

    if path.resolve() == TARGET_PARTIAL.resolve():
        return -100000

    if len(text) < 600:
        return -100000

    if "pfb-market-chart-static" not in text:
        return -100000

    if "market_value_chart" not in text and ".Params.market" not in text:
        return -100000

    if any(token in text for token in BAD_CONTENT_TOKENS):
        return -100000

    if "/public/" in low_path or "/resources/" in low_path or "/node_modules/" in low_path or "/.git/" in low_path:
        return -100000

    score = 0

    if name == "profutbik-market-chart-static.html":
        score += 1200

    if "profutbik-market-chart-static" in name:
        score += 900

    if "market-chart-static" in name:
        score += 700

    if "_backup_promyachik_234_before_rebuild_value_chart_labels" in low_path:
        score += 1600

    if "_backup_promyachik_233" in low_path or "_backup_promyachik_232" in low_path:
        score += 1000

    if "_backup_promyachik_230" in low_path or "_backup_promyachik_231" in low_path:
        score += 700

    if "_backup_promyachik_229" in low_path or "_backup_promyachik_228" in low_path or "_backup_promyachik_227" in low_path:
        score += 500

    if "restore_files" in low_path and ("234_" in low_path or "235_" in low_path or "236_" in low_path or "233_" in low_path or "232_" in low_path):
        score -= 2000

    # Working old chart usually has these data-driven fields and separate labels.
    for token, points in [
        ("$points", 180),
        ("value_label", 180),
        ("date_label", 180),
        ("value_number", 160),
        ("$path", 120),
        ("range $index", 120),
        ("circle", 80),
        ("image", 60),
        ("leftPad", 60),
        ("rightPad", 60),
        ("chartWidth", 60),
        ("chartHeight", 60),
    ]:
        if token in text:
            score += points

    # Avoid files that are not the old partial but contain the markup as report text.
    if path.suffix.lower() not in [".html", ".txt", ".bak"]:
        score -= 500

    if "report" in low_path:
        score -= 1200

    return score

def find_candidates():
    roots = [
        PROJECT,
        PROJECT / "backups",
        PROJECT / "_chatgpt_state",
        PROJECT / "payload",
    ]

    seen = set()
    candidates = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            pstr = str(path)
            if pstr in seen:
                continue
            seen.add(pstr)

            low = pstr.lower().replace("\\", "/")

            if any(skip in low for skip in ["/public/", "/resources/", "/node_modules/", "/.git/", "/static/images/", "/var/"]):
                continue

            if path.stat().st_size > 1_500_000:
                continue

            name = path.name.lower()

            if not (
                "profutbik-market-chart-static" in name
                or "market-chart-static" in name
                or "market" in name and "chart" in name and path.suffix.lower() in [".html", ".txt", ".bak"]
            ):
                continue

            try:
                text = read(path)
            except Exception:
                continue

            score = score_candidate(path, text)

            if score > 0:
                candidates.append((score, path, text))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates

def restore_working_partial():
    candidates = find_candidates()

    for score, path, text in candidates[:20]:
        candidate_log.append({
            "score": score,
            "path": str(path),
            "size": path.stat().st_size,
            "sha": sha(path),
            "has_value_label": "value_label" in text,
            "has_date_label": "date_label" in text,
            "has_bad_tokens": any(token in text for token in BAD_CONTENT_TOKENS),
        })

    if not candidates:
        raise RuntimeError("Не нашёл старый рабочий profutbik-market-chart-static.html в локальных backup-файлах.")

    score, source, text = candidates[0]

    if score < 900:
        raise RuntimeError(f"Лучший кандидат слишком слабый score={score}: {source}")

    copy_file(source, TARGET_PARTIAL, f"restore old working value chart partial from backup score={score}")

    return source, score

def cleanup_style():
    if not STYLE.exists():
        warnings.append(f"style.css not found: {STYLE}")
        return

    text = read(STYLE)
    original = text

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    if text != original:
        write(STYLE, text.rstrip() + "\n", "remove bad value-chart CSS attempts 230-236")

def cleanup_template_includes():
    for rel_path in [
        "layouts/_default/baseof.html",
        "layouts/transfers/single.html",
    ]:
        path = PROJECT / rel_path

        if not path.exists():
            continue

        text = read(path)
        original = text

        for include in BAD_INCLUDES:
            text = text.replace(include, "")

        text = re.sub(r"\n{4,}", "\n\n\n", text)

        if text != original:
            write(path, text, "remove bad value-label JS includes 232/233")

def cleanup_bad_partials():
    for path in BAD_PARTIALS:
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete bad value-label JS partial", True, "exists", "deleted"))

def collect_public_fragments():
    fragments = []
    public_transfers = PROJECT / "public" / "transfers"

    if not public_transfers.exists():
        return fragments

    tokens = ["€20 млн", "€23 млн", "€90 млн", "€100 млн", "€200 тыс.", "€15 млн", "€75 млн"]

    for page in list(public_transfers.glob("*/index.html"))[:40]:
        text = read(page)

        if "pfb-market-chart-static" not in text:
            continue

        for token in tokens:
            idx = text.find(token)
            if idx != -1:
                start = max(0, idx - 500)
                end = min(len(text), idx + 900)
                fragments.append((rel(page), token, text[start:end].replace("\n", " ")[:1400]))
                break

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
    chosen_source = ""
    chosen_score = 0
    hugo = None
    fragments = []
    checks = {}

    try:
        chosen_source, chosen_score = restore_working_partial()
        cleanup_style()
        cleanup_template_includes()
        cleanup_bad_partials()

        hugo = run(["hugo", "-D"])
        fragments = collect_public_fragments()

        partial_text = read(TARGET_PARTIAL)
        style_text = read(STYLE) if STYLE.exists() else ""
        baseof_text = read(PROJECT / "layouts" / "_default" / "baseof.html") if (PROJECT / "layouts" / "_default" / "baseof.html").exists() else ""
        transfer_single_text = read(PROJECT / "layouts" / "transfers" / "single.html") if (PROJECT / "layouts" / "transfers" / "single.html").exists() else ""

        public_transfer_pages = list((PROJECT / "public" / "transfers").glob("*/index.html")) if (PROJECT / "public" / "transfers").exists() else []

        public_sample = ""
        for page in public_transfer_pages[:10]:
            public_sample += read(page)[:10000]

        bad_markers = [
            "PROMYACHIK 230 CENTER MARKET VALUE",
            "PROMYACHIK 231 CENTER VALUE",
            "PROMYACHIK 232 ALIGN VALUE",
            "PROMYACHIK 233 FORCE ALIGN",
            "PROMYACHIK 234 VALUE CHART SVG",
            "PROMYACHIK 235 VERTICAL VALUE",
            "pfb-market-chart-static--234",
            "pfb-market-chart-static--235",
            "pfb-market-chart-static--236",
            "promyachik-align-value-labels-232",
            "promyachik-force-align-value-labels-233",
            "__promyachikForceAlignValueLabels233Ready",
            "__promyachikAlignValueLabels232Ready",
        ]

        checks = {
            "hugo_exit_code": hugo.returncode,
            "chosen_source": str(chosen_source),
            "chosen_score": chosen_score,
            "target_partial_exists": TARGET_PARTIAL.exists(),
            "target_partial_has_market_chart": "pfb-market-chart-static" in partial_text,
            "target_partial_has_value_label": "value_label" in partial_text,
            "target_partial_has_date_label": "date_label" in partial_text,
            "target_partial_no_234_235_236_markup": all(token not in partial_text for token in BAD_CONTENT_TOKENS),
            "bad_css_blocks_removed": all(marker not in style_text for marker in bad_markers),
            "bad_includes_removed_baseof": all(include not in baseof_text for include in BAD_INCLUDES),
            "bad_includes_removed_transfer_single": all(include not in transfer_single_text for include in BAD_INCLUDES),
            "bad_partials_deleted": all(not path.exists() for path in BAD_PARTIALS),
            "public_transfer_pages_found": len(public_transfer_pages),
            "public_has_market_chart": "pfb-market-chart-static" in public_sample,
            "public_bad_markers_absent": all(marker not in public_sample for marker in bad_markers),
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["target_partial_exists"]
            and checks["target_partial_has_market_chart"]
            and checks["target_partial_has_value_label"]
            and checks["target_partial_has_date_label"]
            and checks["target_partial_no_234_235_236_markup"]
            and checks["bad_css_blocks_removed"]
            and checks["bad_includes_removed_baseof"]
            and checks["bad_includes_removed_transfer_single"]
            and checks["bad_partials_deleted"]
            and checks["public_transfer_pages_found"] > 0
            and checks["public_has_market_chart"]
            and checks["public_bad_markers_absent"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 237 - RESTORE WORKING VALUE CHART FROM BACKUP")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No new chart design.")
    lines.append("- No homepage rewrite.")
    lines.append("- No ticker rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- Restores the old working chart partial from real local backups.")
    lines.append("- Removes bad attempts 230/231/232/233/234/235/236.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    if error_text:
        lines.append("ERROR")
        lines.append(error_text)
        lines.append("")
    lines.append("CHOSEN SOURCE")
    lines.append(f"- source: {chosen_source}")
    lines.append(f"- score: {chosen_score}")
    lines.append("")
    lines.append("TOP CANDIDATES")
    if candidate_log:
        for item in candidate_log[:20]:
            lines.append(
                f"- score={item['score']} | size={item['size']} | bad={item['has_bad_tokens']} | "
                f"value_label={item['has_value_label']} | date_label={item['has_date_label']} | {item['path']}"
            )
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
    lines.append("OBSERVED PUBLIC FRAGMENTS")
    if fragments:
        for page, token, fragment in fragments:
            lines.append(f"- {page} | token={token} | {fragment}")
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
