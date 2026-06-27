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

CSS_START = "/* PROFUTBIK CHART CLEAN LOOK V42 START */"
CSS_END = "/* PROFUTBIK CHART CLEAN LOOK V42 END */"
CSS_BLOCK = '\n/* PROFUTBIK CHART CLEAN LOOK V42 START */\n\n.player-market-chart__area {\n    display: none;\n}\n\nbody.transfer-page\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            -50%,\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n.player-market-chart-modal\n.player-market-chart--enlarged\n.player-market-chart__club-marker--last {\n    transform:\n        translate(\n            -50%,\n            calc(-100% - var(--club-logo-gap))\n        );\n}\n\n/* PROFUTBIK CHART CLEAN LOOK V42 END */\n'


def patch_javascript(text: str) -> str:
    text, count = re.subn(
        r'const VERSION = "[^"]+";',
        'const VERSION = "42-pull-last-point-inside-keep-center";',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "The chart JavaScript version marker was not found."
        )

    required = [
        "extendFinalTransferSegment",
        "const edgeX = 312;",
        "player-market-chart__club-marker--last",
    ]

    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(
            "The current chart JavaScript does not contain expected markers: "
            + ", ".join(missing)
        )

    text = text.replace(
        "const edgeX = 312;",
        "const edgeX = 296;",
        1,
    )

    return text


def remove_old_css_blocks(text: str) -> str:
    blocks = [
        (
            "/* PROFUTBIK LAST CHART LOGO INSET V39 START */",
            "/* PROFUTBIK LAST CHART LOGO INSET V39 END */",
        ),
        (
            "/* PROFUTBIK LAST CHART LOGO INSET V40 START */",
            "/* PROFUTBIK LAST CHART LOGO INSET V40 END */",
        ),
        (
            "/* PROFUTBIK CHART CLEAN LOOK V41 START */",
            "/* PROFUTBIK CHART CLEAN LOOK V41 END */",
        ),
        (
            "/* PROFUTBIK CHART CLEAN LOOK V42 START */",
            "/* PROFUTBIK CHART CLEAN LOOK V42 END */",
        ),
    ]

    for start, end in blocks:
        pattern = re.compile(
            re.escape(start) + r".*?" + re.escape(end),
            flags=re.DOTALL,
        )
        text = pattern.sub("", text)

    return text.rstrip()


def patch_css(text: str) -> str:
    text = remove_old_css_blocks(text)
    return text + "\n\n" + CSS_BLOCK.strip() + "\n"


def validate_source(js_text: str, css_text: str) -> None:
    required_js = [
        'const VERSION = "42-pull-last-point-inside-keep-center";',
        "extendFinalTransferSegment",
        "const edgeX = 296;",
        "player-market-chart__club-marker--last",
    ]

    missing_js = [
        marker for marker in required_js
        if marker not in js_text
    ]

    if missing_js:
        raise RuntimeError(
            "Updated JavaScript is missing: "
            + ", ".join(missing_js)
        )

    forbidden_js = [
        "const edgeX = 312;",
    ]

    found_js = [
        marker for marker in forbidden_js
        if marker in js_text
    ]

    if found_js:
        raise RuntimeError(
            "Old last-point position still remains: "
            + ", ".join(found_js)
        )

    required_css = [
        CSS_START,
        CSS_END,
        ".player-market-chart__area",
        "display: none;",
        "calc(-100% - var(--club-logo-gap))",
    ]

    missing_css = [
        marker for marker in required_css
        if marker not in css_text
    ]

    if missing_css:
        raise RuntimeError(
            "Updated CSS is missing: "
            + ", ".join(missing_css)
        )

    forbidden_css = [
        "calc(-50% - 14px)",
        "calc(-50% - 24px)",
    ]

    found_css = [
        marker for marker in forbidden_css
        if marker in css_text
    ]

    if found_css:
        raise RuntimeError(
            "Old logo inset values still remain: "
            + ", ".join(found_css)
        )

    if css_text.count(CSS_START) != 1:
        raise RuntimeError(
            "The V42 CSS block appears an unexpected number of times."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError("Hugo was not found in PATH.")

    with tempfile.TemporaryDirectory(
        prefix="profutbik_chart_v42_"
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
        built_css = destination / "css" / "transfer-player-market-value-chart.css"

        if not built_js.exists() or not built_css.exists():
            raise RuntimeError("Built chart assets were not found.")

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
            "STEP 1 OF 3: moving the final point slightly "
            "inside the block..."
        )

        new_js = patch_javascript(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        print(
            "STEP 2 OF 3: keeping the final logo centered "
            "over that point and preserving the clean look..."
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

        validate_source(new_js, new_css)

        print(
            "STEP 3 OF 3: building a clean temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("FINAL POINT MOVED SLIGHTLY INSIDE THE BLOCK")
        print("FINAL LOGO REMAINS CENTERED OVER ITS POINT")
        print("YELLOW FILLED TRAIL REMAINS HIDDEN")
        print("NORMAL AND ZOOMED CHARTS UPDATED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring the previous chart files...")

        JS.write_bytes(old_js)
        CSS.write_bytes(old_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
