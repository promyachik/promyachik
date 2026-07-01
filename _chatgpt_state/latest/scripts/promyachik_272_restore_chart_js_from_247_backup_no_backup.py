from pathlib import Path
import shutil
import subprocess
import datetime

root = Path(__file__).resolve().parents[1]
report = root / "var" / "promyachik_272_restore_chart_js_from_247_backup_no_backup_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)

log = []
log.append("PROMYACHIK 272 - RESTORE CHART JS FROM UPLOADED 247 BACKUP - NO BACKUP")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {root}")
log.append("")
log.append("RULE")
log.append("- Restore only transfer-player-market-value-chart.js from uploaded 247 rollback backup payload.")
log.append("- Undo package 271 runtime JS price-bottom bug.")
log.append("- Do not hide year in this package.")
log.append("- Do not move prices in this package.")
log.append("- Do not create backup folder or backup file.")
log.append("- No push.")
log.append("- No site opened.")
log.append("")

src = root / "_payload_272" / "static" / "js" / "transfer-player-market-value-chart.js"
dst = root / "static" / "js" / "transfer-player-market-value-chart.js"
public_dst = root / "public" / "js" / "transfer-player-market-value-chart.js"

try:
    if not src.exists():
        raise FileNotFoundError(f"payload missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log.append(f"RESTORED: {dst}")

    # Also restore public copy immediately so localhost/static cache has the fixed runtime even before Hugo copy.
    public_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, public_dst)
    log.append(f"RESTORED: {public_dst}")

    bad_tokens = ["PROMYACHIK 271", "CucurellaHideYearRuntime", "cucurella_hide_year_runtime"]
    js_text = dst.read_text(encoding="utf-8", errors="ignore")
    log.append("")
    log.append("CHECKS BEFORE HUGO")
    for token in bad_tokens:
        log.append(f"bad_token {token}: {token in js_text}")
    log.append(f"js_has_2021: {'2021' in js_text}")
    log.append(f"js_has_price_symbol: {'€' in js_text}")

    proc = subprocess.run(["hugo", "-D"], cwd=root, text=True, capture_output=True)
    log.append("")
    log.append("HUGO")
    log.append(f"exit_code: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append(proc.stdout[-2000:])
    log.append("--- STDERR tail ---")
    log.append(proc.stderr[-2000:])

    target = root / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
    log.append("")
    log.append("TARGET CHECK")
    log.append("target_url: http://localhost:1313/promyachik/transfers/marc-cucurella-real-madrid/")
    log.append(f"target_public_html_exists: {target.exists()}")
    log.append(f"public_js_exists: {public_dst.exists()}")

    ok = proc.returncode == 0 and target.exists() and public_dst.exists()
    log.append("")
    log.append("VERIFIED_OK: " + str(ok))
    log.append("DONE" if ok else "FAILED")
    report.write_text("\n".join(log), encoding="utf-8")
    print("DONE" if ok else "FAILED")
    print(f"REPORT: {report}")
    raise SystemExit(0 if ok else 1)
except Exception as e:
    log.append("ERROR: " + repr(e))
    log.append("FAILED")
    report.write_text("\n".join(log), encoding="utf-8")
    print("FAILED")
    print(f"REPORT: {report}")
    raise SystemExit(1)
