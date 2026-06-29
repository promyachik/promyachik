
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import sys

project = Path.cwd()
backup_dir = project / "_backup_218_restore_ramos_page_and_tickers_only"
backup_dir.mkdir(parents=True, exist_ok=True)

report_path = project / "var" / "profutbik_218_restore_ramos_page_and_tickers_only_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)

RAMOS_PAGE = project / "content" / "transfers" / "goncalo-ramos-ac-milan" / "index.md"
HEADER = project / "layouts" / "partials" / "header.html"
TOP_TICKER = project / "layouts" / "partials" / "transfer-ticker.html"
BOTTOM_TICKER = project / "layouts" / "partials" / "footer-transfer-ticker.html"
BASEOF = project / "layouts" / "_default" / "baseof.html"
STYLE_CSS = project / "static" / "css" / "style.css"

BAD = [
    "\\nplayer_image",
    "\\n\\n",
    "pfb-ramos-v211",
    "ramos-hardfix-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
    "portugal-proper",
    "cite",
]

touched = []
warnings = []
commands = []
hugo_result = ""

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(project)).replace("\\", "/")
    except Exception:
        return str(p)

def add_touched(p: Path):
    if p not in touched:
        touched.append(p)

def backup(p: Path):
    if p.exists():
        dst = backup_dir / rel(p)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(p, dst)

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    backup(p)
    p.write_text(text, encoding="utf-8", newline="\n")
    add_touched(p)

def delete_if_exists(p: Path):
    if p.exists():
        backup(p)
        p.unlink()
        add_touched(p)

def run(cmd):
    p = subprocess.run(cmd, cwd=project, capture_output=True)
    out = p.stdout.decode("utf-8", errors="replace")
    err = p.stderr.decode("utf-8", errors="replace")
    commands.append({"cmd": " ".join(cmd), "returncode": p.returncode, "stdout": out[-4000:], "stderr": err[-4000:]})
    return p.returncode, out, err

def bad_text(text: str) -> bool:
    return any(x in text for x in BAD)

def valid_md(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:] and not bad_text(text)

