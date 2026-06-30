from pathlib import Path
import subprocess
import hashlib
import os
import sys
import datetime
import traceback

PROJECT = Path(__file__).resolve().parents[1]
PAYLOAD = PROJECT / "restore_payload_257_after_247"
REPORT_DIR = PROJECT / "var"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT = REPORT_DIR / "promyachik_257_restore_graph_from_uploaded_247_backup_no_backup_report.txt"

FILES = [
    "layouts/partials/transfer-player-market-value-chart.html",
    "static/css/style.css",
    "static/css/transfer-player-market-value-chart.css",
    "static/js/transfer-player-market-value-chart.js",
]

BAD_TOKENS = [
    "250_HIDE_YEAR",
    "251_RESTORE_PRICE",
    "253_CUCURELLA_HIDE_YEAR",
    "254_RESTORE_CUCURELLA",
    "255_RESTORE_CUCURELLA",
    "256_RESTORE_CHART",
    "PROMYACHIK 250",
    "PROMYACHIK 251",
    "PROMYACHIK 253",
    "PROMYACHIK 254",
    "PROMYACHIK 255",
    "PROMYACHIK 256",
]

log_lines = []

def log(s=""):
    print(s)
    log_lines.append(str(s))

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def run_cmd(cmd):
    try:
        return subprocess.run(cmd, cwd=str(PROJECT), text=True, capture_output=True, shell=False)
    except FileNotFoundError:
        return None

def main():
    log("PROMYACHIK 257 - RESTORE GRAPH FROM UPLOADED 247 BACKUP")
    log("=" * 100)
    log("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log("Project dir: " + str(PROJECT))
    log("")
    log("RULE")
    log("- Restore graph-related files from uploaded backup: 2026-06-29_23-42-56_FULL_BACKUP_CURRENT_STATE_AFTER_247_ROLLBACK.zip")
    log("- Do not create any backup folder or backup file.")
    log("- Do not push.")
    log("- Do not open the site.")
    log("- Restore price/year layout before bad 250-256 changes.")
    log("")
    log("NO BACKUP")
    log("- Full backup: NOT CREATED")
    log("- Safety backup: NOT CREATED")
    log("")

    if not PAYLOAD.exists():
        raise RuntimeError("Missing payload folder: " + str(PAYLOAD))

    copied = []
    for rel in FILES:
        src = PAYLOAD / rel
        dst = PROJECT / rel
        if not src.exists():
            raise RuntimeError("Missing payload file: " + rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        dst.write_bytes(data)
        copied.append(rel)
        log("RESTORED: " + rel + " | bytes=" + str(len(data)) + " | sha256=" + sha256(dst)[:16])

    log("")
    log("MARKER CHECK AFTER RESTORE")
    for rel in FILES:
        p = PROJECT / rel
        txt = read_text_safe(p)
        bad_found = [t for t in BAD_TOKENS if t in txt]
        log(rel + " | bad_markers=" + (", ".join(bad_found) if bad_found else "NONE"))

    log("")
    log("HUGO")
    res = run_cmd(["hugo", "-D"])
    if res is None:
        log("COMMAND: hugo -D")
        log("EXIT_CODE: HUGO_NOT_FOUND")
        hugo_exit = "HUGO_NOT_FOUND"
    else:
        hugo_exit = res.returncode
        log("COMMAND: hugo -D")
        log("EXIT_CODE: " + str(res.returncode))
        log("--- STDOUT tail ---")
        log("\n".join(res.stdout.splitlines()[-25:]))
        log("--- STDERR tail ---")
        log("\n".join(res.stderr.splitlines()[-25:]))

    log("")
    log("PUBLIC CUCURELLA CHECK")
    public_matches = sorted((PROJECT / "public" / "transfers").glob("*cucurella*/index.html")) if (PROJECT / "public" / "transfers").exists() else []
    log("public_cucurella_pages_found: " + str(len(public_matches)))
    for p in public_matches[:20]:
        txt = read_text_safe(p)
        has_point = "player-market-chart__point" in txt
        has_small = "<small>" in txt or "<small" in txt
        has_strong = "<strong>" in txt or "<strong" in txt
        has_euro = "€" in txt or "&euro;" in txt
        log("- " + str(p.relative_to(PROJECT)) + " | point=" + str(has_point) + " | small_year=" + str(has_small) + " | strong_price=" + str(has_strong) + " | euro=" + str(has_euro))

    all_equal = True
    for rel in FILES:
        all_equal = all_equal and (sha256(PAYLOAD / rel) == sha256(PROJECT / rel))

    any_bad = False
    for rel in FILES:
        txt = read_text_safe(PROJECT / rel)
        if any(t in txt for t in BAD_TOKENS):
            any_bad = True
            break

    log("")
    log("CHECKS")
    log("restored_files_count: " + str(len(copied)))
    log("restored_files_equal_payload: " + str(all_equal))
    log("bad_250_256_markers_in_restored_files: " + str(any_bad))
    log("hugo_exit_code: " + str(hugo_exit))
    log("backup_created: False")
    verified = bool(all_equal and not any_bad and (hugo_exit == 0))
    log("VERIFIED_RESTORE_OK: " + str(verified))
    log("")
    log("NO BACKUP CREATED.")
    log("NO PUSH MADE.")
    log("NO SITE OPENED.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("")
        log("ERROR")
        log(traceback.format_exc())
    finally:
        try:
            REPORT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            print("\nREPORT: " + str(REPORT))
        except Exception as e:
            print("REPORT_WRITE_ERROR: " + repr(e))
