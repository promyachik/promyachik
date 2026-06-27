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

SOURCE_PARTIAL = (
    PAYLOAD
    / "layouts"
    / "partials"
    / "transfer-player-stats.html"
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

TARGET_PARTIAL = (
    PROJECT
    / "layouts"
    / "partials"
    / "transfer-player-stats.html"
)


def validate_payload() -> None:
    js = SOURCE_JS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    css = SOURCE_CSS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    partial = SOURCE_PARTIAL.read_text(
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

    required_partial = [
        "$hasRealStats",
        "if $hasRealStats",
        "transfer-player-stats",
    ]

    missing = []

    for marker in required_js:
        if marker not in js:
            missing.append(marker)

    for marker in required_css:
        if marker not in css:
            missing.append(marker)

    for marker in required_partial:
        if marker not in partial:
            missing.append(marker)

    forbidden = []

    for marker in forbidden_js:
        if marker in js:
            forbidden.append(marker)

    for marker in forbidden_css:
        if marker in css:
            forbidden.append(marker)

    if missing:
        raise RuntimeError(
            "Corrected payload is missing: "
            + ", ".join(missing)
        )

    if forbidden:
        raise RuntimeError(
            "Old logo popup remains: "
            + ", ".join(forbidden)
        )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_chart_zoom_stats_"
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

        js = built_js.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        css = built_css.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        if "28-full-chart-zoom" not in js:
            raise RuntimeError(
                "Built site contains old chart JavaScript."
            )

        if ".club-logo-modal" in css:
            raise RuntimeError(
                "Built site still contains old logo modal CSS."
            )


def main() -> int:
    required = [
        SOURCE_JS,
        SOURCE_CSS,
        SOURCE_PARTIAL,
        TARGET_JS,
        TARGET_CSS,
    ]

    for path in required:
        if not path.exists():
            print("ERROR: required file not found:")
            print(path)
            return 1

    previous = {
        TARGET_JS: (
            TARGET_JS.read_bytes()
            if TARGET_JS.exists()
            else None
        ),
        TARGET_CSS: (
            TARGET_CSS.read_bytes()
            if TARGET_CSS.exists()
            else None
        ),
        TARGET_PARTIAL: (
            TARGET_PARTIAL.read_bytes()
            if TARGET_PARTIAL.exists()
            else None
        ),
    }

    try:
        print()
        print(
            "STEP 1 OF 4: removing old individual "
            "logo popup completely..."
        )

        validate_payload()

        print(
            "STEP 2 OF 4: installing full graph "
            "click-to-zoom..."
        )

        shutil.copy2(SOURCE_JS, TARGET_JS)
        shutil.copy2(SOURCE_CSS, TARGET_CSS)

        print(
            "STEP 3 OF 4: hiding statistics when "
            "no real data exists..."
        )

        TARGET_PARTIAL.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            SOURCE_PARTIAL,
            TARGET_PARTIAL,
        )

        print(
            "STEP 4 OF 4: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("FULL GRAPH CLICK-TO-ZOOM READY")
        print("INDIVIDUAL LOGO POPUP REMOVED")
        print("GOLD LOGO CIRCLES REMOVED")
        print("CLUB LOGOS MOVED 3 PX UP")
        print("EMPTY STATISTICS BLOCKS HIDDEN")
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring previous chart and "
            "statistics files..."
        )

        for path, content in previous.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                path.write_bytes(content)

        print("Previous project files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
