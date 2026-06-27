from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
TEMPLATE = PROJECT / "layouts" / "transfers" / "single.html"
PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
CSS = PROJECT / "static" / "css" / "transfer-player-market-value-chart.css"
CONFIG = PROJECT / "scripts" / "transfer_market_chart_pages.json"

BUILD_DIR = PROJECT / "var" / "market_value_chart_direct_build"
BACKUP_DIR = (
    PROJECT
    / "var"
    / (
        "market_value_chart_direct_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
)

PARTIAL_MARKER = '{{ partial "transfer-player-market-value-chart.html" . }}'
CSS_MARKER = "transfer-player-market-value-chart.css"
CSS_LINK = (
    '    <link\n'
    '        rel="stylesheet"\n'
    '        href="{{ "css/transfer-player-market-value-chart.css" | relURL }}"\n'
    '    >\n'
)

modified: list[Path] = []


def backup(path: Path) -> None:
    if path in modified:
        return

    relative = path.resolve().relative_to(PROJECT.resolve())
    destination = BACKUP_DIR / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    modified.append(path)


def restore() -> None:
    for path in reversed(modified):
        relative = path.resolve().relative_to(PROJECT.resolve())
        source = BACKUP_DIR / relative

        if source.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, path)


def write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def install_template_hook() -> None:
    text = TEMPLATE.read_text(encoding="utf-8-sig")
    original = text

    if CSS_MARKER not in text:
        head_close = text.lower().find("</head>")

        if head_close < 0:
            raise RuntimeError(
                "Closing </head> was not found in transfer template."
            )

        text = text[:head_close] + CSS_LINK + "\n" + text[head_close:]

    if PARTIAL_MARKER not in text:
        player_section = text.find('<section class="player-brief">')

        if player_section < 0:
            raise RuntimeError("Player card section was not found.")

        dl_close = text.find("</dl>", player_section)

        if dl_close < 0:
            raise RuntimeError(
                "Player details closing </dl> was not found."
            )

        insert_at = dl_close + len("</dl>")
        text = (
            text[:insert_at]
            + "\n\n                "
            + PARTIAL_MARKER
            + text[insert_at:]
        )

    if text != original:
        backup(TEMPLATE)
        write_utf8(TEMPLATE, text)


def replace_chart_param(front: str, chart_json: str) -> str:
    lines = front.splitlines()
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if re.match(r"^market_value_chart\s*:", line):
            index += 1

            while index < len(lines):
                next_line = lines[index]

                if (
                    next_line
                    and not next_line[0].isspace()
                    and re.match(r"^[A-Za-z0-9_-]+\s*:", next_line)
                ):
                    break

                index += 1

            continue

        output.append(line)
        index += 1

    output.append("market_value_chart: " + chart_json)
    return "\n".join(output)


def update_page(page: Path, market_value: str, chart: dict) -> None:
    text = page.read_text(
        encoding="utf-8-sig",
        errors="strict",
    )

    match = re.match(
        r"\A---\s*\n(.*?)\n---",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise RuntimeError("Invalid front matter: " + str(page))

    front = match.group(1)

    if re.search(r"(?m)^market_value\s*:", front):
        front = re.sub(
            r'(?m)^market_value\s*:.*$',
            'market_value: "' + market_value + '"',
            front,
            count=1,
        )
    else:
        front += '\nmarket_value: "' + market_value + '"'

    chart_json = json.dumps(
        chart,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    front = replace_chart_param(front, chart_json)

    updated = (
        text[:match.start(1)]
        + front
        + text[match.end(1):]
    )

    if updated != text:
        backup(page)
        write_utf8(page, updated)


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
            "Hugo build failed with code " + str(result.returncode)
        )


def validate(keys: list[str]) -> None:
    html_files = list(BUILD_DIR.rglob("*.html"))

    for key in keys:
        marker = 'data-market-chart-key="' + key + '"'
        matches = []

        for html_file in html_files:
            html = html_file.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            if marker in html:
                matches.append(html_file)

        if len(matches) != 1:
            raise RuntimeError(
                "Expected exactly one built chart for "
                + key
                + ", found "
                + str(len(matches))
            )

        print(
            "Validated chart: "
            + key
            + " -> "
            + str(matches[0].relative_to(BUILD_DIR))
        )


def main() -> int:
    for required in (TEMPLATE, PARTIAL, CSS, CONFIG):
        if not required.exists():
            print("ERROR: required file not found: " + str(required))
            return 1

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    resolved = []

    for item in config:
        page = PROJECT / item["path"]

        if not page.exists():
            print("ERROR: page not found: " + str(page))
            return 1

        resolved.append(
            (
                page,
                item["market_value"],
                item["chart"],
            )
        )

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        print()
        print("STEP 1 OF 3: connecting chart inside player card...")
        install_template_hook()

        print(
            "STEP 2 OF 3: writing chart data "
            "directly into eight pages..."
        )

        for page, market_value, chart in resolved:
            update_page(page, market_value, chart)
            print("Updated: " + chart["player"])

        print(
            "STEP 3 OF 3: building and "
            "checking eight real charts..."
        )
        run_hugo()

        keys = [
            chart["key"]
            for _page, _value, chart in resolved
        ]
        validate(keys)

        print()
        print("DONE")
        print("VISIBLE CHARTS FOUND: 8")
        print(
            "Chart data is now stored directly "
            "in each transfer page."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring template and all "
            "modified transfer pages..."
        )
        restore()
        print("Previous project state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
