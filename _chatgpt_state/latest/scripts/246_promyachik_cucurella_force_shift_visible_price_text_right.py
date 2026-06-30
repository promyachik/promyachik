
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_246_before_force_shift_cucurella_price_right_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_246_cucurella_force_shift_visible_price_text_right_report.txt"

SINGLE = PROJECT / "layouts" / "transfers" / "single.html"
BASEOF = PROJECT / "layouts" / "_default" / "baseof.html"
STYLE = PROJECT / "static" / "css" / "style.css"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

SHIFT_PX = 170

START = "<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT START -->"
END = "<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT END -->"

CSS_START = "/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT START */"
CSS_END = "/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT END */"

OLD_INCLUDES = [
    '{{ partial "promyachik-cucurella-align-price-labels-242.html" . }}',
    '{{ partial "promyachik-cucurella-move-prices-to-club-x-244.html" . }}',
]

OLD_PARTIALS = [
    PROJECT / "layouts" / "partials" / "promyachik-cucurella-align-price-labels-242.html",
    PROJECT / "layouts" / "partials" / "promyachik-cucurella-move-prices-to-club-x-244.html",
]

BAD_CSS_BLOCKS = [
    ("/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN START */", "/* PROMYACHIK 242 CUCURELLA PRICE LABEL ALIGN END */"),
    ("/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS START */", "/* PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END */"),
    ("/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT START */", "/* PROMYACHIK 244 CUCURELLA PRICE MOVE SUPPORT END */"),
    ("/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT START */", "/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT END */"),
    (CSS_START, CSS_END),
]

commands = []
changed = []
warnings = []

