
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import sys

project = Path.cwd()
backup_before = project / "_backup_219_before_restore_tested_tickers_from_backup_only"
backup_before.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_219_restore_tested_tickers_from_backup_only_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

# Only these files are allowed to be restored by this package.
TARGETS = [
    "layouts/partials/header.html",
    "layouts/partials/transfer-ticker.html",
    "layouts/partials/footer-transfer-ticker.html",
    "layouts/_default/baseof.html",
    "layouts/partials/footer.html",
    "static/css/style.css",
]

# These files must not be touched.
FORBIDDEN_TOUCH = [
    "layouts/partials/transfer-player-stats.html",
    "layouts/partials/transfer-player-market-value-chart.html",
    "layouts/partials/profutbik-market-chart-static.html",
    "layouts/transfers/single.html",
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
    "pfb-ramos-v211",
    "ramos-hardfix-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
    "portugal-proper",
]

BROKEN_BACKUP_PREFIXES = [
    "_backup_219",
    "_backup_218",
    "_backup_217",
    "_backup_216",
    "_backup_215",
    "_backup_214",
    "_backup_213",
    "_backup_212",
    "_backup_211",
    "_backup_210",
    "_backup_209",
    "_backup_208",
    "_backup_207",
]

commands = []
restored = []
skipped = []
warnings = []
hugo_result = ""

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(project)).replace("\\", "/")
    except Exception:
        return str(path)

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

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def backup_current(path: Path):
    if path.exists():
        dst = backup_before / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write_from_text(path_rel: str, text: str, source: str):
    # Guard: do not write forbidden files.
    if path_rel in FORBIDDEN_TOUCH:
        raise RuntimeError(f"Refusing to touch forbidden file: {path_rel}")
    path = project / path_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_current(path)
    path.write_text(text, encoding="utf-8", newline="\n")
    restored.append((path_rel, source))

def is_bad(text: str) -> bool:
    return any(token in text for token in BAD_TOKENS)

def is_generated_new_ticker(text: str) -> bool:
    lower = text.lower()
    return (
        "restored top transfer ticker" in lower
        or "restored bottom transfer ticker" in lower
        or "218 restore top bottom transfer tickers" in lower
        or "footer-transfer-ticker.html" in lower and "restored bottom" in lower
    )

def clean_enough(path_rel: str, text: str) -> bool:
    if not text.strip():
        return False
    if is_bad(text):
        return False
    if is_generated_new_ticker(text):
        return False

    low = text.lower()
    if path_rel.endswith(".html"):
        if "header.html" in path_rel:
            return "<header" in low or "site-header" in low or "main-nav" in low or "nav" in low
        if "transfer-ticker.html" in path_rel:
            return "ticker" in low and ("<" in text or "{{" in text)
        if "footer-transfer-ticker.html" in path_rel:
            return "ticker" in low and ("<" in text or "{{" in text)
        if "baseof.html" in path_rel:
            return ("<html" in low and "<body" in low) or ("{{ block" in text and "partial" in text and len(text) > 120)
        if "footer.html" in path_rel:
            return "<footer" in low or "footer" in low
    if path_rel.endswith(".css"):
        # Real old stylesheet should not be just the 216/218 patches.
        return len(text) > 500 and ("body" in low or "header" in low or "ticker" in low or "transfer" in low)
    return True

