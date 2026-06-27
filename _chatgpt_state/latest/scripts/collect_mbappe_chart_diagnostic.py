from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
OUTPUT_DIR = PROJECT / "var"
BUILD_DIR = OUTPUT_DIR / "mbappe_chart_diagnostic_build"
COLLECT_DIR = OUTPUT_DIR / "mbappe_chart_diagnostic_files"
ZIP_PATH = OUTPUT_DIR / "MBAPPE_CHART_DIAGNOSTIC.zip"

SEARCH_TERMS = [
    "Килиан Мбаппе",
    "Kylian Mbappe",
    "Kylian Mbappé",
    "mbappe",
]


def safe_read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def copy_file(source: Path, target_root: Path) -> None:
    relative = source.resolve().relative_to(PROJECT.resolve())
    destination = target_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def contains_mbappe(text: str) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in SEARCH_TERMS)


def extract_classes(html: str) -> list[str]:
    classes: set[str] = set()

    for match in re.finditer(
        r'class\s*=\s*["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    ):
        for class_name in match.group(1).split():
            classes.add(class_name)

    return sorted(classes)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in (BUILD_DIR, COLLECT_DIR):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    hugo = shutil.which("hugo")

    if not hugo:
        print("ERROR: Hugo was not found in PATH.")
        return 1

    print("STEP 1 OF 4: building a diagnostic copy of the site...")

    result = subprocess.run(
        [
            hugo,
            "--destination",
            str(BUILD_DIR),
            "--baseURL",
            "http://127.0.0.1:1313/promyachik/",
        ],
        cwd=PROJECT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    build_log = (
        "STDOUT:\n"
        + result.stdout
        + "\n\nSTDERR:\n"
        + result.stderr
        + "\n\nEXIT CODE: "
        + str(result.returncode)
        + "\n"
    )

    (COLLECT_DIR / "hugo_build_log.txt").write_text(
        build_log,
        encoding="utf-8",
    )

    if result.returncode != 0:
        print("ERROR: Hugo diagnostic build failed.")
        print(result.stdout)
        print(result.stderr)
        return 1

    print("STEP 2 OF 4: collecting source files...")

    candidate_sources = [
        PROJECT / "content" / "transfers" / "kylian-mbappe-real-madrid" / "index.md",
        PROJECT / "content" / "transfers" / "kylian-mbappe-real-madrid" / "index.before-mbappe-cutout.md",
        PROJECT / "layouts" / "index.html",
        PROJECT / "layouts" / "players" / "single.html",
        PROJECT / "layouts" / "transfers" / "single.html",
        PROJECT / "layouts" / "_default" / "baseof.html",
        PROJECT / "layouts" / "_default" / "single.html",
        PROJECT / "static" / "js" / "transfer-player-market-value-chart.js",
        PROJECT / "static" / "css" / "transfer-player-market-value-chart.css",
    ]

    for source in candidate_sources:
        if source.exists():
            copy_file(source, COLLECT_DIR)

    for source in (PROJECT / "layouts").rglob("*.html"):
        copy_file(source, COLLECT_DIR)

    print("STEP 3 OF 4: locating the real built Mbappe page...")

    matched_pages: list[Path] = []
    reports = []

    for html_file in BUILD_DIR.rglob("*.html"):
        html = safe_read(html_file)

        if not contains_mbappe(html):
            continue

        matched_pages.append(html_file)

        relative = html_file.relative_to(BUILD_DIR)
        destination = (
            COLLECT_DIR
            / "built_pages"
            / relative
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(html_file, destination)

        report = {
            "built_path": str(relative),
            "title": (
                re.search(
                    r"<title>(.*?)</title>",
                    html,
                    flags=re.IGNORECASE | re.DOTALL,
                ).group(1).strip()
                if re.search(
                    r"<title>(.*?)</title>",
                    html,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                else ""
            ),
            "has_player_brief": "player-brief" in html,
            "has_market_chart_html": "player-market-chart" in html,
            "has_market_chart_js": (
                "transfer-player-market-value-chart.js"
                in html
            ),
            "has_market_chart_css": (
                "transfer-player-market-value-chart.css"
                in html
            ),
            "classes": extract_classes(html),
        }
        reports.append(report)

    report_payload = {
        "generated_at": datetime.now().isoformat(),
        "matched_page_count": len(matched_pages),
        "matched_pages": reports,
    }

    (COLLECT_DIR / "mbappe_page_report.json").write_text(
        json.dumps(
            report_payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if not matched_pages:
        print(
            "ERROR: no built HTML page containing Mbappe "
            "was found."
        )
        return 1

    print(
        "Matched built pages: "
        + str(len(matched_pages))
    )

    print("STEP 4 OF 4: creating diagnostic ZIP...")

    with zipfile.ZipFile(
        ZIP_PATH,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for file in sorted(COLLECT_DIR.rglob("*")):
            if file.is_file():
                archive.write(
                    file,
                    arcname=file.relative_to(COLLECT_DIR).as_posix(),
                )

    if not ZIP_PATH.exists():
        print("ERROR: diagnostic ZIP was not created.")
        return 1

    print()
    print("DONE")
    print("Diagnostic ZIP created:")
    print(str(ZIP_PATH))
    print()
    print("Upload this ZIP into the ChatGPT conversation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
