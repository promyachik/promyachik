from __future__ import annotations

import datetime as _dt
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
index_path = ROOT / "layouts" / "index.html"
partial_dir = ROOT / "layouts" / "partials"
css_dir = ROOT / "static" / "css"
partial_path = partial_dir / "homepage-desktop-hero.html"
css_path = css_dir / "homepage-desktop-step1.css"

if not index_path.exists():
    raise SystemExit(f"Missing file: {index_path}")

stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / "var" / "backups" / f"homepage_step_45_match_approved_{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(index_path, backup_dir / "layouts_index.html")
if partial_path.exists():
    shutil.copy2(partial_path, backup_dir / "homepage-desktop-hero.html")
if css_path.exists():
    shutil.copy2(css_path, backup_dir / "homepage-desktop-step1.css")

partial_dir.mkdir(parents=True, exist_ok=True)
css_dir.mkdir(parents=True, exist_ok=True)

partial = r'''{{/* ProFutbik homepage desktop — approved visual direction, step 45 */}}
<section class="pfh-approved-hero" aria-labelledby="pfh-approved-title">
    <div class="pfh-approved-hero__glow pfh-approved-hero__glow--gold"></div>
    <div class="pfh-approved-hero__glow pfh-approved-hero__glow--blue"></div>

    <div class="pfh-approved-hero__inner">
        <div class="pfh-approved-hero__copy">
            <h1 id="pfh-approved-title" class="pfh-approved-hero__title">
                Трансферы, слухи<br>
                и рыночная стоимость<br>
                футболистов
            </h1>
            <p class="pfh-approved-hero__lead">
                Следите за всеми трансферами, статусами, рыночной стоимостью и историей цен в одном месте.
            </p>
            <div class="pfh-approved-hero__actions" aria-label="Главные действия">
                <a class="pfh-approved-btn pfh-approved-btn--gold" href="{{ "transfers/" | relURL }}">
                    Смотреть трансферы
                    <span aria-hidden="true">→</span>
                </a>
                <a class="pfh-approved-btn pfh-approved-btn--dark" href="#pf-home-search">
                    <span aria-hidden="true">♙</span>
                    Найти игрока
                </a>
            </div>
        </div>

        <div class="pfh-approved-hero__visual" aria-hidden="true">
            <div class="pfh-approved-hero__player-halo"></div>
            <img
                class="pfh-approved-hero__player"
                src="{{ "images/players/cutout/278.png" | relURL }}"
                alt=""
                loading="eager"
            >
            <div class="pfh-approved-hero__slashes"></div>
        </div>
    </div>
</section>

<section id="pf-home-search" class="pfh-approved-search" aria-label="Поиск игрока или трансфера">
    <form class="pfh-approved-search__form" action="{{ "transfers/" | relURL }}" method="get">
        <span class="pfh-approved-search__icon" aria-hidden="true">⌕</span>
        <input
            class="pfh-approved-search__input"
            type="search"
            name="q"
            placeholder="Поиск игроков, клубов или трансферов..."
            aria-label="Поиск игроков, клубов или трансферов"
        >
        <label class="pfh-approved-search__select">
            <span class="pfh-approved-search__select-text">Все</span>
            <span aria-hidden="true">⌄</span>
        </label>
        <button class="pfh-approved-search__button" type="submit">Найти</button>
    </form>
</section>

<section class="pfh-featured-transfer" aria-labelledby="pfh-featured-title">
    <div class="pfh-featured-transfer__heading">
        <span class="pfh-featured-transfer__star" aria-hidden="true">★</span>
        <h2 id="pfh-featured-title">Главный трансфер дня</h2>
    </div>

    <article class="pfh-featured-card">
        <a class="pfh-featured-card__photo-link" href="{{ "transfers/kylian-mbappe-real-madrid/" | relURL }}" aria-label="Открыть страницу трансфера Kylian Mbappé">
            <img
                class="pfh-featured-card__photo"
                src="{{ "images/players/cutout/278.png" | relURL }}"
                alt="Kylian Mbappé"
                loading="eager"
            >
        </a>

        <div class="pfh-featured-card__info">
            <h3 class="pfh-featured-card__name">Kylian<br>Mbappé</h3>
            <div class="pfh-featured-card__country">🇫🇷 Франция</div>

            <div class="pfh-featured-card__route" aria-label="Маршрут трансфера">
                <img src="{{ "images/clubs/api/85.png" | relURL }}" alt="PSG" loading="lazy">
                <span aria-hidden="true">→</span>
                <img src="{{ "images/clubs/api/541.png" | relURL }}" alt="Real Madrid" loading="lazy">
            </div>

            <div class="pfh-featured-card__fee-label">Цена трансфера</div>
            <div class="pfh-featured-card__fee">€ 180M</div>
            <div class="pfh-featured-card__status">● Official</div>
        </div>

        <div class="pfh-featured-card__chart" aria-label="Превью динамики рыночной стоимости">
            <div class="pfh-featured-card__chart-title">
                <span>Рыночная стоимость</span>
                <small>2018–2025</small>
            </div>

            <svg class="pfh-featured-card__chart-svg" viewBox="0 0 520 260" role="img" aria-label="Рост рыночной стоимости Kylian Mbappé до €180M">
                <defs>
                    <linearGradient id="pfhApprovedLine" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0" stop-color="#d69d2f" stop-opacity="0.85"/>
                        <stop offset="1" stop-color="#ffe08a" stop-opacity="1"/>
                    </linearGradient>
                    <linearGradient id="pfhApprovedArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0" stop-color="#f6c75e" stop-opacity="0.18"/>
                        <stop offset="1" stop-color="#f6c75e" stop-opacity="0"/>
                    </linearGradient>
                    <filter id="pfhApprovedGlow" x="-40%" y="-40%" width="180%" height="180%">
                        <feGaussianBlur stdDeviation="4" result="blur"/>
                        <feMerge>
                            <feMergeNode in="blur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>

                <g class="pfh-featured-card__grid">
                    <line x1="58" y1="44" x2="58" y2="218"/>
                    <line x1="58" y1="218" x2="488" y2="218"/>
                    <line x1="58" y1="174" x2="488" y2="174"/>
                    <line x1="58" y1="130" x2="488" y2="130"/>
                    <line x1="58" y1="86" x2="488" y2="86"/>
                    <line x1="130" y1="44" x2="130" y2="218"/>
                    <line x1="202" y1="44" x2="202" y2="218"/>
                    <line x1="274" y1="44" x2="274" y2="218"/>
                    <line x1="346" y1="44" x2="346" y2="218"/>
                    <line x1="418" y1="44" x2="418" y2="218"/>
                    <line x1="488" y1="44" x2="488" y2="218"/>
                </g>

                <path class="pfh-featured-card__area" d="M58 194 L130 184 L202 146 L274 112 L346 92 L418 76 L488 58 L488 218 L58 218 Z"/>
                <path class="pfh-featured-card__line" d="M58 194 L130 184 L202 146 L274 112 L346 92 L418 76 L488 58"/>

                <g class="pfh-featured-card__points" filter="url(#pfhApprovedGlow)">
                    <circle cx="58" cy="194" r="6"/><circle cx="130" cy="184" r="6"/><circle cx="202" cy="146" r="6"/>
                    <circle cx="274" cy="112" r="6"/><circle cx="346" cy="92" r="6"/><circle cx="418" cy="76" r="6"/><circle cx="488" cy="58" r="6"/>
                </g>

                <g class="pfh-featured-card__labels">
                    <text x="42" y="199">€20M</text>
                    <text x="184" y="141">€80M</text>
                    <text x="255" y="107">€120M</text>
                    <text x="326" y="87">€150M</text>
                    <text x="398" y="71">€160M</text>
                    <text x="458" y="50">€180M</text>
                    <text x="50" y="242">2018</text>
                    <text x="122" y="242">2019</text>
                    <text x="194" y="242">2020</text>
                    <text x="266" y="242">2021</text>
                    <text x="338" y="242">2022</text>
                    <text x="410" y="242">2024</text>
                    <text x="480" y="242">2025</text>
                </g>
            </svg>
        </div>
    </article>
</section>
'''

