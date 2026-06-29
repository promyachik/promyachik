
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import sys
import re

project = Path.cwd()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = project / f"_backup_222_before_hard_restore_{timestamp}"
report_path = project / "var" / "profutbik_222_hard_restore_last_good_commit_before_ramos_photo_damage_report.txt"

CRITICAL = [
    "layouts/index.html",
    "layouts/_default/baseof.html",
    "layouts/partials/header.html",
    "layouts/partials/transfer-ticker.html",
    "layouts/transfers/single.html",
    "layouts/partials/transfer-player-stats.html",
    "static/css/style.css",
]

OPTIONAL = [
    "layouts/_default/single.html",
    "layouts/partials/transfer-player-market-value-chart.html",
    "layouts/partials/profutbik-market-chart-static.html",
    "hugo.toml",
    "content/transfers/goncalo-ramos-ac-milan/index.md",
]

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

RAMOS_BAD = [
    "player_image_source_name: Transfermarkt",
    "goncalo-ramos-550550",
    "needs_cutout: false",
    "cutout_player_image: /images/players/api/41585.png",
    "--- title:",
]

PLACEHOLDER = ["Сайт запускается", "# ⚽ Promyachik"]

commands = []
warnings = []
candidate_rows = []
hugo_result = ""

def run(cmd, check=False):
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
        "stdout": p.stdout[-6000:],
        "stderr": p.stderr[-6000:],
    })
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p

def git_show(commit, path):
    p = run(["git", "show", f"{commit}:{path}"])
    if p.returncode == 0:
        return p.stdout
    return None

def has_bad(text):
    if text is None:
        return True
    return any(x in text for x in BAD_TOKENS)

def has_placeholder(text):
    if text is None:
        return True
    return any(x in text for x in PLACEHOLDER)

def valid_md(text):
    return bool(text and text.startswith("---\n") and "\n---\n" in text[4:] and not has_bad(text))

