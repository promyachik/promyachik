from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
HEADER = (
    PROJECT
    / "layouts"
    / "partials"
    / "header.html"
)
RUNTIME_PARTIAL = (
    PROJECT
    / "layouts"
    / "partials"
    / "mbappe-standalone-chart-runtime.html"
)

HOOK = (
    '{{ partial '
    '"mbappe-standalone-chart-runtime.html" . }}'
)

BACKUP = (
    PROJECT
    / "var"
    / (
        "header_before_mbappe_runtime_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".html"
    )
)


def restore_header() -> None:
    if BACKUP.exists():
        shutil.copy2(BACKUP, HEADER)


def main() -> int:
    for required in (HEADER, RUNTIME_PARTIAL):
        if not required.exists():
            print("ERROR: required file not found:")
            print(required)
            return 1

    header = HEADER.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    BACKUP.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    shutil.copy2(HEADER, BACKUP)

    try:
        if HOOK not in header:
            ticker_hook = (
                '{{ partial "transfer-ticker.html" . }}'
            )

            if ticker_hook in header:
                header = header.replace(
                    ticker_hook,
                    ticker_hook
                    + "\n\n"
                    + HOOK,
                    1,
                )
            else:
                header = (
                    header.rstrip()
                    + "\n\n"
                    + HOOK
                    + "\n"
                )

            HEADER.write_text(
                header,
                encoding="utf-8",
                newline="\n",
            )

        hugo = shutil.which("hugo")

        if not hugo:
            raise RuntimeError(
                "Hugo was not found in PATH."
            )

        print(
            "Building a clean temporary verification..."
        )

        with tempfile.TemporaryDirectory(
            prefix="profutbik_mbappe_header_"
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

            page = (
                destination
                / "players"
                / "mbappe"
                / "index.html"
            )

            if not page.exists():
                raise RuntimeError(
                    "Built Mbappe page was not found: "
                    + str(page)
                )

            html = page.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            required_markers = [
                'data-mbappe-runtime-hook="21"',
                "21-mbappe-header-runtime",
                "player-market-chart--mbappe-runtime",
                "pf-mbappe-standalone",
            ]

            missing = [
                marker
                for marker in required_markers
                if marker not in html
            ]

            if missing:
                raise RuntimeError(
                    "Built Mbappe page is missing "
                    "the runtime hook: "
                    + ", ".join(missing)
                )

        if BACKUP.exists():
            BACKUP.unlink()

        print()
        print("DONE")
        print("MBAPPE HEADER RUNTIME VERIFIED")
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring header.html...")
        restore_header()
        print("Previous header restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
