from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
CONTENT = PROJECT / "content"
SHORTCODE = (
    PROJECT
    / "layouts"
    / "shortcodes"
    / "mbappe-market-chart.html"
)

SHORTCODE_CALL = "{{< mbappe-market-chart >}}"

TITLE_PATTERNS = (
    "kylian mbappé",
    "kylian mbappe",
    "килиан мбаппе",
)


def read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )


def find_mbappe_page() -> Path:
    candidates: list[tuple[int, Path]] = []

    for path in CONTENT.rglob("*.md"):
        lowered_name = path.name.casefold()

        if (
            ".before-" in lowered_name
            or lowered_name.endswith(".bak.md")
            or "backup" in {
                part.casefold()
                for part in path.parts
            }
        ):
            continue

        text = read(path)
        lowered = text.casefold()

        if not any(
            pattern in lowered
            for pattern in TITLE_PATTERNS
        ):
            continue

        score = 0
        relative_parts = [
            part.casefold()
            for part in path.relative_to(CONTENT).parts
        ]

        if "players" in relative_parts:
            score += 100

        if "mbappe" in str(path).casefold():
            score += 50

        if re.search(
            r'(?mi)^title\s*:\s*["\']?kylian mbapp',
            text,
        ):
            score += 30

        if "draft: true" not in lowered:
            score += 10

        candidates.append((score, path))

    if not candidates:
        raise RuntimeError(
            "The standalone Mbappe Markdown page "
            "was not found."
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            str(item[1]).casefold(),
        )
    )

    best_score = candidates[0][0]
    best = [
        path
        for score, path in candidates
        if score == best_score
    ]

    if len(best) != 1:
        raise RuntimeError(
            "Several equally suitable Mbappe pages "
            "were found: "
            + ", ".join(str(path) for path in best)
        )

    return best[0]


def insert_shortcode(text: str) -> str:
    text = text.replace(
        SHORTCODE_CALL,
        "",
    )

    match = re.match(
        r"\A---\s*\n.*?\n---\s*\n?",
        text,
        flags=re.DOTALL,
    )

    if match:
        insertion = match.end()

        return (
            text[:insertion]
            + "\n"
            + SHORTCODE_CALL
            + "\n\n"
            + text[insertion:].lstrip("\n")
        )

    return (
        SHORTCODE_CALL
        + "\n\n"
        + text.lstrip("\n")
    )


def find_built_mbappe_page(
    destination: Path,
) -> Path:
    page = (
        destination
        / "players"
        / "mbappe"
        / "index.html"
    )

    if not page.exists():
        raise RuntimeError(
            "Built standalone Mbappe page was not found: "
            + str(page)
        )

    html = page.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    if 'data-market-chart-key="mbappe"' not in html:
        raise RuntimeError(
            "The built standalone Mbappe page does not "
            "contain the market chart marker."
        )

    return page


def main() -> int:
    if not CONTENT.exists():
        print("ERROR: content folder not found:")
        print(CONTENT)
        return 1

    if not SHORTCODE.exists():
        print("ERROR: shortcode file not found:")
        print(SHORTCODE)
        return 1

    page: Path | None = None
    original: bytes | None = None

    try:
        page = find_mbappe_page()
        original = page.read_bytes()

        print()
        print("Standalone Mbappe page found:")
        print(page.relative_to(PROJECT))

        updated = insert_shortcode(
            read(page)
        )

        page.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        hugo = shutil.which("hugo")

        if not hugo:
            raise RuntimeError(
                "Hugo was not found in PATH."
            )

        print()
        print(
            "Building a clean temporary "
            "verification..."
        )

        with tempfile.TemporaryDirectory(
            prefix="profutbik_mbappe_shortcode_"
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

            built_page = find_built_mbappe_page(
                destination
            )

            html = built_page.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            required = [
                'data-market-chart-key="mbappe"',
                "player-market-chart--mbappe-content",
                "ДИНАМИКА СТОИМОСТИ",
                "€180 млн",
            ]

            missing = [
                marker
                for marker in required
                if marker not in html
            ]

            if missing:
                raise RuntimeError(
                    "Built page is missing: "
                    + ", ".join(missing)
                )

            print()
            print("Verified built page:")
            print(
                built_page.relative_to(destination)
            )

        print()
        print("DONE")
        print("MBAPPE CONTENT CHART VERIFIED V2")
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))

        if page is not None and original is not None:
            page.write_bytes(original)
            print(
                "Original Mbappe Markdown restored."
            )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