css = r'''/* ProFutbik homepage desktop — approved visual direction, step 45 */

body {
    background: #05080d;
}

.pfh-approved-hero,
.pfh-approved-search,
.pfh-featured-transfer {
    box-sizing: border-box;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.pfh-approved-hero *,
.pfh-approved-hero *::before,
.pfh-approved-hero *::after,
.pfh-approved-search *,
.pfh-approved-search *::before,
.pfh-approved-search *::after,
.pfh-featured-transfer *,
.pfh-featured-transfer *::before,
.pfh-featured-transfer *::after {
    box-sizing: inherit;
}

.pfh-approved-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    min-height: 440px;
    margin: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background:
        radial-gradient(circle at 70% 44%, rgba(255, 199, 87, 0.24), transparent 20%),
        radial-gradient(circle at 55% 20%, rgba(255, 255, 255, 0.09), transparent 7%),
        linear-gradient(100deg, rgba(5, 8, 13, 1) 0%, rgba(5, 8, 13, 0.96) 38%, rgba(5, 8, 13, 0.40) 62%, rgba(5, 8, 13, 0.82) 100%),
        linear-gradient(135deg, #05080d 0%, #08111a 50%, #020408 100%);
}

.pfh-approved-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -3;
    opacity: 0.55;
    background:
        linear-gradient(125deg, transparent 0 66%, rgba(228, 173, 53, 0.48) 66.2%, transparent 66.8%),
        linear-gradient(126deg, transparent 0 76%, rgba(228, 173, 53, 0.32) 76.1%, transparent 76.6%),
        radial-gradient(circle at 69% 48%, rgba(255, 197, 70, 0.28) 0 1px, transparent 2px),
        radial-gradient(circle at 76% 24%, rgba(255, 197, 70, 0.28) 0 1px, transparent 2px),
        radial-gradient(circle at 84% 64%, rgba(255, 197, 70, 0.28) 0 1px, transparent 2px);
    background-size: auto, auto, 68px 68px, 91px 91px, 73px 73px;
}

.pfh-approved-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -2;
    background:
        linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 82px 82px;
    mask-image: linear-gradient(90deg, transparent, black 40%, transparent 92%);
    opacity: 0.38;
}

.pfh-approved-hero__inner {
    position: relative;
    width: min(1180px, calc(100% - 80px));
    min-height: 440px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: minmax(460px, 0.9fr) minmax(420px, 0.85fr);
    align-items: center;
    gap: 28px;
    padding: 56px 0 70px;
}

.pfh-approved-hero__copy {
    position: relative;
    z-index: 3;
    padding-left: 8px;
}

.pfh-approved-hero__title {
    max-width: 650px;
    margin: 0;
    color: #ffffff;
    font-size: clamp(44px, 4.85vw, 68px);
    line-height: 1.02;
    letter-spacing: -0.055em;
    font-weight: 950;
    text-shadow: 0 14px 42px rgba(0, 0, 0, 0.42);
}

.pfh-approved-hero__lead {
    max-width: 520px;
    margin: 22px 0 0;
    color: rgba(255, 255, 255, 0.76);
    font-size: 18px;
    line-height: 1.55;
}

.pfh-approved-hero__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin-top: 30px;
}

.pfh-approved-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    min-width: 210px;
    min-height: 52px;
    padding: 0 24px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 900;
    line-height: 1;
    text-decoration: none;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.pfh-approved-btn:hover {
    transform: translateY(-1px);
}

.pfh-approved-btn--gold {
    color: #111217;
    background: linear-gradient(135deg, #ffe38a 0%, #f3bd49 48%, #e09b1f 100%);
    border: 1px solid rgba(255, 225, 136, 0.55);
    box-shadow: 0 18px 34px rgba(231, 165, 36, 0.22);
}

.pfh-approved-btn--dark {
    color: #ffffff;
    background: rgba(3, 7, 12, 0.58);
    border: 1px solid rgba(244, 190, 75, 0.55);
}

.pfh-approved-hero__visual {
    position: absolute;
    right: -34px;
    bottom: 0;
    z-index: 2;
    width: min(560px, 48vw);
    height: 430px;
    pointer-events: none;
}

.pfh-approved-hero__player-halo {
    position: absolute;
    right: 84px;
    top: 52px;
    width: 250px;
    height: 250px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 209, 105, 0.34), transparent 68%);
    filter: blur(4px);
}

.pfh-approved-hero__player {
    position: absolute;
    right: 82px;
    bottom: -4px;
    display: block;
    width: min(370px, 38vw);
    max-height: 430px;
    object-fit: contain;
    object-position: center bottom;
    filter: drop-shadow(0 24px 36px rgba(0, 0, 0, 0.58));
}

.pfh-approved-hero__slashes {
    position: absolute;
    right: 8px;
    top: 0;
    width: 240px;
    height: 100%;
    opacity: 0.55;
    background:
        linear-gradient(123deg, transparent 0 52%, rgba(230, 172, 43, 0.62) 52.5%, transparent 53.2%),
        linear-gradient(123deg, transparent 0 68%, rgba(230, 172, 43, 0.36) 68.4%, transparent 69.1%);
}

.pfh-approved-search {
    position: relative;
    z-index: 5;
    width: min(760px, calc(100% - 80px));
    margin: -38px auto 20px;
    transform: translateX(180px);
}

.pfh-approved-search__form {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto auto;
    align-items: center;
    min-height: 66px;
    padding: 8px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 11px;
    background: rgba(13, 18, 24, 0.88);
    box-shadow: 0 18px 56px rgba(0, 0, 0, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.09);
    backdrop-filter: blur(16px);
}

.pfh-approved-search__icon {
    display: inline-flex;
    width: 44px;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-size: 31px;
    line-height: 1;
    opacity: 0.94;
}

.pfh-approved-search__input {
    min-width: 0;
    width: 100%;
    height: 48px;
    border: 0;
    outline: 0;
    background: transparent;
    color: #ffffff;
    font: inherit;
    font-size: 16px;
}

.pfh-approved-search__input::placeholder {
    color: rgba(255, 255, 255, 0.46);
}

.pfh-approved-search__select {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    min-height: 48px;
    padding: 0 16px;
    color: rgba(255, 255, 255, 0.92);
    border-left: 1px solid rgba(255, 255, 255, 0.10);
    font-weight: 700;
}

.pfh-approved-search__button {
    min-width: 120px;
    height: 48px;
    border: 1px solid rgba(255, 225, 136, 0.48);
    border-radius: 8px;
    color: #111217;
    cursor: pointer;
    font: inherit;
    font-size: 15px;
    font-weight: 900;
    background: linear-gradient(135deg, #ffe38a, #f2b63d 55%, #dd9418);
}

.pfh-featured-transfer {
    width: min(1180px, calc(100% - 80px));
    margin: 0 auto 24px;
    padding: 14px 16px 16px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(17, 23, 29, 0.94), rgba(8, 12, 17, 0.96));
    box-shadow: 0 20px 72px rgba(0, 0, 0, 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.pfh-featured-transfer__heading {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 2px 0 12px;
    color: #f4c967;
    text-transform: uppercase;
}

.pfh-featured-transfer__heading h2 {
    margin: 0;
    font-size: 17px;
    line-height: 1;
    letter-spacing: 0.04em;
}

.pfh-featured-transfer__star {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    color: #101216;
    background: #f4c967;
    box-shadow: 0 0 20px rgba(244, 201, 103, 0.38);
}

.pfh-featured-card {
    overflow: hidden;
    display: grid;
    grid-template-columns: 250px 230px minmax(0, 1fr);
    min-height: 285px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    background: rgba(6, 10, 15, 0.76);
}

.pfh-featured-card__photo-link {
    position: relative;
    overflow: hidden;
    display: block;
    min-height: 285px;
    background:
        radial-gradient(circle at 50% 20%, rgba(246, 199, 94, 0.32), transparent 34%),
        linear-gradient(180deg, rgba(255, 210, 100, 0.08), rgba(4, 7, 12, 0.95));
}

.pfh-featured-card__photo-link::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 20% 15%, rgba(255,255,255,0.10), transparent 5%),
        radial-gradient(circle at 70% 35%, rgba(244,201,103,0.20), transparent 4%),
        linear-gradient(145deg, rgba(244, 201, 103, 0.24), transparent 45%);
}

.pfh-featured-card__photo {
    position: relative;
    z-index: 1;
    display: block;
    width: 100%;
    height: 100%;
    min-height: 285px;
    object-fit: contain;
    object-position: center bottom;
    filter: drop-shadow(0 20px 30px rgba(0, 0, 0, 0.48));
}

.pfh-featured-card__info {
    padding: 28px 30px;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012));
}

.pfh-featured-card__name {
    margin: 0;
    color: #ffffff;
    font-size: 32px;
    line-height: 0.96;
    letter-spacing: -0.055em;
}

.pfh-featured-card__country {
    margin-top: 14px;
    color: rgba(255, 255, 255, 0.76);
    font-size: 14px;
}

.pfh-featured-card__route {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-top: 24px;
}

.pfh-featured-card__route img {
    width: 52px;
    height: 52px;
    object-fit: contain;
    filter: drop-shadow(0 7px 10px rgba(0, 0, 0, 0.45));
}

.pfh-featured-card__route span {
    color: #f4c967;
    font-size: 34px;
    line-height: 1;
}

.pfh-featured-card__fee-label {
    margin-top: 22px;
    color: rgba(255, 255, 255, 0.55);
    font-size: 12px;
}

.pfh-featured-card__fee {
    margin-top: 5px;
    color: #f4c967;
    font-family: "Russo One", Inter, system-ui, sans-serif;
    font-size: 34px;
    line-height: 1;
}

.pfh-featured-card__status {
    display: inline-flex;
    margin-top: 9px;
    padding: 6px 10px;
    border-radius: 7px;
    color: #7dffad;
    background: rgba(31, 190, 87, 0.20);
    font-size: 12px;
    font-weight: 900;
    text-transform: uppercase;
}

.pfh-featured-card__chart {
    padding: 24px 26px 14px;
}

.pfh-featured-card__chart-title {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 18px;
    color: #f4c967;
    font-size: 13px;
    font-weight: 900;
    text-transform: uppercase;
}

.pfh-featured-card__chart-title small {
    color: rgba(255, 255, 255, 0.46);
    font-size: 12px;
    font-weight: 700;
    text-transform: none;
}

.pfh-featured-card__chart-svg {
    display: block;
    width: 100%;
    height: 238px;
    margin-top: 2px;
}

.pfh-featured-card__grid line {
    stroke: rgba(255, 255, 255, 0.075);
    stroke-width: 1;
}

.pfh-featured-card__area {
    fill: url(#pfhApprovedArea);
}

.pfh-featured-card__line {
    fill: none;
    stroke: url(#pfhApprovedLine);
    stroke-width: 4;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.pfh-featured-card__points circle {
    fill: #ffd66c;
    stroke: #1a1720;
    stroke-width: 4;
}

.pfh-featured-card__labels text {
    fill: rgba(255, 255, 255, 0.82);
    font-size: 14px;
    font-weight: 800;
}

@media (max-width: 980px) {
    .pfh-approved-hero__inner,
    .pfh-featured-card {
        grid-template-columns: 1fr;
    }

    .pfh-approved-hero__visual {
        opacity: 0.35;
    }

    .pfh-approved-search {
        transform: none;
    }
}
'''

