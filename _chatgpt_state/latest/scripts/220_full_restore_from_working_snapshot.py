
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import sys

project = Path.cwd()
backup_before = project / "_backup_220_before_full_restore_from_working_snapshot"
backup_before.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_220_full_restore_from_working_snapshot_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

BAD = [
    "cite",
    "\\n\\n",
    "\\nplayer_image",
    "Restored top transfer ticker",
    "Restored bottom transfer ticker",
    "218 restore top bottom transfer tickers",
    "216 restore stats icon visual size",
    "pfb-ramos-v211",
    "ramos-hardfix-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
    "portugal-proper",
    "Сайт запускается",
]

CRITICAL = [
    "layouts/index.html",
    "layouts/partials/header.html",
    "layouts/partials/transfer-ticker.html",
    "layouts/_default/baseof.html",
    "layouts/transfers/single.html",
    "layouts/partials/transfer-player-stats.html",
    "static/css/style.css",
]

RESTORE_PATHS = [
    "layouts",
    "content",
    "data",
    "static/css",
    "static/header.css",
    "hugo.toml",
]

commands = []
warnings = []
restored = []
selected = None
hugo_result = ""

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

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project)).replace("\\", "/")
    except Exception:
        return str(p)

def read_path(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def bad_text(text: str) -> bool:
    return any(x in text for x in BAD)

def valid_md(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:] and not bad_text(text)

def git_show(rev: str, path_rel: str):
    p = run(["git", "show", f"{rev}:{path_rel}"])
    if p.returncode == 0:
        return p.stdout
    return None

def git_tree_paths(rev: str):
    p = run(["git", "ls-tree", "-r", "--name-only", rev])
    if p.returncode != 0:
        return set()
    return set(x.strip() for x in p.stdout.splitlines() if x.strip())

def score_file(path_rel: str, text: str) -> int:
    if text is None or not text.strip():
        return -100000
    if bad_text(text):
        return -100000

    low = text.lower()
    s = len(text) // 300

    if path_rel == "layouts/index.html":
        if "<" in text and ">" in text:
            s += 150
        if "# ⚽" in text or "Сайт запускается" in text:
            s -= 100000
        if "hero" in low or "player-card" in low or ".site.regularpages" in low or "mbapp" in low:
            s += 180
        if "Последние новости" in text and "Сайт запускается" not in text:
            s += 30

    elif path_rel == "layouts/partials/header.html":
        if "<header" in low or "site-header" in low:
            s += 180
        if "главная" in low and "трансферы" in low:
            s += 100
        if 'partial "transfer-ticker.html"' in text:
            s += 100

    elif path_rel == "layouts/partials/transfer-ticker.html":
        if "site.data.transfers" in low or ".Site.Data.transfers" in text:
            s += 220
        if "club-logos" in text:
            s += 150
        if "statusLabels" in text or "statuslabels" in low:
            s += 120
        if "from_club" in text and "to_club" in text:
            s += 100
        if "transfer-ticker" in low or "pf-transfer" in low:
            s += 100
        if "range" in text:
            s += 50

    elif path_rel == "layouts/_default/baseof.html":
        if "<html" in low and "<body" in low:
            s += 240
        if 'partial "header.html"' in text:
            s += 120
        if "{{ block" in text:
            s += 100
        if len(text.splitlines()) > 5:
            s += 50

    elif path_rel == "layouts/transfers/single.html":
        if 'transfer-player-stats.html' in text:
            s += 160
        if "market-value-chart" in low or "profutbik-market-chart-static.html" in text:
            s += 160
        if ".Content" in text:
            s += 70
        if "transfer-page" in text:
            s += 50

    elif path_rel == "layouts/partials/transfer-player-stats.html":
        if "pfb-stats-v184" in text:
            s += 240
        if "stats-icons-v184" in text:
            s += 150
        if "previous_club_stats" in text and "pfb-stats-v184" not in text:
            s -= 100000
        if "МАТЧА" in text and "ГОЛА" in text and "pfb-stats-v184" not in text:
            s -= 100000

    elif path_rel == "static/css/style.css":
        if len(text) > 10000:
            s += 150
        if "transfer-ticker" in low or "pf-transfer" in low:
            s += 180
        if "site-header" in low:
            s += 80
        if "pfb-stats-v184" in text:
            s += 80
        if "218 restore" in text or "216 restore" in text:
            s -= 100000

    return s

def score_source_texts(source_name: str, get_text_func):
    total = 0
    details = []
    for path_rel in CRITICAL:
        text = get_text_func(path_rel)
        sc = score_file(path_rel, text)
        details.append((path_rel, sc))
        if sc < 0:
            return -1000000, details
        total += sc

    # Bonus for existing valid transfer content and player pages.
    ramos = get_text_func("content/transfers/goncalo-ramos-ac-milan/index.md")
    if ramos:
        if valid_md(ramos):
            total += 200
        else:
            total -= 300

    # Bonus for known working progress markers / richer layouts.
    chart1 = get_text_func("layouts/partials/transfer-player-market-value-chart.html")
    chart2 = get_text_func("layouts/partials/profutbik-market-chart-static.html")
    if chart1 and not bad_text(chart1):
        total += 100
    if chart2 and not bad_text(chart2):
        total += 100

    return total, details

def backup_dirs_sorted():
    dirs = [p for p in project.glob("_backup_*") if p.is_dir() and p.name != backup_before.name]
    def key(p: Path):
        name = p.name.lower()
        penalty = 0
        # Broken backup series should not win unless no clean old source exists.
        for n in ["_backup_220", "_backup_219", "_backup_218", "_backup_217", "_backup_216", "_backup_215", "_backup_214", "_backup_213", "_backup_212", "_backup_211", "_backup_210", "_backup_209", "_backup_208", "_backup_207"]:
            if name.startswith(n):
                penalty += 100000
        return (penalty, name)
    return sorted(dirs, key=key)

def evaluate_backups():
    results = []
    for root in backup_dirs_sorted():
        def get_text(path_rel, root=root):
            p = root / path_rel
            if p.exists() and p.is_file():
                return read_path(p)
            return None
        score, details = score_source_texts(f"backup:{root.name}", get_text)
        if score > -1000000:
            results.append({"type": "backup", "id": str(root), "name": root.name, "score": score, "details": details})
    return results

def evaluate_git():
    results = []
    p = run(["git", "rev-list", "--all", "--max-count=200"])
    if p.returncode != 0:
        warnings.append("git rev-list failed")
        return results
    revs = [x.strip() for x in p.stdout.splitlines() if x.strip()]
    for rev in revs:
        def get_text(path_rel, rev=rev):
            return git_show(rev, path_rel)
        score, details = score_source_texts(f"git:{rev}", get_text)
        if score > -1000000:
            results.append({"type": "git", "id": rev, "name": rev[:12], "score": score, "details": details})
    return results

def copy_backup_source(root: Path):
    # Copy whole restored structure only from this existing backup folder.
    for path_rel in RESTORE_PATHS:
        src = root / path_rel
        dst = project / path_rel
        if src.exists():
            if dst.exists():
                backup_dst = backup_before / path_rel
                backup_dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.is_dir():
                    if not backup_dst.exists():
                        shutil.copytree(dst, backup_dst, dirs_exist_ok=True)
                    shutil.rmtree(dst)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    if not backup_dst.exists():
                        shutil.copy2(dst, backup_dst)
                    shutil.copy2(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            restored.append(f"{path_rel} <= backup:{root.name}")

def restore_git_source(rev: str):
    tree = git_tree_paths(rev)
    paths = []
    for path_rel in RESTORE_PATHS:
        if path_rel in tree or any(x.startswith(path_rel.rstrip("/") + "/") for x in tree):
            paths.append(path_rel)
    if not paths:
        raise RuntimeError("Selected git snapshot has no restore paths.")

    # Save current whole affected structure first.
    for path_rel in RESTORE_PATHS:
        dst = project / path_rel
        if dst.exists():
            backup_dst = backup_before / path_rel
            backup_dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_dir():
                if not backup_dst.exists():
                    shutil.copytree(dst, backup_dst, dirs_exist_ok=True)
            else:
                if not backup_dst.exists():
                    shutil.copy2(dst, backup_dst)

    p = run(["git", "checkout", rev, "--"] + paths)
    if p.returncode != 0:
        raise RuntimeError("git checkout selected snapshot failed")
    for path_rel in paths:
        restored.append(f"{path_rel} <= git:{rev[:12]}")

def delete_known_broken_leftovers():
    for path_rel in [
        "layouts/partials/ramos-hardfix-v211.html",
        "layouts/partials/footer-transfer-ticker.html",
    ]:
        p = project / path_rel
        if p.exists():
            text = read_path(p)
            if "ramos-hardfix-v211" in path_rel or "Restored bottom transfer ticker" in text or "218 restore" in text:
                b = backup_before / path_rel
                b.parent.mkdir(parents=True, exist_ok=True)
                if not b.exists():
                    shutil.copy2(p, b)
                p.unlink()
                restored.append(f"{path_rel} deleted as broken leftover")

def run_hugo():
    global hugo_result
    p = run(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-3000:]}\nSTDERR tail:\n{p.stderr[-3000:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero")

def verify_after():
    checks = {}
    ok = True

    for path_rel in CRITICAL:
        p = project / path_rel
        exists = p.exists()
        text = read_path(p) if exists else ""
        sc = score_file(path_rel, text)
        clean = exists and sc >= 0 and not bad_text(text)
        checks[path_rel] = {"exists": exists, "score": sc, "clean": clean, "length": len(text)}
        ok = ok and clean

    index_text = read_path(project / "layouts/index.html") if (project / "layouts/index.html").exists() else ""
    checks["home_not_placeholder"] = "Сайт запускается" not in index_text and "# ⚽" not in index_text
    ok = ok and checks["home_not_placeholder"]

    content_root = project / "content"
    md_count = len(list(content_root.rglob("*.md"))) if content_root.exists() else 0
    checks["content_markdown_count"] = md_count
    ok = ok and md_count >= 4

    ramos = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
    ramos_text = read_path(ramos) if ramos.exists() else ""
    checks["ramos_valid_front_matter"] = valid_md(ramos_text) if ramos.exists() else False
    ok = ok and checks["ramos_valid_front_matter"]

    public_index = project / "public" / "index.html"
    public_index_text = read_path(public_index) if public_index.exists() else ""
    checks["public_home_exists"] = public_index.exists()
    checks["public_home_not_placeholder"] = "Сайт запускается" not in public_index_text
    checks["public_has_ticker_or_pf_transfer"] = ("transfer-ticker" in public_index_text or "pf-transfer" in public_index_text)
    ok = ok and checks["public_home_exists"] and checks["public_home_not_placeholder"]

    return ok, checks

try:
    # Backup current broken state of affected folders/files.
    for path_rel in RESTORE_PATHS:
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

    candidates = evaluate_backups() + evaluate_git()
    candidates.sort(key=lambda x: x["score"], reverse=True)

    if not candidates:
        raise RuntimeError("No clean working backup/git snapshot found.")

    selected = candidates[0]
    if selected["score"] < 1200:
        raise RuntimeError(f"Best snapshot score too low: {selected}")

    if selected["type"] == "backup":
        copy_backup_source(Path(selected["id"]))
    else:
        restore_git_source(selected["id"])

    delete_known_broken_leftovers()
    run_hugo()

    ok, checks = verify_after()

    lines = []
    lines.append("PROFUTBIK 220 - FULL RESTORE FROM WORKING SNAPSHOT")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No new ticker/home/player page was written from scratch.")
    lines.append("- Whole affected site structure was restored from one existing working backup/git snapshot.")
    lines.append("- Current broken state was backed up first.")
    lines.append("")
    lines.append("BACKUP OF BROKEN STATE")
    lines.append(f"- {backup_before}")
    lines.append("")
    lines.append("SELECTED SNAPSHOT")
    lines.append(f"- type: {selected['type']}")
    lines.append(f"- id: {selected['id']}")
    lines.append(f"- score: {selected['score']}")
    lines.append("- detail scores:")
    for path_rel, sc in selected["details"]:
        lines.append(f"  - {path_rel}: {sc}")
    lines.append("")
    lines.append("RESTORED")
    for item in restored:
        lines.append(f"- {item}")
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
    for c in commands[-40:]:
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
    lines.append("PROFUTBIK 220 - FULL RESTORE FROM WORKING SNAPSHOT")
    lines.append("=" * 90)
    lines.append("FAILED")
    lines.append(f"Error: {e}")
    lines.append("")
    lines.append("No new ticker/home/player page was written from scratch.")
    lines.append("Current broken state backup folder:")
    lines.append(f"- {backup_before}")
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands[-40:]:
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
