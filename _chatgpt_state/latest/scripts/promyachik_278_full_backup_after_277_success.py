from pathlib import Path
import shutil
import datetime
import os
import sys
import subprocess
import json

PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
BACKUPS_ROOT = Path(r"C:\Users\Dmitrii\Promyachik_BACKUPS")
STAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_NAME = f"{STAMP}_FULL_BACKUP_AFTER_277_HIDE_YEAR_ALL_PLAYER_CHARTS_SUCCESS"
BACKUP_DIR = BACKUPS_ROOT / BACKUP_NAME
REPORT = PROJECT / "var" / "promyachik_278_full_backup_after_277_success_report.txt"

EXCLUDE_NAMES = {
    ".git",              # not needed for visual/site rollback; keeps backup lighter and safer
    "resources",         # Hugo cache, can be regenerated
    ".hugo_build.lock",
}
EXCLUDE_PREFIXES = (
    "_backup_promyachik_",
)

log = []
log.append("PROMYACHIK 278 - FULL BACKUP AFTER 277 SUCCESS")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {PROJECT}")
log.append(f"Backup dir: {BACKUP_DIR}")
log.append("")
log.append("RULE")
log.append("- User explicitly requested backup now.")
log.append("- Create full recovery backup after package 277 success.")
log.append("- No code/style/content changes.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")
log.append("CURRENT SAFE STATE")
log.append("- 276 worked for Cucurella: year hidden CSS-only, prices stayed in place.")
log.append("- 277 worked globally: year hidden on all current and future player charts via CSS-only.")
log.append("- JS is not patched for hiding years.")
log.append("- Runtime positioning is not touched.")
log.append("")

try:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if not PROJECT.exists():
        raise RuntimeError(f"Project folder not found: {PROJECT}")
    BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
    if BACKUP_DIR.exists():
        raise RuntimeError(f"Backup dir already exists: {BACKUP_DIR}")

    def ignore_func(dirpath, names):
        ignored = []
        for name in names:
            if name in EXCLUDE_NAMES:
                ignored.append(name)
                continue
            if any(name.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                ignored.append(name)
                continue
            if name.endswith(".tmp") or name.endswith(".lock"):
                ignored.append(name)
        return ignored

    log.append("COPY")
    shutil.copytree(PROJECT, BACKUP_DIR, ignore=ignore_func)
    log.append("copytree: done")

    files = 0
    dirs = 0
    total_bytes = 0
    for p in BACKUP_DIR.rglob("*"):
        try:
            if p.is_dir():
                dirs += 1
            elif p.is_file():
                files += 1
                total_bytes += p.stat().st_size
        except OSError:
            pass

    log.append("")
    log.append("COUNTS")
    log.append(f"files: {files}")
    log.append(f"dirs: {dirs}")
    log.append(f"bytes: {total_bytes}")

    # Minimal verification of key files after 277.
    css = BACKUP_DIR / "static" / "css" / "transfer-player-market-value-chart.css"
    js = BACKUP_DIR / "static" / "js" / "transfer-player-market-value-chart.js"
    partial = BACKUP_DIR / "layouts" / "partials" / "transfer-player-market-value-chart.html"
    content_cuc = BACKUP_DIR / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

    checks = {
        "css_exists": css.exists(),
        "js_exists": js.exists(),
        "partial_exists": partial.exists(),
        "cucurella_content_exists": content_cuc.exists(),
    }
    css_text = css.read_text(encoding="utf-8", errors="ignore") if css.exists() else ""
    # Accept any of the markers/semantics from 276/277 CSS-only hide-year packages.
    checks["css_has_276_or_277_marker"] = ("PROMYACHIK 276" in css_text) or ("PROMYACHIK 277" in css_text) or ("HIDE YEAR" in css_text.upper() and "player-market" in css_text)
    checks["css_mentions_chart"] = "player-market" in css_text
    checks["css_mentions_visibility_or_opacity"] = ("opacity" in css_text) or ("visibility" in css_text) or ("color: transparent" in css_text)

    log.append("")
    log.append("VERIFY")
    for k, v in checks.items():
        log.append(f"{k}: {v}")

    progress_md = BACKUP_DIR / "PROFUTBIK_PROGRESS_AFTER_277_SUCCESS.md"
    progress_md.write_text("""# ProFutbik / Promyachik — recovery point after 277 success

**Date:** {date}  
**Project:** `C:\\Users\\Dmitrii\\Promyachik`  
**Local site:** `http://localhost:1313/promyachik/`

## Safe state

- Package **275** restored the chart JS after the failed 274 attempt.
- Package **276** successfully hid the year on the Cucurella chart using CSS-only.
- Package **277** successfully applied the same CSS-only year hiding to all current and future player value charts.
- Prices stayed visible and did not move to the footer.
- Runtime JS positioning must not be changed for this task.

## Working principle

Do **not** delete year/date nodes from JS/HTML. Keep DOM structure intact and hide the year visually with CSS-only. This keeps the existing price positioning logic stable.

## Backup

This backup folder is the recovery point after package 277 success:

`{backup}`

## Do not repeat

- Do not patch `static/js/transfer-player-market-value-chart.js` to remove years.
- Do not remove date/year DOM nodes.
- Do not use BaseFileName checks for Cucurella.
- Do not create backups unless explicitly requested.
""".format(date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), backup=str(BACKUP_DIR)), encoding="utf-8")
    log.append(f"progress_md: {progress_md}")

    ok = all(checks.values())
    log.append("")
    log.append(f"VERIFIED_OK: {ok}")
    log.append("DONE" if ok else "DONE_WITH_WARNINGS")
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "DONE_WITH_WARNINGS")
    print(f"BACKUP: {BACKUP_DIR}")
    print(f"REPORT: {REPORT}")
    sys.exit(0 if ok else 0)

except Exception as e:
    log.append("")
    log.append(f"ERROR: {type(e).__name__}: {e}")
    log.append("FAILED")
    try:
        REPORT.write_text("\n".join(log), encoding="utf-8")
    except Exception:
        pass
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise
