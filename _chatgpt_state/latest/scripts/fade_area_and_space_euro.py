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

V34_BLOCK = '        const first = coordinates[0];\n        const last = coordinates[coordinates.length - 1];\n        const areaLeft = 0;\n        const areaRight = 320;\n\n        /*\n         * Close the filled area at the invisible SVG edges,\n         * not directly below the first and last data points.\n         * This removes the visible vertical cut-off.\n         */\n        const area =\n            `${line} `\n            + `L ${areaRight} ${last.y} `\n            + `L ${areaRight} ${bottom} `\n            + `L ${areaLeft} ${bottom} `\n            + `L ${areaLeft} ${first.y} Z`;\n'
NORMAL_AREA_BLOCK = '        const last = coordinates[coordinates.length - 1];\n\n        /*\n         * End the filled area under the real final point.\n         * A horizontal alpha mask hides the vertical closing edge.\n         */\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n'
GRADIENT_END = '                        </linearGradient>\n                    </defs>\n'
FADE_DEFS = '                        </linearGradient>\n\n                        <linearGradient\n                            id="pf-market-fade-${escapeHTML(player.key)}"\n                            x1="0"\n                            y1="0"\n                            x2="320"\n                            y2="0"\n                            gradientUnits="userSpaceOnUse"\n                        >\n                            <stop\n                                offset="0%"\n                                stop-color="#ffffff"\n                                stop-opacity="1"\n                            ></stop>\n\n                            <stop\n                                offset="86%"\n                                stop-color="#ffffff"\n                                stop-opacity="1"\n                            ></stop>\n\n                            <stop\n                                offset="100%"\n                                stop-color="#ffffff"\n                                stop-opacity="0"\n                            ></stop>\n                        </linearGradient>\n\n                        <mask\n                            id="pf-market-mask-${escapeHTML(player.key)}"\n                            x="0"\n                            y="0"\n                            width="320"\n                            height="150"\n                            maskUnits="userSpaceOnUse"\n                            style="mask-type: alpha;"\n                        >\n                            <rect\n                                x="0"\n                                y="0"\n                                width="320"\n                                height="150"\n                                fill="url(#pf-market-fade-${escapeHTML(player.key)})"\n                            ></rect>\n                        </mask>\n                    </defs>\n'
AREA_PATH = '                    <path\n                        class="player-market-chart__area"\n                        fill="url(#pf-market-gradient-${escapeHTML(player.key)})"\n                        d="${escapeHTML(chart.area)}"\n                    ></path>\n'
MASKED_AREA_PATH = '                    <path\n                        class="player-market-chart__area"\n                        fill="url(#pf-market-gradient-${escapeHTML(player.key)})"\n                        mask="url(#pf-market-mask-${escapeHTML(player.key)})"\n                        d="${escapeHTML(chart.area)}"\n                    ></path>\n'
OLD_LABEL = '                <strong>${escapeHTML(item.value_label)}</strong>'
NEW_LABEL = '                <strong>${escapeHTML(\n                    item.value_label.replace(/^€\\s*/, "€\\u202F")\n                )}</strong>'


def patch_geometry(text: str) -> str:
    if V34_BLOCK in text:
        text = text.replace(
            V34_BLOCK,
            NORMAL_AREA_BLOCK,
            1,
        )

    if (
        "`${line} L ${last.x} ${bottom} `"
        not in text
        or "`L ${coordinates[0].x} ${bottom} Z`"
        not in text
    ):
        raise RuntimeError(
            "The expected final-point area geometry "
            "was not found."
        )

    return text


def patch_fade(text: str) -> str:
    if (
        'id="pf-market-mask-${escapeHTML(player.key)}"'
        not in text
    ):
        if GRADIENT_END not in text:
            raise RuntimeError(
                "The SVG gradient definition was not found."
            )

        text = text.replace(
            GRADIENT_END,
            FADE_DEFS,
            1,
        )

    if (
        'mask="url(#pf-market-mask-${escapeHTML(player.key)})"'
        not in text
    ):
        if AREA_PATH not in text:
            raise RuntimeError(
                "The market-area SVG path was not found."
            )

        text = text.replace(
            AREA_PATH,
            MASKED_AREA_PATH,
            1,
        )

    return text


def patch_price_spacing(text: str) -> str:
    if NEW_LABEL in text:
        return text

    if OLD_LABEL not in text:
        raise RuntimeError(
            "The visible price-label template was not found."
        )

    return text.replace(
        OLD_LABEL,
        NEW_LABEL,
        1,
    )


def patch_javascript(text: str) -> str:
    text, count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "36-fade-area-space-euro";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "The chart version marker was not found."
        )

    text = patch_geometry(text)
    text = patch_fade(text)
    text = patch_price_spacing(text)

    return text


def validate_source(text: str) -> None:
    required = [
        'const VERSION = "36-fade-area-space-euro";',
        "`${line} L ${last.x} ${bottom} `",
        'id="pf-market-fade-${escapeHTML(player.key)}"',
        'id="pf-market-mask-${escapeHTML(player.key)}"',
        'mask="url(#pf-market-mask-${escapeHTML(player.key)})"',
        'offset="86%"',
        'stop-opacity="0"',
        'replace(/^€\\s*/, "€\\u202F")',
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
        "const areaRight = 320;",
        "L ${areaRight} ${last.y}",
        OLD_LABEL,
    ]

    found = [
        marker
        for marker in forbidden
        if marker in text
    ]

    if found:
        raise RuntimeError(
            "Old chart code remains: "
            + ", ".join(found)
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_fade_area_space_euro_"
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
            "STEP 1 OF 4: ending the filled area "
            "at the final chart point..."
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
            "STEP 2 OF 4: applying a horizontal "
            "fade to the right edge..."
        )

        print(
            "STEP 3 OF 4: adding a narrow space "
            "after the euro sign..."
        )

        validate_source(updated)

        print(
            "STEP 4 OF 4: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("MARKET AREA ENDS AT THE FINAL POINT")
        print("RIGHT AREA EDGE FADES OUT HORIZONTALLY")
        print("EURO SIGN AND PRICE NOW HAVE A SMALL GAP")
        print("LINE, POINTS, LOGOS AND YEARS UNCHANGED")
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
