from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = ROOT / "static" / "css" / "transfer-article.css"
ICON_SRC = ROOT / "payload" / "stats-icons"
ICON_DST = ROOT / "static" / "images" / "stats-icons"
BACKUP_DIR = ROOT / "_backup_164_fix_yellow_red_stats_icons"
REPORT_PATH = ROOT / "_164_fix_yellow_red_stats_icons_report.txt"

MARKER = "PROFUTBIK FIX YELLOW RED STATS ICONS V164"
ICONS = [
    "matches.png",
    "goals.png",
    "assists.png",
    "minutes.png",
    "yellow_cards.png",
    "red_cards.png",
    "season.png",
]

CSS_BLOCK = r'''

/* PROFUTBIK FIX YELLOW RED STATS ICONS V164 START */
/* Fix stat icon mapping after V163: robust class names + nth-of-type fallback. */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card span,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card small {
    font-size: 0 !important;
    line-height: 1 !important;
    min-height: 18px !important;
    height: 18px !important;
    margin-top: 2px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card small::before {
    content: "" !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 22px !important;
    height: 22px !important;
    min-width: 22px !important;
    min-height: 22px !important;
    font-size: 0 !important;
    line-height: 1 !important;
    background-color: transparent !important;
    background-repeat: no-repeat !important;
    background-position: center center !important;
    background-size: contain !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: none !important;
    filter: none !important;
}

/* Matches = approved option 1 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--matches span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--matches small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(1) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(1) small::before {
    background-image: url("../images/stats-icons/matches.png") !important;
}

/* Goals = approved option 3 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--goals span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--goals small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(2) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(2) small::before {
    background-image: url("../images/stats-icons/goals.png") !important;
}

/* Assists = approved option 2 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--assists span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--assists small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(3) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(3) small::before {
    background-image: url("../images/stats-icons/assists.png") !important;
}

/* Minutes = approved option 1 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--minutes span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--minutes small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(4) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(4) small::before {
    background-image: url("../images/stats-icons/minutes.png") !important;
}

/* Yellow cards = approved option 3 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow-card span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow-card small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow-cards span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow-cards small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow_card span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow_card small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow_cards span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--yellow_cards small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--bookings span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--bookings small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(5) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(5) small::before {
    background-image: url("../images/stats-icons/yellow_cards.png") !important;
}

/* Red cards = approved option 3 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red-card span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red-card small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red-cards span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red-cards small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red_card span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red_card small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red_cards span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--red_cards small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(6) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(6) small::before {
    background-image: url("../images/stats-icons/red_cards.png") !important;
}

/* Season = approved option 2 */
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--season span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__card--season small::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(7) span::before,
body.transfer-page .transfer-stats--under-market-chart .transfer-stats__grid > .transfer-stats__card:nth-of-type(7) small::before {
    width: 21px !important;
    height: 21px !important;
    min-width: 21px !important;
    min-height: 21px !important;
    background-image: url("../images/stats-icons/season.png") !important;
}
/* PROFUTBIK FIX YELLOW RED STATS ICONS V164 END */
'''


def fail(message: str) -> None:
    REPORT_PATH.write_text("FAILED\n" + message + "\n", encoding="utf-8")
    raise SystemExit(message)


def main() -> None:
    if not CSS_PATH.exists():
        fail(f"CSS not found: {CSS_PATH}")
    if not ICON_SRC.exists():
        fail(f"Icon payload not found: {ICON_SRC}")

    missing = [name for name in ICONS if not (ICON_SRC / name).exists()]
    if missing:
        fail("Missing icon files: " + ", ".join(missing))

    BACKUP_DIR.mkdir(exist_ok=True)
    ICON_DST.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    shutil.copy2(CSS_PATH, BACKUP_DIR / f"transfer-article.before_v164_{timestamp}.css")

    copied = []
    for name in ICONS:
        src = ICON_SRC / name
        dst = ICON_DST / name
        if dst.exists():
            shutil.copy2(dst, BACKUP_DIR / f"{dst.stem}.before_v164_{timestamp}{dst.suffix}")
        shutil.copy2(src, dst)
        copied.append(str(dst.relative_to(ROOT)))

    css = CSS_PATH.read_text(encoding="utf-8")
    if MARKER not in css:
        CSS_PATH.write_text(css.rstrip() + CSS_BLOCK + "\n", encoding="utf-8")
        css_status = "added"
    else:
        css_status = "already_present"

    report = [
        "DONE_164_FULL_FIX_YELLOW_RED_STATS_ICONS",
        f"root={ROOT}",
        f"css={CSS_PATH.relative_to(ROOT)}",
        f"css_block={css_status}",
        "icons_copied:",
        *[f"- {item}" for item in copied],
        "fix:",
        "- yellow_cards and red_cards get robust class + nth-of-type selectors",
        "- no layout/partial/market chart changes",
    ]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("DONE_164_FULL_FIX_YELLOW_RED_STATS_ICONS")


if __name__ == "__main__":
    main()
