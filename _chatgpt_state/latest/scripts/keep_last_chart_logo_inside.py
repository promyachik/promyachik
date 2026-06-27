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

CLASS_LINE_MULTILINE = '            marker.className =\n                "player-market-chart__club-marker";\n'
CLASS_REPLACEMENT = '            marker.className =\n                "player-market-chart__club-marker";\n\n            if (index === player.points.length - 1) {\n                marker.classList.add(\n                    "player-market-chart__club-marker--last"\n                );\n            }\n'
CSS_BLOCK = '\n/* PROFUTBIK LAST CHART LOGO INSET V39 START */\n\nbody.transfer-page\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            calc(-50% - 14px),\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n.player-market-chart-modal\n.player-market-chart--enlarged\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            calc(-50% - 24px),\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n/* PROFUTBIK LAST CHART LOGO INSET V39 END */\n'

CSS_START = "/* PROFUTBIK LAST CHART LOGO INSET V39 START */"
CSS_END = "/* PROFUTBIK LAST CHART LOGO INSET V39 END */"


def patch_javascript(text: str) -> str:
    text, count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "39-last-logo-inset";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "The chart JavaScript version marker was not found."
        )

    if "player-market-chart__club-marker--last" in text:
        return text

    if CLASS_LINE_MULTILINE in text:
        return text.replace(
            CLASS_LINE_MULTILINE,
            CLASS_REPLACEMENT,
            1,
        )

    compact = (
        '            marker.className = '
        '"player-market-chart__club-marker";'
    )

    if compact in text:
        return text.replace(
            compact,
            CLASS_REPLACEMENT.rstrip(),
            1,
        )

    raise RuntimeError(
        "The club-marker creation block was not found."
    )


def patch_css(text: str) -> str:
    pattern = re.compile(
        re.escape(CSS_START)
        + r".*?"
        + re.escape(CSS_END),
        flags=re.DOTALL,
    )

    text = pattern.sub("", text).rstrip()

    return text + "\n\n" + CSS_BLOCK.strip() + "\n"


def validate_source(
    js_text: str,
    css_text: str,
) -> None:
    required = [
        'const VERSION = "39-last-logo-inset";',
        "index === player.points.length - 1",
        "player-market-chart__club-marker--last",
        CSS_START,
        CSS_END,
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
            "Updated chart files are missing: "
            + ", ".join(missing)
        )

    if css_text.count(CSS_START) != 1:
        raise RuntimeError(
            "The final-logo CSS block appears more than once."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_last_logo_inside_"
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

    previous_js = JS.read_bytes()
    previous_css = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: marking only the final "
            "club logo on the chart..."
        )

        updated_js = patch_javascript(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        print(
            "STEP 2 OF 3: shifting the final logo "
            "inside the right boundary..."
        )

        updated_css = patch_css(
            CSS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        JS.write_text(
            updated_js,
            encoding="utf-8",
            newline="\n",
        )

        CSS.write_text(
            updated_css,
            encoding="utf-8",
            newline="\n",
        )

        validate_source(
            updated_js,
            updated_css,
        )

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("FINAL CLUB LOGO MOVED INSIDE THE CHART")
        print("FINAL LINE AND POINT POSITION UNCHANGED")
        print("NORMAL AND ZOOMED CHARTS UPDATED")
        print("OTHER CLUB LOGOS UNCHANGED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring the previous chart files...")

        JS.write_bytes(previous_js)
        CSS.write_bytes(previous_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
