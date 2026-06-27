from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image
import hashlib
import io
import json
import math
import shutil
import sys
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT
    / "data"
    / "transfers.json"
)

OUTPUT_DIR = (
    ROOT
    / "static"
    / "images"
    / "clubs"
)

SITE_PREFIX = "/promyachik"

CANVAS_SIZE = 128

# Одинаковая видимая площадь всех эмблем.
TARGET_VISIBLE_AREA = 7000

# Максимальная длина одной стороны эмблемы.
MAX_SIDE = 116

ALPHA_LIMIT = 8


def open_source(source):
    if source.startswith("http://") or source.startswith("https://"):
        request = Request(
            source,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
        )

        with urlopen(
            request,
            timeout=20,
        ) as response:
            image_data = response.read()

        return Image.open(
            io.BytesIO(image_data)
        ).convert("RGBA")

    clean_path = source.replace("\\", "/")

    site_prefix = (
        SITE_PREFIX.rstrip("/")
        + "/"
    )

    if clean_path.startswith(site_prefix):
        clean_path = clean_path[
            len(site_prefix):
        ]

    elif clean_path.startswith("/"):
        clean_path = clean_path[1:]

    local_file = (
        ROOT
        / "static"
        / clean_path
    )

    return Image.open(
        local_file
    ).convert("RGBA")


def make_filename(club_name, club_id):
    if club_id not in (
        None,
        "",
        0,
        "0",
    ):
        return (
            f"team-{club_id}"
            f"-balanced.png"
        )

    digest = hashlib.sha1(
        club_name.encode("utf-8")
    ).hexdigest()[:10]

    return (
        f"club-{digest}"
        f"-balanced.png"
    )


def balance_logo(image):
    image = image.convert("RGBA")

    alpha = image.getchannel("A")

    mask = alpha.point(
        lambda value: (
            255
            if value > ALPHA_LIMIT
            else 0
        )
    )

    bounding_box = mask.getbbox()

    if bounding_box is None:
        raise ValueError(
            "Изображение пустое"
        )

    cropped = image.crop(
        bounding_box
    )

    cropped_alpha = (
        cropped.getchannel("A")
    )

    histogram = (
        cropped_alpha.histogram()
    )

    visible_pixels = sum(
        histogram[
            ALPHA_LIMIT + 1:
        ]
    )

    if visible_pixels == 0:
        raise ValueError(
            "В эмблеме нет видимых пикселей"
        )

    # Масштаб по реальной видимой площади.
    area_scale = math.sqrt(
        TARGET_VISIBLE_AREA
        / visible_pixels
    )

    # Ограничение, чтобы эмблема
    # не выходила за квадрат.
    side_scale = min(
        MAX_SIDE / cropped.width,
        MAX_SIDE / cropped.height,
    )

    scale = min(
        area_scale,
        side_scale,
    )

    new_width = max(
        1,
        round(
            cropped.width
            * scale
        ),
    )

    new_height = max(
        1,
        round(
            cropped.height
            * scale
        ),
    )

    resized = cropped.resize(
        (
            new_width,
            new_height,
        ),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGBA",
        (
            CANVAS_SIZE,
            CANVAS_SIZE,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    position_x = (
        CANVAS_SIZE
        - new_width
    ) // 2

    position_y = (
        CANVAS_SIZE
        - new_height
    ) // 2

    canvas.alpha_composite(
        resized,
        (
            position_x,
            position_y,
        ),
    )

    return (
        canvas,
        new_width,
        new_height,
    )


def read_club(
    transfer,
    side,
):
    nested_club = transfer.get(
        f"{side}_club"
    )

    if isinstance(
        nested_club,
        dict,
    ):
        return (
            nested_club,
            "logo",
            str(
                nested_club.get(
                    "name",
                    "",
                )
            ).strip(),
            nested_club.get("id"),
        )

    return (
        transfer,
        f"{side}_club_logo",
        str(
            transfer.get(
                f"{side}_club_name",
                "",
            )
        ).strip(),
        transfer.get(
            f"{side}_club_id"
        ),
    )


def main():
    if not DATA_FILE.exists():
        print(
            "ОШИБКА: не найден файл:"
        )
        print(DATA_FILE)

        return 1

    try:
        transfers = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as error:
        print(
            f"ОШИБКА JSON: {error}"
        )

        return 1

    if not isinstance(
        transfers,
        list,
    ):
        print(
            "ОШИБКА: transfers.json "
            "должен содержать список"
        )

        return 1

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = (
        datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )
    )

    backup_file = (
        DATA_FILE.parent
        / (
            "transfers.backup-"
            f"{timestamp}.json"
        )
    )

    shutil.copy2(
        DATA_FILE,
        backup_file,
    )

    processed_logos = {}

    processed_count = 0
    placeholder_count = 0

    for transfer in transfers:
        if not isinstance(
            transfer,
            dict,
        ):
            continue

        for side in (
            "from",
            "to",
        ):
            (
                target,
                logo_key,
                club_name,
                club_id,
            ) = read_club(
                transfer,
                side,
            )

            logo_source = str(
                target.get(
                    logo_key,
                    "",
                )
            ).strip()

            if not logo_source:
                placeholder_count += 1
                continue

            cache_key = str(
                club_id
                or logo_source
            )

            if cache_key in processed_logos:
                target[logo_key] = (
                    processed_logos[
                        cache_key
                    ]
                )

                continue

            try:
                source_image = open_source(
                    logo_source
                )

                (
                    balanced_image,
                    visible_width,
                    visible_height,
                ) = balance_logo(
                    source_image
                )

                filename = make_filename(
                    club_name
                    or "club",
                    club_id,
                )

                output_file = (
                    OUTPUT_DIR
                    / filename
                )

                balanced_image.save(
                    output_file,
                    format="PNG",
                    optimize=True,
                )

                web_path = (
                    f"{SITE_PREFIX}"
                    f"/images/clubs/"
                    f"{filename}"
                )

                target[logo_key] = web_path

                processed_logos[
                    cache_key
                ] = web_path

                processed_count += 1

                print(
                    f"ГОТОВО: "
                    f"{club_name} "
                    f"-> "
                    f"{visible_width}x"
                    f"{visible_height}"
                )

            except Exception as error:
                target[logo_key] = ""

                placeholder_count += 1

                print(
                    f"ОШИБКА: "
                    f"{club_name}: "
                    f"{error}"
                )

    DATA_FILE.write_text(
        json.dumps(
            transfers,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        f"Обработано: "
        f"{processed_count}"
    )

    print(
        f"Заглушек: "
        f"{placeholder_count}"
    )

    print(
        f"Резервная копия: "
        f"{backup_file.name}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())