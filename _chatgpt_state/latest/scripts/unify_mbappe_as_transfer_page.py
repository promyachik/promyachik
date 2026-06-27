from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

TRANSFER_PAGE = (
    PROJECT
    / "content"
    / "transfers"
    / "kylian-mbappe-real-madrid"
    / "index.md"
)

OLD_PLAYER_PAGE = (
    PROJECT
    / "content"
    / "players"
    / "mbappe.md"
)

CHART_JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)

TRANSFER_URL = "/transfers/kylian-mbappe-real-madrid/"
OLD_PLAYER_URL = "/players/mbappe/"


def split_front_matter(text: str) -> tuple[str, str]:
    match = re.match(
        r"\A---\s*\n(.*?)\n---\s*\n?",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "Transfer page has no valid YAML front matter."
        )

    return match.group(1), text[match.end():]


def remove_yaml_block(
    front: str,
    key: str,
) -> str:
    lines = front.splitlines()
    output: list[str] = []
    index = 0
    pattern = re.compile(
        rf"^{re.escape(key)}\s*:",
        flags=re.IGNORECASE,
    )

    while index < len(lines):
        line = lines[index]

        if not pattern.match(line):
            output.append(line)
            index += 1
            continue

        index += 1

        while index < len(lines):
            next_line = lines[index]

            if (
                next_line
                and not next_line[0].isspace()
                and re.match(
                    r"^[A-Za-z0-9_-]+\s*:",
                    next_line,
                )
            ):
                break

            index += 1

    return "\n".join(output)


def set_scalar(
    front: str,
    key: str,
    value: str,
) -> str:
    pattern = re.compile(
        rf"(?mi)^{re.escape(key)}\s*:.*$"
    )

    replacement = f'{key}: "{value}"'

    if pattern.search(front):
        return pattern.sub(
            replacement,
            front,
            count=1,
        )

    return front.rstrip() + "\n" + replacement


def prepare_transfer_page(text: str) -> str:
    front, body = split_front_matter(text)

    draft_pattern = re.compile(
        r"(?mi)^draft\s*:.*$"
    )

    if draft_pattern.search(front):
        front = draft_pattern.sub(
            "draft: false",
            front,
            count=1,
        )
    else:
        front = front.rstrip() + "\ndraft: false"

    front = remove_yaml_block(
        front,
        "aliases",
    )

    aliases_block = (
        'aliases:\n'
        '  - "/players/mbappe/"'
    )

    draft_line = re.search(
        r"(?mi)^draft\s*:\s*false\s*$",
        front,
    )

    if draft_line:
        insert_at = draft_line.end()

        front = (
            front[:insert_at]
            + "\n\n"
            + aliases_block
            + front[insert_at:]
        )
    else:
        front = (
            front.rstrip()
            + "\n\n"
            + aliases_block
        )

    front = set_scalar(
        front,
        "player_url",
        TRANSFER_URL,
    )

    front = set_scalar(
        front,
        "market_value_url",
        TRANSFER_URL + "#market-value",
    )

    return (
        "---\n"
        + front.strip()
        + "\n---\n\n"
        + body.lstrip("\n")
    )


def run_hugo(destination: Path) -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo was not found in PATH."
        )

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


def validate(destination: Path) -> None:
    transfer_html = (
        destination
        / "transfers"
        / "kylian-mbappe-real-madrid"
        / "index.html"
    )

    alias_html = (
        destination
        / "players"
        / "mbappe"
        / "index.html"
    )

    if not transfer_html.exists():
        raise RuntimeError(
            "Built Mbappe transfer page was not found: "
            + str(transfer_html)
        )

    html = transfer_html.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    required_markers = [
        "player-brief",
        "Килиан Мбаппе",
        "transfer-player-market-value-chart.js",
        "transfer-player-market-value-chart.css",
    ]

    missing = [
        marker
        for marker in required_markers
        if marker not in html
    ]

    if missing:
        raise RuntimeError(
            "Built Mbappe transfer page is missing: "
            + ", ".join(missing)
        )

    if not alias_html.exists():
        raise RuntimeError(
            "Redirect page for /players/mbappe/ "
            "was not created."
        )

    alias = alias_html.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    if (
        "kylian-mbappe-real-madrid"
        not in alias
    ):
        raise RuntimeError(
            "The old Mbappe URL does not redirect "
            "to the transfer page."
        )

    js_text = CHART_JS.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    if (
        "/transfers/kylian-mbappe-real-madrid/"
        not in js_text
    ):
        raise RuntimeError(
            "Current chart JavaScript has no Mbappe "
            "transfer-page path mapping."
        )


def main() -> int:
    if not TRANSFER_PAGE.exists():
        print("ERROR: Mbappe transfer page not found:")
        print(TRANSFER_PAGE)
        return 1

    if not CHART_JS.exists():
        print("ERROR: chart JavaScript not found:")
        print(CHART_JS)
        return 1

    transfer_original = TRANSFER_PAGE.read_bytes()
    old_player_existed = OLD_PLAYER_PAGE.exists()
    old_player_original = (
        OLD_PLAYER_PAGE.read_bytes()
        if old_player_existed
        else None
    )

    try:
        print()
        print(
            "STEP 1 OF 3: converting Mbappe to the "
            "working transfer player-brief page..."
        )

        updated = prepare_transfer_page(
            TRANSFER_PAGE.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        TRANSFER_PAGE.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        if OLD_PLAYER_PAGE.exists():
            OLD_PLAYER_PAGE.unlink()
            print(
                "Removed obsolete standalone page: "
                "content\\players\\mbappe.md"
            )

        print(
            "STEP 2 OF 3: building a clean temporary "
            "copy..."
        )

        with tempfile.TemporaryDirectory(
            prefix="profutbik_mbappe_unified_"
        ) as temporary:
            destination = Path(temporary)
            run_hugo(destination)

            print(
                "STEP 3 OF 3: validating player-brief, "
                "chart assets and redirect..."
            )
            validate(destination)

        print()
        print("DONE")
        print("MBAPPE TRANSFER PLAYER-BRIEF READY")
        print(
            "OLD /players/mbappe/ URL REDIRECTS "
            "TO THE TRANSFER PAGE"
        )
        print(
            "Temporary verification build removed."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print(
            "Restoring the previous Mbappe files..."
        )

        TRANSFER_PAGE.write_bytes(
            transfer_original
        )

        if old_player_existed:
            OLD_PLAYER_PAGE.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            OLD_PLAYER_PAGE.write_bytes(
                old_player_original
            )
        elif OLD_PLAYER_PAGE.exists():
            OLD_PLAYER_PAGE.unlink()

        print("Previous state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
