from __future__ import annotations

import datetime as _dt
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
index_path = ROOT / "layouts" / "index.html"
partial_dir = ROOT / "layouts" / "partials"
css_dir = ROOT / "static" / "css"

if not index_path.exists():
    raise SystemExit(f"Missing file: {index_path}")

stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / "var" / "backups" / f"homepage_step_44_{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(index_path, backup_dir / "layouts_index.html")

partial_dir.mkdir(parents=True, exist_ok=True)
css_dir.mkdir(parents=True, exist_ok=True)

partial_path = partial_dir / "homepage-desktop-hero.html"
css_path = css_dir / "homepage-desktop-step1.css"

partial = r'''{{/* ProFutbik homepage desktop hero — step 44 */}}
<section class="pf-home-hero" aria-labelledby="pf-home-hero-title">
    <div class="pf-home-hero__bg pf-home-hero__bg--one"></div>
    <div class="pf-home-hero__bg pf-home-hero__bg--two"></div>

    <div class="pf-home-hero__inner">
        <div class="pf-home-hero__content">
            <div class="pf-home-hero__eyebrow">
                <span class="pf-home-hero__pulse"></span>
                Transfer watch
            </div>

            <h1 id="pf-home-hero-title" class="pf-home-hero__title">
                Трансферы, слухи и рыночная стоимость футболистов
            </h1>

            <p class="pf-home-hero__lead">
                Следи за переходами игроков, статусом сделок, клубами и историей изменения цены в одном месте.
            </p>

            <div class="pf-home-hero__actions" aria-label="Главные действия">
                <a class="pf-home-hero__button pf-home-hero__button--primary" href="{{ "transfers/" | relURL }}">
                    Смотреть трансферы
                </a>
                <a class="pf-home-hero__button pf-home-hero__button--ghost" href="#pf-home-search">
                    Найти игрока
                </a>
            </div>
        </div>

        <aside class="pf-home-hero__panel" aria-label="Главный трансфер дня">
            <div class="pf-home-hero__panel-top">
                <span class="pf-home-hero__panel-label">Главный трансфер дня</span>
                <span class="pf-home-hero__status">Официально</span>
            </div>

            <div class="pf-home-hero__player-row">
                <div class="pf-home-hero__player-photo-wrap">
                    <img
                        class="pf-home-hero__player-photo"
                        src="{{ "images/players/cutout/278.png" | relURL }}"
                        alt="Kylian Mbappé"
                        loading="eager"
                    >
                </div>

                <div class="pf-home-hero__player-info">
                    <strong class="pf-home-hero__player-name">Kylian Mbappé</strong>
                    <span class="pf-home-hero__player-route">PSG → Real Madrid</span>
                    <span class="pf-home-hero__price">€ 180M</span>
                </div>
            </div>

            <div class="pf-home-hero__mini-chart" aria-hidden="true">
                <span class="pf-home-hero__chart-line"></span>
                <span class="pf-home-hero__chart-dot pf-home-hero__chart-dot--one"></span>
                <span class="pf-home-hero__chart-dot pf-home-hero__chart-dot--two"></span>
                <span class="pf-home-hero__chart-dot pf-home-hero__chart-dot--three"></span>
                <span class="pf-home-hero__chart-dot pf-home-hero__chart-dot--four"></span>
            </div>

            <a class="pf-home-hero__details" href="{{ "transfers/kylian-mbappe-real-madrid/" | relURL }}">
                Открыть страницу трансфера →
            </a>
        </aside>
    </div>
</section>

<section id="pf-home-search" class="pf-home-search" aria-label="Поиск игрока">
    <div class="pf-home-search__inner">
        <div>
            <span class="pf-home-search__label">Поиск игрока</span>
            <strong class="pf-home-search__title">Найди трансфер или футболиста</strong>
        </div>
        <form class="pf-home-search__form" action="{{ "transfers/" | relURL }}" method="get">
            <input class="pf-home-search__input" type="search" name="q" placeholder="Mbappé, Wirtz, Konaté..." aria-label="Введите имя игрока">
            <button class="pf-home-search__button" type="submit">Найти</button>
        </form>
    </div>
</section>
'''

