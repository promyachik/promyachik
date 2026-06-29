
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import re
import hashlib
import sys

PROJECT_CANDIDATES = [
    Path(r"C:\Users\Dmitrii\Promyachik"),
    Path(r"C:\Users\Dmitrii\promyachik"),
]
PROJECT = next((p for p in PROJECT_CANDIDATES if p.exists()), PROJECT_CANDIDATES[0])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = PROJECT / f"_backup_promyachik_228_before_remove_ramos_v211_hardfix_{timestamp}"
REPORT = PROJECT / "var" / "promyachik_228_remove_ramos_v211_hardfix_report.txt"

commands = []
changed = []
warnings = []

BAD_MARKERS = [
    "ramos-hardfix-v211.html",
    "pfb-ramos-v211-hardfix-style",
    "pfb-ramos-v211-hardfix",
    "pfb-ramos-v211",
    "goncalo-ramos-550550-black-v211",
    "goncalo-ramos-550550-black-v210",
    "portugal-v211",
    "portugal-v210",
]

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
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    })
    return p

def remove_v211_blocks(text: str) -> str:
    original = text

    # Remove direct missing partial call.
    text = re.sub(
        r'[ \t]*{{\s*partial\s+"ramos-hardfix-v211\.html"\s+\.\s*}}\s*\n?',
        "",
        text
    )

    # Remove conditional inline hardfix blocks that were injected after the partial.
    # They usually start with: {{ if in .RelPermalink "/transfers/goncalo-ramos-ac-milan/" }}
    # and contain pfb-ramos-v211-hardfix-style / script.
    pattern = re.compile(
        r'\s*{{\s*if\s+in\s+\.RelPermalink\s+"/transfers/goncalo-ramos-ac-milan/"\s*}}\s*'
        r'(?:(?!{{\s*end\s*}}).)*?'
        r'(?:pfb-ramos-v211-hardfix-style|pfb-ramos-v211-hardfix|pfb-ramos-v211)'
        r'(?:(?!{{\s*end\s*}}).)*?'
        r'{{\s*end\s*}}\s*',
        flags=re.S
    )
    text = pattern.sub("\n", text)

    # Remove any raw style/script blocks by IDs if left without wrapper.
    text = re.sub(
        r'\s*<style[^>]*id=["\']pfb-ramos-v211-hardfix-style["\'][^>]*>.*?</style>\s*',
        "\n",
        text,
        flags=re.I | re.S
    )
    text = re.sub(
        r'\s*<script[^>]*id=["\']pfb-ramos-v211-hardfix["\'][^>]*>.*?</script>\s*',
        "\n",
        text,
        flags=re.I | re.S
    )

    # Remove broken old image refs if they appear inside templates.
    text = text.replace("/images/players/transfermarkt/goncalo-ramos-550550-black-v211.png", "/images/players/api/41585.png")
    text = text.replace("/images/players/transfermarkt/goncalo-ramos-550550-black-v210.png", "/images/players/api/41585.png")
    text = text.replace("/images/flags/portugal-v211.png", "/images/flags/portugal.svg")
    text = text.replace("/images/flags/portugal-v210.png", "/images/flags/portugal.svg")

    # Normalize literal slash-n if present in templates.
    text = text.replace("\\n\\n", "\n")
    text = text.replace("\\n", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text

def cleanup_templates():
    roots = [
        PROJECT / "layouts",
    ]

    for root in roots:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.html")):
            old = read(path)
            new = remove_v211_blocks(old)
            if new != old:
                write(path, new, "remove broken Ramos v211 hardfix references")

    # Delete the missing/broken partial if it exists, so it cannot be reused.
    partial = PROJECT / "layouts" / "partials" / "ramos-hardfix-v211.html"
    if partial.exists():
        backup(partial)
        partial.unlink()
        changed.append((rel(partial), "delete broken hardfix partial", True, "exists", "deleted"))

def verify_no_bad_markers():
    remaining = []
    for path in (PROJECT / "layouts").rglob("*.html"):
        text = read(path)
        for marker in BAD_MARKERS:
            if marker in text:
                remaining.append((rel(path), marker))
    return remaining

def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT.exists():
        REPORT.write_text(f"ERROR: PROJECT NOT FOUND: {PROJECT}", encoding="utf-8")
        print(REPORT.read_text(encoding="utf-8", errors="ignore"))
        sys.exit(1)

    cleanup_templates()

    remaining_before_hugo = verify_no_bad_markers()

    hugo = run(["hugo", "-D"])

    public_home = PROJECT / "public" / "index.html"
    public_text = read(public_home) if public_home.exists() else ""

    remaining_after = verify_no_bad_markers()

    checks = {
        "hugo_exit_code": hugo.returncode,
        "remaining_v211_markers_in_layouts": remaining_after,
        "public_index_exists": public_home.exists(),
        "public_index_not_placeholder": "Сайт запускается" not in public_text,
        "public_no_literal_slash_n": "\\n" not in public_text,
        "public_has_ticker": ("pf-ticker" in public_text or "bottom-transfer-strip-v3" in public_text),
    }

    ok = (
        hugo.returncode == 0
        and not remaining_after
        and public_home.exists()
        and checks["public_no_literal_slash_n"]
    )

    changed_count = sum(1 for _, _, did, _, _ in changed if did)

    lines = []
    lines.append("PROMYACHIK 228 - REMOVE BROKEN RAMOS V211 HARDFIX FROM TEMPLATES")
    lines.append("=" * 100)
    lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Project dir: {PROJECT}")
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