RUNTIME_SCRIPT_TEMPLATE = r'''
{{ if in .RelPermalink "/transfers/marc-cucurella-real-madrid/" }}
<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT START -->
<script>
(function () {
    if (window.__promyachikCucurellaForceShift246Ready) {
        return;
    }

    window.__promyachikCucurellaForceShift246Ready = true;

    var SHIFT = __SHIFT_PX__;
    var PRICE_RE = /€\s*\d+(?:[.,]\d+)?\s*(?:M|млн|m|тыс|k)?/i;
    var BAD_RE = /(bonus|бонус|сделк|переход|источник|первоисточник|official|официально|сейчас|current|updated|обновлено|ticker|трансферная новость)/i;

    function txt(node) {
        return (node && node.textContent || "").replace(/\s+/g, " ").trim();
    }

    function visible(el) {
        if (!el || !(el instanceof Element)) {
            return false;
        }

        var rect = el.getBoundingClientRect();
        var style = window.getComputedStyle(el);

        return rect.width > 0 &&
            rect.height > 0 &&
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            style.opacity !== "0";
    }

    function badContainer(el) {
        return !!(el && el.closest("header, nav, footer, .pf-ticker, .bottom-transfer-strip-v3, script, style"));
    }

    function setImportant(el, prop, value) {
        el.style.setProperty(prop, value, "important");
    }

    function wrapPriceTextNodes() {
        var walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function (node) {
                    var value = (node.nodeValue || "").replace(/\s+/g, " ").trim();

                    if (!PRICE_RE.test(value) || BAD_RE.test(value) || value.length > 90) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    var parent = node.parentElement;

                    if (!parent || badContainer(parent) || parent.closest(".promyachik-cucurella-force-price-246")) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        var nodes = [];
        var node;

        while ((node = walker.nextNode())) {
            nodes.push(node);
        }

        nodes.forEach(function (textNode) {
            var span = document.createElement("span");
            span.className = "promyachik-cucurella-force-price-246";
            span.setAttribute("data-promyachik-shift", String(SHIFT));
            span.textContent = textNode.nodeValue;
            textNode.parentNode.replaceChild(span, textNode);
        });
    }

    function collectHtmlPrices() {
        var nodes = Array.prototype.slice.call(document.querySelectorAll(".promyachik-cucurella-force-price-246, span, strong, em, b, div, li, p, a"))
            .filter(function (el) {
                var t = txt(el);
                return visible(el) &&
                    !badContainer(el) &&
                    PRICE_RE.test(t) &&
                    !BAD_RE.test(t) &&
                    t.length <= 110;
            })
            .map(function (el) {
                var r = el.getBoundingClientRect();
                return {
                    el: el,
                    text: txt(el),
                    top: r.top,
                    left: r.left,
                    width: r.width,
                    height: r.height
                };
            });

        var out = [];

        nodes.sort(function (a, b) {
            var dt = Math.abs(a.top - b.top);
            if (dt > 6) return a.top - b.top;
            return (a.width * a.height) - (b.width * b.height);
        });

        nodes.forEach(function (item) {
            var duplicate = out.some(function (old) {
                return Math.abs(old.top - item.top) < 8 &&
                    Math.abs(old.left - item.left) < 8 &&
                    old.text === item.text;
            });

            if (!duplicate) {
                out.push(item);
            }
        });

        return out;
    }

    function chooseBottomPriceCluster(items) {
        if (!items.length) {
            return [];
        }

        var rows = [];

        items.forEach(function (item) {
            var row = rows.find(function (r) {
                return Math.abs(r.top - item.top) < 32;
            });

            if (!row) {
                row = { top: item.top, items: [] };
                rows.push(row);
            }

            row.items.push(item);
            row.top = (row.top * (row.items.length - 1) + item.top) / row.items.length;
        });

        rows.forEach(function (row) {
            row.items.sort(function (a, b) { return a.left - b.left; });
        });

        rows.sort(function (a, b) {
            if (b.items.length !== a.items.length) {
                return b.items.length - a.items.length;
            }

            return b.top - a.top;
        });

        var chosen = rows.find(function (row) {
            return row.items.length >= 2;
        });

        if (chosen) {
            return chosen.items.slice(0, 8);
        }

        return items.sort(function (a, b) { return b.top - a.top; }).slice(0, 5);
    }

    function shiftHtmlPrices() {
        wrapPriceTextNodes();

        var items = chooseBottomPriceCluster(collectHtmlPrices());

        items.forEach(function (item) {
            var el = item.el;

            el.classList.add("promyachik-cucurella-force-shifted-246");
            el.setAttribute("data-promyachik-force-shifted-246", "right-" + SHIFT);

            setImportant(el, "display", "inline-flex");
            setImportant(el, "flex-direction", "column");
            setImportant(el, "align-items", "center");
            setImportant(el, "justify-content", "flex-start");
            setImportant(el, "text-align", "center");
            setImportant(el, "white-space", "nowrap");
            setImportant(el, "position", "relative");
            setImportant(el, "left", SHIFT + "px");
            setImportant(el, "transform", "translateX(" + SHIFT + "px)");
            setImportant(el, "margin-left", SHIFT + "px");
            setImportant(el, "z-index", "999");
        });

        return items.length;
    }

    function shiftSvgPrices() {
        var shifted = 0;

        Array.prototype.slice.call(document.querySelectorAll("svg text")).forEach(function (el) {
            var t = txt(el);

            if (!PRICE_RE.test(t) || BAD_RE.test(t) || !visible(el)) {
                return;
            }

            el.classList.add("promyachik-cucurella-force-shifted-246");
            el.setAttribute("data-promyachik-force-shifted-246", "svg-right-" + SHIFT);

            var current = el.getAttribute("transform") || "";
            el.setAttribute("transform", (current + " translate(" + SHIFT + " 0)").trim());
            shifted += 1;
        });

        return shifted;
    }

    function run() {
        var htmlCount = shiftHtmlPrices();
        var svgCount = shiftSvgPrices();
        document.documentElement.setAttribute("data-promyachik-cucurella-force-shift-246", String(htmlCount + svgCount));
    }

    function boot() {
        run();
        [80, 180, 420, 900, 1600, 2600].forEach(function (delay) {
            window.setTimeout(run, delay);
        });

        window.addEventListener("resize", function () {
            window.requestAnimationFrame(run);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
</script>
<!-- PROMYACHIK 246 CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT END -->
{{ end }}
'''
RUNTIME_SCRIPT = RUNTIME_SCRIPT_TEMPLATE.replace("__SHIFT_PX__", str(SHIFT_PX))

CSS_BLOCK = r'''
/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT START */

.promyachik-cucurella-force-price-246,
.promyachik-cucurella-force-shifted-246 {
    text-align: center !important;
    white-space: nowrap !important;
}

.promyachik-cucurella-force-shifted-246 {
    position: relative !important;
    left: __SHIFT_PX__px !important;
    transform: translateX(__SHIFT_PX__px) !important;
    margin-left: __SHIFT_PX__px !important;
    z-index: 999 !important;
}

/* PROMYACHIK 246 CUCURELLA FORCE PRICE SHIFT END */
'''.replace("__SHIFT_PX__", str(SHIFT_PX))

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

def run_cmd(cmd):
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

def strip_between(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)

def cleanup_old_templates():
    for path in [SINGLE, BASEOF]:
        if not path.exists():
            continue

        text = read(path)
        original = text

        text = strip_between(text, START, END)

        for include in OLD_INCLUDES:
            text = text.replace(include, "")

        text = re.sub(r"\n{4,}", "\n\n\n", text)

        if text != original:
            write(path, text, "remove old Cucurella align/shift hooks")

    for path in OLD_PARTIALS:
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete old Cucurella align partial", True, "exists", "deleted"))

def install_runtime_in_single():
    if not SINGLE.exists():
        raise RuntimeError(f"missing transfer single template: {SINGLE}")

    text = read(SINGLE)
    text = strip_between(text, START, END)
    text = text.rstrip() + "\n\n" + RUNTIME_SCRIPT.strip() + "\n"
    write(SINGLE, text, f"append Cucurella-only runtime force shift script by {SHIFT_PX}px")

