from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")

JS = (
    PROJECT
    / "static"
    / "js"
    / "transfer-player-market-value-chart.js"
)

CSS = (
    PROJECT
    / "static"
    / "css"
    / "transfer-player-market-value-chart.css"
)

NORMALIZER_JS = '    const normalizeClubLogo = (image) => {\n        if (\n            image.dataset.visibleLogoNormalized === "1"\n            || !image.complete\n            || image.naturalWidth < 1\n            || image.naturalHeight < 1\n        ) {\n            return;\n        }\n\n        try {\n            const source = document.createElement("canvas");\n            const sourceContext = source.getContext(\n                "2d",\n                { willReadFrequently: true }\n            );\n\n            if (!sourceContext) {\n                return;\n            }\n\n            source.width = image.naturalWidth;\n            source.height = image.naturalHeight;\n\n            sourceContext.drawImage(\n                image,\n                0,\n                0,\n                source.width,\n                source.height\n            );\n\n            const pixels = sourceContext.getImageData(\n                0,\n                0,\n                source.width,\n                source.height\n            );\n\n            let left = source.width;\n            let right = -1;\n            let top = source.height;\n            let bottom = -1;\n\n            for (let y = 0; y < source.height; y += 1) {\n                for (let x = 0; x < source.width; x += 1) {\n                    const alpha =\n                        pixels.data[\n                            ((y * source.width) + x) * 4 + 3\n                        ];\n\n                    if (alpha <= 12) {\n                        continue;\n                    }\n\n                    left = Math.min(left, x);\n                    right = Math.max(right, x);\n                    top = Math.min(top, y);\n                    bottom = Math.max(bottom, y);\n                }\n            }\n\n            if (right < left || bottom < top) {\n                image.dataset.visibleLogoNormalized = "1";\n                return;\n            }\n\n            const cropWidth = right - left + 1;\n            const cropHeight = bottom - top + 1;\n            const outputSize = 160;\n            const padding = 8;\n            const available = outputSize - (padding * 2);\n            const scale = Math.min(\n                available / cropWidth,\n                available / cropHeight\n            );\n\n            const drawWidth = cropWidth * scale;\n            const drawHeight = cropHeight * scale;\n            const drawX = (outputSize - drawWidth) / 2;\n            const drawY = (outputSize - drawHeight) / 2;\n\n            const output = document.createElement("canvas");\n            const outputContext = output.getContext("2d");\n\n            if (!outputContext) {\n                return;\n            }\n\n            output.width = outputSize;\n            output.height = outputSize;\n\n            outputContext.drawImage(\n                source,\n                left,\n                top,\n                cropWidth,\n                cropHeight,\n                drawX,\n                drawY,\n                drawWidth,\n                drawHeight\n            );\n\n            image.dataset.visibleLogoNormalized = "1";\n            image.src = output.toDataURL("image/png");\n        } catch (_error) {\n            image.dataset.visibleLogoNormalized = "1";\n        }\n    };\n\n'


def replace_css_block(
    text: str,
    selector: str,
    replacement: str,
) -> str:
    pattern = re.compile(
        re.escape(selector) + r"\s*\{.*?\}",
        flags=re.DOTALL,
    )

    updated, count = pattern.subn(
        replacement,
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "CSS block not found: " + selector
        )

    return updated


def patch_js(text: str) -> str:
    text = re.sub(
        r'const VERSION = "[^"]+";',
        'const VERSION = "31-visible-logo-equalizer";',
        text,
        count=1,
    )

    if "const normalizeClubLogo = (image) => {" not in text:
        marker = "    const geometry = (points) => {"

        if marker not in text:
            raise RuntimeError(
                "Geometry marker not found."
            )

        text = text.replace(
            marker,
            NORMALIZER_JS + marker,
            1,
        )

    old_positions = [
        "`${((coordinate.y - 33) / 150) * 100}%`",
        "`${((coordinate.y - 34) / 150) * 100}%`",
    ]

    replaced = False

    for old in old_positions:
        if old in text:
            text = text.replace(
                old,
                "`${(coordinate.y / 150) * 100}%`",
                1,
            )
            replaced = True
            break

    if (
        not replaced
        and "`${(coordinate.y / 150) * 100}%`"
        not in text
    ):
        raise RuntimeError(
            "Club-logo position formula not found."
        )

    load_marker = """            image.loading = "lazy";

            setLogoSource(
                image,
                logoCandidates(item.club)
            );"""

    load_replacement = """            image.loading = "lazy";

            image.addEventListener(
                "load",
                () => normalizeClubLogo(image)
            );

            setLogoSource(
                image,
                logoCandidates(item.club)
            );"""

    if "normalizeClubLogo(image)" not in text:
        if load_marker not in text:
            raise RuntimeError(
                "Logo loading block not found."
            )

        text = text.replace(
            load_marker,
            load_replacement,
            1,
        )

    return text


