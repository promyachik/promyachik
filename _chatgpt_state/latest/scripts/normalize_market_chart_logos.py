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


def replace_once(
    text: str,
    old: str,
    new: str,
    description: str,
) -> str:
    if old not in text:
        raise RuntimeError(
            description + " was not found."
        )

    return text.replace(old, new, 1)


def patch_js(text: str) -> str:
    text = replace_once(
        text,
        "`${((coordinate.y - 34) / 150) * 100}%`",
        "`${((coordinate.y - 33) / 150) * 100}%`",
        "The current club-logo vertical offset",
    )

    text = re.sub(
        r'const VERSION = "[^"]+";',
        'const VERSION = "30-normalized-club-logos";',
        text,
        count=1,
    )

    return text


def patch_css(text: str) -> str:
    old_marker = '''body.transfer-page .player-market-chart__club-marker {
    position: absolute;
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    z-index: 3;
    pointer-events: none;
    transform: translate(-50%, -50%);
}'''

    new_marker = '''body.transfer-page .player-market-chart__club-marker {
    --club-logo-size: 27px;
    position: absolute;
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    z-index: 3;
    pointer-events: none;
    transform: translate(-50%, -50%);
}'''

    old_logo = '''body.transfer-page .player-market-chart__club-logo {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
}'''

    new_logo = '''body.transfer-page .player-market-chart__club-logo {
    display: block;
    width: var(--club-logo-size);
    height: var(--club-logo-size);
    min-width: var(--club-logo-size);
    min-height: var(--club-logo-size);
    max-width: var(--club-logo-size);
    max-height: var(--club-logo-size);
    object-fit: contain;
    object-position: center;
}'''

    old_enlarged = '''.player-market-chart-modal
.player-market-chart--enlarged
.player-market-chart__club-marker {
    width: 54px;
    height: 54px;
}'''

    new_enlarged = '''.player-market-chart-modal
.player-market-chart--enlarged
.player-market-chart__club-marker {
    --club-logo-size: 46px;
    width: 54px;
    height: 54px;
}'''

    old_mobile = '''    body.transfer-page .player-market-chart__club-marker {
        width: 29px;
        height: 29px;
    }'''

    new_mobile = '''    body.transfer-page .player-market-chart__club-marker {
        --club-logo-size: 25px;
        width: 29px;
        height: 29px;
    }'''

    old_mobile_enlarged = '''    .player-market-chart-modal
    .player-market-chart--enlarged
    .player-market-chart__club-marker {
        width: 43px;
        height: 43px;
    }'''

    new_mobile_enlarged = '''    .player-market-chart-modal
    .player-market-chart--enlarged
    .player-market-chart__club-marker {
        --club-logo-size: 38px;
        width: 43px;
        height: 43px;
    }'''

    text = replace_once(
        text,
        old_marker,
        new_marker,
        "The normal club-marker CSS block",
    )

    text = replace_once(
        text,
        old_logo,
        new_logo,
        "The club-logo CSS block",
    )

    text = replace_once(
        text,
        old_enlarged,
        new_enlarged,
        "The enlarged-chart club-marker block",
    )

    if old_mobile in text:
        text = text.replace(
            old_mobile,
            new_mobile,
            1,
        )

    if old_mobile_enlarged in text:
        text = text.replace(
            old_mobile_enlarged,
            new_mobile_enlarged,
            1,
        )

    return text


def validate_source(
    js_text: str,
    css_text: str,
) -> None:
    required = [
        "30-normalized-club-logos",
        "coordinate.y - 33",
        "--club-logo-size: 27px",
        "width: var(--club-logo-size)",
        "height: var(--club-logo-size)",
        "--club-logo-size: 46px",
    ]

    missing = [
        marker
        for marker in required
        if marker not in js_text
        and marker not in css_text
    ]

    if missing:
        raise RuntimeError(
            "Updated files are missing: "
            + ", ".join(missing)
        )

    if "coordinate.y - 34" in js_text:
        raise RuntimeError(
            "The previous logo position is still present."
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_equal_chart_logos_"
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

        if not built_js.exists():
            raise RuntimeError(
                "Built chart JavaScript was not found."
            )

        if not built_css.exists():
            raise RuntimeError(
                "Built chart CSS was not found."
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
    for required in (JS, CSS):
        if not required.exists():
            print("ERROR: required file not found:")
            print(required)
            return 1

    original_js = JS.read_bytes()
    original_css = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: setting one equal "
            "size for all chart logos..."
        )

        updated_js = patch_js(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
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

        print(
            "STEP 2 OF 3: moving all chart "
            "logos 1 pixel lower..."
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
        print("ALL MARKET CHART LOGOS HAVE EQUAL SIZE")
        print("ALL MARKET CHART LOGOS MOVED 1 PX DOWN")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring the previous chart files..."
        )

        JS.write_bytes(original_js)
        CSS.write_bytes(original_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
