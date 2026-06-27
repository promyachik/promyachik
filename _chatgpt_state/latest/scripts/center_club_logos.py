from pathlib import Path, PurePosixPath
from PIL import Image
import json
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT
    / "data"
    / "transfers.json"
)

STATIC_DIR = (
    ROOT
    / "static"
)

CANVAS_SIZE = 128
ALPHA_THRESHOLD = 8


def get_logo_field(transfer, side):
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
        )

    return (
        transfer,
        f"{side}_club_logo",
    )


def web_path_to_file(logo_path):
    normalized_path = logo_path.replace(
        "\\",
        "/",
    )

    project_prefix = "/promyachik/"

    if normalized_path.startswith(
        project_prefix
    ):
        relative_path = normalized_path[
            len(project_prefix):
        ]

    elif normalized_path.startswith("/"):
        relative_path = normalized_path[1:]

    else:
        relative_path = normalized_path

    return (
        STATIC_DIR
        / relative_path
    )


def make_output_name(source_file):
    stem = source_file.stem

    removable_suffixes = (
        "-bottom",
        "-balanced",
        "-centered",
        "-final",
    )

    changed = True

    while changed:
        changed = False

        for suffix in removable_suffixes:
            if stem.endswith(suffix):
                stem = stem[
                    :-len(suffix)
                ]

                changed = True

    return f"{stem}-centered.png"


def center_visible_content(
    source_file,
    output_file,
):
    image = Image.open(
        source_file
    ).convert("RGBA")

    alpha_channel = image.getchannel("A")

    visible_mask = alpha_channel.point(
        lambda value: (
            255
            if value > ALPHA_THRESHOLD
            else 0
        )
    )

    visible_box = visible_mask.getbbox()

    if visible_box is None:
        raise ValueError(
            "Изображение полностью прозрачное"
        )

    cropped_logo = image.crop(
        visible_box
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
        - cropped_logo.width
    ) // 2

    position_y = (
        CANVAS_SIZE
        - cropped_logo.height
    ) // 2

    canvas.alpha_composite(
        cropped_logo,
        (
            position_x,
            position_y,
        ),
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.save(
        output_file,
        format="PNG",
        optimize=True,
    )


def replace_filename(
    old_web_path,
    new_filename,
):
    web_path = PurePosixPath(
        old_web_path.replace(
            "\\",
            "/",
        )
    )

    return str(
        web_path.with_name(
            new_filename
        )
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

    backup_file = DATA_FILE.with_name(
        "transfers.before-center.json"
    )

    shutil.copy2(
        DATA_FILE,
        backup_file,
    )

    processed_logos = {}
    updated_count = 0

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
                logo_container,
                logo_key,
            ) = get_logo_field(
                transfer,
                side,
            )

            logo_path = str(
                logo_container.get(
                    logo_key,
                    "",
                )
            ).strip()

            if not logo_path:
                continue

            if logo_path.startswith(
                (
                    "http://",
                    "https://",
                )
            ):
                print(
                    "ПРОПУЩЕН ВНЕШНИЙ URL: "
                    f"{logo_path}"
                )

                continue

            if logo_path in processed_logos:
                logo_container[logo_key] = (
                    processed_logos[
                        logo_path
                    ]
                )

                continue

            source_file = web_path_to_file(
                logo_path
            )

            if not source_file.exists():
                print(
                    "ФАЙЛ НЕ НАЙДЕН: "
                    f"{source_file}"
                )

                continue

            output_name = make_output_name(
                source_file
            )

            output_file = source_file.with_name(
                output_name
            )

            try:
                center_visible_content(
                    source_file,
                    output_file,
                )

            except (
                OSError,
                ValueError,
            ) as error:
                print(
                    "ОШИБКА: "
                    f"{source_file.name}: "
                    f"{error}"
                )

                continue

            new_web_path = replace_filename(
                logo_path,
                output_name,
            )

            logo_container[logo_key] = (
                new_web_path
            )

            processed_logos[
                logo_path
            ] = new_web_path

            updated_count += 1

            print(
                "ГОТОВО: "
                f"{source_file.name} "
                "-> "
                f"{output_name}"
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
        "Обновлено логотипов: "
        f"{updated_count}"
    )

    print(
        "Резервная копия: "
        f"{backup_file.name}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())