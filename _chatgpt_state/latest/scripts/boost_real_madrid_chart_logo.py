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


def patch_js(text: str) -> str:
    marker = '''            marker.className =
                "player-market-chart__club-marker";
'''

    replacement = '''            marker.className =
                "player-market-chart__club-marker";

            marker.dataset.clubSlug = item.club.slug;
'''

    if 'marker.dataset.clubSlug = item.club.slug;' not in text:
        if marker not in text:
            raise RuntimeError(
                "Club marker creation block was not found."
            )

        text = text.replace(
            marker,
            replacement,
            1,
        )

    text = re.sub(
        r'const VERSION = "[^"]+";',
        'const VERSION = "32-real-madrid-logo-boost";',
        text,
        count=1,
    )

    return text


def patch_css(text: str) -> str:
    rule = '''
body.transfer-page
.player-market-chart__club-marker[data-club-slug="real-madrid"]
.player-market-chart__club-logo {
    transform: scale(1.12);
    transform-origin: center;
}
'''

    if rule.strip() not in text:
        text = text.rstrip() + "\n" + rule

    return text


def validate_source(
    js_text: str,
    css_text: str,
) -> None:
    required = [
        "32-real-madrid-logo-boost",
        "marker.dataset.clubSlug = item.club.slug",
        '[data-club-slug="real-madrid"]',
        "transform: scale(1.12)",
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


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_real_logo_boost_"
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
            print("ERROR: required file not found:")
            print(path)
            return 1

    old_js = JS.read_bytes()
    old_css = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: adding a club identifier "
            "to every chart logo..."
        )

        new_js = patch_js(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        print(
            "STEP 2 OF 3: increasing only the "
            "Real Madrid logo by 12 percent..."
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
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("REAL MADRID CHART LOGO ENLARGED BY 12 PERCENT")
        print("OTHER CLUB LOGOS WERE NOT CHANGED")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring previous chart files...")

        JS.write_bytes(old_js)
        CSS.write_bytes(old_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
