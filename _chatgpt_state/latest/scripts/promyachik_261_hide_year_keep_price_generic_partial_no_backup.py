from pathlib import Path
import subprocess
import datetime
import re

PROJECT = Path(__file__).resolve().parents[1]
PARTIAL = PROJECT / "layouts" / "partials" / "transfer-player-market-value-chart.html"
REPORT = PROJECT / "var" / "promyachik_261_hide_year_keep_price_generic_partial_no_backup_report.txt"

MARK_START = "{{/* PROMYACHIK 261: hide chart year only on Cucurella; keep price */}}"
VAR_LINE = '{{- $promyachik261HideYearOnly := or (in (lower (default "" .RelPermalink)) "cucurella") (in (lower (default "" .Title)) "cucurella") -}}'

log = []

def write_report(status):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    body = []
    body.append("PROMYACHIK 261 - HIDE YEAR KEEP PRICE - GENERIC PARTIAL - NO BACKUP")
    body.append("=" * 100)
    body.append(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    body.append(f"Project dir: {PROJECT}")
    body.append("")
    body.append("RULE")
    body.append("- Hide only the year/date line above price labels in the player dynamic value chart.")
    body.append("- Keep price/value_label visible.")
    body.append("- Do not move prices in this package.")
    body.append("- Do not create any backup folder or backup file.")
    body.append("- No push.")
    body.append("- No site opened.")
    body.append("")
    body.extend(log)
    body.append("")
    body.append(status)
    REPORT.write_text("\n".join(body), encoding="utf-8")

try:
    if not PARTIAL.exists():
        log.append(f"ERROR: partial not found: {PARTIAL}")
        write_report("FAILED")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        raise SystemExit(1)

    text = PARTIAL.read_text(encoding="utf-8")
    original = text

    # Remove old failed marker blocks if they exist, but do not touch unrelated CSS/files.
    old_markers = [
        "PROMYACHIK 258",
        "PROMYACHIK 259",
        "PROMYACHIK 260",
    ]
    for marker in old_markers:
        count = text.count(marker)
        log.append(f"old marker check {marker}: occurrences={count}")

    # Make sure the page-level variable exists once, directly after $chart definition.
    if "$promyachik261HideYearOnly" not in text:
        m = re.search(r"(\{\{-\s*\$chart\s*:=\s*\.Params\.market_value_chart\s*-\}\})", text)
        if not m:
            log.append("ERROR: could not find $chart := .Params.market_value_chart line")
            write_report("FAILED")
            print("FAILED")
            print(f"REPORT: {REPORT}")
            raise SystemExit(1)
        text = text[:m.end()] + "\n" + VAR_LINE + "\n" + MARK_START + text[m.end():]
        log.append("inserted 261 page variable: yes")
    else:
        log.append("inserted 261 page variable: already existed")

    replacements = 0

    # Pattern A: the common backup/current structure: <small>{{ .date }}</small> above <strong>{{ .value_label }}</strong>
    patterns = [
        (
            re.compile(r"(?P<indent>[ \t]*)<small>\s*\{\{\s*\.date\s*\}\}\s*</small>", re.MULTILINE),
            "date small"
        ),
        (
            re.compile(r"(?P<indent>[ \t]*)<small>\s*\{\{\s*\.label\s*\}\}\s*</small>", re.MULTILINE),
            "label small"
        ),
        (
            re.compile(r"(?P<indent>[ \t]*)<span([^>]*class=\"[^\"]*(?:date|year|label)[^\"]*\"[^>]*)>\s*\{\{\s*\.(?:date|label|year|date_label)\s*\}\}\s*</span>", re.MULTILINE),
            "date/label/year span"
        ),
    ]

    for regex, name in patterns:
        def repl(match):
            global replacements
            indent = match.group('indent')
            whole = match.group(0)
            if "$promyachik261HideYearOnly" in whole:
                return whole
            return (
                f"{indent}{{{{- if not $promyachik261HideYearOnly -}}}}\n"
                f"{whole}\n"
                f"{indent}{{{{- end -}}}}"
            )
        text, count = regex.subn(repl, text)
        replacements += count
        log.append(f"wrapped {name}: replacements={count}")

    # Pattern B: inline tokens like {{ .date }} {{ .value_label }}.
    # For Cucurella only, output only price. For all other pages, keep date + price.
    inline_patterns = [
        ("{{ .date }} {{ .value_label }}", '{{ if $promyachik261HideYearOnly }}{{ .value_label }}{{ else }}{{ .date }} {{ .value_label }}{{ end }}'),
        ("{{ .label }} {{ .value_label }}", '{{ if $promyachik261HideYearOnly }}{{ .value_label }}{{ else }}{{ .label }} {{ .value_label }}{{ end }}'),
        ("{{ .year }} {{ .value_label }}", '{{ if $promyachik261HideYearOnly }}{{ .value_label }}{{ else }}{{ .year }} {{ .value_label }}{{ end }}'),
    ]
    for old, new in inline_patterns:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
        replacements += count
        log.append(f"inline token replace {old}: replacements={count}")

    if replacements == 0:
        log.append("ERROR: no year/date markup was found in partial")
        write_report("FAILED")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        raise SystemExit(1)

    # Hard safety: price token must still exist after edit.
    if "value_label" not in text:
        log.append("ERROR: value_label disappeared; stopped before write")
        write_report("FAILED")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        raise SystemExit(1)

    if text != original:
        PARTIAL.write_text(text, encoding="utf-8", newline="\n")
        log.append(f"CHANGED: {PARTIAL}")
    else:
        log.append("UNCHANGED: partial already had 261 edit")

    # Build Hugo.
    cmd = ["hugo", "-D"]
    proc = subprocess.run(cmd, cwd=str(PROJECT), text=True, capture_output=True)
    log.append("")
    log.append("HUGO")
    log.append("COMMAND: hugo -D")
    log.append(f"EXIT_CODE: {proc.returncode}")
    log.append("--- STDOUT tail ---")
    log.append("\n".join(proc.stdout.splitlines()[-30:]))
    log.append("--- STDERR tail ---")
    log.append("\n".join(proc.stderr.splitlines()[-30:]))

    if proc.returncode != 0:
        write_report("FAILED")
        print("FAILED")
        print(f"REPORT: {REPORT}")
        raise SystemExit(proc.returncode)

    log.append("")
    log.append("CHECKS")
    log.append("backup_created: False")
    log.append(f"partial_has_261_variable: {'$promyachik261HideYearOnly' in PARTIAL.read_text(encoding='utf-8')}")
    log.append(f"partial_still_has_value_label: {'value_label' in PARTIAL.read_text(encoding='utf-8')}")
    log.append(f"replacements_total: {replacements}")
    write_report("DONE")
    print("DONE")
    print(f"REPORT: {REPORT}")

except Exception as e:
    log.append(f"UNHANDLED_ERROR: {type(e).__name__}: {e}")
    try:
        write_report("FAILED")
    except Exception:
        pass
    print("FAILED")
    print(f"REPORT: {REPORT}")
    raise
