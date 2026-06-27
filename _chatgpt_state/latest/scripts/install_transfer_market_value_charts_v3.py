from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
CONTENT_ROOT = PROJECT / "content" / "transfers"
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

BUILD_DIR = PROJECT / "var" / "market_value_chart_build_v3"
BACKUP_DIR = (
    PROJECT
    / "var"
    / (
        "market_value_chart_backup_v3_"
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

PLAYERS = [
    {
        "name": "Килиан Мбаппе",
        "player_id": "278",
        "aliases": [
            "Килиан Мбаппе",
            "Kylian Mbappé",
            "Kylian Mbappe",
            "Mbappé",
            "Mbappe",
        ],
        "value": "180 млн евро",
    },
    {
        "name": "Флориан Вирц",
        "player_id": "203224",
        "aliases": [
            "Флориан Вирц",
            "Florian Wirtz",
            "F. Wirtz",
        ],
        "value": "100 млн евро",
    },
    {
        "name": "Ибраима Конате",
        "player_id": "",
        "aliases": [
            "Ибраима Конате",
            "Ibrahima Konaté",
            "Ibrahima Konate",
        ],
        "value": "45 млн евро",
    },
    {
        "name": "Марк Кукурелья",
        "player_id": "",
        "aliases": [
            "Марк Кукурелья",
            "Marc Cucurella",
        ],
        "value": "50 млн евро",
    },
    {
        "name": "Дензел Дюмфрис",
        "player_id": "",
        "aliases": [
            "Дензел Дюмфрис",
            "Denzel Dumfries",
        ],
        "value": "25 млн евро",
    },
    {
        "name": "Хулиан Альварес",
        "player_id": "",
        "aliases": [
            "Хулиан Альварес",
            "Julián Álvarez",
            "Julian Alvarez",
        ],
        "value": "100 млн евро",
    },
    {
        "name": "Эллиот Андерсон",
        "player_id": "",
        "aliases": [
            "Эллиот Андерсон",
            "Elliot Anderson",
        ],
        "value": "75 млн евро",
    },
    {
        "name": "Бернарду Силва",
        "player_id": "",
        "aliases": [
            "Бернарду Силва",
            "Bernardo Silva",
        ],
        "value": "22 млн евро",
    },
]

modified_files: list[Path] = []


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(
        r"[^a-zа-я0-9]+",
        " ",
        without_marks.casefold(),
    ).strip()


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


def front_matter(text: str) -> str:
    match = re.match(
        r"\A---\s*\n(.*?)\n---",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1)


def find_player_page(player: dict, pages: list[Path]) -> Path:
    player_id = str(player["player_id"]).strip()
    aliases = [normalize(alias) for alias in player["aliases"]]
    scored: list[tuple[int, Path]] = []

    for page in pages:
        text = page.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )
        front = front_matter(text)
        normalized_front = normalize(front)
        normalized_path = normalize(str(page))
        score = 0

        if player_id:
            id_match = re.search(
                r"(?m)^player_id\s*:\s*[\"']?"
                + re.escape(player_id)
                + r"[\"']?\s*$",
                front,
            )

            if id_match:
                score += 100

        for alias in aliases:
            if alias and alias in normalized_front:
                score += 20

            if alias and alias in normalized_path:
                score += 5

        if score > 0:
            scored.append((score, page))

    if not scored:
        raise RuntimeError(
            "Transfer page was not found for "
            + player["name"]
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -len(str(item[1])),
        ),
        reverse=True,
    )

    best_score = scored[0][0]
    best_pages = [
        page
        for score, page in scored
        if score == best_score
    ]

    if len(best_pages) != 1:
        paths = ", ".join(str(path) for path in best_pages)
        raise RuntimeError(
            "Several equally suitable pages were found for "
            + player["name"]
            + ": "
            + paths
        )

    return best_pages[0]


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

    match = re.match(
        r"\A---\s*\n(.*?)\n---",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "Invalid front matter: " + str(page)
        )

    front = match.group(1)

    if re.search(r"(?m)^market_value\s*:", front):
        front = re.sub(
            r'(?m)^market_value\s*:.*$',
            'market_value: "' + value + '"',
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
                + '\nmarket_value: "'
                + value
                + '"'
                + front[position:]
            )
        else:
            front += '\nmarket_value: "' + value + '"'

    text = (
        text[:match.start(1)]
        + front
        + text[match.end(1):]
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
            "Hugo build failed with code "
            + str(result.returncode)
        )


def validate_page(
    player: dict,
    source_page: Path,
) -> None:
    del source_page

    unique_label = (
        "График изменения рыночной стоимости "
        + player["name"]
    )
    matches: list[Path] = []

    for built_page in BUILD_DIR.rglob("*.html"):
        html = built_page.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

        if (
            'class="player-market-chart"' in html
            and unique_label in html
            and "ДИНАМИКА СТОИМОСТИ" in html
        ):
            matches.append(built_page)

    if not matches:
        raise RuntimeError(
            "Built chart was not found for "
            + player["name"]
        )

    if len(matches) > 1:
        paths = ", ".join(str(path) for path in matches)
        raise RuntimeError(
            "The chart for "
            + player["name"]
            + " appeared on several built pages: "
            + paths
        )


def main() -> int:
    required = [
        CONTENT_ROOT,
        TEMPLATE,
        DATA_FILE,
        PARTIAL_FILE,
        CSS_FILE,
    ]

    for path in required:
        if not path.exists():
            print("ERROR: required path not found: " + str(path))
            return 1

    candidate_pages = [
        page
        for page in CONTENT_ROOT.rglob("index.md")
        if page.is_file()
    ]

    detected: list[tuple[dict, Path]] = []

    try:
        for player in PLAYERS:
            page = find_player_page(player, candidate_pages)
            detected.append((player, page))
            print(
                "Detected: "
                + player["name"]
                + " -> "
                + str(page.relative_to(PROJECT))
            )
    except Exception as error:
        print()
        print("ERROR: " + str(error))
        return 1

    unique_pages = {page.resolve() for _player, page in detected}

    if len(unique_pages) != len(PLAYERS):
        print()
        print(
            "ERROR: two players were matched to the same page. "
            "No changes were made."
        )
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        print()
        print("STEP 1 OF 3: installing chart inside player card...")
        install_template_hooks()

        print("STEP 2 OF 3: updating detected player pages...")
        for player, page in detected:
            update_market_value(page, player["value"])
            print(
                "Updated: "
                + player["name"]
                + " -> "
                + player["value"]
            )

        print("STEP 3 OF 3: validating Hugo and detected URLs...")
        run_hugo()

        for player, page in detected:
            validate_page(player, page)
            print("Validated: " + player["name"])

        print()
        print("DONE")
        print(
            "Market value charts were installed "
            "for all eight transfer players."
        )
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring all modified project files...")
        restore()
        print("Previous project state restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