def score_text(path_rel: str, text: str) -> int:
    if not clean_enough(path_rel, text):
        return -100000
    low = text.lower()
    s = len(text) // 200

    if path_rel == "layouts/partials/transfer-ticker.html":
        if ".site.data.transfers" in low or "site.data.transfers" in low:
            s += 250
        if "club-logos" in text:
            s += 150
        if "statuslabels" in low or "statuslabels" in text:
            s += 120
        if "from_club" in text and "to_club" in text:
            s += 120
        if "api_player" in text or "player_image" in text:
            s += 60
        if "transfer-ticker" in low:
            s += 100
        if "range" in text:
            s += 40

    elif path_rel == "layouts/partials/header.html":
        if "partial \"transfer-ticker.html\"" in text or "partial `transfer-ticker.html`" in text:
            s += 250
        if "<header" in low:
            s += 150
        if "profutbik" in low or "promyachik" in low:
            s += 80
        if "главная" in low and "трансферы" in low:
            s += 100
        if "cite" in low:
            s -= 1000

    elif path_rel == "layouts/_default/baseof.html":
        if "<html" in low and "<body" in low:
            s += 250
        if "partial \"header.html\"" in text:
            s += 150
        if "{{ block \"main\"" in text or "{{ block" in text:
            s += 100
        if "footer" in low:
            s += 50

    elif path_rel == "static/css/style.css":
        if "transfer-ticker" in low:
            s += 200
        if "site-header" in low or "main-nav" in low or "header" in low:
            s += 100
        if "pfb-stats-v184" in text:
            s += 50
        if "218 restore" in text or "216 restore" in text:
            s -= 1000

    elif "footer" in path_rel:
        if "transfer-ticker" in low:
            s += 100
        if "<footer" in low:
            s += 80

    return s

def backup_dirs_sorted():
    dirs = [p for p in project.glob("_backup_*") if p.is_dir()]
    def key(p: Path):
        name = p.name
        penalty = 0
        for prefix in BROKEN_BACKUP_PREFIXES:
            if name.startswith(prefix):
                penalty += 100000
        # Prefer older clean backups before 207-218.
        return (penalty, name)
    return sorted(dirs, key=key)

def file_candidates_from_backups(path_rel: str):
    out = []
    for root in backup_dirs_sorted():
        if root.name == backup_before.name:
            continue
        p = root / path_rel
        if p.exists() and p.is_file():
            try:
                out.append((f"backup:{root.name}", read(p)))
            except Exception as e:
                warnings.append(f"Could not read {root.name}/{path_rel}: {e}")
    return out

def file_candidates_from_git(path_rel: str):
    out = []
    hashes = []
    p = run(["git", "log", "--all", "--format=%H", "--", path_rel])
    if p.returncode == 0:
        hashes.extend([h.strip() for h in p.stdout.splitlines() if h.strip()])
    for i in range(0, 100):
        hashes.append("HEAD" if i == 0 else f"HEAD~{i}")
    seen = set()
    for rev in hashes:
        if rev in seen:
            continue
        seen.add(rev)
        show = run(["git", "show", f"{rev}:{path_rel}"])
        if show.returncode == 0 and show.stdout.strip():
            out.append((f"git:{rev}", show.stdout))
    return out

def choose_file(path_rel: str):
    candidates = file_candidates_from_backups(path_rel) + file_candidates_from_git(path_rel)
    best = None
    for source, text in candidates:
        score = score_text(path_rel, text)
        if best is None or score > best[0]:
            best = (score, source, text)
    return best

def restore_target(path_rel: str, required: bool):
    best = choose_file(path_rel)
    if not best or best[0] < 0:
        msg = "no clean tested backup/git candidate found"
        if required:
            raise RuntimeError(f"{path_rel}: {msg}")
        skipped.append((path_rel, msg))
        # If optional file is only our bad generated bottom ticker, remove it.
        p = project / path_rel
        if p.exists():
            current = read(p)
            if is_bad(current) or is_generated_new_ticker(current):
                backup_current(p)
                p.unlink()
                restored.append((path_rel, "deleted broken/generated file; no clean old candidate found"))
        return
    score, source, text = best
    write_from_text(path_rel, text, f"{source}, score={score}")

def run_hugo():
    global hugo_result
    p = run(["hugo", "-D"])
    hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-2500:]}\nSTDERR tail:\n{p.stderr[-2500:]}"
    if p.returncode != 0:
        warnings.append("hugo -D returned non-zero")

