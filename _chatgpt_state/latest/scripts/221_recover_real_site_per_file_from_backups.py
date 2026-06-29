
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import sys

project = Path.cwd()
backup_before = project / "_backup_221_before_recover_real_site_per_file"
backup_before.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_221_recover_real_site_per_file_from_backups_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

BAD_TOKENS = [
    "cite",
    "\\n\\n",
    "\\nplayer_image",
    "Restored top transfer ticker",
    "Restored bottom transfer ticker",
    "218 restore top bottom transfer tickers",
    "216 restore stats icon visual size",
    "211 verified Ramos hardfix",
    "210 hard Ramos photo flag value fix",
    "209 final Ramos photo flag value fix",
    "208 ramos flag visibility",
    "207 real fix Ramos",
    "pfb-ramos-v211",
    "ramos-hardfix-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
    "portugal-proper",
]

PLACEHOLDER_TOKENS = [
    "Сайт запускается",
    "# ⚽",
    "скоро появятся",
]

ESSENTIAL_FILES = [
    "layouts/index.html",
    "layouts/_default/baseof.html",
    "layouts/_default/single.html",
    "layouts/partials/header.html",
    "layouts/partials/transfer-ticker.html",
    "layouts/transfers/single.html",
    "layouts/partials/transfer-player-stats.html",
    "layouts/partials/transfer-player-market-value-chart.html",
    "layouts/partials/profutbik-market-chart-static.html",
    "static/css/style.css",
    "static/header.css",
    "hugo.toml",
]

OPTIONAL_FILES = [
    "layouts/partials/footer.html",
    "layouts/partials/footer-transfer-ticker.html",
]

DELETE_IF_BAD = [
    "layouts/partials/ramos-hardfix-v211.html",
]