css = r'''/* ProFutbik homepage desktop hero — step 44 */

body {
    background: #05070d;
}

.pf-home-hero,
.pf-home-search {
    box-sizing: border-box;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.pf-home-hero *,
.pf-home-hero *::before,
.pf-home-hero *::after,
.pf-home-search *,
.pf-home-search *::before,
.pf-home-search *::after {
    box-sizing: inherit;
}

.pf-home-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    margin: 28px auto 18px;
    width: min(1180px, calc(100% - 40px));
    min-height: 560px;
    padding: 62px;
    border: 1px solid rgba(255, 210, 96, 0.18);
    border-radius: 34px;
    background:
        radial-gradient(circle at 20% 12%, rgba(255, 196, 70, 0.18), transparent 28%),
        radial-gradient(circle at 85% 20%, rgba(51, 102, 255, 0.16), transparent 30%),
        linear-gradient(135deg, rgba(12, 16, 28, 0.98), rgba(4, 7, 13, 0.98) 58%, rgba(10, 8, 4, 0.98));
    box-shadow: 0 28px 90px rgba(0, 0, 0, 0.48);
}

.pf-home-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -2;
    opacity: 0.28;
    background-image:
        linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px);
    background-size: 54px 54px;
    mask-image: linear-gradient(135deg, black, transparent 78%);
}

.pf-home-hero::after {
    content: "";
    position: absolute;
    right: -140px;
    bottom: -200px;
    z-index: -1;
    width: 560px;
    height: 560px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 190, 59, 0.21), transparent 68%);
    filter: blur(2px);
}

.pf-home-hero__inner {
    display: grid;
    grid-template-columns: minmax(0, 1.04fr) minmax(380px, 0.72fr);
    gap: 50px;
    align-items: center;
    min-height: 430px;
}

.pf-home-hero__eyebrow,
.pf-home-search__label {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 18px;
    color: #f4c967;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.pf-home-hero__pulse {
    width: 9px;
    height: 9px;
    border-radius: 999px;
    background: #f4c967;
    box-shadow: 0 0 0 6px rgba(244, 201, 103, 0.14), 0 0 26px rgba(244, 201, 103, 0.72);
}

.pf-home-hero__title {
    max-width: 760px;
    margin: 0;
    color: #ffffff;
    font-size: clamp(44px, 5vw, 76px);
    line-height: 0.94;
    letter-spacing: -0.065em;
    text-wrap: balance;
}

.pf-home-hero__lead {
    max-width: 620px;
    margin: 24px 0 0;
    color: rgba(255, 255, 255, 0.72);
    font-size: 19px;
    line-height: 1.62;
}

.pf-home-hero__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin-top: 34px;
}

.pf-home-hero__button,
.pf-home-search__button,
.pf-home-hero__details {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 900;
    text-decoration: none;
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.pf-home-hero__button:hover,
.pf-home-search__button:hover,
.pf-home-hero__details:hover {
    transform: translateY(-1px);
}

.pf-home-hero__button--primary,
.pf-home-search__button {
    padding: 0 24px;
    color: #090b10;
    background: linear-gradient(135deg, #ffe08a, #f4b840 48%, #d99218);
    box-shadow: 0 14px 34px rgba(232, 176, 51, 0.25);
}

.pf-home-hero__button--ghost {
    padding: 0 24px;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(255, 255, 255, 0.055);
}

.pf-home-hero__button--ghost:hover {
    border-color: rgba(244, 201, 103, 0.42);
    color: #f7d27b;
}

.pf-home-hero__panel {
    position: relative;
    overflow: hidden;
    padding: 26px;
    border: 1px solid rgba(255, 255, 255, 0.11);
    border-radius: 28px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.105), rgba(255, 255, 255, 0.045));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12), 0 24px 70px rgba(0, 0, 0, 0.34);
    backdrop-filter: blur(14px);
}

.pf-home-hero__panel::before {
    content: "";
    position: absolute;
    inset: -1px;
    z-index: -1;
    background: radial-gradient(circle at 50% 0%, rgba(244, 201, 103, 0.22), transparent 42%);
}

.pf-home-hero__panel-top,
.pf-home-hero__player-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
}

.pf-home-hero__panel-label {
    color: rgba(255, 255, 255, 0.72);
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.pf-home-hero__status {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 0 11px;
    border: 1px solid rgba(70, 255, 165, 0.24);
    border-radius: 999px;
    color: #91ffc7;
    background: rgba(28, 210, 118, 0.09);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.pf-home-hero__player-row {
    margin-top: 26px;
    justify-content: flex-start;
}

.pf-home-hero__player-photo-wrap {
    position: relative;
    flex: 0 0 138px;
    height: 172px;
    overflow: hidden;
    border-radius: 24px;
    background:
        radial-gradient(circle at 50% 26%, rgba(244, 201, 103, 0.32), transparent 42%),
        linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.025));
}

.pf-home-hero__player-photo-wrap::after {
    content: "";
    position: absolute;
    inset: auto 14px 0;
    height: 42px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.24);
    filter: blur(12px);
}

.pf-home-hero__player-photo {
    position: relative;
    z-index: 1;
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
    object-position: center bottom;
    filter: drop-shadow(0 22px 30px rgba(0, 0, 0, 0.44));
}

.pf-home-hero__player-info {
    display: grid;
    gap: 7px;
}

.pf-home-hero__player-name {
    color: #ffffff;
    font-size: 27px;
    line-height: 1.05;
    letter-spacing: -0.035em;
}

.pf-home-hero__player-route {
    color: rgba(255, 255, 255, 0.68);
    font-size: 14px;
    font-weight: 700;
}

.pf-home-hero__price {
    margin-top: 6px;
    color: #f4c967;
    font-family: "Russo One", Inter, system-ui, sans-serif;
    font-size: 38px;
    line-height: 1;
    letter-spacing: -0.04em;
}

.pf-home-hero__mini-chart {
    position: relative;
    height: 112px;
    margin-top: 28px;
    border-radius: 22px;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.025)),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.055) 0 1px, transparent 1px 56px);
}

.pf-home-hero__chart-line {
    position: absolute;
    left: 30px;
    right: 30px;
    top: 58px;
    height: 3px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(244,201,103,0.30), #f4c967, #ffe6a1);
    transform: rotate(-9deg);
    transform-origin: center;
    box-shadow: 0 0 18px rgba(244, 201, 103, 0.34);
}

.pf-home-hero__chart-dot {
    position: absolute;
    width: 12px;
    height: 12px;
    border: 2px solid #0b0d13;
    border-radius: 50%;
    background: #f4c967;
    box-shadow: 0 0 0 4px rgba(244, 201, 103, 0.14);
}

.pf-home-hero__chart-dot--one { left: 36px; bottom: 32px; }
.pf-home-hero__chart-dot--two { left: 33%; bottom: 42px; }
.pf-home-hero__chart-dot--three { left: 62%; bottom: 56px; }
.pf-home-hero__chart-dot--four { right: 34px; top: 30px; }

.pf-home-hero__details {
    width: 100%;
    margin-top: 18px;
    color: #f4c967;
    border: 1px solid rgba(244, 201, 103, 0.22);
    background: rgba(244, 201, 103, 0.07);
}

.pf-home-search {
    width: min(1180px, calc(100% - 40px));
    margin: 0 auto 34px;
    padding: 22px;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 26px;
    background: rgba(255, 255, 255, 0.045);
    box-shadow: 0 18px 54px rgba(0, 0, 0, 0.22);
}

.pf-home-search__inner {
    display: grid;
    grid-template-columns: minmax(230px, 0.7fr) minmax(420px, 1fr);
    gap: 20px;
    align-items: center;
}

.pf-home-search__label {
    margin-bottom: 7px;
}

.pf-home-search__title {
    display: block;
    color: #ffffff;
    font-size: 24px;
    line-height: 1.16;
    letter-spacing: -0.035em;
}

.pf-home-search__form {
    display: flex;
    gap: 10px;
    padding: 7px;
    border: 1px solid rgba(255, 255, 255, 0.11);
    border-radius: 999px;
    background: rgba(5, 7, 13, 0.72);
}

.pf-home-search__input {
    min-width: 0;
    flex: 1 1 auto;
    height: 46px;
    padding: 0 18px;
    border: 0;
    outline: 0;
    color: #ffffff;
    background: transparent;
    font: inherit;
    font-size: 15px;
}

.pf-home-search__input::placeholder {
    color: rgba(255, 255, 255, 0.42);
}

.pf-home-search__button {
    min-width: 108px;
    min-height: 46px;
    border: 0;
    cursor: pointer;
}

@media (max-width: 920px) {
    .pf-home-hero {
        padding: 34px 22px;
        width: min(100% - 24px, 680px);
        border-radius: 26px;
    }

    .pf-home-hero__inner,
    .pf-home-search__inner {
        grid-template-columns: 1fr;
    }

    .pf-home-hero__title {
        font-size: clamp(38px, 10vw, 56px);
    }

    .pf-home-search {
        width: min(100% - 24px, 680px);
    }

    .pf-home-search__form {
        border-radius: 22px;
        flex-direction: column;
    }
}
'''

