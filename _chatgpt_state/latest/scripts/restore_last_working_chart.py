
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

CSS = (
    PROJECT
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)

HELPER_JS = '    const extendFinalTransferSegment = (chart) => {\n        const coordinates = chart.coordinates.map(\n            (point) => ({ ...point })\n        );\n\n        if (coordinates.length < 2) {\n            return chart;\n        }\n\n        const lastIndex = coordinates.length - 1;\n        const previous = coordinates[lastIndex - 1];\n        const originalLast = coordinates[lastIndex];\n\n        const edgeX = 312;\n        const bottom = 122;\n        const horizontalDistance = Math.max(\n            1,\n            originalLast.x - previous.x\n        );\n        const extensionRatio = Math.max(\n            0,\n            (edgeX - originalLast.x)\n            / horizontalDistance\n        );\n        const trendDelta =\n            originalLast.y - previous.y;\n        const naturalShift =\n            trendDelta * extensionRatio;\n        const visualShift = Math.max(\n            -5,\n            Math.min(\n                5,\n                trendDelta * 0.12\n            )\n        );\n        const edgeY = Math.max(\n            16,\n            Math.min(\n                bottom - 8,\n                originalLast.y\n                + naturalShift\n                + visualShift\n            )\n        );\n\n        coordinates[lastIndex] = {\n            ...originalLast,\n            x: edgeX,\n            y: Number(edgeY.toFixed(2)),\n        };\n\n        const line = coordinates\n            .map((point, index) =>\n                `${index === 0 ? "M" : "L"} `\n                + `${point.x} ${point.y}`\n            )\n            .join(" ");\n\n        const last = coordinates[lastIndex];\n        const area =\n            `${line} L ${last.x} ${bottom} `\n            + `L ${coordinates[0].x} ${bottom} Z`;\n\n        return {\n            ...chart,\n            coordinates,\n            line,\n            area,\n        };\n    };\n\n'
LAST_LOGO_CLASS = '            marker.className =\n                "player-market-chart__club-marker";\n\n            if (index === player.points.length - 1) {\n                marker.classList.add(\n                    "player-market-chart__club-marker--last"\n                );\n            }\n'
LAST_LOGO_CSS = '\n/* PROFUTBIK LAST CHART LOGO INSET V40 START */\n\nbody.transfer-page\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            calc(-50% - 14px),\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n.player-market-chart-modal\n.player-market-chart--enlarged\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            calc(-50% - 24px),\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n/* PROFUTBIK LAST CHART LOGO INSET V40 END */\n'

HELPER_START = "    const extendFinalTransferSegment = (chart) => {"
CREATE_MARKER = "    const createChart = () => {"

CSS_START = "/* PROFUTBIK LAST CHART LOGO INSET V40 START */"
CSS_END = "/* PROFUTBIK LAST CHART LOGO INSET V40 END */"


def remove_bat37_code(text: str) -> str:
    start_marker = (
        "        const visualCoordinates = "
        "coordinates.slice();"
    )
    line_marker = "        const line = visualCoordinates"

    while start_marker in text:
        start = text.find(start_marker)
        line_start = text.find(line_marker, start)

        if line_start < 0:
            raise RuntimeError(
                "BAT 37 block starts but cannot be closed safely."
            )

        line_end = line_start + len(line_marker)

        text = (
            text[:start]
            + "        const line = coordinates"
            + text[line_end:]
        )

    text = text.replace(
        "coordinates: visualCoordinates,",
        "coordinates,",
    )
    text = text.replace(
        "visualCoordinates[visualCoordinates.length - 1]",
        "coordinates[coordinates.length - 1]",
    )
    text = text.replace(
        "visualCoordinates[0].x",
        "coordinates[0].x",
    )

    return text


def remove_existing_helper(text: str) -> str:
    while HELPER_START in text:
        start = text.find(HELPER_START)
        end = text.find(CREATE_MARKER, start)

        if end < 0:
            raise RuntimeError(
                "Existing helper cannot be isolated safely."
            )

        text = text[:start] + text[end:]

    return text


def unwrap_geometry_call(text: str) -> str:
    text = text.replace(
        "extendFinalTransferSegment(geometry(player.points))",
        "geometry(player.points)",
    )

    text = text.replace(
        "extendFinalTransferSegment(\n"
        "            geometry(player.points)\n"
        "        )",
        "geometry(player.points)",
    )

    return text


def remove_old_fade(text: str) -> str:
    fade_id = (
        'id="pf-market-fade-'
        '${escapeHTML(player.key)}"'
    )

    if fade_id in text:
        marker_pos = text.find(fade_id)
        start = text.rfind("<linearGradient", 0, marker_pos)
        end_marker = text.find("</mask>", marker_pos)

        if start >= 0 and end_marker >= 0:
            end = end_marker + len("</mask>")
            text = text[:start] + text[end:]

    mask_attr = (
        'mask="url(#pf-market-mask-'
        '${escapeHTML(player.key)})"'
    )

    text = text.replace(mask_attr, "")

    return text


def ensure_euro_spacing(text: str) -> str:
    spaced = (
        '                <strong>${escapeHTML(\n'
        '                    item.value_label.replace(/^€\\s*/, "€\\u202F")\n'
        '                )}</strong>'
    )

    plain = (
        '                <strong>'
        '${escapeHTML(item.value_label)}'
        '</strong>'
    )

    if spaced in text:
        return text

    if plain in text:
        return text.replace(plain, spaced, 1)

    return text


