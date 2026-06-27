from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)
BUILD = PROJECT / "var" / "mbappe_market_chart_fix_build"


def main() -> int:
    if not JS.exists():
        print("ERROR: JavaScript file not found: " + str(JS))
        return 1

    text = JS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required_markers = [
        'window.__PFMarketChartVersion = "13-mbappe-fix"',
        '".mbappe-card"',
        "existingRuntimeChart",
        "findCard(player)",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in text
    ]

    if missing:
        print(
            "ERROR: patched JavaScript is incomplete: "
            + ", ".join(missing)
        )
        return 1

    hugo = shutil.which("hugo")

    if not hugo:
        print("ERROR: Hugo was not found in PATH.")
        return 1

    if BUILD.exists():
        shutil.rmtree(BUILD)

    print("Building Hugo after Mbappe chart fix...")

    result = subprocess.run(
        [
            hugo,
            "--minify",
            "--destination",
            str(BUILD),
            "--baseURL",
            "http://127.0.0.1:1313/promyachik/",
        ],
        cwd=PROJECT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print(
            "ERROR: Hugo build failed with code "
            + str(result.returncode)
        )
        return 1

    built_js = (
        BUILD
        / "js"
        / "transfer-player-market-value-chart.js"
    )

    if not built_js.exists():
        print(
            "ERROR: patched JavaScript was not copied "
            "into the Hugo build."
        )
        return 1

    built_text = built_js.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    if '13-mbappe-fix' not in built_text:
        print(
            "ERROR: Hugo build contains an old JavaScript file."
        )
        return 1

    print()
    print("DONE")
    print("MBAPPE MARKET CHART FIX INSTALLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
