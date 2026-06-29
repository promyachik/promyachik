
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import hashlib
import re
import sys

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_229_before_ticker_drag_clean_bottom_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_229_ticker_drag_clean_bottom_report.txt"

commands = []
changed = []

CSS_START = "/* PROMYACHIK 229 TICKER DRAG AND CLEAN BOTTOM START */"
CSS_END = "/* PROMYACHIK 229 TICKER DRAG AND CLEAN BOTTOM END */"

SCRIPT_START = "<!-- PROMYACHIK 229 TICKER DRAG SCRIPT START -->"
SCRIPT_END = "<!-- PROMYACHIK 229 TICKER DRAG SCRIPT END -->"

CSS_BLOCK = '''
/* PROMYACHIK 229 TICKER DRAG AND CLEAN BOTTOM START */

/* Верхняя и нижняя строки снова можно тянуть мышкой */
.pf-ticker--drag-ready .pf-ticker__viewport,
.bottom-transfer-strip-v3--drag-ready .bottom-transfer-strip-v3__viewport {
    cursor: grab !important;
    touch-action: pan-y !important;
    user-select: none !important;
    -webkit-user-select: none !important;
}

.pf-ticker--drag-ready .pf-ticker__viewport.is-dragging,
.bottom-transfer-strip-v3--drag-ready .bottom-transfer-strip-v3__viewport.is-dragging {
    cursor: grabbing !important;
}

.pf-ticker--drag-ready .pf-ticker__track,
.bottom-transfer-strip-v3--drag-ready .bottom-transfer-strip-v3__track {
    animation: none !important;
    will-change: transform !important;
}

.pf-ticker--drag-ready img,
.bottom-transfer-strip-v3--drag-ready img {
    pointer-events: none !important;
    -webkit-user-drag: none !important;
}

/* Нижняя строка: убрать карточные блоки/рамки/подложки за игроками */
.bottom-transfer-strip-v3 {
    min-height: 86px !important;
}

.bottom-transfer-strip-v3__group {
    gap: 34px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

.bottom-transfer-strip-v3__card {
    width: auto !important;
    min-width: 0 !important;
    min-height: 74px !important;
    padding: 0 18px 0 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
    outline: 0 !important;
}

.bottom-transfer-strip-v3__card::before,
.bottom-transfer-strip-v3__card::after {
    content: none !important;
    display: none !important;
}

.bottom-transfer-strip-v3__photo {
    width: 64px !important;
    height: 78px !important;
    flex: 0 0 64px !important;
    overflow: visible !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}

.bottom-transfer-strip-v3__photo img {
    width: 64px !important;
    height: 78px !important;
    object-fit: contain !important;
    object-position: center bottom !important;
    filter: drop-shadow(0 8px 11px rgba(0, 0, 0, 0.55)) !important;
}

.bottom-transfer-strip-v3__body {
    align-self: center !important;
    min-width: 210px !important;
    padding: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}

.bottom-transfer-strip-v3__route,
.bottom-transfer-strip-v3__player,
.bottom-transfer-strip-v3__status {
    background: transparent !important;
    box-shadow: none !important;
}

/* Если фото игрока не загрузилось — оставить маленький текст PF, но без большой карточки */
.bottom-transfer-strip-v3__photo.is-placeholder {
    width: 50px !important;
    height: 50px !important;
    flex-basis: 50px !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 50% !important;
    background: rgba(212, 175, 55, 0.06) !important;
}

/* PROMYACHIK 229 TICKER DRAG AND CLEAN BOTTOM END */
'''

