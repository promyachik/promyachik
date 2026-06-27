from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TEMPLATE = PROJECT / "layouts" / "players" / "single.html"
BUILD = PROJECT / "var" / "mbappe_hardcoded_chart_test"


def remove_build() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)


def main() -> int:
    if not TEMPLATE.exists():
        print("ERROR: template not found:")
        print(TEMPLATE)
        return 1

    source = TEMPLATE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    source_markers = [
        'data-market-chart-key="mbappe"',
        "ДИНАМИКА СТОИМОСТИ",
        'class="transfer-page player-profile-page"',
        'class="player-text"',
    ]

    missing_source = [
        marker
        for marker in source_markers
        if marker not in source
    ]

    if missing_source:
        print("ERROR: replacement template is incomplete:")

        for marker in missing_source:
            print("-", marker)

        return 1

    hugo = shutil.which("hugo")

    if not hugo:
        print("ERROR: Hugo was not found in PATH.")
        return 1

    remove_build()

    print("Building the hardcoded Mbappe chart...")

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
        print(
            "ERROR: Hugo build failed with code "
            + str(result.returncode)
        )
        remove_build()
        return 1

    page = BUILD / "players" / "mbappe" / "index.html"

    if not page.exists():
        print("ERROR: built Mbappe page was not found:")
        print(page)
        remove_build()
        return 1

    html = page.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    built_markers = [
        'data-market-chart-key="mbappe"',
        "ДИНАМИКА СТОИМОСТИ",
        "€180 млн",
        'class="transfer-page player-profile-page"',
    ]

    missing_built = [
        marker
        for marker in built_markers
        if marker not in html
    ]

    if missing_built:
        print("ERROR: built page is missing:")

        for marker in missing_built:
            print("-", marker)

        remove_build()
        return 1

    info_position = html.find('class="player-info"')
    chart_position = html.find(
        'data-market-chart-key="mbappe"'
    )
    text_position = html.find('class="player-text"')

    if not (
        info_position >= 0
        and chart_position > info_position
        and text_position > chart_position
    ):
        print(
            "ERROR: chart is not located between "
            "player-info and player-text."
        )
        remove_build()
        return 1

    remove_build()

    print()
    print("DONE")
    print("MBAPPE HARDCODED CHART VERIFIED")
    print("Temporary test build removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
