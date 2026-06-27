from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
PAYLOAD = (
    PROJECT
    / "scripts"
    / "profutbik_enhancement_payload"
)

SOURCE_JS = (
    PAYLOAD
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)
SOURCE_CSS = (
    PAYLOAD
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)

TARGET_JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)
TARGET_CSS = (
    PROJECT
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)


def validate_source() -> None:
    js = SOURCE_JS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
    css = SOURCE_CSS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required_js = [
        "28-full-chart-zoom",
        "player-market-chart-modal",
        "player-market-chart__club-marker",
        "openChartModal(section)",
    ]

    forbidden_js = [
        "club-logo-modal",
        "player-market-chart__club-button",
        "openModal(item, image)",
    ]

    required_css = [
        ".player-market-chart-modal",
        ".player-market-chart__club-marker",
        ".player-market-chart--enlarged",
    ]

    forbidden_css = [
        ".club-logo-modal",
        ".player-market-chart__club-button",
    ]

    missing = [
        item
        for item in required_js
        if item not in js
    ] + [
        item
        for item in required_css
        if item not in css
    ]

    forbidden = [
        item
        for item in forbidden_js
        if item in js
    ] + [
        item
        for item in forbidden_css
        if item in css
    ]

    if missing:
        raise RuntimeError(
            "Corrected payload is missing: "
            + ", ".join(missing)
        )

    if forbidden:
        raise RuntimeError(
            "Old individual-logo modal remains: "
            + ", ".join(forbidden)
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_full_chart_zoom_"
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

        if (
            "28-full-chart-zoom"
            not in built_js.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        ):
            raise RuntimeError(
                "Built site contains an old chart JavaScript."
            )


def main() -> int:
    for required in (
        SOURCE_JS,
        SOURCE_CSS,
        TARGET_JS,
        TARGET_CSS,
    ):
        if not required.exists():
            print("ERROR: required file not found:")
            print(required)
            return 1

    old_js = TARGET_JS.read_bytes()
    old_css = TARGET_CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 3: removing individual "
            "logo popup and gold circles..."
        )
        validate_source()

        shutil.copy2(SOURCE_JS, TARGET_JS)
        shutil.copy2(SOURCE_CSS, TARGET_CSS)

        print(
            "STEP 2 OF 3: enabling full graph "
            "click-to-zoom..."
        )

        print(
            "STEP 3 OF 3: building a clean "
            "temporary Hugo copy..."
        )
        validate_build()

        print()
        print("DONE")
        print("FULL GRAPH CLICK-TO-ZOOM READY")
        print("INDIVIDUAL LOGO POPUP REMOVED")
        print("GOLD LOGO CIRCLES REMOVED")
        print("CLUB LOGOS MOVED 3 PX UP")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring previous chart files...")

        TARGET_JS.write_bytes(old_js)
        TARGET_CSS.write_bytes(old_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
