from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TEMPLATE = PROJECT / "layouts" / "players" / "single.html"
PARTIAL = (
    PROJECT
    / "layouts"
    / "partials"
    / "mbappe-player-market-value-chart.html"
)
BUILD = PROJECT / "var" / "mbappe_direct_chart_build"
BACKUP = (
    PROJECT
    / "var"
    / (
        "mbappe_direct_chart_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
)

MARKER = '{{ partial "mbappe-player-market-value-chart.html" . }}'


def restore() -> None:
    backup_file = BACKUP / "layouts" / "players" / "single.html"

    if backup_file.exists():
        TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, TEMPLATE)


def main() -> int:
    for required in (TEMPLATE, PARTIAL):
        if not required.exists():
            print(
                "ERROR: required file not found: "
                + str(required)
            )
            return 1

    BACKUP.mkdir(parents=True, exist_ok=True)
    backup_file = BACKUP / "layouts" / "players" / "single.html"
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, backup_file)

    try:
        text = TEMPLATE.read_text(
            encoding="utf-8-sig",
            errors="strict",
        )
        original = text

        body_match = re.search(
            r"<body(?:\s[^>]*)?>",
            text,
            flags=re.IGNORECASE,
        )

        if not body_match:
            raise RuntimeError(
                "Opening body tag was not found."
            )

        body_tag = body_match.group(0)

        if "transfer-page" not in body_tag:
            if "class=" in body_tag.casefold():
                updated_body = re.sub(
                    r'class\s*=\s*"([^"]*)"',
                    lambda match: (
                        'class="'
                        + match.group(1)
                        + ' transfer-page player-profile-page"'
                    ),
                    body_tag,
                    count=1,
                    flags=re.IGNORECASE,
                )
            else:
                updated_body = (
                    body_tag[:-1]
                    + ' class="transfer-page player-profile-page">'
                )

            text = (
                text[:body_match.start()]
                + updated_body
                + text[body_match.end():]
            )

        if MARKER not in text:
            player_text_marker = '<div class="player-text">'

            position = text.find(player_text_marker)

            if position < 0:
                raise RuntimeError(
                    'Block <div class="player-text"> was not found.'
                )

            insertion = (
                '{{ if eq .Title "Kylian Mbappé" }}\n'
                + MARKER
                + "\n{{ end }}\n\n"
            )

            text = (
                text[:position]
                + insertion
                + text[position:]
            )

        if text != original:
            TEMPLATE.write_text(
                text,
                encoding="utf-8",
                newline="\n",
            )

        hugo = shutil.which("hugo")

        if not hugo:
            raise RuntimeError(
                "Hugo was not found in PATH."
            )

        if BUILD.exists():
            shutil.rmtree(BUILD)

        print(
            "Building the Mbappe player page "
            "with a direct chart..."
        )

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

        built_page = (
            BUILD
            / "players"
            / "mbappe"
            / "index.html"
        )

        if not built_page.exists():
            raise RuntimeError(
                "Built Mbappe player page was not found: "
                + str(built_page)
            )

        html = built_page.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        required_markers = [
            'data-market-chart-key="mbappe"',
            "ДИНАМИКА СТОИМОСТИ",
            "€180 млн",
            "player-market-chart__canvas",
        ]

        missing = [
            marker
            for marker in required_markers
            if marker not in html
        ]

        if missing:
            raise RuntimeError(
                "The built Mbappe page is missing: "
                + ", ".join(missing)
            )

        chart_position = html.find(
            'data-market-chart-key="mbappe"'
        )
        info_position = html.find(
            'class="player-info"'
        )
        text_position = html.find(
            'class="player-text"'
        )

        if not (
            info_position >= 0
            and chart_position > info_position
            and text_position > chart_position
        ):
            raise RuntimeError(
                "The chart is not located between "
                "player-info and player-text."
            )

        print()
        print("DONE")
        print("MBAPPE DIRECT MARKET CHART INSTALLED")
        print(
            "Validated page: "
            "players\\mbappe\\index.html"
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring layouts\\players\\single.html..."
        )
        restore()
        print("Previous template state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
