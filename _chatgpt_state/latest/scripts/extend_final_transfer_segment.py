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

INJECT_BLOCK = '        const visualCoordinates = coordinates.slice();\n\n        if (visualCoordinates.length > 1) {\n            const lastIndex = visualCoordinates.length - 1;\n            const previous = visualCoordinates[lastIndex - 1];\n            const last = visualCoordinates[lastIndex];\n\n            /*\n             * Push the final transfer point close to the right edge\n             * and continue the last trend slightly up or down.\n             * This makes the chart look finished instead of cut off.\n             */\n            const edgeX = 306;\n            const trendShift = Math.max(\n                -6,\n                Math.min(\n                    6,\n                    (last.y - previous.y) * 0.22\n                )\n            );\n            const edgeY = Math.max(\n                16,\n                Math.min(\n                    bottom - 8,\n                    last.y + trendShift\n                )\n            );\n\n            visualCoordinates[lastIndex] = {\n                ...last,\n                x: edgeX,\n                y: Math.round(edgeY),\n            };\n        }\n\n'
OLD_AREA_1 = '        const last = coordinates[coordinates.length - 1];\n\n        /*\n         * End the filled area under the real final point.\n         * A horizontal alpha mask hides the vertical closing edge.\n         */\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n'
OLD_AREA_2 = '        const last = coordinates[coordinates.length - 1];\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n'
NEW_AREA = '        const last =\n            visualCoordinates[visualCoordinates.length - 1];\n\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${visualCoordinates[0].x} ${bottom} Z`;\n'
OLD_LABEL = '                <strong>${escapeHTML(item.value_label)}</strong>'
NEW_LABEL = '                <strong>${escapeHTML(\n                    item.value_label.replace(/^€\\s*/, "€\\u202F")\n                )}</strong>'
FADE_MARKER = 'id="pf-market-fade-${escapeHTML(player.key)}"'
MASK_ATTR_LINE = '                        mask="url(#pf-market-mask-${escapeHTML(player.key)})"\n'


def patch_version(text: str) -> str:
    updated, count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "37-extended-final-segment";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "The chart version marker was not found."
        )

    return updated


def patch_price_spacing(text: str) -> str:
    if NEW_LABEL in text:
        return text

    if OLD_LABEL in text:
        return text.replace(
            OLD_LABEL,
            NEW_LABEL,
            1,
        )

    return text


def patch_visual_coordinates(text: str) -> str:
    if "const visualCoordinates = coordinates.slice();" in text:
        return text

    marker = "        const line = coordinates\n"
    replacement = INJECT_BLOCK + "        const line = visualCoordinates\n"

    if marker not in text:
        raise RuntimeError(
            "The chart line-construction block was not found."
        )

    return text.replace(marker, replacement, 1)


def patch_area(text: str) -> str:
    if OLD_AREA_1 in text:
        return text.replace(OLD_AREA_1, NEW_AREA, 1)

    if OLD_AREA_2 in text:
        return text.replace(OLD_AREA_2, NEW_AREA, 1)

    if (
        "visualCoordinates[visualCoordinates.length - 1]" in text
        and "L ${visualCoordinates[0].x} ${bottom} Z" in text
    ):
        return text

    raise RuntimeError(
        "The filled-area geometry block was not found."
    )


def patch_return_coordinates(text: str) -> str:
    if "coordinates: visualCoordinates," in text:
        return text

    variants = [
        ("coordinates,\n            line,", "coordinates: visualCoordinates,\n            line,"),
        ("coordinates,\r\n            line,", "coordinates: visualCoordinates,\r\n            line,"),
        ("coordinates,\n            area,", "coordinates: visualCoordinates,\n            area,"),
        ("coordinates,\r\n            area,", "coordinates: visualCoordinates,\r\n            area,"),
    ]

    for old, new in variants:
        if old in text:
            return text.replace(old, new, 1)

    raise RuntimeError(
        "The return block with chart coordinates was not found."
    )


def patch_remove_fade(text: str) -> str:
    if FADE_MARKER in text:
        start = text.find("                        <linearGradient\n                            " + FADE_MARKER)
        if start != -1:
            end = text.find("                    </mask>\n", start)
            if end != -1:
                end += len("                    </mask>\n")
                text = text[:start] + text[end:]

    if MASK_ATTR_LINE in text:
        text = text.replace(MASK_ATTR_LINE, "", 1)

    return text


def patch_javascript(text: str) -> str:
    text = patch_version(text)
    text = patch_price_spacing(text)
    text = patch_visual_coordinates(text)
    text = patch_area(text)
    text = patch_return_coordinates(text)
    text = patch_remove_fade(text)
    return text


def validate_source(text: str) -> None:
    required = [
        'const VERSION = "37-extended-final-segment";',
        "const visualCoordinates = coordinates.slice();",
        "const edgeX = 306;",
        "(last.y - previous.y) * 0.22",
        "const line = visualCoordinates",
        "visualCoordinates[visualCoordinates.length - 1]",
        "L ${visualCoordinates[0].x} ${bottom} Z",
        "coordinates: visualCoordinates,",
    ]

    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(
            "Updated chart JavaScript is missing: "
            + ", ".join(missing)
        )

    forbidden = [
        'id="pf-market-fade-${escapeHTML(player.key)}"',
        'mask="url(#pf-market-mask-${escapeHTML(player.key)})"',
    ]

    found = [marker for marker in forbidden if marker in text]
    if found:
        raise RuntimeError(
            "The previous fade-based ending remains: "
            + ", ".join(found)
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")
    if not hugo:
        raise RuntimeError("Hugo was not found in PATH.")

    with tempfile.TemporaryDirectory(
        prefix="profutbik_extend_final_segment_"
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

        built_js = destination / "js" / "transfer-player-market-value-chart.js"
        if not built_js.exists():
            raise RuntimeError("Built chart JavaScript was not found.")

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
        print("STEP 1 OF 3: extending the final transfer segment to the edge...")

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

        print("STEP 2 OF 3: moving the final point and logo to the new visual end...")

        validate_source(updated)

        print("STEP 3 OF 3: building a clean temporary Hugo copy...")

        validate_build()

        print()
        print("DONE")
        print("FINAL TRANSFER SEGMENT EXTENDED TO THE RIGHT EDGE")
        print("LAST POINT AND LOGO SHIFTED TO THE VISUAL END")
        print("LAST SLOPE NOW CONTINUES SLIGHTLY UP OR DOWN")
        print("EURO-PRICE GAP PRESERVED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring the previous chart JavaScript...")

        JS.write_bytes(previous)

        print("Previous chart JavaScript restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
