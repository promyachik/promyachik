from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
BUILD = PROJECT / "var" / "mbappe_exact_chart_test"
TEMPLATE = PROJECT / "layouts" / "players" / "single.html"
PARTIAL = (
    PROJECT
    / "layouts"
    / "partials"
    / "mbappe-player-market-value-chart.html"
)


def main() -> int:
    for path in (TEMPLATE, PARTIAL):
        if not path.exists():
            print("ERROR: required file not found:")
            print(path)
            return 1

    template = TEMPLATE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required_template_markers = [
        'class="transfer-page player-profile-page"',
        'strings.Contains .RelPermalink "/players/mbappe/"',
        'partial "mbappe-player-market-value-chart.html"',
    ]

    for marker in required_template_markers:
        if marker not in template:
            print("ERROR: template marker is missing:")
            print(marker)
            return 1

    hugo = shutil.which("hugo")

    if not hugo:
        print("ERROR: Hugo was not found in PATH.")
        return 1

    if BUILD.exists():
        shutil.rmtree(BUILD)

    print("Building the exact Mbappe player page fix...")

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
        return 1

    page = BUILD / "players" / "mbappe" / "index.html"

    if not page.exists():
        print("ERROR: built Mbappe page was not found:")
        print(page)
        return 1

    html = page.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required_html_markers = [
        'data-market-chart-key="mbappe"',
        "ДИНАМИКА СТОИМОСТИ",
        "€180 млн",
        'class="transfer-page player-profile-page"',
    ]

    missing = [
        marker
        for marker in required_html_markers
        if marker not in html
    ]

    if missing:
        print("ERROR: built page is missing:")
        for marker in missing:
            print("-", marker)
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
            "ERROR: chart is not between "
            "player-info and player-text."
        )
        return 1

    shutil.rmtree(BUILD)

    print()
    print("DONE")
    print("MBAPPE EXACT PAGE CHART VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