def clean_bad_refs(text: str) -> str:
    text = text.replace('{{ partial "ramos-hardfix-v211.html" . }}', "")
    text = text.replace("{{ partial \"ramos-hardfix-v211.html\" . }}", "")
    text = re.sub(r'<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*', "", text, flags=re.I | re.S)
    text = re.sub(r'<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*', "", text, flags=re.I | re.S)
    replacements = [
        ("\\nplayer_image:", "player_image:"),
        ("\\napi_player_image:", "api_player_image:"),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "/images/players/api/41585.png"),
        ("/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "/images/players/api/41585.png"),
        ("/images/flags/portugal-v211.png", "/images/flags/portugal.svg"),
        ("/images/flags/portugal-v210.png", "/images/flags/portugal.svg"),
        ("/images/flags/portugal-proper.png", "/images/flags/portugal.svg"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def backup_candidates(path_rel: str):
    out = []
    for root in sorted(project.glob("_backup_*"), key=lambda p: p.name):
        if root.name == backup_dir.name:
            continue
        p = root / path_rel
        if p.exists() and p.is_file():
            try:
                out.append((f"backup:{root.name}", read(p)))
            except Exception:
                pass
    return out

def git_candidates(path_rel: str):
    out = []
    hashes = []
    code, stdout, stderr = run(["git", "log", "--all", "--format=%H", "--", path_rel])
    if code == 0:
        hashes.extend([h.strip() for h in stdout.splitlines() if h.strip()])
    for i in range(0, 80):
        hashes.append("HEAD" if i == 0 else f"HEAD~{i}")
    seen = set()
    for rev in hashes:
        if rev in seen:
            continue
        seen.add(rev)
        code, stdout, stderr = run(["git", "show", f"{rev}:{path_rel}"])
        if code == 0 and stdout.strip():
            out.append((f"git:{rev}", stdout))
    return out

def score_ramos(text: str) -> int:
    text = clean_bad_refs(text)
    score = 0
    if valid_md(text):
        score += 1000
    else:
        score -= 1000
    if "Gonçalo Ramos" in text: score += 100
    if "AC Milan" in text: score += 50
    if "Paris" in text: score += 30
    if "market_value" in text: score += 30
    if "market_value_chart" in text: score += 50
    if bad_text(text): score -= 5000
    return score

def restore_ramos_if_missing_or_broken():
    path_rel = "content/transfers/goncalo-ramos-ac-milan/index.md"
    current = read(RAMOS_PAGE) if RAMOS_PAGE.exists() else ""
    if RAMOS_PAGE.exists() and valid_md(current):
        return "current kept"

    candidates = backup_candidates(path_rel) + git_candidates(path_rel)
    best = None
    for source, txt in candidates:
        txt2 = clean_bad_refs(txt)
        sc = score_ramos(txt2)
        if best is None or sc > best[0]:
            best = (sc, source, txt2)
    if best and best[0] >= 900:
        write(RAMOS_PAGE, best[2])
        return f"restored from {best[1]}, score={best[0]}"

    minimal = '''---
title: "Gonçalo Ramos переходит в AC Milan из Paris Saint-Germain"
description: "Gonçalo Ramos согласовал переход из Paris Saint-Germain в AC Milan. Сумма сделки — €74M + add-ons."
date: 2026-06-27
draft: false
type: "transfers"
slug: "goncalo-ramos-ac-milan"
url: "/transfers/goncalo-ramos-ac-milan/"
player: "Gonçalo Ramos"
club_from: "Paris Saint-Germain"
club_to: "AC Milan"
status_label: "СОГЛАСОВАНО"
transfer_fee: "€74M + add-ons"
source_name: "Fabrizio Romano"
player_image: "/images/players/api/41585.png"
api_player_image: "/images/players/api/41585.png"
country_flag_image: "/images/flags/portugal.svg"
flag_image: "/images/flags/portugal.svg"
market_value: "€30M"
value: "€30M"
---

## Gonçalo Ramos → AC Milan

Gonçalo Ramos готовится перейти из Paris Saint-Germain в AC Milan. Сумма сделки — **€74M + add-ons**.
'''
    write(RAMOS_PAGE, minimal)
    warnings.append("Ramos page restored from minimal fallback because no clean backup/git candidate was found.")
    return "minimal fallback created"

def write_ticker_partials():
    top = r'''{{/* Restored top transfer ticker. Do not put literal \n in this file. */}}
{{ $pages := where .Site.RegularPages "Section" "transfers" }}
{{ if gt (len $pages) 0 }}
<div class="transfer-ticker transfer-ticker--top" aria-label="Трансферная строка">
  <div class="transfer-ticker__viewport">
    <div class="transfer-ticker__track">
      {{ range first 16 $pages.ByDate.Reverse }}
        <a class="transfer-ticker__item" href="{{ .RelPermalink }}">
          <span class="transfer-ticker__badge">{{ or .Params.status_label "ТРАНСФЕР" }}</span>
          <span class="transfer-ticker__player">{{ or .Params.player .Params.player_name .Title }}</span>
          {{ with (or .Params.club_to .Params.to .Params.to_club .Params.new_club) }}
            <span class="transfer-ticker__arrow">→</span>
            <span class="transfer-ticker__club">{{ . }}</span>
          {{ end }}
        </a>
      {{ end }}
      {{ range first 16 $pages.ByDate.Reverse }}
        <a class="transfer-ticker__item" href="{{ .RelPermalink }}" aria-hidden="true" tabindex="-1">
          <span class="transfer-ticker__badge">{{ or .Params.status_label "ТРАНСФЕР" }}</span>
          <span class="transfer-ticker__player">{{ or .Params.player .Params.player_name .Title }}</span>
          {{ with (or .Params.club_to .Params.to .Params.to_club .Params.new_club) }}
            <span class="transfer-ticker__arrow">→</span>
            <span class="transfer-ticker__club">{{ . }}</span>
          {{ end }}
        </a>
      {{ end }}
    </div>
  </div>
</div>
{{ end }}
'''
    bottom = r'''{{/* Restored bottom transfer ticker. Do not put literal \n in this file. */}}
{{ $pages := where .Site.RegularPages "Section" "transfers" }}
{{ if gt (len $pages) 0 }}
<div class="transfer-ticker transfer-ticker--bottom" aria-label="Нижняя трансферная строка">
  <div class="transfer-ticker__viewport">
    <div class="transfer-ticker__track transfer-ticker__track--reverse">
      {{ range first 16 $pages.ByDate.Reverse }}
        <a class="transfer-ticker__item" href="{{ .RelPermalink }}">
          <span class="transfer-ticker__badge">{{ or .Params.status_label "ТРАНСФЕР" }}</span>
          <span class="transfer-ticker__player">{{ or .Params.player .Params.player_name .Title }}</span>
          {{ with (or .Params.club_to .Params.to .Params.to_club .Params.new_club) }}
            <span class="transfer-ticker__arrow">→</span>
            <span class="transfer-ticker__club">{{ . }}</span>
          {{ end }}
        </a>
      {{ end }}
      {{ range first 16 $pages.ByDate.Reverse }}
        <a class="transfer-ticker__item" href="{{ .RelPermalink }}" aria-hidden="true" tabindex="-1">
          <span class="transfer-ticker__badge">{{ or .Params.status_label "ТРАНСФЕР" }}</span>
          <span class="transfer-ticker__player">{{ or .Params.player .Params.player_name .Title }}</span>
          {{ with (or .Params.club_to .Params.to .Params.to_club .Params.new_club) }}
            <span class="transfer-ticker__arrow">→</span>
            <span class="transfer-ticker__club">{{ . }}</span>
          {{ end }}
        </a>
      {{ end }}
    </div>
  </div>
</div>
{{ end }}
'''
    write(TOP_TICKER, top)
    write(BOTTOM_TICKER, bottom)

def ensure_header_include():
    if not HEADER.exists():
        write(HEADER, '<header class="site-header"></header>\n{{ partial "transfer-ticker.html" . }}\n')
        return
    text = clean_bad_refs(read(HEADER))
    if 'partial "transfer-ticker.html"' not in text:
        if re.search(r"</header>", text, flags=re.I):
            text = re.sub(r"(?i)</header>", '</header>\n{{ partial "transfer-ticker.html" . }}', text, count=1)
        else:
            text = text.rstrip() + '\n{{ partial "transfer-ticker.html" . }}\n'
    write(HEADER, text)

def ensure_bottom_include():
    include = '{{ partial "footer-transfer-ticker.html" . }}'
    if not BASEOF.exists():
        warnings.append("layouts/_default/baseof.html not found; bottom ticker include was not inserted.")
        return
    text = clean_bad_refs(read(BASEOF))
    if include not in text:
        if re.search(r"</body>", text, flags=re.I):
            text = re.sub(r"(?i)</body>", include + "\n</body>", text, count=1)
        else:
            text = text.rstrip() + "\n" + include + "\n"
    write(BASEOF, text)

def ensure_ticker_css():
    css = read(STYLE_CSS) if STYLE_CSS.exists() else ""
    marker = "218 restore top bottom transfer tickers"
    if marker in css:
        return
    block = r'''
/* 218 restore top bottom transfer tickers */
.transfer-ticker {
  width: 100%;
  overflow: hidden;
  background: #000;
  border-top: 1px solid rgba(212,175,55,.22);
  border-bottom: 1px solid rgba(212,175,55,.22);
  color: #f6d56b;
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
  position: relative;
  z-index: 20;
}
.transfer-ticker--top { margin: 0; }
.transfer-ticker--bottom { margin-top: 28px; }
.transfer-ticker__viewport { width: 100%; overflow: hidden; }
.transfer-ticker__track {
  display: inline-flex;
  align-items: center;
  gap: 18px;
  min-width: max-content;
  padding: 9px 0;
  animation: pfb-transfer-ticker-scroll 34s linear infinite;
}
.transfer-ticker__track--reverse {
  animation-name: pfb-transfer-ticker-scroll-reverse;
  animation-duration: 38s;
}
.transfer-ticker__item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: inherit;
  text-decoration: none;
  padding: 0 4px;
}
.transfer-ticker__badge {
  color: #000;
  background: #d4af37;
  border-radius: 999px;
  padding: 4px 7px;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .05em;
}
.transfer-ticker__player { color: #fff4ba; font-weight: 800; }
.transfer-ticker__arrow, .transfer-ticker__club { color: #d4af37; font-weight: 700; }
@keyframes pfb-transfer-ticker-scroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
@keyframes pfb-transfer-ticker-scroll-reverse {
  from { transform: translateX(-50%); }
  to { transform: translateX(0); }
}
'''
    write(STYLE_CSS, css.rstrip() + "\n\n" + block.strip() + "\n")

def run_hugo():
    global hugo_result
    code, out, err = run(["hugo", "-D"])
    hugo_result = f"returncode={code}\nSTDOUT tail:\n{out[-2500:]}\nSTDERR tail:\n{err[-2500:]}"
    if code != 0:
        warnings.append("hugo -D returned non-zero.")

ramos_result = restore_ramos_if_missing_or_broken()
write_ticker_partials()
ensure_header_include()
ensure_bottom_include()
ensure_ticker_css()
delete_if_exists(project / "layouts" / "partials" / "ramos-hardfix-v211.html")
run_hugo()

public_ramos = project / "public" / "transfers" / "goncalo-ramos-ac-milan" / "index.html"
public_home = project / "public" / "index.html"
public_ramos_text = read(public_ramos) if public_ramos.exists() else ""
public_home_text = read(public_home) if public_home.exists() else ""
header_text = read(HEADER) if HEADER.exists() else ""
top_text = read(TOP_TICKER) if TOP_TICKER.exists() else ""
bottom_text = read(BOTTOM_TICKER) if BOTTOM_TICKER.exists() else ""
baseof_text = read(BASEOF) if BASEOF.exists() else ""

ramos_page_exists = RAMOS_PAGE.exists()
ramos_public_exists = public_ramos.exists()
top_include_ok = 'partial "transfer-ticker.html"' in header_text
bottom_include_ok = 'partial "footer-transfer-ticker.html"' in baseof_text
ticker_partial_ok = "transfer-ticker__track" in top_text and "\\n\\n" not in top_text
bottom_partial_ok = "transfer-ticker__track" in bottom_text and "\\n\\n" not in bottom_text
generated_ticker_ok = "transfer-ticker__track" in public_home_text or "transfer-ticker__track" in public_ramos_text
no_bad_ramos = not bad_text(public_ramos_text) if public_ramos_text else False

verified = (
    ramos_page_exists
    and ramos_public_exists
    and top_include_ok
    and bottom_include_ok
    and ticker_partial_ok
    and bottom_partial_ok
    and generated_ticker_ok
    and no_bad_ramos
)

lines = []
lines.append("PROFUTBIK 218 - RESTORE RAMOS PAGE AND TICKERS ONLY")
lines.append("=" * 90)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("SCOPE")
lines.append("- Did NOT touch stats partial.")
lines.append("- Did NOT touch market chart partial.")
lines.append("- Restored only Ramos route if missing/broken and top/bottom tickers.")
lines.append("")
lines.append("RAMOS PAGE")
lines.append(f"- result: {ramos_result}")
lines.append(f"- content exists: {ramos_page_exists}")
lines.append(f"- public generated exists: {ramos_public_exists}")
lines.append("")
lines.append("TICKERS")
lines.append(f"- top_include_ok_header: {top_include_ok}")
lines.append(f"- bottom_include_ok_baseof: {bottom_include_ok}")
lines.append(f"- ticker_partial_ok: {ticker_partial_ok}")
lines.append(f"- bottom_partial_ok: {bottom_partial_ok}")
lines.append(f"- generated_ticker_ok: {generated_ticker_ok}")
lines.append("")
lines.append("VERIFY")
lines.append(f"- no_bad_ramos_generated: {no_bad_ramos}")
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
lines.append("COMMAND LOG")
for c in commands[-20:]:
    lines.append("-" * 60)
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

write(report_path, "\n".join(lines))
print(read(report_path))

if not verified:
    sys.exit(1)