partial_path.write_text(partial, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")

original = index_path.read_text(encoding="utf-8")

start_marker = "<!-- PROFUTBIK_HOMEPAGE_STEP44_START -->"
end_marker = "<!-- PROFUTBIK_HOMEPAGE_STEP44_END -->"
block = f'''{start_marker}
<link rel="stylesheet" href="{{{{ "css/homepage-desktop-step1.css" | relURL }}}}">
{{{{ partial "homepage-desktop-hero.html" . }}}}
{end_marker}
'''

# Remove previous step 44 block if the script is run again.
pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\s*", re.DOTALL)
updated = pattern.sub("", original)

inserted = False

# Best case: Hugo base template with define "main".
match = re.search(r"({{\s*define\s+\"main\"\s*}})", updated)
if match:
    pos = match.end()
    updated = updated[:pos] + "\n" + block + updated[pos:]
    inserted = True

# Common current project pattern: header partial exists in index itself.
if not inserted:
    match = re.search(r"({{\s*partial\s+\"header\.html\"\s+\.\s*}})", updated)
    if match:
        pos = match.end()
        updated = updated[:pos] + "\n" + block + updated[pos:]
        inserted = True

# Full HTML without baseof: place after opening body if possible.
if not inserted:
    match = re.search(r"(<body[^>]*>)", updated, flags=re.IGNORECASE)
    if match:
        pos = match.end()
        updated = updated[:pos] + "\n" + block + updated[pos:]
        inserted = True

# Safe fallback: put it at the top of the homepage template.
if not inserted:
    updated = block + "\n" + updated

index_path.write_text(updated, encoding="utf-8")

print("Backup:", backup_dir)
print("Updated:", index_path)
print("Created:", partial_path)
print("Created:", css_path)
