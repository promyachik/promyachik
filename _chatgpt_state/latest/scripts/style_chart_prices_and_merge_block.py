from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

CSS = (
    PROJECT
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)

MARKER_START = "/* PROFUTBIK CHART PRICE STYLE V33 START */"
MARKER_END = "/* PROFUTBIK CHART PRICE STYLE V33 END */"

FONT_IMPORT = (
    '@import url("https://fonts.googleapis.com/css2?'
    'family=Russo+One&display=swap");'
)

OVERRIDE = '\n/* PROFUTBIK CHART PRICE STYLE V33 START */\n\n/*\n * Join the chart directly to the information separator\n * under the final player-detail row.\n */\nbody.transfer-page\n.player-brief__list {\n    margin-bottom: 0 !important;\n}\n\nbody.transfer-page\n.player-brief__list + .player-market-chart,\nbody.transfer-page\n.player-brief dl + .player-market-chart {\n    margin-top: 0 !important;\n    padding-top: 0 !important;\n    border-top: 0 !important;\n}\n\nbody.transfer-page\n.player-brief__list + .player-market-chart\n.player-market-chart__canvas,\nbody.transfer-page\n.player-brief dl + .player-market-chart\n.player-market-chart__canvas {\n    border-top: 0 !important;\n    border-top-left-radius: 0 !important;\n    border-top-right-radius: 0 !important;\n}\n\nbody.transfer-page\n.player-brief,\nbody.transfer-page\n.transfer-side-column,\nbody.transfer-page\n.player-market-chart {\n    height: auto !important;\n    min-height: 0 !important;\n    max-height: none !important;\n    overflow: visible !important;\n}\n\n/*\n * Keep years restrained and make only progression prices\n * use the stronger sports-style display face.\n */\nbody.transfer-page\n.player-market-chart__point small {\n    font-family:\n        "Montserrat",\n        Arial,\n        sans-serif;\n    letter-spacing: 0.015em;\n}\n\nbody.transfer-page\n.player-market-chart__point strong {\n    font-family:\n        "Russo One",\n        "Montserrat",\n        Arial,\n        sans-serif;\n    font-size: 9px;\n    font-weight: 400;\n    line-height: 1.15;\n    letter-spacing: 0.01em;\n    color: #f1f3f5;\n    text-shadow:\n        0 0 8px rgba(231, 198, 91, 0.14);\n}\n\n.player-market-chart-modal\n.player-market-chart--enlarged\n.player-market-chart__point strong {\n    font-size: 16px;\n    letter-spacing: 0.015em;\n    text-shadow:\n        0 0 12px rgba(231, 198, 91, 0.18);\n}\n\n/* PROFUTBIK CHART PRICE STYLE V33 END */\n'


def remove_previous_override(text: str) -> str:
    pattern = re.compile(
        re.escape(MARKER_START)
        + r".*?"
        + re.escape(MARKER_END),
        flags=re.DOTALL,
    )

    return pattern.sub("", text).rstrip()


def insert_font_import(text: str) -> str:
    if FONT_IMPORT in text:
        return text

    charset_pattern = re.compile(
        r'\A@charset\s+"[^"]+";\s*',
        flags=re.IGNORECASE,
    )

    match = charset_pattern.match(text)

    if match:
        return (
            text[:match.end()]
            + "\n"
            + FONT_IMPORT
            + "\n\n"
            + text[match.end():].lstrip()
        )

    return FONT_IMPORT + "\n\n" + text


def patch_css(text: str) -> str:
    text = remove_previous_override(text)
    text = insert_font_import(text)

    return (
        text.rstrip()
        + "\n\n"
        + OVERRIDE.strip()
        + "\n"
    )


def validate_source(text: str) -> None:
    required = [
        FONT_IMPORT,
        MARKER_START,
        MARKER_END,
        '"Russo One"',
        "margin-top: 0 !important",
        "padding-top: 0 !important",
        "border-top-left-radius: 0 !important",
        "font-size: 16px",
    ]

    missing = [
        marker
        for marker in required
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            "Updated chart CSS is missing: "
            + ", ".join(missing)
        )

    if text.count(MARKER_START) != 1:
        raise RuntimeError(
            "The V33 chart style block appears "
            "more than once."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_chart_price_style_"
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

        built_css = (
            destination
            / "css"
            / "transfer-player-market-value-chart.css"
        )

        if not built_css.exists():
            raise RuntimeError(
                "Built market-chart CSS was not found."
            )

        validate_source(
            built_css.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )


def main() -> int:
    if not CSS.exists():
        print("ERROR: market-chart CSS not found:")
        print(CSS)
        return 1

    previous = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: applying Russo One "
            "to progression prices..."
        )

        updated = patch_css(
            CSS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        CSS.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        print(
            "STEP 2 OF 3: joining the chart "
            "to the player information separator..."
        )

        validate_source(updated)

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("RUSSO ONE APPLIED TO CHART PRICES")
        print("CHART JOINED TO PLAYER INFORMATION BLOCK")
        print("EXTRA GAP AND TOP CLIPPING REMOVED")
        print("ZOOMED CHART PRICE STYLE UPDATED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring the previous chart CSS...")

        CSS.write_bytes(previous)

        print("Previous chart CSS restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
