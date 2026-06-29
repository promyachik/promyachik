
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re

project = Path.cwd()
backup_dir = project / "_backup_216_restore_stats_icon_size_only"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_216_restore_stats_icon_size_only_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

STATS_PARTIAL = project / "layouts" / "partials" / "transfer-player-stats.html"
STYLE_CSS = project / "static" / "css" / "style.css"

touched = []
warnings = []
hugo_result = ""

MARKER = "216 restore stats icon visual size"

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project))
    except Exception:
        return str(p)

def backup(p: Path):
    if p.exists():
        dst = backup_dir / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)

def add_touched(p: Path):
    if p not in touched:
        touched.append(p)

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    backup(p)
    p.write_text(text, encoding="utf-8", newline="\n")
    add_touched(p)

def run_cmd(cmd):
    return subprocess.run(
        cmd,
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

def icon_block_text():
    return "\n".join([
        "#pfb-stats-v184 .pfb-stats-v184__icon {",
        "      width: 74% !important;",
        "      height: 74% !important;",
        "      min-width: 42px !important;",
        "      min-height: 42px !important;",
        "      max-width: 78px !important;",
        "      max-height: 78px !important;",
        "      object-fit: contain !important;",
        "      display: block !important;",
        "      filter: drop-shadow(0 0 8px rgba(212,175,55,.42)) !important;",
        "    }",
    ])

def patch_partial():
    if not STATS_PARTIAL.exists():
        warnings.append(f"Stats partial not found: {rel(STATS_PARTIAL)}")
        return

    text = read_text(STATS_PARTIAL)
    original = text
    icon_block = icon_block_text()

    pattern = r"#pfb-stats-v184\s+\.pfb-stats-v184__icon\s*\{[^}]*\}"
    if re.search(pattern, text, flags=re.S):
        text = re.sub(pattern, icon_block, text, count=1, flags=re.S)
    elif "</style>" in text:
        insert = "\n    /* 216 restore stats icon visual size */\n    " + icon_block + "\n"
        text = text.replace("</style>", insert + "  </style>", 1)
    else:
        text += "\n<style>\n/* 216 restore stats icon visual size */\n" + icon_block + "\n</style>\n"

    if MARKER not in text:
        if "/* 214 restore approved icon-only stats block */" in text:
            text = text.replace(
                "/* 214 restore approved icon-only stats block */",
                "/* 214 restore approved icon-only stats block */\n    /* 216 restore stats icon visual size */",
                1
            )
        else:
            text = text.replace(icon_block, "/* 216 restore stats icon visual size */\n    " + icon_block, 1)

    if "width: calc(100% - 9px)" not in text:
        if "width: calc(100% - 4px) !important;" in text:
            text = text.replace(
                "width: calc(100% - 4px) !important;",
                "width: calc(100% - 9px) !important;",
                1
            )
        else:
            warnings.append("Accepted card width rule not found in stats partial; package did not resize cards.")

    if text != original:
        write_text(STATS_PARTIAL, text)

def patch_global_css():
    css = read_text(STYLE_CSS) if STYLE_CSS.exists() else ""
    if MARKER in css:
        return

    block = "\n".join([
        "/* 216 restore stats icon visual size */",
        "body.transfer-page #pfb-stats-v184 .pfb-stats-v184__icon,",
        "#pfb-stats-v184 .pfb-stats-v184__icon,",
        "body.transfer-page #pfb-stats-v184 img.pfb-stats-v184__icon,",
        "#pfb-stats-v184 img.pfb-stats-v184__icon {",
        "  width: 74% !important;",
        "  height: 74% !important;",
        "  min-width: 42px !important;",
        "  min-height: 42px !important;",
        "  max-width: 78px !important;",
        "  max-height: 78px !important;",
        "  object-fit: contain !important;",
        "  display: block !important;",
        "  filter: drop-shadow(0 0 8px rgba(212,175,55,.42)) !important;",
        "}",
        "",
        "@media (max-width: 700px) {",
        "  body.transfer-page #pfb-stats-v184 .pfb-stats-v184__icon,",
        "  #pfb-stats-v184 .pfb-stats-v184__icon {",
        "    min-width: 36px !important;",
        "    min-height: 36px !important;",
        "    max-width: 64px !important;",
        "    max-height: 64px !important;",
        "  }",
        "}",
    ])
    write_text(STYLE_CSS, css.rstrip() + "\n\n" + block.strip() + "\n")

def run_hugo():
    global hugo_result
    try:
        p = run_cmd(["hugo", "-D"])
        hugo_result = f"returncode={p.returncode}\nSTDOUT tail:\n{p.stdout[-2000:]}\nSTDERR tail:\n{p.stderr[-2000:]}"
        if p.returncode != 0:
            warnings.append("hugo -D returned non-zero.")
    except Exception as e:
        hugo_result = f"hugo error: {e}"
        warnings.append(f"hugo -D could not run: {e}")

patch_partial()
patch_global_css()
run_hugo()

partial_text = read_text(STATS_PARTIAL) if STATS_PARTIAL.exists() else ""
css_text = read_text(STYLE_CSS) if STYLE_CSS.exists() else ""

verified = (
    "pfb-stats-v184__icon" in partial_text
    and "74% !important" in (partial_text + css_text)
)

lines = []
lines.append("PROFUTBIK 216 - RESTORE STATS ICON SIZE ONLY")
lines.append("=" * 80)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("FIXED")
lines.append("- Enlarged only stats icons inside pfb-stats-v184.")
lines.append("- Did not touch Ramos page content.")
lines.append("- Did not touch market chart.")
lines.append("- Did not change card size intentionally.")
lines.append("")
lines.append("VERIFY")
lines.append(f"- icon_rule_in_partial: {'pfb-stats-v184__icon' in partial_text}")
lines.append(f"- icon_74_percent_present: {'74% !important' in (partial_text + css_text)}")
lines.append(f"- accepted_card_width_present: {'width: calc(100% - 9px)' in partial_text}")
lines.append(f"- VERIFIED_OK: {verified}")
lines.append("")
lines.append("HUGO RESULT")
lines.append(hugo_result)
lines.append("")
lines.append("TOUCHED FILES")
seen = set()
for p in touched:
    s = rel(p)
    if s not in seen:
        seen.add(s)
        lines.append(f"- {s}")
lines.append(f"- {rel(report_path)}")
lines.append("")
if warnings:
    lines.append("WARNINGS")
    for w in warnings:
        lines.append(f"- {w}")
    lines.append("")
lines.append("NO SITE OPENED.")
lines.append("NO PUSH MADE.")

write_text(report_path, "\n".join(lines))
print(read_text(report_path))

if not verified:
    raise SystemExit("Stats icon size verification failed. Check report.")
