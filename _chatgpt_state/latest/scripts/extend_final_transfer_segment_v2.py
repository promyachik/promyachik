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

HELPER_JS = '    const extendFinalTransferSegment = (chart) => {\n        const coordinates = chart.coordinates.map(\n            (point) => ({ ...point })\n        );\n\n        if (coordinates.length < 2) {\n            return chart;\n        }\n\n        const lastIndex = coordinates.length - 1;\n        const previous = coordinates[lastIndex - 1];\n        const originalLast = coordinates[lastIndex];\n\n        const edgeX = 312;\n        const bottom = 122;\n        const horizontalDistance = Math.max(\n            1,\n            originalLast.x - previous.x\n        );\n        const extensionRatio = Math.max(\n            0,\n            (edgeX - originalLast.x)\n            / horizontalDistance\n        );\n        const trendDelta =\n            originalLast.y - previous.y;\n        const naturalShift =\n            trendDelta * extensionRatio;\n        const visualShift = Math.max(\n            -5,\n            Math.min(\n                5,\n                trendDelta * 0.12\n            )\n        );\n        const edgeY = Math.max(\n            16,\n            Math.min(\n                bottom - 8,\n                originalLast.y\n                + naturalShift\n                + visualShift\n            )\n        );\n\n        coordinates[lastIndex] = {\n            ...originalLast,\n            x: edgeX,\n            y: Number(edgeY.toFixed(2)),\n        };\n\n        const line = coordinates\n            .map((point, index) =>\n                `${index === 0 ? "M" : "L"} `\n                + `${point.x} ${point.y}`\n            )\n            .join(" ");\n\n        const last = coordinates[lastIndex];\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n\n        return {\n            ...chart,\n            coordinates,\n            line,\n            area,\n        };\n    };\n\n'

HELPER_START = "    const extendFinalTransferSegment = (chart) => {"
CREATE_MARKER = "    const createChart = () => {"


def remove_previous_helper(text: str) -> str:
    if HELPER_START not in text:
        return text

    start = text.find(HELPER_START)
    end = text.find(CREATE_MARKER, start)

    if end < 0:
        raise RuntimeError(
            "Previous helper could not be isolated."
        )

    return text[:start] + text[end:]


def remove_old_fade(text: str) -> str:
    fade_id = 'id="pf-market-fade-${escapeHTML(player.key)}"'

    if fade_id in text:
        marker_position = text.find(fade_id)
        start = text.rfind("<linearGradient", 0, marker_position)
        end_marker = text.find("</mask>", marker_position)

        if start >= 0 and end_marker >= 0:
            end = end_marker + len("</mask>")
            text = text[:start] + text[end:]

    mask_pattern = re.compile(
        r'\s*mask=\"url\(\#pf-market-mask-\$\{escapeHTML\(player\.key\)\}\)\"'
    )

    return mask_pattern.sub(
        "",
        text,
        count=1,
    )


def ensure_euro_spacing(text: str) -> str:
    spaced = (
        '                <strong>${escapeHTML(\n'
        '                    item.value_label.replace(/^€\\s*/, "€\\u202F")\n'
        '                )}</strong>'
    )

    if spaced in text:
        return text

    plain = (
        '                <strong>'
        '${escapeHTML(item.value_label)}'
        '</strong>'
    )

    if plain in text:
        return text.replace(plain, spaced, 1)

    return text


def install_helper(text: str) -> str:
    text = remove_previous_helper(text)

    if CREATE_MARKER not in text:
        raise RuntimeError(
            "createChart marker was not found."
        )

    text = text.replace(
        CREATE_MARKER,
        HELPER_JS + CREATE_MARKER,
        1,
    )

    old_call = (
        "        const chart = "
        "geometry(player.points);"
    )

    new_call = (
        "        const chart = "
        "extendFinalTransferSegment("
        "geometry(player.points)"
        ");"
    )

    if old_call in text:
        return text.replace(old_call, new_call, 1)

    if new_call in text:
        return text

    pattern = re.compile(
        r'\s{8}const\s+chart\s*=\s*geometry\(player\.points\)\s*;'
    )

    updated, count = pattern.subn(
        "\n" + new_call,
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "geometry(player.points) call was not found."
        )

    return updated


def patch_javascript(text: str) -> str:
    text, count = re.subn(
        r'const VERSION = \"[^\"]+\";',
        'const VERSION = "38-extended-final-segment-v2";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "Chart version marker was not found."
        )

    text = remove_old_fade(text)
    text = ensure_euro_spacing(text)
    text = install_helper(text)

    return text


def validate_source(text: str) -> None:
    required = [
        'const VERSION = "38-extended-final-segment-v2";',
        "const extendFinalTransferSegment",
        "const edgeX = 312;",
        "trendDelta * 0.12",
        "extendFinalTransferSegment(geometry(player.points))",
        "coordinates,",
        "line,",
        "area,",
    ]

    missing = [
        marker
        for marker in required
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            "Updated JavaScript is missing: "
            + ", ".join(missing)
        )

    forbidden = [
        'id="pf-market-fade-${escapeHTML(player.key)}"',
        'id="pf-market-mask-${escapeHTML(player.key)}"',
        'mask="url(#pf-market-mask-${escapeHTML(player.key)})"',
    ]

    found = [
        marker
        for marker in forbidden
        if marker in text
    ]

    if found:
        raise RuntimeError(
            "Previous fade ending remains: "
            + ", ".join(found)
        )

    if text.count(HELPER_START) != 1:
        raise RuntimeError(
            "Final-segment helper appears an unexpected number of times."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_final_segment_v2_"
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
            "STEP 1 OF 3: installing the robust "
            "final-segment transformer..."
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
            "STEP 2 OF 3: shifting the final "
            "point and logo toward the right edge..."
        )

        validate_source(updated)

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("FINAL TRANSFER SEGMENT EXTENDED TO THE RIGHT EDGE")
        print("LAST POINT AND LOGO SHIFTED TO THE VISUAL END")
        print("FINAL SLOPE CONTINUES SLIGHTLY UP OR DOWN")
        print("OLD FADE ENDING REMOVED")
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
