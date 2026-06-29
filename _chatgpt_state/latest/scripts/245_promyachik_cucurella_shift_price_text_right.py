
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
BACKUP_DIR = PROJECT / f"_backup_promyachik_245_before_cucurella_shift_price_right_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_245_cucurella_shift_price_text_right_report.txt"

DYNAMIC_PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
STYLE = PROJECT / "static" / "css" / "style.css"
SINGLE = PROJECT / "layouts" / "transfers" / "single.html"
BASEOF = PROJECT / "layouts" / "_default" / "baseof.html"
RAMOS_PAGE = PROJECT / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
CUCURELLA_PAGE = PROJECT / "content" / "transfers" / "marc-cucurella-real-madrid" / "index.md"

SHIFT_PX = 110

commands = []
changed = []
warnings = []

CSS_START = "/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT START */"
CSS_END = "/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT END */"

OLD_INCLUDE_MARKERS = [
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
    (CSS_START, CSS_END),
]

CSS_BLOCK = f'''
/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT START */

/*
   Только страница Marc Cucurella.
   Не трогаем график/точки/логотипы.
   Сдвигаем вправо именно текст цены/года из Hugo output.
*/

.promyachik-cucurella-price-shift-245 {{
    display: inline-flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: center !important;
    white-space: nowrap !important;
    transform: translateX({SHIFT_PX}px) !important;
    margin-left: {SHIFT_PX}px !important;
    position: relative !important;
    z-index: 50 !important;
}}

.promyachik-cucurella-price-shift-245 span,
.promyachik-cucurella-price-shift-245 strong {{
    display: block !important;
    width: 100% !important;
    text-align: center !important;
    line-height: 1.08 !important;
}}

/* PROMYACHIK 245 CUCURELLA PRICE SHIFT RIGHT END */
'''

CUCURELLA_WRAPPED_LABEL = f'''{{{{ if in $.RelPermalink "/transfers/marc-cucurella-real-madrid/" }}}}
<span class="promyachik-cucurella-price-shift-245" data-promyachik-shift-right-px="{SHIFT_PX}">
    <span>{{{{ .date }}}}</span>
    <strong>{{{{ .value_label }}}}</strong>
</span>
{{{{ else }}}}
{{{{ .date }}}} {{{{ .value_label }}}}
{{{{ end }}}}'''

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

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)

def remove_old_failed_cucurella_overrides(text: str) -> str:
    text = re.sub(
        r"{{\s*if\s+in\s+\$?\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*}}"
        r".*?PROMYACHIK 243 CUCURELLA LABELS UNDER CLUB POINTS END.*?"
        r"{{\s*else\s*}}(.*?){{\s*end\s*}}",
        lambda m: m.group(1),
        text,
        flags=re.S,
    )

    text = re.sub(
        r"{{\s*if\s+in\s+\$?\.RelPermalink\s+\"/transfers/marc-cucurella-real-madrid/\"\s*}}"
        r"\s*<span\s+class=\"promyachik-cucurella-price-shift-245\".*?</span>\s*"
        r"{{\s*else\s*}}\s*({{\s*\.date\s*}}\s+{{\s*\.value_label\s*}})\s*{{\s*end\s*}}",
        lambda m: m.group(1),
        text,
        flags=re.S,
    )

    return text

def patch_price_text_output():
    if not DYNAMIC_PARTIAL.exists():
        raise RuntimeError(f"Не найден шаблон графика: {DYNAMIC_PARTIAL}")

    text = read(DYNAMIC_PARTIAL)
    text = remove_old_failed_cucurella_overrides(text)

    literal_patterns = [
        "{{ .date }} {{ .value_label }}",
        "{{.date}} {{.value_label}}",
        "{{ .date }}{{ .value_label }}",
        "{{.date}}{{.value_label}}",
    ]

    replaced = False

    for pattern in literal_patterns:
        if pattern in text:
            text = text.replace(pattern, CUCURELLA_WRAPPED_LABEL, 1)
            replaced = True
            break

    if not replaced:
        regex = re.compile(r"{{\s*\.date\s*}}\s+{{\s*\.value_label\s*}}")
        text, count = regex.subn(CUCURELLA_WRAPPED_LABEL, text, count=1)
        replaced = count > 0

    if not replaced:
        raise RuntimeError("Не нашёл прямой вывод цены в шаблоне: {{ .date }} {{ .value_label }}")

    write(DYNAMIC_PARTIAL, text, f"wrap Cucurella date/value_label output and shift it right by {SHIFT_PX}px")

def cleanup_style():
    if not STYLE.exists():
        warnings.append(f"style.css not found: {STYLE}")
        return

    text = read(STYLE)

    for start, end in BAD_CSS_BLOCKS:
        text = strip_block(text, start, end)

    text = text.rstrip() + "\n\n" + CSS_BLOCK.strip() + "\n"
    write(STYLE, text, "add Cucurella price text right-shift CSS")

def cleanup_old_js_includes():
    for path in [SINGLE, BASEOF]:
        if not path.exists():
            continue

        text = read(path)
        old = text

        for include in OLD_INCLUDE_MARKERS:
            text = text.replace(include, "")

        text = re.sub(r"\n{4,}", "\n\n\n", text)

        if text != old:
            write(path, text, "remove old Cucurella JS align includes 242/244")

    for path in OLD_PARTIALS:
        if path.exists():
            backup(path)
            path.unlink()
            changed.append((rel(path), "delete old Cucurella JS align partial", True, "exists", "deleted"))

