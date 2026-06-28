from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import sys

PROJECT = Path(r"C:\Users\Dmitrii\Promyachik")
if not PROJECT.exists():
    # Fallback for unusual launch paths
    PROJECT = Path(__file__).resolve().parents[1]

VERSION = "151_full_limit_player_teams_last5"
BACKUP_DIR = PROJECT / "_backup_151_limit_player_teams_last5"
REPORT_PATH = PROJECT / f"_151_limit_player_teams_last5_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

MARKER_START = "<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_START -->"
MARKER_END = "<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_END -->"

INJECT_BLOCK = r'''
<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_START -->
<style>
  .pfb-hidden-old-team-logo {
    display: none !important;
  }
</style>
<script>
(function () {
  var LIMIT = 5;

  function unique(list) {
    var out = [];
    list.forEach(function (item) {
      if (item && out.indexOf(item) === -1) out.push(item);
    });
    return out;
  }

  function isInsideTicker(el) {
    return !!(el.closest('.transfer-ticker') || el.closest('.top-transfer-ticker') || el.closest('.bottom-transfer-ticker') || el.closest('[data-ticker]'));
  }

  function isUsefulTeamNode(el) {
    if (!el || isInsideTicker(el)) return false;
    if (el.matches('[data-club-name], [data-team-name], [data-market-club], [data-player-club]')) return true;
    if (el.getAttribute('title') || el.getAttribute('aria-label')) return true;
    if (el.querySelector('img, svg')) return true;
    if (el.matches('img, svg')) return true;
    return false;
  }

  function compactNestedNodes(nodes) {
    nodes = nodes.filter(isUsefulTeamNode);
    return nodes.filter(function (node) {
      return !nodes.some(function (other) {
        return other !== node && other.contains(node);
      });
    });
  }

  function limitRow(row) {
    var selectors = [
      '[data-club-name]',
      '[data-team-name]',
      '[data-market-club]',
      '[data-player-club]',
      '.market-chart-club',
      '.market-club',
      '.player-market-club',
      '.market-club-logo',
      '.club-logo-item',
      '.club-logo-wrap',
      '.club-badge',
      '.team-logo-item',
      '.team-badge'
    ];

    var nodes = unique(Array.prototype.slice.call(row.querySelectorAll(selectors.join(','))));
    nodes = compactNestedNodes(nodes);

    if (nodes.length <= LIMIT) {
      nodes.forEach(function (node) { node.classList.remove('pfb-hidden-old-team-logo'); });
      return;
    }

    var firstVisibleIndex = nodes.length - LIMIT;
    nodes.forEach(function (node, index) {
      if (index < firstVisibleIndex) {
        node.classList.add('pfb-hidden-old-team-logo');
      } else {
        node.classList.remove('pfb-hidden-old-team-logo');
      }
    });
  }

  function limitPlayerMarketTeams() {
    var rootSelectors = [
      '.player-market-chart',
      '.profutbik-market-chart',
      '.market-value-chart',
      '.transfer-value-history',
      '.transfer-market-chart',
      '.market-chart',
      '[data-player-market-chart]',
      '[data-market-chart]'
    ];

    var rowSelectors = [
      '.market-chart-clubs',
      '.player-market-chart-clubs',
      '.club-history',
      '.club-timeline',
      '.chart-clubs',
      '.clubs-row',
      '.teams-row',
      '[data-club-timeline]',
      '[data-team-list]'
    ];

    var roots = unique(Array.prototype.slice.call(document.querySelectorAll(rootSelectors.join(','))));

    roots.forEach(function (root) {
      if (isInsideTicker(root)) return;

      var rows = unique(Array.prototype.slice.call(root.querySelectorAll(rowSelectors.join(','))));
      if (!rows.length) rows = [root];

      rows.forEach(limitRow);
    });
  }

  function runSoon() {
    limitPlayerMarketTeams();
    window.setTimeout(limitPlayerMarketTeams, 250);
    window.setTimeout(limitPlayerMarketTeams, 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runSoon);
  } else {
    runSoon();
  }

  window.addEventListener('pageshow', runSoon);
})();
</script>
<!-- PROFUTBIK_LIMIT_PLAYER_TEAMS_LAST5_END -->
'''.strip() + "\n"


def write_report(lines: list[str]) -> None:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def backup_file(path: Path, lines: list[str]) -> None:
    rel = path.relative_to(PROJECT)
    dst = BACKUP_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, dst)
        lines.append(f"BACKUP {rel} -> {dst.relative_to(PROJECT)}")


def replace_or_append_block(text: str, block: str) -> tuple[str, str]:
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    if start != -1 and end != -1 and end > start:
        end = end + len(MARKER_END)
        return text[:start] + block + text[end:].lstrip("\r\n"), "replaced_existing_block"
    return text.rstrip() + "\n\n" + block, "appended_new_block"


def main() -> int:
    lines: list[str] = []
    lines.append(f"VERSION {VERSION}")
    lines.append(f"PROJECT {PROJECT}")

    if not PROJECT.exists():
        lines.append("ERROR project folder does not exist")
        write_report(lines)
        return 1

    candidate_files = [
        PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html",
        PROJECT / "layouts" / "transfers" / "single.html",
        PROJECT / "layouts" / "_default" / "single.html",
    ]

    target = None
    for path in candidate_files:
        if path.exists():
            target = path
            break

    if target is None:
        target = PROJECT / "layouts" / "partials" / "profutbik-market-chart-static.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
        lines.append(f"CREATED {target.relative_to(PROJECT)}")

    backup_file(target, lines)

    try:
        old = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        old = target.read_text(encoding="utf-8-sig")

    new, action = replace_or_append_block(old, INJECT_BLOCK)
    target.write_text(new, encoding="utf-8", newline="\n")

    lines.append(f"UPDATED {target.relative_to(PROJECT)}")
    lines.append(f"ACTION {action}")
    lines.append("RULE show only last 5 team logos in player market charts")
    lines.append("SCOPE all players")
    lines.append("DO_NOT_TOUCH ticker ramos endrick favicon var")
    write_report(lines)

    print("DONE_151_FULL_LIMIT_PLAYER_TEAMS_LAST5")
    print(f"REPORT {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
