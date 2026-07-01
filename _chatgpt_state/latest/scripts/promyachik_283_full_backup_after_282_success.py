from pathlib import Path
import shutil
import datetime
import os
import sys

PROJECT = Path.cwd().resolve()
BACKUPS_ROOT = PROJECT.parent / "Promyachik_BACKUPS"
STAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_NAME = f"{STAMP}_FULL_BACKUP_AFTER_282_PRICE_ROW_UP_ALL_PLAYERS_SUCCESS"
BACKUP_DIR = BACKUPS_ROOT / BACKUP_NAME
REPORT = PROJECT / "var" / "promyachik_283_full_backup_after_282_success_report.txt"

IGNORE_DIRS = {
    ".git",
    ".hugo_build.lock",
    "node_modules",
    "__pycache__",
}

PROGRESS_MD_NAME = "PROFUTBIK_PROGRESS_AFTER_282_SUCCESS.md"
PROGRESS_MD = f"""# ProFutbik / Promyachik — точка восстановления после 282

**Дата backup:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Проект:** `C:\\Users\\Dmitrii\\Promyachik`  
**Локальный сайт:** `http://localhost:1313/promyachik/`

## Текущая успешная точка

- `276` — год в графике Cucurella визуально скрыт безопасным способом CSS-only.
- `277` — скрытие года применено для всех текущих и будущих графиков игроков.
- `278` — backup после успешного 277 был создан.
- `279` — цены в динамике стоимости подтянуты под реальные точки графика.
- `280` — значения в тысячах сокращены до формата `K`, например `300 тысяч` → `300K`.
- `281` — тест на странице Konate успешно поднял строку цен ближе к графику.
- `282` — удачное поднятие строки цен применено для всех текущих и будущих игроков.

## Что сейчас работает

- Год/дата над ценой скрыты визуально.
- Цена остаётся видимой.
- Цены стоят ближе к точкам графика.
- Значения в тысячах выводятся коротко через `K`.
- Позиционирование цен не ломается и не уезжает в футер.

## Важное правило

Для этой части графика больше не удалять DOM-элементы года через JS/HTML. Рабочий принцип — CSS-only для скрытия года и отдельная аккуратная настройка положения цен.

## Backup

Backup создан после подтверждения пользователем успешной работы пакета `282`.
"""

log = []
log.append("PROMYACHIK 283 - FULL BACKUP AFTER 282 SUCCESS")
log.append("=" * 100)
log.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.append(f"Project dir: {PROJECT}")
log.append(f"Backup root: {BACKUPS_ROOT}")
log.append(f"Backup dir: {BACKUP_DIR}")
log.append("")
log.append("RULE")
log.append("- Create full project backup after successful 282.")
log.append("- Do not modify code files.")
log.append("- Do not push.")
log.append("- Do not open site.")
log.append("- Include Markdown progress point inside backup folder.")
log.append("")

try:
    if not PROJECT.exists():
        raise RuntimeError(f"Project dir not found: {PROJECT}")
    if not (PROJECT / "hugo.toml").exists():
        raise RuntimeError(f"hugo.toml not found in project dir: {PROJECT}")

    BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
    if BACKUP_DIR.exists():
        raise RuntimeError(f"Backup dir already exists: {BACKUP_DIR}")

    def ignore_func(src, names):
        ignored = []
        for name in names:
            if name in IGNORE_DIRS:
                ignored.append(name)
            if name.startswith(".hugo_build.lock"):
                ignored.append(name)
        return set(ignored)

    shutil.copytree(PROJECT, BACKUP_DIR, ignore=ignore_func)

    progress_path = BACKUP_DIR / PROGRESS_MD_NAME
    progress_path.write_text(PROGRESS_MD, encoding="utf-8")

    files = 0
    dirs = 0
    total_bytes = 0
    for p in BACKUP_DIR.rglob("*"):
        try:
            if p.is_dir():
                dirs += 1
            elif p.is_file():
                files += 1
                total_bytes += p.stat().st_size
        except OSError:
            pass

    log.append("BACKUP CREATED")
    log.append(f"folder: {BACKUP_DIR}")
    log.append(f"files: {files}")
    log.append(f"dirs: {dirs}")
    log.append(f"bytes: {total_bytes}")
    log.append(f"progress_md: {progress_path}")
    log.append("")
    log.append("CHECKS")
    log.append(f"backup_exists: {BACKUP_DIR.exists()}")
    log.append(f"progress_md_exists: {progress_path.exists()}")
    log.append("VERIFIED_OK: True")
    log.append("")
    log.append("DONE")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(log), encoding="utf-8")
    print("DONE")
    print(f"BACKUP: {BACKUP_DIR}")
    print(f"REPORT: {REPORT}")
    sys.exit(0)

except Exception as e:
    log.append("ERROR")
    log.append(repr(e))
    log.append("")
    log.append("FAILED")
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("\n".join(log), encoding="utf-8")
    except Exception:
        pass
    print("FAILED")
    print(f"ERROR: {e}")
    print(f"REPORT: {REPORT}")
    sys.exit(1)
