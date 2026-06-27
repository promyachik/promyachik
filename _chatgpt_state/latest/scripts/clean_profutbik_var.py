from __future__ import annotations

import shutil
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
VAR = PROJECT / "var"

EXACT_DIRECTORIES = [
    "current_transfer_batch_backups",
    "current_transfer_batch_build",
    "favicon_build_test_v2",
    "fill_six_transfer_pages_backups",
    "fill_six_transfer_pages_build",
    "fix_transfer_pages_backup_v2",
    "fix_transfer_pages_build_v2",
    "market_value_chart_build",
    "market_value_chart_build_v2",
    "market_value_chart_build_v3",
    "market_value_chart_build_v4",
    "market_value_chart_direct_build",
    "market_value_chart_direct_build_v2",
    "mbappe_chart_diagnostic_build",
    "mbappe_chart_diagnostic_files",
    "mbappe_market_chart_fix_build",
    "mbappe_direct_chart_build",
    "runtime_market_chart_build",
    "runtime_market_chart_build_v2",
]

DIRECTORY_PREFIXES = [
    "favicon_integration_backup_",
    "market_value_chart_backup_",
    "market_value_chart_backup_v2_",
    "market_value_chart_backup_v3_",
    "market_value_chart_backup_v4_",
    "market_value_chart_direct_backup_",
    "mbappe_direct_chart_backup_",
    "runtime_market_chart_backup_",
    "runtime_market_chart_backup_v2_",
]

EXACT_FILES = [
    "current_transfer_batch_report.json",
    "fill_six_transfer_pages_report.json",
    "MBAPPE_CHART_DIAGNOSTIC.zip",
]

PROTECTED_NAMES = {
    "playerdb",
}


def size_bytes(path: Path) -> int:
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0

    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                pass

    return total


def format_size(value: int) -> str:
    units = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    size = float(value)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{value} Б"


def collect_targets() -> list[Path]:
    targets: list[Path] = []

    for name in EXACT_DIRECTORIES:
        path = VAR / name

        if path.exists() and path.name not in PROTECTED_NAMES:
            targets.append(path)

    for child in VAR.iterdir():
        if not child.is_dir():
            continue

        if child.name in PROTECTED_NAMES:
            continue

        if any(
            child.name.startswith(prefix)
            for prefix in DIRECTORY_PREFIXES
        ):
            targets.append(child)

    for name in EXACT_FILES:
        path = VAR / name

        if path.exists():
            targets.append(path)

    unique: dict[str, Path] = {}

    for target in targets:
        unique[str(target.resolve()).casefold()] = target

    return sorted(
        unique.values(),
        key=lambda path: path.name.casefold(),
    )


def main() -> int:
    if not VAR.exists():
        print("ERROR: папка var не найдена:")
        print(VAR)
        return 1

    targets = collect_targets()

    if not targets:
        print()
        print("Очистка не требуется.")
        print("Известные временные файлы не найдены.")
        print()
        print("Папка playerdb не затронута.")
        return 0

    total = sum(size_bytes(path) for path in targets)

    print()
    print("Будут удалены только временные файлы ProFutbik:")
    print()

    for target in targets:
        kind = "ПАПКА" if target.is_dir() else "ФАЙЛ "
        print(
            f"{kind}  {target.name}  "
            f"({format_size(size_bytes(target))})"
        )

    print()
    print("Общий размер:", format_size(total))
    print()
    print("Папка playerdb НЕ БУДЕТ удалена.")
    print("Незнакомые файлы и папки НЕ БУДУТ удалены.")
    print()

    answer = input(
        "Для удаления введи слово DELETE и нажми Enter: "
    ).strip()

    if answer != "DELETE":
        print()
        print("Очистка отменена. Ничего не удалено.")
        return 0

    removed = 0
    failed: list[tuple[Path, str]] = []

    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            removed += 1
            print("Удалено:", target.name)

        except Exception as error:
            failed.append((target, str(error)))
            print(
                "НЕ УДАЛЕНО:",
                target.name,
                "-",
                error,
            )

    print()
    print("ГОТОВО")
    print("Удалено объектов:", removed)
    print("Освобождено примерно:", format_size(total))

    if failed:
        print()
        print("Некоторые объекты удалить не удалось:")

        for target, error in failed:
            print("-", target, "->", error)

        return 1

    print()
    print("playerdb сохранена.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