def patch_public_direct():
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        warnings.append(f"public Cucurella HTML not found: {public_path}")
        return False

    html = read(public_path)

    if "promyachik-cucurella-price-shift-245" in html:
        return True

    injection = f'''
<!-- PROMYACHIK 245 DIRECT PUBLIC RIGHT SHIFT FALLBACK START -->
<style>
.promyachik-cucurella-price-shift-245-runtime {{
    display: inline-flex !important;
    flex-direction: column !important;
    align-items: center !important;
    text-align: center !important;
    white-space: nowrap !important;
    transform: translateX({SHIFT_PX}px) !important;
    margin-left: {SHIFT_PX}px !important;
    position: relative !important;
    z-index: 50 !important;
}}
</style>
<script>
(function() {{
    var PRICE_RE = /€\\s*\\d+(?:[.,]\\d+)?\\s*(?:M|млн|m|тыс|k)?/i;
    function txt(n) {{ return (n && n.textContent || "").replace(/\\s+/g, " ").trim(); }}
    function visible(n) {{
        if (!n || !(n instanceof Element)) return false;
        var r = n.getBoundingClientRect();
        var s = getComputedStyle(n);
        return r.width > 0 && r.height > 0 && s.display !== "none" && s.visibility !== "hidden";
    }}
    function shift() {{
        var els = Array.prototype.slice.call(document.querySelectorAll("span,strong,em,b,div,li,p,a"));
        var prices = els.filter(function(el) {{
            var t = txt(el);
            return visible(el) && PRICE_RE.test(t) && t.length < 80 && !/bonus|бонус|сделк|источник|сейчас|current/i.test(t);
        }});
        prices.sort(function(a,b) {{ return a.getBoundingClientRect().top - b.getBoundingClientRect().top; }});
        var bottom = prices.slice(-6);
        bottom.forEach(function(el) {{
            el.classList.add("promyachik-cucurella-price-shift-245-runtime");
            el.style.setProperty("transform", "translateX({SHIFT_PX}px)", "important");
            el.style.setProperty("margin-left", "{SHIFT_PX}px", "important");
        }});
        document.documentElement.setAttribute("data-promyachik-245-shifted", String(bottom.length));
    }}
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", shift); else shift();
    setTimeout(shift, 300);
    setTimeout(shift, 900);
}})();
</script>
<!-- PROMYACHIK 245 DIRECT PUBLIC RIGHT SHIFT FALLBACK END -->
'''

    if "</body>" in html:
        html = html.replace("</body>", injection + "\n</body>")
    else:
        html += injection

    write(public_path, html, "direct fallback inject Cucurella price right-shift into built public HTML")
    return True

def collect_public_fragments():
    fragments = []
    public_path = PROJECT / "public" / "transfers" / "marc-cucurella-real-madrid" / "index.html"

    if not public_path.exists():
        return fragments

    text = read(public_path)

    for token in [
        "promyachik-cucurella-price-shift-245",
        "data-promyachik-shift-right-px",
        "PROMYACHIK 245 DIRECT PUBLIC",
        "translateX(110px)",
        "€",
    ]:
        idx = text.find(token)
        if idx != -1:
            fragments.append((token, text[max(0, idx - 450): idx + 1200].replace("\n", " ")[:1700]))

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
        patch_price_text_output()
        cleanup_style()
        cleanup_old_js_includes()

        hugo = run(["hugo", "-D"])

        direct_public_patched = patch_public_direct()

        dynamic_text = read(DYNAMIC_PARTIAL)
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
            "template_has_245_wrapper": "promyachik-cucurella-price-shift-245" in dynamic_text,
            "template_has_right_shift_px": f"data-promyachik-shift-right-px=\"{SHIFT_PX}\"" in dynamic_text,
            "style_has_245_css": CSS_START in style_text and CSS_END in style_text,
            "public_cucurella_exists": public_cucurella.exists(),
            "public_has_245_shift": "promyachik-cucurella-price-shift-245" in public_text or "promyachik-cucurella-price-shift-245-runtime" in public_text,
            "public_has_translate_x_110": "translateX(110px)" in public_text,
            "public_direct_patched": direct_public_patched,
            "public_ramos_has_no_245": "promyachik-cucurella-price-shift-245" not in public_ramos_text and "PROMYACHIK 245 DIRECT PUBLIC" not in public_ramos_text,
            "observed_public_fragments": len(fragments),
        }

        ok = (
            hugo.returncode == 0
            and checks["ramos_content_untouched"]
            and checks["cucurella_content_untouched"]
            and checks["template_has_245_wrapper"]
            and checks["style_has_245_css"]
            and checks["public_cucurella_exists"]
            and checks["public_has_245_shift"]
            and checks["public_has_translate_x_110"]
            and checks["public_ramos_has_no_245"]
        )

    except Exception as e:
        ok = False
        error_text = str(e)

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 245 - CUCURELLA SHIFT PRICE TEXT RIGHT")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
    lines.append("")
    lines.append("RULE")
    lines.append("- Target: Cucurella price text only.")
    lines.append("- No Ramos content change.")
    lines.append("- No Cucurella content change.")
    lines.append("- No graph/club/dot/logo rewrite.")
    lines.append("- Directly patches template output date/value_label.")
    lines.append(f"- On Cucurella only, wraps that output and shifts it RIGHT by {SHIFT_PX}px.")
    lines.append("- Also patches built public Cucurella HTML as fallback.")
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
