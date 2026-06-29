
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import re
import json
import sys

PACKAGE_DIR = Path(__file__).resolve().parents[1]
PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
RESTORE = PACKAGE_DIR / "restore_files"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_226_before_home_tickers_links_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_226_restore_home_tickers_links_report.txt"

files_to_copy = [
    ("layouts/partials/header.html", "restore clean old-style header and top ticker include"),
    ("layouts/_default/baseof.html", "restore clean baseof and bottom ticker include"),
    ("layouts/partials/transfer-ticker.html", "restore top ticker partial"),
    ("layouts/partials/footer-transfer-ticker.html", "restore bottom ticker partial"),
    ("layouts/index.html", "restore homepage from step-66 logic"),
    ("static/css/transfer-ticker.css", "restore old ticker CSS file"),
    ("data/transfers.json", "restore ticker data with real page links"),
]

commands = []
changed = []
warnings = []

def sha(path: Path):
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")

def backup(path: Path):
    if path.exists():
        rel = path.relative_to(PROJECT)
        dst = BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def copy_rel(rel: str, label: str):
    src = RESTORE / rel
    dst = PROJECT / rel
    if not src.exists():
        raise RuntimeError(f"Missing package restore file: {src}")

    before = sha(dst)
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    after = sha(dst)
    changed.append((rel, label, before != after, before, after))

def write_text(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((str(path.relative_to(PROJECT)), label, before != after, before, after))

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
        "stdout": p.stdout[-3000:],
        "stderr": p.stderr[-3000:],
    })
    return p

def clean_literal_noise(path: Path):
    if not path.exists():
        return
    text = read(path)
    original = text
    text = re.sub(r"cite[^]*", "", text)
    text = text.replace("\\n\\n", "\n")
    text = text.replace("\\n", "\n")
    if text != original:
        write_text(path, text, "remove literal slash-n / citation garbage")

def append_css_bundle():
    style = PROJECT / "static" / "css" / "style.css"
    home_css = read(RESTORE / "static/css/home-restore.css")
    ticker_css = read(RESTORE / "static/css/transfer-ticker.css")
    existing = read(style) if style.exists() else ""

    # Remove our previous bad/duplicate generated blocks.
    existing = re.sub(
        r"/\* 218 restore top bottom transfer tickers \*/.*?(?=/\*|$)",
        "",
        existing,
        flags=re.S
    )
    existing = re.sub(
        r"/\* PROMYACHIK 225 OLD TESTED TICKER CSS START \*/.*?/\* PROMYACHIK 225 OLD TESTED TICKER CSS END \*/",
        "",
        existing,
        flags=re.S
    )
    existing = re.sub(
        r"/\* PROMYACHIK 226 HOME HEADER TICKER RESTORE START \*/.*?/\* PROMYACHIK 226 HOME HEADER TICKER RESTORE END \*/",
        "",
        existing,
        flags=re.S
    )

    block = (
        "\n\n/* PROMYACHIK 226 HOME HEADER TICKER RESTORE START */\n"
        + home_css.rstrip()
        + "\n\n"
        + ticker_css.rstrip()
        + "\n/* PROMYACHIK 226 HOME HEADER TICKER RESTORE END */\n"
    )

    write_text(style, existing.rstrip() + block, "append home/header/ticker CSS bundle")

def disable_bad_footer_old():
    # If a fake/generated footer ticker from earlier package exists, it is overwritten by copy_rel.
    pass

def verify_transfers_links():
    data_path = PROJECT / "data" / "transfers.json"
    data = json.loads(read(data_path))
    missing = []
    for item in data:
        url = item.get("url", "")
        if not url.startswith("transfers/"):
            missing.append((item.get("player"), url, "bad-url"))
            continue
        page = PROJECT / "content" / url.strip("/") / "index.md"
        if not page.exists():
            missing.append((item.get("player"), url, str(page)))
    return missing

def main():
    ok = True

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    # Backup known affected files before copy.
    for rel, _ in files_to_copy:
        backup(PROJECT / rel)
    backup(PROJECT / "static/css/style.css")

    for rel, label in files_to_copy:
        copy_rel(rel, label)

    append_css_bundle()

    # Clean remaining slash-n/citation noise in files that can print it into HTML.
    for rel in [
        "layouts/partials/header.html",
        "layouts/_default/baseof.html",
        "layouts/index.html",
        "layouts/partials/transfer-ticker.html",
        "layouts/partials/footer-transfer-ticker.html",
    ]:
        clean_literal_noise(PROJECT / rel)

    missing_links = verify_transfers_links()
    if missing_links:
        warnings.append("Some ticker URLs do not have matching content pages: " + repr(missing_links))

    hugo = run(["hugo", "-D"])

    public_home = PROJECT / "public" / "index.html"
    public_text = read(public_home) if public_home.exists() else ""

    public_transfer_pages = {}
    for item in json.loads(read(PROJECT / "data" / "transfers.json")):
        url = item["url"].strip("/")
        html = PROJECT / "public" / url / "index.html"
        public_transfer_pages[url] = html.exists()

    checks = {
        "hugo_exit_code": hugo.returncode,
        "public_index_exists": public_home.exists(),
        "public_index_not_placeholder": "Сайт запускается" not in public_text,
        "public_no_literal_slash_n": "\\n" not in public_text,
        "public_has_top_ticker": "pf-ticker" in public_text,
        "public_has_ticker_items": "pf-ticker__item" in public_text,
        "public_has_home_slider": "home-slider" in public_text,
        "public_has_main_transfer": "Главный трансфер дня" in public_text,
        "all_ticker_content_pages_exist": all(public_transfer_pages.values()) if public_transfer_pages else False,
        "ticker_pages": public_transfer_pages,
        "missing_content_links": missing_links,
    }

    if hugo.returncode != 0:
        ok = False
    for key in [
        "public_index_exists",
        "public_index_not_placeholder",
        "public_no_literal_slash_n",
        "public_has_top_ticker",
        "public_has_ticker_items",
        "public_has_home_slider",
        "public_has_main_transfer",
    ]:
        if not checks[key]:
            ok = False

    # Missing pages should be reported, but not fail if user has not rebuilt all old content.
    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 226 - RESTORE HOME + TOP/BOTTOM TICKERS + LINKS")
    lines.append("=" * 90)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Package dir: {PACKAGE_DIR}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("CHANGED FILES")
    for rel, label, did, before, after in changed:
        lines.append(f"- {rel} | {label} | changed={did}")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    lines.append("CHECKS")
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("HUGO")
    lines.append(f"- exit_code: {hugo.returncode}")
    lines.append("--- STDOUT tail ---")
    lines.append(hugo.stdout[-2000:])
    lines.append("--- STDERR tail ---")
    lines.append(hugo.stderr[-2000:])
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands:
        lines.append("-" * 60)
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