def install_helper(text: str) -> str:
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

    raise RuntimeError(
        "geometry(player.points) call was not found."
    )


def ensure_last_logo_class(text: str) -> str:
    class_name = "player-market-chart__club-marker--last"

    if class_name in text:
        start = text.find(
            "            if (index === player.points.length - 1)"
        )
        if start >= 0:
            end = text.find("            }", start)
            if end >= 0:
                end += len("            }")
                text = text[:start] + text[end:]

    multiline = (
        '            marker.className =\n'
        '                "player-market-chart__club-marker";\n'
    )

    compact = (
        '            marker.className = '
        '"player-market-chart__club-marker";'
    )

    if multiline in text:
        return text.replace(
            multiline,
            LAST_LOGO_CLASS,
            1,
        )

    if compact in text:
        return text.replace(
            compact,
            LAST_LOGO_CLASS.rstrip(),
            1,
        )

    raise RuntimeError(
        "Club-marker creation block was not found."
    )


def patch_javascript(text: str) -> str:
    text = remove_bat37_code(text)
    text = remove_existing_helper(text)
    text = unwrap_geometry_call(text)
    text = remove_old_fade(text)
    text = ensure_euro_spacing(text)
    text = install_helper(text)
    text = ensure_last_logo_class(text)

    text, count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "40-restored-last-working-chart";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "Chart version marker was not found."
        )

    return text


def patch_css(text: str) -> str:
    blocks = [
        (
            "/* PROFUTBIK LAST CHART LOGO INSET V39 START */",
            "/* PROFUTBIK LAST CHART LOGO INSET V39 END */",
        ),
        (
            "/* PROFUTBIK LAST CHART LOGO INSET V40 START */",
            "/* PROFUTBIK LAST CHART LOGO INSET V40 END */",
        ),
    ]

    for start, end in blocks:
        while start in text and end in text:
            block_start = text.find(start)
            block_end = text.find(end, block_start) + len(end)
            text = text[:block_start] + text[block_end:]

    return text.rstrip() + "\n\n" + LAST_LOGO_CSS.strip() + "\n"


def validate_source(js_text: str, css_text: str) -> None:
    required = [
        'const VERSION = "40-restored-last-working-chart";',
        "const extendFinalTransferSegment",
        "const edgeX = 312;",
        "extendFinalTransferSegment(geometry(player.points))",
        "player-market-chart__club-marker--last",
        "index === player.points.length - 1",
        CSS_START,
        "calc(-50% - 14px)",
        "calc(-50% - 24px)",
    ]

    missing = [
        marker
        for marker in required
        if marker not in js_text
        and marker not in css_text
    ]

    if missing:
        raise RuntimeError(
            "Restored files are missing: "
            + ", ".join(missing)
        )

    forbidden = [
        "const visualCoordinates = coordinates.slice();",
        "const line = visualCoordinates",
        "coordinates: visualCoordinates,",
        'id="pf-market-fade-${escapeHTML(player.key)}"',
        'mask="url(#pf-market-mask-${escapeHTML(player.key)})"',
    ]

    found = [
        marker
        for marker in forbidden
        if marker in js_text
    ]

    if found:
        raise RuntimeError(
            "Old BAT 37 code remains: "
            + ", ".join(found)
        )

    if js_text.count(HELPER_START) != 1:
        raise RuntimeError(
            "Clean chart helper count is not 1."
        )

    if css_text.count(CSS_START) != 1:
        raise RuntimeError(
            "Final-logo CSS block count is not 1."
        )


def validate_node() -> None:
    node = shutil.which("node")

    if not node:
        return

    result = subprocess.run(
        [node, "--check", str(JS)],
        cwd=PROJECT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "JavaScript syntax check failed."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_restore_chart_"
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
        built_css = (
            destination
            / "css"
            / "transfer-player-market-value-chart.css"
        )

        if not built_js.exists() or not built_css.exists():
            raise RuntimeError(
                "Built chart assets were not found."
            )

        validate_source(
            built_js.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ),
            built_css.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ),
        )


def main() -> int:
    for path in (JS, CSS):
        if not path.exists():
            print("ERROR: required chart file not found:")
            print(path)
            return 1

    old_js = JS.read_bytes()
    old_css = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 4: removing repeated "
            "BAT 37 code..."
        )

        new_js = patch_javascript(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )
        new_css = patch_css(
            CSS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        JS.write_text(
            new_js,
            encoding="utf-8",
            newline="\n",
        )
        CSS.write_text(
            new_css,
            encoding="utf-8",
            newline="\n",
        )

        print(
            "STEP 2 OF 4: restoring the "
            "last working chart..."
        )

        validate_source(new_js, new_css)

        print(
            "STEP 3 OF 4: checking JavaScript "
            "syntax when Node is available..."
        )

        validate_node()

        print(
            "STEP 4 OF 4: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("GRAPH RESTORED")
        print("ALL REPEATED BAT 37 CODE REMOVED")
        print("FINAL SEGMENT RESTORED")
        print("FINAL LOGO KEPT INSIDE THE BLOCK")
        print("EURO-PRICE GAP PRESERVED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring files from before "
            "this recovery attempt..."
        )

        JS.write_bytes(old_js)
        CSS.write_bytes(old_css)

        print("Previous files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
