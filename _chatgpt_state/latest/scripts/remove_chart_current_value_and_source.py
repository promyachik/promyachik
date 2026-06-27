from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)


def patch_javascript(text: str) -> str:
    updated = re.sub(
        r'\s*<strong\s+class="player-market-chart__current">\s*.*?\s*</strong>',
        "",
        text,
        flags=re.DOTALL,
    )

    updated = re.sub(
        r'\s*<a\s+class="player-market-chart__source".*?</a>',
        "",
        updated,
        flags=re.DOTALL,
    )

    updated = re.sub(
        r'const VERSION = "[^"]+";',
        'const VERSION = "25-clean-chart-header";',
        updated,
        count=1,
    )

    return updated


def check_javascript(text: str, location: str) -> None:
    forbidden = [
        'class="player-market-chart__current"',
        'class="player-market-chart__source"',
        ">Transfermarkt<",
    ]

    found = [
        marker
        for marker in forbidden
        if marker in text
    ]

    if found:
        raise RuntimeError(
            location
            + " still contains removed elements: "
            + ", ".join(found)
        )

    required = [
        "ДИНАМИКА СТОИМОСТИ",
        "player-market-chart__canvas",
        "player-market-chart__points",
        "25-clean-chart-header",
    ]

    missing = [
        marker
        for marker in required
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            location
            + " is missing required chart elements: "
            + ", ".join(missing)
        )


def verify_hugo_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_clean_chart_header_"
    ) as temporary:
        destination = Path(temporary)

        result = subprocess.run(
            [
                hugo,
                "--minify",
                "--destination",
                str(destination),
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

        built_js = (
            destination
            / "js"
            / "transfer-player-market-value-chart.js"
        )

        if not built_js.exists():
            raise RuntimeError(
                "Built chart JavaScript was not found."
            )

        built_text = built_js.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        check_javascript(
            built_text,
            "Built JavaScript",
        )


def main() -> int:
    if not JS.exists():
        print("ERROR: chart JavaScript not found:")
        print(JS)
        return 1

    original = JS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: removing the current "
            "value and source button..."
        )

        source_text = JS.read_text(
            encoding="utf-8-sig",
            errors="strict",
        )

        updated = patch_javascript(
            source_text
        )

        if updated == source_text:
            raise RuntimeError(
                "The JavaScript did not change. "
                "Expected chart header elements "
                "were not found."
            )

        JS.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        print(
            "STEP 2 OF 3: checking the updated "
            "chart JavaScript..."
        )

        check_javascript(
            updated,
            "Source JavaScript",
        )

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        verify_hugo_build()

        print()
        print("DONE")
        print(
            "CURRENT VALUE REMOVED FROM ALL CHARTS"
        )
        print(
            "TRANSFERMARKT BUTTON REMOVED FROM ALL CHARTS"
        )
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring the previous chart "
            "JavaScript..."
        )

        JS.write_bytes(original)

        print("Previous JavaScript restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