def verify():
    checks = {}

    for path_rel in TARGETS:
        p = project / path_rel
        if not p.exists():
            checks[path_rel] = {"exists": False, "clean": path_rel in ["layouts/partials/footer-transfer-ticker.html", "layouts/partials/footer.html"], "note": "optional missing"}
            continue
        text = read(p)
        checks[path_rel] = {
            "exists": True,
            "clean": clean_enough(path_rel, text),
            "has_bad_tokens": is_bad(text),
            "generated_new_ticker": is_generated_new_ticker(text),
            "len": len(text),
        }

    header_text = read(project / "layouts/partials/header.html") if (project / "layouts/partials/header.html").exists() else ""
    ticker_text = read(project / "layouts/partials/transfer-ticker.html") if (project / "layouts/partials/transfer-ticker.html").exists() else ""
    baseof_text = read(project / "layouts/_default/baseof.html") if (project / "layouts/_default/baseof.html").exists() else ""
    css_text = read(project / "static/css/style.css") if (project / "static/css/style.css").exists() else ""

    checks["header_has_ticker_include"] = 'partial "transfer-ticker.html"' in header_text
    checks["ticker_looks_old_tested"] = (
        ("site.data.transfers" in ticker_text.lower() or ".Site.Data.transfers" in ticker_text or "club-logos" in ticker_text)
        and "Restored top transfer ticker" not in ticker_text
        and "cite" not in ticker_text
    )
    checks["baseof_has_real_structure"] = "<html" in baseof_text.lower() or ("{{ block" in baseof_text and len(baseof_text) > 120)
    checks["css_not_only_216_218"] = "216 restore stats icon visual size" not in css_text and "218 restore top bottom transfer tickers" not in css_text

    forbidden_changed = []
    for path_rel in FORBIDDEN_TOUCH:
        if (backup_before / path_rel).exists():
            forbidden_changed.append(path_rel)
    checks["forbidden_files_touched"] = forbidden_changed

    ok = (
        checks["layouts/partials/header.html"]["clean"]
        and checks["layouts/partials/transfer-ticker.html"]["clean"]
        and checks["layouts/_default/baseof.html"]["clean"]
        and checks["static/css/style.css"]["clean"]
        and checks["header_has_ticker_include"]
        and checks["ticker_looks_old_tested"]
        and checks["baseof_has_real_structure"]
        and checks["css_not_only_216_218"]
        and not forbidden_changed
    )
    return ok, checks

try:
    # Backup current affected files before restore.
    for path_rel in TARGETS + FORBIDDEN_TOUCH:
        p = project / path_rel
        if p.exists():
            backup_current(p)

    # Required: real old top ticker, header, base layout, stylesheet.
    restore_target("layouts/partials/transfer-ticker.html", required=True)
    restore_target("layouts/partials/header.html", required=True)
    restore_target("layouts/_default/baseof.html", required=True)
    restore_target("static/css/style.css", required=True)

    # Optional: restore old footer/bottom ticker only if it existed in clean backup/git.
    restore_target("layouts/partials/footer-transfer-ticker.html", required=False)
    restore_target("layouts/partials/footer.html", required=False)

    run_hugo()
    ok, checks = verify()

    lines = []
    lines.append("PROFUTBIK 219 - RESTORE TESTED TICKERS FROM BACKUP ONLY")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project: {project}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No ticker was written from scratch.")
    lines.append("- Files were copied only from existing _backup_* folders or git history.")
    lines.append("- Stats block, chart partials, transfer layout, and Ramos content were not touched.")
    lines.append("")
    lines.append("BACKUP OF CURRENT AFFECTED FILES")
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
    lines = []
    lines.append("PROFUTBIK 219 - RESTORE TESTED TICKERS FROM BACKUP ONLY")
    lines.append("=" * 90)
    lines.append("FAILED")
    lines.append(f"Error: {e}")
    lines.append("")
    lines.append("No new ticker was written from scratch.")
    lines.append("Check backup/git candidates manually before retrying.")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8", errors="ignore"))
    sys.exit(1)
