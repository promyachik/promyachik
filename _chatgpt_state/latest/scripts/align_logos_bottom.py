from pathlib import Path
from PIL import Image
import json
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = ROOT / "data" / "transfers.json"

STATIC_DIR = ROOT / "static"

CANVAS_SIZE = 128

BOTTOM_PADDING = 6


def align_image_bottom(source_file, output_file):
    image = Image.open(source_file).convert("RGBA")

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if bbox is None:
        raise ValueError("Изображение полностью прозрачное")

    cropped = image.crop(bbox)

    canvas = Image.new(
        "RGBA",
        (CANVAS_SIZE, CANVAS_SIZE),
        (0, 0, 0, 0),
    )

    position_x = (
        CANVAS_SIZE - cropped.width
    ) // 2

    position_y = (
        CANVAS_SIZE
        - cropped.height
        - BOTTOM_PADDING
    )

    if position_y < 0:
        position_y = 0

    canvas.alpha_composite(
        cropped,
        (position_x, position_y),
    )

    canvas.save(
        output_file,
        format="PNG",
        optimize=True,
    )


def get_local_file(logo_path):
    clean_path = logo_path.replace("\\", "/")

    prefix = "/promyachik/"

    if clean_path.startswith(prefix):
        clean_path = clean_path[len(prefix):]

    elif clean_path.startswith("/"):
        clean_path = clean_path[1:]

    return STATIC_DIR / clean_path


def create_new_logo_path(old_path):
    old_path = old_path.replace("\\", "/")

    path = Path(old_path)

    new_name = (
        path.stem
        + "-bottom"
        + path.suffix
    )

    return str(
        path.with_name(new_name)
    ).replace("\\", "/")


def process_logo(logo_path):
    if not logo_path:
        return logo_path

    if logo_path.startswith(
        ("http://", "https://")
    ):
        print(
            f"ПРОПУЩЕН ВНЕШНИЙ URL: {logo_path}"
        )

        return logo_path

    source_file = get_local_file(
        logo_path
    )

    if not source_file.exists():
        print(
            f"ФАЙЛ НЕ НАЙДЕН: {source_file}"
        )

        return logo_path

    new_logo_path = create_new_logo_path(
        logo_path
    )

    output_file = get_local_file(
        new_logo_path
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    align_image_bottom(
        source_file,
        output_file,
    )

    print(
        f"ГОТОВО: {output_file.name}"
    )

    return new_logo_path


def process_transfer(transfer):
    for side in ("from", "to"):
        nested_key = f"{side}_club"

        nested_club = transfer.get(
            nested_key
        )

        if isinstance(
            nested_club,
            dict,
        ):
            old_logo = str(
                nested_club.get(
                    "logo",
                    "",
                )
            ).strip()

            nested_club["logo"] = (
                process_logo(old_logo)
            )

            continue

        flat_key = f"{side}_club_logo"

        old_logo = str(
            transfer.get(
                flat_key,
                "",
            )
        ).strip()

        transfer[flat_key] = (
            process_logo(old_logo)
        )


def main():
    if not DATA_FILE.exists():
        print(
            "ОШИБКА: не найден файл"
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

    backup_file = (
        DATA_FILE.parent
        / "transfers.before-bottom-align.json"
    )

    shutil.copy2(
        DATA_FILE,
        backup_file,
    )

    for transfer in transfers:
        if isinstance(
            transfer,
            dict,
        ):
            process_transfer(
                transfer
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
        "Логотипы выровнены по нижней линии."
    )

    print(
        "transfers.json обновлён."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())