SCRIPT_BLOCK = '''
<!-- PROMYACHIK 229 TICKER DRAG SCRIPT START -->
<script>
(function () {
    if (window.__promyachikTickerDrag229Ready) {
        return;
    }

    window.__promyachikTickerDrag229Ready = true;

    function normalizeOffset(value, loopWidth) {
        if (!loopWidth) {
            return 0;
        }

        while (value <= -loopWidth) {
            value += loopWidth;
        }

        while (value > 0) {
            value -= loopWidth;
        }

        return value;
    }

    function setupTicker(root, options) {
        if (!root || root.dataset.promyachikDrag229 === "true") {
            return;
        }

        const viewport = root.querySelector(options.viewportSelector);
        const track = root.querySelector(options.trackSelector);
        const firstGroup = track ? track.querySelector(options.groupSelector) : null;

        if (!viewport || !track || !firstGroup) {
            return;
        }

        root.dataset.promyachikDrag229 = "true";
        root.classList.add(options.readyClass);

        const baseDuration =
            Math.max(Number(root.dataset.tickerDuration) || options.defaultDuration || 42, 1);

        let loopWidth = 0;
        let offset = 0;
        let lastFrame = performance.now();
        let pointerIsDown = false;
        let isDragging = false;
        let activePointerId = null;
        let dragStartX = 0;
        let dragStartOffset = 0;
        let resumeAt = 0;
        let suppressClickUntil = 0;

        function render() {
            track.style.transform = "translate3d(" + offset + "px, 0, 0)";
        }

        function measure() {
            const previousWidth = loopWidth;
            const rect = firstGroup.getBoundingClientRect();
            const nextWidth = rect.width;

            if (!nextWidth) {
                return;
            }

            const progress = previousWidth ? -offset / previousWidth : 0;

            loopWidth = nextWidth;
            offset = normalizeOffset(-progress * loopWidth, loopWidth);
            render();
        }

        function animate(now) {
            const elapsed = Math.min((now - lastFrame) / 1000, 0.1);
            lastFrame = now;

            if (!pointerIsDown && now >= resumeAt && loopWidth) {
                const speed = loopWidth / baseDuration;

                offset = normalizeOffset(offset - speed * elapsed, loopWidth);
                render();
            }

            requestAnimationFrame(animate);
        }

        function finishPointer(event) {
            if (!pointerIsDown || event.pointerId !== activePointerId) {
                return;
            }

            pointerIsDown = false;

            if (isDragging) {
                isDragging = false;
                suppressClickUntil = performance.now() + 250;
                viewport.classList.remove("is-dragging");

                if (viewport.hasPointerCapture && viewport.hasPointerCapture(event.pointerId)) {
                    viewport.releasePointerCapture(event.pointerId);
                }

                resumeAt = performance.now() + 800;
            } else {
                resumeAt = performance.now();
            }

            activePointerId = null;
        }

        viewport.addEventListener("pointerdown", function (event) {
            if (event.button !== 0 || !loopWidth) {
                return;
            }

            pointerIsDown = true;
            isDragging = false;
            activePointerId = event.pointerId;
            dragStartX = event.clientX;
            dragStartOffset = offset;
            resumeAt = Number.POSITIVE_INFINITY;
        });

        viewport.addEventListener("pointermove", function (event) {
            if (!pointerIsDown || event.pointerId !== activePointerId) {
                return;
            }

            const deltaX = event.clientX - dragStartX;

            if (!isDragging) {
                if (Math.abs(deltaX) < 8) {
                    return;
                }

                isDragging = true;
                viewport.classList.add("is-dragging");

                if (viewport.setPointerCapture) {
                    viewport.setPointerCapture(event.pointerId);
                }
            }

            offset = normalizeOffset(dragStartOffset + deltaX, loopWidth);
            render();
            event.preventDefault();
        });

        viewport.addEventListener("pointerup", finishPointer);
        viewport.addEventListener("pointercancel", finishPointer);

        viewport.addEventListener(
            "click",
            function (event) {
                if (performance.now() < suppressClickUntil) {
                    event.preventDefault();
                    event.stopPropagation();
                }
            },
            true
        );

        viewport.addEventListener("dragstart", function (event) {
            event.preventDefault();
        });

        if ("ResizeObserver" in window) {
            const resizeObserver = new ResizeObserver(measure);
            resizeObserver.observe(firstGroup);
            resizeObserver.observe(viewport);
        } else {
            window.addEventListener("resize", measure);
        }

        requestAnimationFrame(function () {
            measure();
            lastFrame = performance.now();
            requestAnimationFrame(animate);
        });
    }

    function boot() {
        document.querySelectorAll(".pf-ticker").forEach(function (root) {
            setupTicker(root, {
                viewportSelector: ".pf-ticker__viewport",
                trackSelector: ".pf-ticker__track",
                groupSelector: ".pf-ticker__group",
                readyClass: "pf-ticker--drag-ready",
                defaultDuration: 42
            });
        });

        document.querySelectorAll(".bottom-transfer-strip-v3").forEach(function (root) {
            setupTicker(root, {
                viewportSelector: ".bottom-transfer-strip-v3__viewport",
                trackSelector: ".bottom-transfer-strip-v3__track",
                groupSelector: ".bottom-transfer-strip-v3__group",
                readyClass: "bottom-transfer-strip-v3--drag-ready",
                defaultDuration: 52
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
</script>
<!-- PROMYACHIK 229 TICKER DRAG SCRIPT END -->
'''

