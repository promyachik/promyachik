
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import sys

project = Path.cwd()
backup_before = project / "_backup_217_before_restore_site_blocks_from_real_backup"
backup_before.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_217_restore_site_blocks_from_real_backup_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

commands = []
warnings = []
restored = []
skipped = []
hugo_result = ""

BAD_TOKENS = [
    "\\n\\n",
    "\\nplayer_image",
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
    "207 real fix Ramos",
    "cite",
]

CRITICAL_FILES = [
    "layouts/partials/header.html",
    "layouts/partials/transfer-ticker.html",
    "layouts/partials/transfer-player-stats.html",
    "layouts/partials/transfer-player-market-value-chart.html",
    "layouts/partials/profutbik-market-chart-static.html",
    "layouts/transfers/single.html",
    "layouts/_default/single.html",
    "layouts/_default/baseof.html",
    "static/css/style.css",
]

DELETE_FILES = [
    "layouts/partials/ramos-hardfix-v211.html",
]

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project)).replace("\\", "/")
    except Exception:
        return str(p)

def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False
    )
    commands.append({
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    })
    return p

def read_file(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_file(p: Path, text: str, source: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        dst = backup_before / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)
    p.write_text(text, encoding="utf-8", newline="\n")
    restored.append((rel(p), source))

def copy_file(src: Path, dst: Path, source_label: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        b = backup_before / rel(dst)
        b.parent.mkdir(parents=True, exist_ok=True)
        if not b.exists():
            shutil.copy2(dst, b)
    shutil.copy2(src, dst)
    restored.append((rel(dst), source_label))

def is_bad(text: str) -> bool:
    return any(t in text for t in BAD_TOKENS)

def has_real_html(text: str) -> bool:
    return "<" in text and ">" in text and "cite" not in text

def clean_bad_refs(text: str) -> str:
    text = text.replace('{{ partial "ramos-hardfix-v211.html" . }}', "")
    text = text.replace("{{ partial \"ramos-hardfix-v211.html\" . }}", "")
    text = re.sub(r'<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*', "", text, flags=re.I | re.S)
    text = re.sub(r'<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*', "", text, flags=re.I | re.S)
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

def backup_candidates(path_rel: str):
    out = []
    # Prefer older package backups before the broken 207-216 series, then all backups.
    backups = [p for p in project.glob("_backup_*") if p.is_dir()]
    def key(p):
        name = p.name.lower()
        penalty = 0
        for n in ["_backup_217", "_backup_216", "_backup_215", "_backup_214", "_backup_213", "_backup_212", "_backup_211", "_backup_210", "_backup_209", "_backup_208", "_backup_207"]:
            if n in name:
                penalty += 1000
        return (penalty, name)
    for root in sorted(backups, key=key):
        p = root / path_rel
        if p.exists() and p.is_file():
            try:
                out.append((f"backup:{root.name}", read_file(p)))
            except Exception as e:
                warnings.append(f"Could not read backup candidate {root.name}/{path_rel}: {e}")
    return out

def git_candidates(path_rel: str):
    out = []
    # commits that touched file, plus simple HEAD~N fallback
    hashes = []
    p = run(["git", "log", "--all", "--format=%H", "--", path_rel])
    if p.returncode == 0:
        for h in p.stdout.splitlines():
            h = h.strip()
            if h and h not in hashes:
                hashes.append(h)
    for i in range(0, 80):
        rev = "HEAD" if i == 0 else f"HEAD~{i}"
        if rev not in hashes:
            hashes.append(rev)
    for rev in hashes:
        show = run(["git", "show", f"{rev}:{path_rel}"])
        if show.returncode == 0 and show.stdout:
            out.append((f"git:{rev}", show.stdout))
    return out

def score_file(path_rel: str, text: str) -> int:
    s = 0
    low = text.lower()
    if is_bad(text):
        s -= 10000
    if path_rel.endswith(".html"):
        if has_real_html(text):
            s += 100
        if "{{" in text and "}}" in text:
            s += 30
    if path_rel == "layouts/partials/header.html":
        if "transfer-ticker.html" in text:
            s += 80
        if "<header" in low or "site-header" in low or "main-nav" in low:
            s += 100
    elif path_rel == "layouts/partials/transfer-ticker.html":
        if "transfer-ticker" in low or "ticker" in low:
            s += 120
        if "range" in text and ".Site.Data.transfers" in text:
            s += 80
        if "ТРАНСФЕРЫ" in text:
            s += 40
    elif path_rel == "layouts/partials/transfer-player-stats.html":
        if "pfb-stats-v184" in text:
            s += 200
        if "stats-icons-v184" in text:
            s += 100
        if "previous_club_stats" in text and "pfb-stats-v184" not in text:
            s -= 400
        if "МАТЧА" in text and "ГОЛА" in text and "pfb-stats-v184" not in text:
            s -= 500
    elif path_rel == "layouts/transfers/single.html":
        if "transfer-player-stats.html" in text:
            s += 120
        if "market-value-chart" in low or "profutbik-market-chart-static.html" in text:
            s += 120
        if ".Content" in text:
            s += 50
        if "ramos-hardfix" in text:
            s -= 1000
    elif "market-value-chart" in path_rel:
        if "market_value_chart" in text or "value_number" in text:
            s += 160
    elif path_rel.endswith(".css"):
        if "transfer-ticker" in low:
            s += 60
        if "pfb-stats-v184" in text:
            s += 80
    return s

def choose_clean_file(path_rel: str):
    candidates = []
    candidates.extend(backup_candidates(path_rel))
    candidates.extend(git_candidates(path_rel))
    current = project / path_rel
    if current.exists():
        candidates.append(("current-cleaned", clean_bad_refs(read_file(current))))
    best = None
    for source, text in candidates:
        text = clean_bad_refs(text)
        score = score_file(path_rel, text)
        if best is None or score > best[0]:
            best = (score, source, text)
    return best

def restore_critical_file(path_rel: str, min_score: int):
    best = choose_clean_file(path_rel)
    if not best:
        skipped.append((path_rel, "no candidates"))
        return
    score, source, text = best
    if score < min_score:
        skipped.append((path_rel, f"best score too low: {score} from {source}"))
        return
    write_file(project / path_rel, text, f"{source}, score={score}")

def valid_markdown_front_matter(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    if "\\n" in text[:end+5]:
        return False
    if "cite" in text:
        return False
    return True

def score_md(path_rel: str, text: str) -> int:
    s = 0
    if valid_markdown_front_matter(text):
        s += 1000
    else:
        s -= 1000
    if "market_value" in text:
        s += 40
    if "previous_club_stats" in text or "market_value_chart" in text:
        s += 80
    if is_bad(text):
        s -= 10000
    if "\\nplayer_image" in text:
        s -= 10000
    return s

def choose_clean_md(path_rel: str):
    candidates = []
    candidates.extend(backup_candidates(path_rel))
    candidates.extend(git_candidates(path_rel))
    best = None
    for source, text in candidates:
        text = clean_bad_refs(text)
        score = score_md(path_rel, text)
        if best is None or score > best[0]:
            best = (score, source, text)
    return best

def restore_broken_transfer_pages():
    content_root = project / "content" / "transfers"
    if not content_root.exists():
        warnings.append("content/transfers does not exist")
        return
    for md in content_root.rglob("*.md"):
        path_rel = rel(md)
        try:
            cur = read_file(md)
        except Exception:
            continue
        broken = not valid_markdown_front_matter(cur) or "\\nplayer_image" in cur or is_bad(cur)
        if not broken:
            continue
        best = choose_clean_md(path_rel)
        if best and best[0] >= 900:
            score, source, text = best
            write_file(md, text, f"{source}, score={score}")
        else:
            skipped.append((path_rel, "broken markdown but no clean backup/git candidate"))

def remove_broken_files():
    for path_rel in DELETE_FILES:
        p = project / path_rel
        if p.exists():
            dst = backup_before / path_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(p, dst)
            p.unlink()
            restored.append((path_rel, "deleted broken hardfix file"))

def run_hugo():
    global hugo_result
    p = run(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-2500:]}\nSTDERR tail:\n{p.stderr[-2500:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero")

def verify():
    checks = {}
    for path_rel in [
        "layouts/partials/header.html",
        "layouts/partials/transfer-ticker.html",
        "layouts/partials/transfer-player-stats.html",
        "layouts/transfers/single.html",
    ]:
        p = project / path_rel
        txt = read_file(p) if p.exists() else ""
        checks[path_rel] = {
            "exists": p.exists(),
            "no_bad_tokens": not is_bad(txt),
            "length": len(txt),
        }
    stats = read_file(project / "layouts/partials/transfer-player-stats.html") if (project/"layouts/partials/transfer-player-stats.html").exists() else ""
    checks["stats_has_accepted_block"] = "pfb-stats-v184" in stats and "stats-icons-v184" in stats
    checks["stats_not_text_previous_only"] = not ("previous_club_stats" in stats and "pfb-stats-v184" not in stats)
    ticker = read_file(project / "layouts/partials/transfer-ticker.html") if (project/"layouts/partials/transfer-ticker.html").exists() else ""
    checks["ticker_no_literal_newline"] = "\\n\\n" not in ticker
    header = read_file(project / "layouts/partials/header.html") if (project/"layouts/partials/header.html").exists() else ""
    checks["header_no_literal_newline"] = "\\n\\n" not in header
    checks["broken_hardfix_deleted"] = not (project/"layouts/partials/ramos-hardfix-v211.html").exists()

    bad_md = []
    content_root = project / "content" / "transfers"
    if content_root.exists():
        for md in content_root.rglob("*.md"):
            try:
                txt = read_file(md)
                if not valid_markdown_front_matter(txt) or "\\nplayer_image" in txt or is_bad(txt):
                    bad_md.append(rel(md))
            except Exception:
                bad_md.append(rel(md))
    checks["bad_transfer_markdown_files"] = bad_md[:50]
    checks["bad_transfer_markdown_count"] = len(bad_md)

    ok = (
        checks["stats_has_accepted_block"]
        and checks["stats_not_text_previous_only"]
        and checks["ticker_no_literal_newline"]
        and checks["header_no_literal_newline"]
        and checks["broken_hardfix_deleted"]
        and checks["bad_transfer_markdown_count"] == 0
        and all(checks[p]["exists"] and checks[p]["no_bad_tokens"] for p in [
            "layouts/partials/header.html",
            "layouts/partials/transfer-ticker.html",
            "layouts/partials/transfer-player-stats.html",
            "layouts/transfers/single.html",
        ])
    )
    return ok, checks

try:
    # Save current state of important folders before restore.
    for folder in ["layouts", "content/transfers", "static/css"]:
        src = project / folder
        if src.exists():
            dst = backup_before / folder
            if not dst.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    remove_broken_files()

    # Restore critical templates/partials/css from real backups/git history.
    restore_critical_file("layouts/partials/header.html", 100)
    restore_critical_file("layouts/partials/transfer-ticker.html", 100)
    restore_critical_file("layouts/partials/transfer-player-stats.html", 200)
    restore_critical_file("layouts/partials/transfer-player-market-value-chart.html", 80)
    restore_critical_file("layouts/partials/profutbik-market-chart-static.html", 80)
    restore_critical_file("layouts/transfers/single.html", 100)
    restore_critical_file("layouts/_default/single.html", 50)
    restore_critical_file("layouts/_default/baseof.html", 50)
    restore_critical_file("static/css/style.css", 40)

    # Restore every broken transfer page only if a clean version exists.
    restore_broken_transfer_pages()

    run_hugo()

    ok, checks = verify()

    lines = []
    lines.append("PROFUTBIK 217 - RESTORE SITE BLOCKS FROM REAL BACKUP")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    lines.append("BACKUP OF CURRENT BROKEN STATE")
    lines.append(f"- {backup_before}")
    lines.append("")
    lines.append("RESTORED / CHANGED")
    if restored:
        for path_rel, source in restored:
            lines.append(f"- {path_rel} <= {source}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("SKIPPED")
    if skipped:
        for item in skipped:
            lines.append(f"- {item[0]}: {item[1]}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("VERIFY")
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    lines.append("HUGO RESULT")
    lines.append(hugo_result)
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("COMMAND LOG")
    for c in commands[-30:]:
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

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

except Exception as e:
    report_path.write_text(f"PROFUTBIK 217 FAILED\nError: {e}\n", encoding="utf-8")
    print(report_path.read_text(encoding="utf-8", errors="ignore"))
    sys.exit(1)
