from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
LAYOUTS = PROJECT / "layouts"
CSS = PROJECT / "static" / "css" / "transfer-player-market-value-chart.css"
JS = PROJECT / "static" / "js" / "transfer-player-market-value-chart.js"
BUILD = PROJECT / "var" / "runtime_market_chart_build"
BACKUP = PROJECT / "var" / (
    "runtime_market_chart_backup_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)

CSS_MARKER = "transfer-player-market-value-chart.css"
JS_MARKER = "transfer-player-market-value-chart.js"

INJECTION = '''    <link rel="stylesheet" href="{{ "css/transfer-player-market-value-chart.css" | relURL }}">
    <script defer src="{{ "js/transfer-player-market-value-chart.js" | relURL }}"></script>
'''

modified: list[Path] = []


def relative(path: Path) -> Path:
    return path.resolve().relative_to(PROJECT.resolve())


def backup(path: Path) -> None:
    if path in modified:
        return

    destination = BACKUP / relative(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    modified.append(path)


def restore() -> None:
    for path in reversed(modified):
        source = BACKUP / relative(path)

        if source.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, path)


def install_links() -> int:
    changed = 0

    for template in LAYOUTS.rglob("*.html"):
        text = template.read_text(
            encoding="utf-8-sig",
            errors="strict",
        )

        if re.search(r"(?i)</head>", text) is None:
            continue

        if CSS_MARKER in text and JS_MARKER in text:
            continue

        updated = re.sub(
            r"(?i)</head>",
            INJECTION + "\n</head>",
            text,
            count=1,
        )

        if updated != text:
            backup(template)
            template.write_text(
                updated,
                encoding="utf-8",
                newline="\n",
            )
            changed += 1
            print("Connected in: " + str(relative(template)))

    return changed


def run_hugo() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError("Hugo was not found in PATH.")

    if BUILD.exists():
        shutil.rmtree(BUILD)

    result = subprocess.run(
        [
            hugo,
            "--minify",
            "--destination",
            str(BUILD),
            "--baseURL",
            "http://127.0.0.1:1313/promyachik/",
        ],
        cwd=PROJECT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Hugo build failed with code "
            + str(result.returncode)
        )


def validate() -> None:
    html_files = list(BUILD.rglob("*.html"))
    connected_pages = []

    for html_file in html_files:
        html = html_file.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        if (
            JS_MARKER in html
            and CSS_MARKER in html
            and "player-brief" in html
        ):
            connected_pages.append(html_file)

    if len(connected_pages) < 8:
        raise RuntimeError(
            "Expected at least 8 connected transfer pages, found "
            + str(len(connected_pages))
        )

    print(
        "Connected transfer pages found: "
        + str(len(connected_pages))
    )


def main() -> int:
    for required in (LAYOUTS, CSS, JS):
        if not required.exists():
            print("ERROR: required path not found: " + str(required))
            return 1

    BACKUP.mkdir(parents=True, exist_ok=True)

    try:
        print()
        print("STEP 1 OF 3: connecting CSS and JavaScript...")
        changed = install_links()

        if changed == 0:
            print("Links were already present.")

        print("STEP 2 OF 3: building Hugo...")
        run_hugo()

        print("STEP 3 OF 3: checking transfer pages...")
        validate()

        print()
        print("DONE")
        print("RUNTIME CHART CONNECTION READY")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring every modified layout file...")
        restore()
        print("Previous layout state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