def sha(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT)).replace("\\", "/")
    except Exception:
        return str(path)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def backup(path: Path):
    if path.exists():
        dst = BACKUP_DIR / rel(path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(path, dst)

def write(path: Path, text: str, label: str):
    before = sha(path)
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    after = sha(path)
    changed.append((rel(path), label, before != after, before, after))

def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False
    )
    commands.append({
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout": p.stdout[-3500:],
        "stderr": p.stderr[-3500:],
    })
    return p

def replace_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), flags=re.S)
    text = pattern.sub("", text)
    return text.rstrip() + "\n\n" + block.strip() + "\n"

def append_css():
    style = PROJECT / "static" / "css" / "style.css"
    existing = read(style) if style.exists() else ""
    new_text = replace_block(existing, CSS_START, CSS_END, CSS_BLOCK)
    write(style, new_text, "add drag cursor + remove bottom player background cards")

def append_drag_script_to_partial(partial_path: Path):
    if not partial_path.exists():
        return

    existing = read(partial_path)
    new_text = replace_block(existing, SCRIPT_START, SCRIPT_END, SCRIPT_BLOCK)
    write(partial_path, new_text, "add guarded drag script for top/bottom tickers")

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    append_css()

    append_drag_script_to_partial(PROJECT / "layouts" / "partials" / "transfer-ticker.html")
    append_drag_script_to_partial(PROJECT / "layouts" / "partials" / "footer-transfer-ticker.html")

    hugo = run(["hugo", "-D"])

    public_home = PROJECT / "public" / "index.html"
    public_text = read(public_home) if public_home.exists() else ""
    style_text = read(PROJECT / "static" / "css" / "style.css") if (PROJECT / "static" / "css" / "style.css").exists() else ""

    checks = {
        "hugo_exit_code": hugo.returncode,
        "public_index_exists": public_home.exists(),
        "public_has_drag_script": "__promyachikTickerDrag229Ready" in public_text,
        "public_has_top_drag_ready_css_class_reference": "pf-ticker--drag-ready" in public_text,
        "public_has_bottom_drag_ready_css_class_reference": "bottom-transfer-strip-v3--drag-ready" in public_text,
        "style_has_229_css_block": CSS_START in style_text and CSS_END in style_text,
        "style_removes_bottom_card_background": "bottom-transfer-strip-v3__card" in style_text and "background: transparent !important" in style_text,
        "public_no_literal_slash_n": "\\n" not in public_text,
    }

    ok = (
        hugo.returncode == 0
        and public_home.exists()
        and checks["public_has_drag_script"]
        and checks["style_has_229_css_block"]
        and checks["public_no_literal_slash_n"]
    )

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 229 - TICKER DRAG + CLEAN BOTTOM PLAYER BACKGROUNDS")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- No homepage rewrite.")
    lines.append("- No data/transfers rewrite.")
    lines.append("- No logo/photo path rewrite.")
    lines.append("- Only ticker drag script and bottom ticker visual CSS overrides.")
    lines.append("")
    lines.append("BACKUP")
    lines.append(f"- {BACKUP_DIR}")
    lines.append("")
    lines.append("CHANGED FILES")
    if changed:
        for path_rel, label, did, before, after in changed:
            lines.append(f"- {path_rel} | {label} | changed={did}")
    else:
        lines.append("- none")
    lines.append(f"- EFFECTIVE_CHANGED_FILES: {changed_count}")
    lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    lines.append("HUGO")
    lines.append(f"- exit_code: {hugo.returncode}")
    lines.append("--- STDOUT tail ---")
    lines.append(hugo.stdout[-2500:])
    lines.append("--- STDERR tail ---")
    lines.append(hugo.stderr[-2500:])
    lines.append("")
    lines.append("COMMAND LOG")
    for c in commands:
        lines.append("-" * 70)
        lines.append(f"COMMAND: {c['cmd']}")
        lines.append(f"EXIT_CODE: {c['returncode']}")
        if c["stdout"]:
            lines.append("--- STDOUT ---")
            lines.append(c["stdout"])
        if c["stderr"]:
            lines.append("--- STDERR ---")
            lines.append(c["stderr"])
    lines.append("")
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