def file_score(path, text):
    if text is None or not text.strip():
        return -100000
    if has_bad(text):
        return -100000
    if path.endswith(".html") and len(text.splitlines()) <= 2 and len(text) > 220:
        return -100000

    low = text.lower()
    s = min(len(text) // 80, 300)

    if path == "layouts/index.html":
        if has_placeholder(text):
            return -100000
        if "{{" in text and "}}" in text:
            s += 150
        if ".site.regularpages" in low or "regularpages" in low:
            s += 250
        if "transfer" in low or "трансфер" in low:
            s += 150
        if "player" in low or "игрок" in low or "mbapp" in low:
            s += 120
        if "<main" in low or "home" in low:
            s += 80

    elif path == "layouts/_default/baseof.html":
        if "<html" in low and "<body" in low:
            s += 300
        if 'partial "header.html"' in text:
            s += 250
        if "{{ block" in text:
            s += 250
        if "</body>" in low and "</html>" in low:
            s += 120

    elif path == "layouts/partials/header.html":
        if "<header" in low or "site-header" in low:
            s += 250
        if "главная" in low and "трансферы" in low:
            s += 200
        if 'partial "transfer-ticker.html"' in text:
            s += 200
        if "profutbik" in low or "promyachik" in low:
            s += 100

    elif path == "layouts/partials/transfer-ticker.html":
        if "transfer-ticker" in low:
            s += 250
        if ".Site.Data.transfers" in text or "site.data.transfers" in low:
            s += 350
        if "club-logos" in text:
            s += 300
        if "statusLabels" in text or "statuslabels" in low:
            s += 220
        if "from_club" in text and "to_club" in text:
            s += 180
        if "divider" in low or "seam" in low:
            s += 350
        if "range" in text:
            s += 130
        if "span" in low and "divider" in low:
            s += 250

    elif path == "layouts/transfers/single.html":
        if "transfer-page" in text:
            s += 180
        if ".Content" in text:
            s += 220
        if 'transfer-player-stats.html' in text:
            s += 250
        if "market-value-chart" in low or "profutbik-market-chart-static.html" in text:
            s += 250
        if "ramos-hardfix" in low:
            return -100000

    elif path == "layouts/partials/transfer-player-stats.html":
        if "pfb-stats-v184" in text:
            s += 500
        if "stats-icons-v184" in text:
            s += 420
        if "previous_club_stats" in text and "pfb-stats-v184" not in text:
            return -100000
        if "МАТЧА" in text and "ГОЛА" in text and "pfb-stats-v184" not in text:
            return -100000

    elif path == "static/css/style.css":
        if len(text) > 8000:
            s += 250
        if "transfer-ticker" in low:
            s += 350
        if "site-header" in low or "header" in low:
            s += 150
        if "pfb-stats-v184" in text:
            s += 150
        if "216 restore" in text or "218 restore" in text:
            return -100000

    return s

def score_commit(commit):
    total = 0
    details = []
    for path in CRITICAL:
        text = git_show(commit, path)
        sc = file_score(path, text)
        details.append((path, sc))
        if sc < 0:
            return -1000000, details
        total += sc

    # Content count: avoid commits before the site pages existed.
    tree = run(["git", "ls-tree", "-r", "--name-only", commit, "content"])
    md_count = 0
    if tree.returncode == 0:
        md_count = len([x for x in tree.stdout.splitlines() if x.endswith(".md")])
    if md_count >= 4:
        total += min(md_count * 15, 300)
    else:
        total -= 400
    details.append(("content_md_count", md_count))

    # Ramos page is optional, but if it exists and is already bad, reject this commit.
    ramos = git_show(commit, "content/transfers/goncalo-ramos-ac-milan/index.md")
    if ramos is not None:
        if any(x in ramos for x in RAMOS_BAD) or has_bad(ramos) or not valid_md(ramos):
            return -1000000, details + [("ramos_status", -100000)]
        total += 180
        details.append(("ramos_valid", 180))
    else:
        details.append(("ramos_missing_ok", 0))

    # Prefer commits with accepted ticker report present, but do not require it.
    rep = git_show(commit, "_chatgpt_state/latest/_latest_reports/_146_full_upper_ticker_real_seam_divider_report_20260628_000952.txt")
    if rep and "SELF CHECK: OK" in rep:
        total += 500
        details.append(("report_146_self_check", 500))

    msg = run(["git", "log", "-1", "--format=%s", commit]).stdout.strip()
    if re.search(r"ramos|transfermarkt|black|cutout|v211|v210|v209|v208|v207", msg, re.I):
        total -= 800
        details.append(("message_penalty", -800))

    return total, details

def backup_current_state():
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in ["layouts", "content", "data", "static/css", "static/header.css", "hugo.toml"]:
        p = project / path
        if p.exists():
            dst = backup_dir / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if p.is_dir():
                if not dst.exists():
                    shutil.copytree(p, dst, dirs_exist_ok=True)
            else:
                if not dst.exists():
                    shutil.copy2(p, dst)

def write_report(ok, selected, verify_checks, extra_error=None):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("PROFUTBIK 222 - HARD RESTORE LAST GOOD COMMIT BEFORE RAMOS PHOTO DAMAGE")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No new ticker/home/player page was written from scratch.")
    lines.append("- This package selects a real old git commit and hard-resets local repo to it.")
    lines.append("- It does not push.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- Broken state copied to: {backup_dir}")
    lines.append("")
    if selected:
        lines.append("SELECTED COMMIT")
        lines.append(f"- commit: {selected['commit']}")
        lines.append(f"- score: {selected['score']}")
        lines.append(f"- message: {selected['message']}")
        lines.append("- detail scores:")
        for k, v in selected["details"]:
            lines.append(f"  - {k}: {v}")
        lines.append("")
    if extra_error:
        lines.append("ERROR")
        lines.append(str(extra_error))
        lines.append("")
    lines.append("TOP CANDIDATES")
    for row in candidate_rows[:15]:
        lines.append(f"- score={row['score']} commit={row['commit'][:12]} message={row['message']}")
    lines.append("")
    lines.append("VERIFY")
    for k, v in verify_checks.items():
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
    for c in commands[-80:]:
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

def run_hugo():
    global hugo_result
    p = run(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-3000:]}\nSTDERR tail:\n{p.stderr[-3000:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero")

def verify_after():
    checks = {}
    ok = True

    for path in CRITICAL:
        p = project / path
        text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
        sc = file_score(path, text)
        clean = p.exists() and sc >= 0 and not has_bad(text)
        checks[path] = {"exists": p.exists(), "score": sc, "clean": clean, "length": len(text)}
        ok = ok and clean

    home = project / "layouts" / "index.html"
    home_text = home.read_text(encoding="utf-8", errors="ignore") if home.exists() else ""
    checks["home_not_placeholder"] = not has_placeholder(home_text)
    ok = ok and checks["home_not_placeholder"]

    content = project / "content"
    md_count = len(list(content.rglob("*.md"))) if content.exists() else 0
    checks["content_md_count"] = md_count
    ok = ok and md_count >= 4

    ticker = project / "layouts" / "partials" / "transfer-ticker.html"
    ticker_text = ticker.read_text(encoding="utf-8", errors="ignore") if ticker.exists() else ""
    checks["ticker_not_generated_218"] = "Restored top transfer ticker" not in ticker_text and "218 restore" not in ticker_text
    checks["ticker_has_real_logic"] = ("divider" in ticker_text.lower() or "site.data.transfers" in ticker_text.lower() or "club-logos" in ticker_text)
    ok = ok and checks["ticker_not_generated_218"] and checks["ticker_has_real_logic"]

    stats = project / "layouts" / "partials" / "transfer-player-stats.html"
    stats_text = stats.read_text(encoding="utf-8", errors="ignore") if stats.exists() else ""
    checks["stats_v184_ok"] = "pfb-stats-v184" in stats_text and "stats-icons-v184" in stats_text
    ok = ok and checks["stats_v184_ok"]

    public_home = project / "public" / "index.html"
    public_home_text = public_home.read_text(encoding="utf-8", errors="ignore") if public_home.exists() else ""
    checks["public_home_exists"] = public_home.exists()
    checks["public_home_not_placeholder"] = "Сайт запускается" not in public_home_text
    checks["public_home_has_content"] = len(public_home_text) > 1000
    ok = ok and checks["public_home_exists"] and checks["public_home_not_placeholder"] and checks["public_home_has_content"]

    return ok, checks

try:
    git_root = run(["git", "rev-parse", "--show-toplevel"], check=True).stdout.strip()
    current_head = run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()
    current_branch = run(["git", "branch", "--show-current"], check=True).stdout.strip() or "main"

    backup_current_state()

    backup_branch = f"backup-before-222-hard-restore-{timestamp}"
    run(["git", "branch", backup_branch, current_head], check=False)

    revs_out = run(["git", "rev-list", "--all", "--max-count=500"], check=True).stdout
    revs = [x.strip() for x in revs_out.splitlines() if x.strip()]

    for commit in revs:
        if commit == current_head:
            continue
        sc, details = score_commit(commit)
        msg = run(["git", "log", "-1", "--format=%s", commit]).stdout.strip()
        candidate_rows.append({"commit": commit, "score": sc, "message": msg, "details": details})

    candidate_rows.sort(key=lambda x: x["score"], reverse=True)

    if not candidate_rows or candidate_rows[0]["score"] < 2200:
        raise RuntimeError("Could not find a clean old working commit with enough score.")

    selected = candidate_rows[0]

    # Hard restore local repo to selected real commit.
    run(["git", "reset", "--hard", selected["commit"]], check=True)

    # Remove known untracked/generated hardfix leftovers if present.
    for leftover in [
        project / "layouts" / "partials" / "ramos-hardfix-v211.html",
        project / "layouts" / "partials" / "footer-transfer-ticker.html",
    ]:
        if leftover.exists():
            txt = leftover.read_text(encoding="utf-8", errors="ignore")
            if "ramos-hardfix-v211" in leftover.name or "Restored bottom transfer ticker" in txt or "218 restore" in txt:
                leftover.unlink()

    run_hugo()
    ok, verify_checks = verify_after()
    write_report(ok, selected, verify_checks)
    if not ok:
        sys.exit(1)

except Exception as e:
    write_report(False, None, {}, extra_error=e)
    sys.exit(1)