partial_path.write_text(partial, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")

original = index_path.read_text(encoding="utf-8")

markers = [
    ("<!-- PROFUTBIK_HOMEPAGE_STEP44_START -->", "<!-- PROFUTBIK_HOMEPAGE_STEP44_END -->"),
    ("<!-- PROFUTBIK_HOMEPAGE_STEP45_START -->", "<!-- PROFUTBIK_HOMEPAGE_STEP45_END -->"),
]
updated = original
for start_marker, end_marker in markers:
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\s*", re.DOTALL)
    updated = pattern.sub("", updated)

start_marker = "<!-- PROFUTBIK_HOMEPAGE_STEP45_START -->"
end_marker = "<!-- PROFUTBIK_HOMEPAGE_STEP45_END -->"
block = f'''{start_marker}
<link rel="stylesheet" href="{{{{ "css/homepage-desktop-step1.css" | relURL }}}}">
{{{{ partial "homepage-desktop-hero.html" . }}}}
{end_marker}
'''

inserted = False
match = re.search(r"({{\s*define\s+\"main\"\s*}})", updated)
if match:
    pos = match.end()
    updated = updated[:pos] + "\n" + block + updated[pos:]
    inserted = True

if not inserted:
    match = re.search(r"({{\s*partial\s+\"header\.html\"\s+\.\s*}})", updated)
    if match:
        pos = match.end()
        updated = updated[:pos] + "\n" + block + updated[pos:]
        inserted = True

if not inserted:
    match = re.search(r"(<body[^>]*>)", updated, flags=re.IGNORECASE)
    if match:
        pos = match.end()
        updated = updated[:pos] + "\n" + block + updated[pos:]
        inserted = True

if not inserted:
    updated = block + "\n" + updated

index_path.write_text(updated, encoding="utf-8")

print("Backup:", backup_dir)
print("Updated:", index_path)
print("Replaced partial:", partial_path)
print("Replaced CSS:", css_path)
print("Removed wrong step 44 block if it existed")
