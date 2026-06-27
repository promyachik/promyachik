from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

INDEX = PROJECT / "layouts" / "index.html"
PLAYER_TEMPLATE = (
    PROJECT
    / "layouts"
    / "players"
    / "single.html"
)
JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)
HOME_CSS = (
    PROJECT
    / "static"
    / "css"
    / "home-placeholder.css"
)
PLAYER_ADDON_CSS = (
    PROJECT
    / "static"
    / "css"
    / "player-brief-standalone-addon.css"
)


def require(path: Path, markers: list[str]) -> None:
    if not path.exists():
        raise RuntimeError(
            "Required file was not found: "
            + str(path)
        )

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    missing = [
        marker
        for marker in markers
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            str(path)
            + " is missing: "
            + ", ".join(missing)
        )


def main() -> int:
    try:
        print()
        print(
            "STEP 1 OF 3: checking homepage "
            "and player-brief files..."
        )

        require(
            INDEX,
            [
                "home-feature-placeholder",
                "Главный блок в разработке",
            ],
        )

        index_text = INDEX.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        if 'partial "player-value-chart.html"' in index_text:
            raise RuntimeError(
                "Old Mbappe homepage chart is still connected."
            )

        require(
            PLAYER_TEMPLATE,
            [
                "player-card player-brief player-brief--standalone",
                "transfer-player-market-value-chart.js",
                "player-brief-standalone-addon.css",
            ],
        )

        require(
            JS,
            [
                "20-path-based-player-charts",
                "/players/mbappe/",
                "/transfers/julian-alvarez-barcelona/",
                "playerFromPath || playerFromTitle()",
            ],
        )

        require(HOME_CSS, ["home-feature-placeholder"])
        require(
            PLAYER_ADDON_CSS,
            ["player-brief--standalone"],
        )

        print(
            "STEP 2 OF 3: building a clean temporary "
            "copy of Hugo..."
        )

        hugo = shutil.which("hugo")

        if not hugo:
            raise RuntimeError(
                "Hugo was not found in PATH."
            )

        with tempfile.TemporaryDirectory(
            prefix="profutbik_chart_reset_"
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

            print(
                "STEP 3 OF 3: checking homepage, "
                "Mbappe and Alvarez pages..."
            )

            home = destination / "index.html"
            mbappe = (
                destination
                / "players"
                / "mbappe"
                / "index.html"
            )
            alvarez = (
                destination
                / "transfers"
                / "julian-alvarez-barcelona"
                / "index.html"
            )

            for path in (home, mbappe, alvarez):
                if not path.exists():
                    raise RuntimeError(
                        "Built page was not found: "
                        + str(path)
                    )

            home_html = home.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            if "home-feature-placeholder" not in home_html:
                raise RuntimeError(
                    "Homepage placeholder is missing."
                )

            if "value-dashboard" in home_html:
                raise RuntimeError(
                    "Old Mbappe homepage dashboard "
                    "is still present."
                )

            mbappe_html = mbappe.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            for marker in (
                "player-brief--standalone",
                "transfer-player-market-value-chart.js",
                "player-brief-standalone-addon.css",
            ):
                if marker not in mbappe_html:
                    raise RuntimeError(
                        "Mbappe page is missing: "
                        + marker
                    )

            alvarez_html = alvarez.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            for marker in (
                "player-brief",
                "transfer-player-market-value-chart.js",
            ):
                if marker not in alvarez_html:
                    raise RuntimeError(
                        "Alvarez page is missing: "
                        + marker
                    )

        print()
        print("DONE")
        print("HOMEPAGE PLACEHOLDER INSTALLED")
        print("MBAPPE PLAYER-BRIEF READY")
        print("ALVAREZ PATH-BASED CHART READY")
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