def cleanup_style():
    if not STYLE.exists():
        warnings.append(f"style.css not found: {STYLE}")
        return

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_between(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "add 246 force shift support CSS")

def patch_public_direct():
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        warnings.append(f"public Cucurella HTML not found: {public_path}")
        return False

    html = read(public_path)
    html = strip_between(html, START, END)

    script = re.sub(r"{{\s*if\s+in\s+\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*}}", "", RUNTIME_SCRIPT)
    script = re.sub(r"{{\s*end\s*}}\s*$", "", script.strip())

    if "</body>" in html:
        html = html.replace("</body>", script + "\n</body>")
    else:
        html = html.rstrip() + "\n" + script + "\n"

    write(public_path, html, "directly inject 246 force shift script into built public Cucurella HTML")
    return True

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in [
        "__promyachikCucurellaForceShift246Ready",
        "promyachik-cucurella-force-shifted-246",
        f"left: {SHIFT_PX}px",
        f"translateX({SHIFT_PX}px)",
        "data-promyachik-cucurella-force-shift-246",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 450): idx + 1500].replace("\n", " ")[:1950]))

    return fragments[:10]

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    ramos_before = sha(RAMOS_PAGE)
    cucurella_before = sha(CUCURELLA_PAGE)

    ok = True
    error_text = ""
    hugo = None
    checks = {}
    fragments = []
    direct_public_patched = False

    try:
        cleanup_old_templates()
        install_runtime_in_single()
        cleanup_style()

        hugo = run_cmd(["hugo", "-D"])

        direct_public_patched = patch_public_direct()

        single_text = read(SINGLE) if SINGLE.exists() else ""
        style_text = read(STYLE) if STYLE.exists() else ""

        public_cucurella = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"
        public_text = read(public_cucurella) if public_cucurella.exists() else ""
        public_ramos = PROJECT / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
        public_ramos_text = read(public_ramos) if public_ramos.exists() else ""

        ramos_after = sha(RAMOS_PAGE)
        cucurella_after = sha(CUCURELLA_PAGE)

        fragments = collect_public_fragments()

        checks = {
            "hugo_exit_code": hugo.returncode,
            "shift_px": SHIFT_PX,
            "ramos_content_untouched": ramos_before == ramos_after,
            "cucurella_content_untouched": cucurella_before == cucurella_after,
            "single_has_246_script": "__promyachikCucurellaForceShift246Ready" in single_text,
            "style_has_246_css": CSS_START in style_text and CSS_END in style_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_has_246_script": "__promyachikCucurellaForceShift246Ready" in public_text,
            "public_has_force_shift_class": "promyachik-cucurella-force-shifted-246" in public_text,
            "public_has_shift_px": f"left: {SHIFT_PX}px" in public_text and f"translateX({SHIFT_PX}px)" in public_text,
            "public_direct_patched": direct_public_patched,
            "public_ramos_has_no_246_script": "__promyachikCucurellaForceShift246Ready" not in public_ramos_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["single_has_246_script"]
            and checks["style_has_246_css"]
            and checks["public_cucurella_exists"]
            and checks["public_has_246_script"]
            and checks["public_has_force_shift_class"]
            and checks["public_has_shift_px"]
            and checks["public_ramos_has_no_246_script"]
        )
    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 246 - CUCURELLA FORCE SHIFT VISIBLE PRICE TEXT RIGHT")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("WHY 245 DID NOTHING")
    lines.append("- 245 stopped before Hugo because it did not find the exact template output.")
    lines.append("- Report 245 showed changed files = 0.")
    lines.append("")
    lines.append("RULE")
    lines.append("- Target: Cucurella visible EUR price text only.")
    lines.append("- No Ramos content change.")
    lines.append("- No Cucurella content change.")
    lines.append("- No graph/club/dot/logo rewrite.")
    lines.append("- This does NOT search the template output.")
    lines.append("- It injects a runtime script into the transfer page template and also directly into built public Cucurella HTML.")
    lines.append(f"- The runtime script wraps visible EUR price text nodes and shifts selected bottom price row RIGHT by {SHIFT_PX}px.")
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
    if error_text:
        lines.append("ERROR")
        lines.append(error_text)
        lines.append("")
    lines.append("OBSERVED CUCURELLA PUBLIC FRAGMENTS")
    if fragments:
        for token, fragment in fragments:
            lines.append(f"- token={token} | {fragment}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("CHECKS")
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- VERIFIED_OK: {ok}")
    lines.append("")
    if warnings:
        lines.append("WARNINGS")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("HUGO")
    if hugo is None:
        lines.append("- not run")
    else:
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
    lines.append("NO RAMOS CONTENT CHANGE.")
    lines.append("NO CUCURELLA CONTENT CHANGE.")
    lines.append("NO SITE OPENED.")
    lines.append("NO PUSH MADE.")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8", errors="ignore"))

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