commands = []
restored = []
skipped = []
warnings = []
hugo_result = ""
candidate_summary = {}

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
        "stdout": p.stdout[-5000:],
        "stderr": p.stderr[-5000:],
    })
    return p

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def backup_current(path: Path):
    if path.exists():
        dst = backup_before / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            if path.is_dir():
                shutil.copytree(path, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(path, dst)

def write_file(path_rel: str, text: str, source: str, score: int):
    path = project / path_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_current(path)
    before = read(path) if path.exists() else None
    path.write_text(text, encoding="utf-8", newline="\n")
    after = read(path)
    changed = (before != after)
    restored.append((path_rel, source, score, changed))

def bad_text(text: str) -> bool:
    if text is None:
        return True
    return any(token in text for token in BAD_TOKENS)

def placeholder_text(text: str) -> bool:
    if text is None:
        return True
    return any(token in text for token in PLACEHOLDER_TOKENS)

def valid_md(text: str) -> bool:
    if not text or not text.startswith("---\n"):
        return False
    if "\n---\n" not in text[4:]:
        return False
    if bad_text(text):
        return False
    return True

def backup_number(name: str):
    m = re.match(r"_backup_(\d+)", name)
    if m:
        return int(m.group(1))
    return None

def backup_source_weight(name: str) -> int:
    n = backup_number(name)
    if n is None:
        return 0
    # User-approved / pre-disaster range. 146 is tested ticker, 184/203 stats, before 207 Ramos disaster.
    if 147 <= n <= 206:
        return 9000 + n
    if n == 146:
        return 8900
    if 120 <= n <= 145:
        return 7000 + n
    if 100 <= n <= 119:
        return 5000 + n
    # Broken or later backups are last resort only.
    if n >= 207:
        return -10000 - n
    return 1000 + n

def backup_dirs_sorted():
    dirs = [p for p in project.glob("_backup_*") if p.is_dir() and p.name != backup_before.name]
    return sorted(dirs, key=lambda p: backup_source_weight(p.name), reverse=True)

def git_revs():
    p = run(["git", "rev-list", "--all", "--max-count=250"])
    if p.returncode != 0:
        return []
    return [x.strip() for x in p.stdout.splitlines() if x.strip()]

def git_show(rev: str, path_rel: str):
    p = run(["git", "show", f"{rev}:{path_rel}"])
    if p.returncode == 0 and p.stdout:
        return p.stdout
    return None

def file_candidates(path_rel: str):
    out = []
    for root in backup_dirs_sorted():
        p = root / path_rel
        if p.exists() and p.is_file():
            try:
                out.append((f"backup:{root.name}", backup_source_weight(root.name), read(p)))
            except Exception as e:
                warnings.append(f"Could not read backup candidate {root.name}/{path_rel}: {e}")

    # Add git history candidates, but prefer backups in accepted numeric range.
    seen_revs = set()
    p = run(["git", "log", "--all", "--format=%H", "--", path_rel])
    if p.returncode == 0:
        for rev in p.stdout.splitlines():
            rev = rev.strip()
            if rev:
                seen_revs.add(rev)

    for rev in git_revs():
        seen_revs.add(rev)

    for rev in list(seen_revs)[:250]:
        text = git_show(rev, path_rel)
        if text:
            out.append((f"git:{rev[:12]}", 3000, text))
    return out

def common_score(path_rel: str, text: str, source_weight: int) -> int:
    if not text or not text.strip():
        return -1000000
    if bad_text(text):
        return -1000000

    s = source_weight + min(len(text) // 50, 300)

    # Penalize one-line flattened templates heavily.
    if path_rel.endswith(".html") and len(text.splitlines()) <= 2 and len(text) > 250:
        s -= 2500

    # Penalize placeholder homepage.
    if path_rel == "layouts/index.html" and placeholder_text(text):
        s -= 1000000

    return s

def score_candidate(path_rel: str, text: str, source_weight: int) -> int:
    s = common_score(path_rel, text, source_weight)
    if s < -999999:
        return s

    low = text.lower()

    if path_rel == "layouts/index.html":
        if "{{" in text and "}}" in text: s += 300
        if "regularpages" in low or ".site.regularpages" in low: s += 350
        if "transfer" in low or "трансфер" in low: s += 250
        if "player" in low or "игрок" in low or "mbapp" in low: s += 200
        if "<main" in low or "home" in low: s += 150
        if placeholder_text(text): s -= 1000000

    elif path_rel == "layouts/_default/baseof.html":
        if "<html" in low and "<body" in low: s += 500
        if 'partial "header.html"' in text or "partial \"header.html\"" in text: s += 300
        if "{{ block" in text: s += 300
        if "</body>" in low and "</html>" in low: s += 200

    elif path_rel == "layouts/_default/single.html":
        if ".Content" in text: s += 300
        if "partial" in text: s += 150
        if "<main" in low or "single" in low: s += 100

    elif path_rel == "layouts/partials/header.html":
        if "<header" in low or "site-header" in low: s += 400
        if "главная" in low and "трансферы" in low: s += 300
        if 'partial "transfer-ticker.html"' in text: s += 250
        if "profutbik" in low or "promyachik" in low: s += 200
        if "кнопка" in low and "трансферы" in low: s -= 500

    elif path_rel == "layouts/partials/transfer-ticker.html":
        if "transfer-ticker" in low: s += 300
        if ".site.data.transfers" in low or "site.data.transfers" in low: s += 450
        if "club-logos" in text: s += 400
        if "statuslabels" in low: s += 300
        if "from_club" in text and "to_club" in text: s += 250
        if "divider" in low or "раздел" in low or "seam" in low: s += 250
        if "range" in text: s += 150
        # Report 146 says real DOM divider + black ticker + no dot/photo frame; these are likely in accepted version.
        if "ticker-divider" in low or "real-divider" in low or "__divider" in low: s += 400
        if "photo" in low and "frame" in low and "removed" in low: s += 100
        # Reject my generated fake ticker.
        if "Restored top transfer ticker" in text or "Restored bottom transfer ticker" in text:
            s -= 1000000

    elif path_rel == "layouts/transfers/single.html":
        if "transfer-page" in text: s += 250
        if ".Content" in text: s += 250
        if 'transfer-player-stats.html' in text: s += 350
        if "market-value-chart" in low or "profutbik-market-chart-static.html" in text: s += 350
        if "ramos-hardfix" in low: s -= 1000000

    elif path_rel == "layouts/partials/transfer-player-stats.html":
        if "pfb-stats-v184" in text: s += 600
        if "stats-icons-v184" in text: s += 500
        if "previous_club_stats" in text and "pfb-stats-v184" not in text: s -= 1000000
        if "МАТЧА" in text and "ГОЛА" in text and "pfb-stats-v184" not in text: s -= 1000000

    elif path_rel in ["layouts/partials/transfer-player-market-value-chart.html", "layouts/partials/profutbik-market-chart-static.html"]:
        if "market_value_chart" in text or "value_number" in text: s += 400
        if "svg" in low or "chart" in low: s += 200

    elif path_rel == "static/css/style.css":
        if len(text) > 10000: s += 400
        if "transfer-ticker" in low: s += 500
        if "site-header" in low: s += 200
        if "pfb-stats-v184" in text: s += 200
        if "218 restore top bottom transfer tickers" in text or "216 restore stats icon visual size" in text: s -= 1000000

    elif path_rel == "static/header.css":
        if "header" in low or "site" in low: s += 200

    elif path_rel == "hugo.toml":
        if "baseurl" in low and "promyachik" in low: s += 400
        if "menu.main" in text: s += 150

    elif path_rel.endswith(".md"):
        if valid_md(text): s += 500
        else: s -= 1000000
        if "Gonçalo Ramos" in text and "AC Milan" in text: s += 200

    return s

def choose_best(path_rel: str, required: bool):
    candidates = file_candidates(path_rel)
    best = None
    top = []
    for source, weight, text in candidates:
        score = score_candidate(path_rel, text, weight)
        top.append((score, source, len(text)))
        if best is None or score > best[0]:
            best = (score, source, text)
    top.sort(reverse=True)
    candidate_summary[path_rel] = top[:8]

    if not best or best[0] < 0:
        if required:
            raise RuntimeError(f"No clean backup/git candidate for {path_rel}. Top={top[:5]}")
        skipped.append((path_rel, "no clean candidate"))
        return None
    return best

def restore_file(path_rel: str, required=True):
    best = choose_best(path_rel, required)
    if not best:
        return
    score, source, text = best
    write_file(path_rel, text, source, score)

def content_files_to_restore():
    paths = set()
    content = project / "content"
    if content.exists():
        for p in content.rglob("*.md"):
            try:
                txt = read(p)
                if (not valid_md(txt)) or bad_text(txt) or placeholder_text(txt):
                    paths.add(rel(p))
            except Exception:
                paths.add(rel(p))
    # Always verify Ramos specifically.
    paths.add("content/transfers/goncalo-ramos-ac-milan/index.md")
    return sorted(paths)

def restore_content_files():
    for path_rel in content_files_to_restore():
        try:
            restore_file(path_rel, required=False)
        except Exception as e:
            skipped.append((path_rel, f"content restore failed: {e}"))

def delete_bad_leftovers():
    for path_rel in DELETE_IF_BAD:
        p = project / path_rel
        if p.exists():
            backup_current(p)
            p.unlink()
            restored.append((path_rel, "deleted bad leftover", 0, True))
    # Remove fake bottom ticker only if it is from package 218 and no clean old version was found.
    p = project / "layouts/partials/footer-transfer-ticker.html"
    if p.exists():
        txt = read(p)
        if "Restored bottom transfer ticker" in txt or "218 restore" in txt:
            backup_current(p)
            p.unlink()
            restored.append(("layouts/partials/footer-transfer-ticker.html", "deleted fake 218 bottom ticker", 0, True))

def run_hugo():
    global hugo_result
    p = run(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-3000:]}\nSTDERR tail:\n{p.stderr[-3000:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero")

def verify():
    checks = {}
    ok = True

    for path_rel in [
        "layouts/index.html",
        "layouts/_default/baseof.html",
        "layouts/partials/header.html",
        "layouts/partials/transfer-ticker.html",
        "layouts/transfers/single.html",
        "layouts/partials/transfer-player-stats.html",
        "static/css/style.css",
    ]:
        p = project / path_rel
        text = read(p) if p.exists() else ""
        score = score_candidate(path_rel, text, 0)
        clean = p.exists() and score >= 0 and not bad_text(text)
        checks[path_rel] = {"exists": p.exists(), "clean": clean, "score": score, "length": len(text)}
        ok = ok and clean

    index_text = read(project / "layouts/index.html") if (project / "layouts/index.html").exists() else ""
    checks["home_layout_not_placeholder"] = not placeholder_text(index_text)
    ok = ok and checks["home_layout_not_placeholder"]

    ticker_text = read(project / "layouts/partials/transfer-ticker.html") if (project / "layouts/partials/transfer-ticker.html").exists() else ""
    checks["ticker_not_fake_218"] = "Restored top transfer ticker" not in ticker_text and "218 restore top bottom transfer tickers" not in ticker_text
    checks["ticker_has_template_logic"] = ("range" in ticker_text or "Site.Data" in ticker_text or ".Site" in ticker_text) and "transfer" in ticker_text.lower()
    ok = ok and checks["ticker_not_fake_218"] and checks["ticker_has_template_logic"]

    stats_text = read(project / "layouts/partials/transfer-player-stats.html") if (project / "layouts/partials/transfer-player-stats.html").exists() else ""
    checks["stats_accepted_v184"] = "pfb-stats-v184" in stats_text and "stats-icons-v184" in stats_text
    ok = ok and checks["stats_accepted_v184"]

    content_root = project / "content"
    md_files = list(content_root.rglob("*.md")) if content_root.exists() else []
    bad_md = []
    for p in md_files:
        txt = read(p)
        if not valid_md(txt) or bad_text(txt):
            bad_md.append(rel(p))
    checks["markdown_count"] = len(md_files)
    checks["bad_markdown_count"] = len(bad_md)
    checks["bad_markdown_files_sample"] = bad_md[:20]
    ok = ok and len(md_files) >= 4 and len(bad_md) == 0

    public_index = project / "public" / "index.html"
    public_index_text = read(public_index) if public_index.exists() else ""
    checks["public_home_exists"] = public_index.exists()
    checks["public_home_not_placeholder"] = "Сайт запускается" not in public_index_text
    checks["public_home_has_content"] = len(public_index_text) > 1000
    ok = ok and checks["public_home_exists"] and checks["public_home_not_placeholder"] and checks["public_home_has_content"]

    public_ramos = project / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
    checks["public_ramos_exists"] = public_ramos.exists()
    ok = ok and checks["public_ramos_exists"]

    return ok, checks

try:
    # Save current affected tree before touching anything.
    for path_rel in ["layouts", "content", "data", "static/css", "static/header.css", "hugo.toml"]:
        p = project / path_rel
        if p.exists():
            dst = backup_before / path_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if p.is_dir():
                if not dst.exists():
                    shutil.copytree(p, dst, dirs_exist_ok=True)
            else:
                if not dst.exists():
                    shutil.copy2(p, dst)

    # Restore per file from existing backups/git, not generated from scratch.
    for path_rel in ESSENTIAL_FILES:
        restore_file(path_rel, required=True)

    for path_rel in OPTIONAL_FILES:
        restore_file(path_rel, required=False)

    restore_content_files()
    delete_bad_leftovers()
    run_hugo()

    ok, checks = verify()

    changed_count = sum(1 for _, _, _, changed in restored if changed)
    if changed_count == 0:
        ok = False
        warnings.append("RESTORED_COUNT is 0: package made no effective changes.")

    lines = []
    lines.append("PROFUTBIK 221 - RECOVER REAL SITE PER FILE FROM BACKUPS")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No new ticker/home/player page was written from scratch.")
    lines.append("- Every restored file came from an existing _backup_* folder or git history.")
    lines.append("- Current broken state was backed up first.")
    lines.append("")
    lines.append("BACKUP OF BROKEN STATE")
    lines.append(f"- {backup_before}")
    lines.append("")
    lines.append("RESTORED")
    for path_rel, source, score, changed in restored:
        lines.append(f"- {path_rel} <= {source}, score={score}, changed={changed}")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    lines.append("SKIPPED")
    if skipped:
        for path_rel, reason in skipped:
            lines.append(f"- {path_rel}: {reason}")
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
    lines.append("TOP CANDIDATES")
    for path_rel, tops in candidate_summary.items():
        lines.append(f"- {path_rel}:")
        for score, source, length in tops:
            lines.append(f"  - score={score}; source={source}; len={length}")
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("COMMAND LOG")
    for c in commands[-60:]:
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
    lines = []
    lines.append("PROFUTBIK 221 - RECOVER REAL SITE PER FILE FROM BACKUPS")
    lines.append("=" * 90)
    lines.append("FAILED")
    lines.append(f"Error: {e}")
    lines.append("")
    lines.append("No new ticker/home/player page was written from scratch.")
    lines.append(f"Backup before attempted restore: {backup_before}")
    lines.append("")
    if candidate_summary:
        lines.append("TOP CANDIDATES")
        for path_rel, tops in candidate_summary.items():
            lines.append(f"- {path_rel}:")
            for score, source, length in tops:
                lines.append(f"  - score={score}; source={source}; len={length}")
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands[-60:]:
        lines.append("-" * 70)
        lines.append(f"COMMAND: {c['cmd']}")
        lines.append(f"EXIT_CODE: {c['returncode']}")
        if c["stdout"]:
            lines.append("--- STDOUT ---")
            lines.append(c["stdout"])
        if c["stderr"]:
            lines.append("--- STDERR ---")
            lines.append(c["stderr"])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8", errors="ignore"))
    sys.exit(1)
