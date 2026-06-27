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

OLD_BLOCK = '        const last = coordinates[coordinates.length - 1];\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n'
NEW_BLOCK = '        const first = coordinates[0];\n        const last = coordinates[coordinates.length - 1];\n        const areaLeft = 0;\n        const areaRight = 320;\n\n        /*\n         * Close the filled area at the invisible SVG edges,\n         * not directly below the first and last data points.\n         * This removes the visible vertical cut-off.\n         */\n        const area =\n            `${line} `\n            + `L ${areaRight} ${last.y} `\n            + `L ${areaRight} ${bottom} `\n            + `L ${areaLeft} ${bottom} `\n            + `L ${areaLeft} ${first.y} Z`;\n'


def patch_javascript(text: str) -> str:
    text, version_count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "34-smooth-area-edges";',
        text,
        count=1,
    )

    if version_count != 1:
        raise RuntimeError(
            "The chart JavaScript version marker "
            "was not found."
        )

    if OLD_BLOCK in text:
        return text.replace(
            OLD_BLOCK,
            NEW_BLOCK,
            1,
        )

    if (
        "const areaRight = 320;"
        in text
        and "L ${areaRight} ${last.y}"
        in text
    ):
        return text

    raise RuntimeError(
        "The current filled-area geometry block "
        "was not found."
    )


def validate_source(text: str) -> None:
    required = [
        'const VERSION = "34-smooth-area-edges";',
        "const areaLeft = 0;",
        "const areaRight = 320;",
        "L ${areaRight} ${last.y}",
        "L ${areaLeft} ${first.y} Z",
    ]

    missing = [
        marker
        for marker in required
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            "Updated chart JavaScript is missing: "
            + ", ".join(missing)
        )

    forbidden = [
        "`${line} L ${last.x} ${bottom} `",
        "`L ${coordinates[0].x} ${bottom} Z`",
    ]

    found = [
        marker
        for marker in forbidden
        if marker in text
    ]

    if found:
        raise RuntimeError(
            "The old visible area cut-off remains: "
            + ", ".join(found)
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_smooth_area_edge_"
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

        validate_source(
            built_js.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )


def main() -> int:
    if not JS.exists():
        print("ERROR: chart JavaScript not found:")
        print(JS)
        return 1

    previous = JS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: moving the filled-area "
            "closing edges outside the visible plot..."
        )

        updated = patch_javascript(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        JS.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        print(
            "STEP 2 OF 3: checking that the "
            "vertical cut-off was removed..."
        )

        validate_source(updated)

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("MARKET CHART AREA EDGE FIXED")
        print("VISIBLE VERTICAL CUT-OFF REMOVED")
        print("LINE, POINTS, LOGOS AND PRICE STYLE UNCHANGED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring the previous chart JavaScript..."
        )

        JS.write_bytes(previous)

        print("Previous chart JavaScript restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
