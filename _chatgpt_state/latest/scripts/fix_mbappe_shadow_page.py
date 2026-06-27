from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TEMPLATE = PROJECT / "layouts" / "players" / "single.html"

SKIP_TOP_LEVEL = {
    ".git",
    "public",
    "var",
    "node_modules",
}

EXPECTED_MARKER = 'data-market-chart-key="mbappe"'


def is_skipped(path: Path) -> bool:
    try:
        relative = path.relative_to(PROJECT)
    except ValueError:
        return True

    return bool(relative.parts) and relative.parts[0].casefold() in SKIP_TOP_LEVEL


def find_shadow_pages() -> list[Path]:
    found: list[Path] = []

    for path in PROJECT.rglob("*.html"):
        if is_skipped(path):
            continue

        relative_parts = [
            part.casefold()
            for part in path.relative_to(PROJECT).parts
        ]

        if len(relative_parts) < 3:
            continue

        if relative_parts[-3:] != [
            "players",
            "mbappe",
            "index.html",
        ]:
            continue

        if relative_parts[0] == "layouts":
            continue

        found.append(path)

    return sorted(
        found,
        key=lambda item: str(item).casefold(),
    )


def build_site(destination: Path) -> tuple[int, str]:
    hugo = shutil.which("hugo")

    if not hugo:
        return 127, "Hugo was not found in PATH."

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
        capture_output=True,
    )

    log = (
        result.stdout
        + "\n"
        + result.stderr
    )

    return result.returncode, log


def verify_output(destination: Path) -> tuple[bool, str]:
    page = (
        destination
        / "players"
        / "mbappe"
        / "index.html"
    )

    if not page.exists():
        return False, (
            "Built Mbappe page was not found: "
            + str(page)
        )

    html = page.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required = [
        EXPECTED_MARKER,
        "ДИНАМИКА СТОИМОСТИ",
        "€180 млн",
        'class="transfer-page player-profile-page"',
    ]

    missing = [
        marker
        for marker in required
        if marker not in html
    ]

    if missing:
        return False, (
            "Built page is missing: "
            + ", ".join(missing)
        )

    info_position = html.find(
        'class="player-info"'
    )
    chart_position = html.find(
        EXPECTED_MARKER
    )
    text_position = html.find(
        'class="player-text"'
    )

    if not (
        info_position >= 0
        and chart_position > info_position
        and text_position > chart_position
    ):
        return False, (
            "Chart is not located between "
            "player-info and player-text."
        )

    return True, str(page)


def main() -> int:
    if not TEMPLATE.exists():
        print("ERROR: template was not found:")
        print(TEMPLATE)
        return 1

    template_text = TEMPLATE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    if EXPECTED_MARKER not in template_text:
        print(
            "ERROR: the replacement player template "
            "does not contain the Mbappe chart."
        )
        return 1

    shadow_pages = find_shadow_pages()

    print()
    print("Searching for files that overwrite /players/mbappe/ ...")

    if shadow_pages:
        for page in shadow_pages:
            print(
                "CONFLICT FOUND: "
                + str(page.relative_to(PROJECT))
            )
    else:
        print(
            "No direct players\\mbappe\\index.html "
            "conflict was found."
        )

    saved_files: list[tuple[Path, bytes]] = []

    try:
        for page in shadow_pages:
            saved_files.append(
                (page, page.read_bytes())
            )
            page.unlink()
            print(
                "Removed conflicting generated HTML: "
                + str(page.relative_to(PROJECT))
            )

            parent = page.parent

            while (
                parent != PROJECT
                and parent.exists()
                and not any(parent.iterdir())
            ):
                parent.rmdir()
                parent = parent.parent

        with tempfile.TemporaryDirectory(
            prefix="profutbik_mbappe_verify_"
        ) as temporary:
            destination = Path(temporary)

            print()
            print("Building a clean temporary copy...")

            code, log = build_site(destination)

            print(log)

            if code != 0:
                raise RuntimeError(
                    "Hugo build failed with code "
                    + str(code)
                )

            valid, detail = verify_output(destination)

            if not valid:
                raise RuntimeError(detail)

            print()
            print("Verified built page:")
            print(detail)

        print()
        print("DONE")
        print("MBAPPE SHADOW PAGE CONFLICT FIXED")
        print(
            "The temporary verification build "
            "was deleted automatically."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring every removed conflicting file..."
        )

        for path, content in saved_files:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            path.write_bytes(content)
            print(
                "Restored: "
                + str(path.relative_to(PROJECT))
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