def patch_css(text: str) -> str:
    normal_marker = """body.transfer-page .player-market-chart__club-marker {
    --club-logo-size: 38px;
    --club-logo-gap: 10px;
    position: absolute;
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    z-index: 3;
    pointer-events: none;
    transform: translate(-50%, calc(-100% - var(--club-logo-gap)));
}"""

    logo = """body.transfer-page .player-market-chart__club-logo {
    display: block;
    width: var(--club-logo-size);
    height: var(--club-logo-size);
    min-width: var(--club-logo-size);
    min-height: var(--club-logo-size);
    max-width: var(--club-logo-size);
    max-height: var(--club-logo-size);
    object-fit: contain;
    object-position: center;
}"""

    enlarged = """.player-market-chart-modal
.player-market-chart--enlarged
.player-market-chart__club-marker {
    --club-logo-size: 62px;
    --club-logo-gap: 20px;
    width: 68px;
    height: 68px;
}"""

    text = replace_css_block(
        text,
        "body.transfer-page .player-market-chart__club-marker",
        normal_marker,
    )

    text = replace_css_block(
        text,
        "body.transfer-page .player-market-chart__club-logo",
        logo,
    )

    text = replace_css_block(
        text,
        ".player-market-chart-modal\n.player-market-chart--enlarged\n.player-market-chart__club-marker",
        enlarged,
    )

    return text


def validate(js_text: str, css_text: str) -> None:
    required = [
        "31-visible-logo-equalizer",
        "normalizeClubLogo",
        "output.toDataURL",
        "coordinate.y / 150",
        "--club-logo-size: 38px",
        "--club-logo-gap: 10px",
        "--club-logo-size: 62px",
        "--club-logo-gap: 20px",
    ]

    missing = [
        marker
        for marker in required
        if marker not in js_text
        and marker not in css_text
    ]

    if missing:
        raise RuntimeError(
            "Updated files missing: "
            + ", ".join(missing)
        )

    for old in (
        "coordinate.y - 33",
        "coordinate.y - 34",
    ):
        if old in js_text:
            raise RuntimeError(
                "Old logo offset remains: " + old
            )


def validate_build() -> None:
    hugo = shutil.which("hugo")

    if not hugo:
        raise RuntimeError(
            "Hugo not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="profutbik_equal_visible_logos_"
    ) as temporary:
        destination = Path(temporary)

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

        built_js = (
            destination
            / "js"
            / "transfer-player-market-value-chart.js"
        )

        built_css = (
            destination
            / "css"
            / "transfer-player-market-value-chart.css"
        )

        if not built_js.exists() or not built_css.exists():
            raise RuntimeError(
                "Built chart assets not found."
            )

        validate(
            built_js.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ),
            built_css.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ),
        )


def main() -> int:
    for path in (JS, CSS):
        if not path.exists():
            print("ERROR: required file not found:")
            print(path)
            return 1

    old_js = JS.read_bytes()
    old_css = CSS.read_bytes()

    try:
        print()
        print(
            "STEP 1 OF 4: trimming transparent "
            "space inside club logos..."
        )

        new_js = patch_js(
            JS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        print(
            "STEP 2 OF 4: increasing and equalizing "
            "visible logo sizes..."
        )

        new_css = patch_css(
            CSS.read_text(
                encoding="utf-8-sig",
                errors="strict",
            )
        )

        JS.write_text(
            new_js,
            encoding="utf-8",
            newline="\n",
        )

        CSS.write_text(
            new_css,
            encoding="utf-8",
            newline="\n",
        )

        print(
            "STEP 3 OF 4: fixing the gap "
            "above every chart point..."
        )

        validate(new_js, new_css)

        print(
            "STEP 4 OF 4: building a clean "
            "temporary Hugo copy..."
        )

        validate_build()

        print()
        print("DONE")
        print("VISIBLE CLUB LOGO SIZES EQUALIZED")
        print("TRANSPARENT LOGO PADDING REMOVED")
        print("NORMAL CHART LOGOS ENLARGED")
        print("ZOOMED CHART LOGOS ENLARGED")
        print("FIXED GAP ABOVE EVERY CHART POINT")
        print("Temporary verification build removed.")
        return 0

    except Exception as error:
        print()
        print("ERROR: " + str(error))
        print("Restoring previous chart files...")

        JS.write_bytes(old_js)
        CSS.write_bytes(old_css)

        print("Previous chart files restored.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
