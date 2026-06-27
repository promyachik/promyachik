from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TEMPLATE = PROJECT / "layouts" / "transfers" / "single.html"
DATA_FILE = PROJECT / "data" / "player-market-values.json"
PARTIAL_FILE = (
    PROJECT
    / "layouts"
    / "partials"
    / "transfer-player-market-value-chart.html"
)
CSS_FILE = (
    PROJECT
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)

BUILD_DIR = PROJECT / "var" / "market_value_chart_build"
BACKUP_DIR = (
    PROJECT
    / "var"
    / (
        "market_value_chart_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
)

PARTIAL_MARKER = (
    '{{ partial "transfer-player-market-value-chart.html" . }}'
)
STYLESHEET_MARKER = "transfer-player-market-value-chart.css"
STYLESHEET_LINK = '''    <link
        rel="stylesheet"
        href="{{ "css/transfer-player-market-value-chart.css" | relURL }}"
    >
'''

PAGES = [
    ("kylian-mbappe-real-madrid", "180 млн евро"),
    ("florian-wirtz-liverpool", "100 млн евро"),
    ("ibrahima-konate-real-madrid", "45 млн евро"),
    ("marc-cucurella-real-madrid", "50 млн евро"),
    ("denzel-dumfries-real-madrid", "25 млн евро"),
    ("julian-alvarez-barcelona", "100 млн евро"),
    ("elliot-anderson-manchester-city", "75 млн евро"),
    ("bernardo-silva-real-madrid", "22 млн евро"),
]

modified_files: list[Path] = []


def relative_to_project(path: Path) -> Path:
    return path.resolve().relative_to(PROJECT.resolve())


def backup(path: Path) -> None:
    if path in modified_files:
        return

    destination = BACKUP_DIR / relative_to_project(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    modified_files.append(path)


def restore() -> None:
    for path in reversed(modified_files):
        source = BACKUP_DIR / relative_to_project(path)

        if source.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, path)


def write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def install_template_hooks() -> None:
    text = TEMPLATE.read_text(encoding="utf-8-sig")
    original = text

    if STYLESHEET_MARKER not in text:
        head_close = text.lower().find("</head>")

        if head_close < 0:
            raise RuntimeError(
                "Closing </head> was not found in transfer template."
            )

        text = (
            text[:head_close]
            + STYLESHEET_LINK
            + "\n"
            + text[head_close:]
        )

    if PARTIAL_MARKER not in text:
        player_section = text.find(
            '<section class="player-brief">'
        )

        if player_section < 0:
            raise RuntimeError(
                'Section <section class="player-brief"> was not found.'
            )

        list_close = text.find("</dl>", player_section)

        if list_close < 0:
            raise RuntimeError(
                "Player details closing </dl> was not found."
            )

        insert_at = list_close + len("</dl>")
        text = (
            text[:insert_at]
            + "\n\n                "
            + PARTIAL_MARKER
            + text[insert_at:]
        )

    if text != original:
        backup(TEMPLATE)
        write_utf8(TEMPLATE, text)


def update_market_value(page: Path, value: str) -> None:
    text = page.read_text(encoding="utf-8-sig")
    original = text

    front_match = re.match(
        r"\A---\s*\n(.*?)\n---",
        text,
        flags=re.DOTALL,
    )

    if not front_match:
        raise RuntimeError(
            f"Invalid front matter: {page}"
        )

    front = front_match.group(1)

    if re.search(r"(?m)^market_value\s*:", front):
        front = re.sub(
            r'(?m)^market_value\s*:.*$',
            f'market_value: "{value}"',
            front,
            count=1,
        )
    else:
        preferred = re.search(
            r"(?m)^preferred_foot\s*:.*$",
            front,
        )

        if preferred:
            position = preferred.end()
            front = (
                front[:position]
                + f'\nmarket_value: "{value}"'
                + front[position:]
            )
        else:
            front += f'\nmarket_value: "{value}"'

    text = (
        text[:front_match.start(1)]
        + front
        + text[front_match.end(1):]
    )

    if text != original:
        backup(page)
        write_utf8(page, text)


def run_hugo() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError("Hugo was not found in PATH.")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    result = subprocess.run(
        [
            hugo,
            "--minify",
            "--destination",
            str(BUILD_DIR),
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
            f"Hugo build failed with code {result.returncode}."
        )


def validate_pages() -> None:
    for slug, _value in PAGES:
        built_page = (
            BUILD_DIR
            / "transfers"
            / slug
            / "index.html"
        )

        if not built_page.exists():
            raise RuntimeError(
                f"Hugo did not build: {built_page}"
            )

        html = built_page.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        if 'class="player-market-chart"' not in html:
            raise RuntimeError(
                f"Market value chart is missing: {slug}"
            )


def main() -> int:
    required = [
        TEMPLATE,
        DATA_FILE,
        PARTIAL_FILE,
        CSS_FILE,
    ]

    for path in required:
        if not path.exists():
            print(f"ERROR: required file not found: {path}")
            return 1

    pages: list[tuple[Path, str, str]] = []

    for slug, value in PAGES:
        page = (
            PROJECT
            / "content"
            / "transfers"
            / slug
            / "index.md"
        )

        if not page.exists():
            print(f"ERROR: transfer page not found: {page}")
            return 1

        pages.append((page, slug, value))

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        print()
        print("STEP 1 OF 3: installing chart inside player card...")
        install_template_hooks()

        print("STEP 2 OF 3: updating current market values...")
        for page, slug, value in pages:
            update_market_value(page, value)
            print(f"Updated: {slug} -> {value}")

        print("STEP 3 OF 3: validating Hugo and eight pages...")
        run_hugo()
        validate_pages()

        print()
        print("DONE")
        print(
            "Market value charts were installed "
            "for all eight transfer players."
        )
        print(
            "Future transfer players will receive a chart "
            "when their record is added to "
            "data\\player-market-values.json."
        )
        return 0

    except Exception as error:
        print()
        print(f"ERROR: {error}")
        print("Restoring all modified project files...")
        restore()
        print("Previous project state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
