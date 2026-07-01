from pathlib import Path
import re, subprocess, sys, datetime, json

ROOT = Path(r'C:\Users\Dmitrii\Promyachik')
REPORT = ROOT / 'var' / 'promyachik_303_hide_only_white_konate_45_duplicate_no_backup_report.txt'
PARTIAL = ROOT / 'layouts' / 'partials' / 'transfer-player-market-value-chart.html'
STATIC_JS_MAIN = ROOT / 'static' / 'js' / 'transfer-player-market-value-chart.js'
PUBLIC_JS_MAIN = ROOT / 'public' / 'js' / 'transfer-player-market-value-chart.js'
STATIC_JS_303 = ROOT / 'static' / 'js' / 'promyachik-konate-hide-white-45-303.js'
PUBLIC_JS_303 = ROOT / 'public' / 'js' / 'promyachik-konate-hide-white-45-303.js'

START_300 = '// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE START'
END_300 = '// PROMYACHIK 300 KONATE HIDE DUPLICATE WHITE CURRENT PRICE END'

lines = []
def log(s):
    lines.append(str(s))

def read(p):
    return p.read_text(encoding='utf-8', errors='replace')

def write(p, t):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding='utf-8', newline='\n')

def strip_block(text, start, end):
    if start in text and end in text:
        pattern = re.escape(start) + r'.*?' + re.escape(end)
        text, n = re.subn(pattern, '', text, flags=re.S)
        return text, n
    return text, 0

JS_303 = r'''
(function () {
  'use strict';

  var PATH_RE = /ibrahima-konate-real-madrid/i;
  var ATTR = 'data-promyachik-hide-white-konate-45-303';

  function isKonatePage() {
    return PATH_RE.test(window.location.pathname || '');
  }

  function norm(text) {
    return String(text || '')
      .replace(/\u00a0/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function isTargetPrice(text) {
    var t = norm(text);
    return t === '€45 млн' || t === '€45млн' || t === '€45m' || t === '€45 m' || t === '45 млн';
  }

  function hasExactPriceChild(el) {
    var children = Array.prototype.slice.call(el.children || []);
    return children.some(function (child) { return isTargetPrice(child.textContent); });
  }

  function isAlreadyHidden(el) {
    var cs = window.getComputedStyle ? window.getComputedStyle(el) : null;
    if (!cs) return false;
    return cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0;
  }

  function isGoldenOverlayOrMovedPrice(el) {
    if (!el) return true;
    if (el.closest('.promyachik-konate-price-layer-302')) return true;
    if (el.closest('.promyachik-konate-price-label-302')) return true;
    if (el.closest('.promyachik-konate-price-layer-299')) return true;
    if (el.closest('.promyachik-konate-price-point-299')) return true;
    if (el.closest('.promyachik-konate-price-value-299')) return true;
    var cls = String(el.className || '');
    return /promyachik-konate-price-(label|layer|point|value)-30[0-9]/i.test(cls);
  }

  function hideWhiteDuplicate() {
    if (!isKonatePage()) return;

    var chart = document.querySelector('.player-market-chart');
    if (!chart) return;

    var canvas = chart.querySelector('.player-market-chart__canvas') || chart;
    var canvasRect = canvas.getBoundingClientRect();
    var chartRect = chart.getBoundingClientRect();
    if (!canvasRect || !chartRect || chartRect.width <= 0 || chartRect.height <= 0) return;

    var root = chart.closest('.player-brief, .transfer-side-column, article, main') || document.body;
    var nodes = Array.prototype.slice.call(root.querySelectorAll('span,strong,b,em,small,p,div'));
    var hidden = 0;

    nodes.forEach(function (el) {
      if (!el || el.nodeType !== 1) return;
      if (el.closest('script,style,noscript,svg')) return;
      if (isGoldenOverlayOrMovedPrice(el)) return;
      if (!isTargetPrice(el.textContent)) return;
      if (hasExactPriceChild(el)) return;
      if (isAlreadyHidden(el)) return;

      var rect = el.getBoundingClientRect();
      if (!rect || rect.width <= 0 || rect.height <= 0) return;

      // Hide only the visible white duplicate that sits below the chart canvas/under the graph.
      // Do not touch the golden overlay labels near the points and do not touch prices above the graph.
      if (rect.top < canvasRect.bottom - 2) return;
      if (rect.top > chartRect.bottom + 160) return;

      el.setAttribute(ATTR, '1');
      el.style.setProperty('display', 'none', 'important');
      el.style.setProperty('visibility', 'hidden', 'important');
      el.style.setProperty('opacity', '0', 'important');
      hidden += 1;
    });

    if (hidden > 0) {
      document.body.setAttribute('data-promyachik-konate-white-45-hidden-303', String(hidden));
    }
  }

  var timer = 0;
  function schedule() {
    if (!isKonatePage()) return;
    window.clearTimeout(timer);
    timer = window.setTimeout(hideWhiteDuplicate, 40);
  }

  function runMany() {
    hideWhiteDuplicate();
    window.setTimeout(hideWhiteDuplicate, 120);
    window.setTimeout(hideWhiteDuplicate, 350);
    window.setTimeout(hideWhiteDuplicate, 900);
    window.setTimeout(hideWhiteDuplicate, 1600);
    window.setTimeout(hideWhiteDuplicate, 2600);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runMany);
  } else {
    runMany();
  }
  window.addEventListener('load', runMany);
  window.addEventListener('resize', runMany);

  if (window.MutationObserver) {
    var started = false;
    var startObserver = function () {
      if (started || !document.body || !isKonatePage()) return;
      started = true;
      var mo = new MutationObserver(schedule);
      mo.observe(document.body, { childList: true, subtree: true, characterData: true });
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', startObserver);
    } else {
      startObserver();
    }
  }
})();
'''.strip() + '\n'

try:
    log('PROMYACHIK 303 - HIDE ONLY WHITE KONATE 45 DUPLICATE - NO BACKUP')
    log('started_at=' + datetime.datetime.now().isoformat(timespec='seconds'))
    log('root=' + str(ROOT))

    if not ROOT.exists():
        raise RuntimeError('Project root not found: ' + str(ROOT))
    if not PARTIAL.exists():
        raise RuntimeError('Partial not found: ' + str(PARTIAL))

    # Remove the dangerous 300 runtime block if it is still present anywhere.
    removed_300_static = 0
    if STATIC_JS_MAIN.exists():
        txt = read(STATIC_JS_MAIN)
        txt, removed_300_static = strip_block(txt, START_300, END_300)
        write(STATIC_JS_MAIN, txt.rstrip() + '\n')
    log('removed_300_from_static_js=' + str(removed_300_static))

    removed_300_public = 0
    if PUBLIC_JS_MAIN.exists():
        txt = read(PUBLIC_JS_MAIN)
        txt, removed_300_public = strip_block(txt, START_300, END_300)
        write(PUBLIC_JS_MAIN, txt.rstrip() + '\n')
    log('removed_300_from_public_js=' + str(removed_300_public))

    write(STATIC_JS_303, JS_303)
    log('written_static_js_303=' + str(STATIC_JS_303))
    if PUBLIC_JS_303.parent.exists():
        write(PUBLIC_JS_303, JS_303)
        log('written_public_js_303=' + str(PUBLIC_JS_303))
    else:
        log('written_public_js_303=skipped_missing_public_js_folder')

    partial = read(PARTIAL)
    partial = re.sub(r'\s*{{\s*if\s+in\s+\(lower\s+\.RelPermalink\)\s+"ibrahima-konate-real-madrid"\s*}}\s*<script[^>]+promyachik-konate-hide-white-45-303\.js[^>]*></script>\s*{{\s*end\s*}}\s*', '\n', partial, flags=re.I)
    partial = re.sub(r'\s*<script[^>]+promyachik-konate-hide-white-45-303\.js[^>]*></script>\s*', '\n', partial, flags=re.I)
    include = '{{ if in (lower .RelPermalink) "ibrahima-konate-real-madrid" }}<script src="{{ "js/promyachik-konate-hide-white-45-303.js" | relURL }}?v=303" defer></script>{{ end }}'
    partial = partial.rstrip() + '\n' + include + '\n'
    write(PARTIAL, partial)
    log('partial_updated=' + str(PARTIAL))

    hugo = subprocess.run(['hugo', '-D'], cwd=str(ROOT), text=True, capture_output=True, encoding='utf-8', errors='ignore', timeout=120)
    log('hugo_exit_code=' + str(hugo.returncode))
    if hugo.stdout:
        log('hugo_stdout_tail=')
        log(hugo.stdout[-3000:])
    if hugo.stderr:
        log('hugo_stderr_tail=')
        log(hugo.stderr[-4000:])

    target = ROOT / 'public' / 'transfers' / 'ibrahima-konate-real-madrid' / 'index.html'
    html = read(target) if target.exists() else ''
    checks = {
        'target_html_exists': target.exists(),
        'target_is_konate': ('konate' in html.lower() or 'konaté' in html.lower()),
        'target_has_303_script': 'promyachik-konate-hide-white-45-303.js' in html,
        'static_js_303_exists': STATIC_JS_303.exists(),
        'static_js_303_has_attr': 'data-promyachik-hide-white-konate-45-303' in read(STATIC_JS_303),
        'danger_300_removed_from_static_main_js': (not STATIC_JS_MAIN.exists()) or (START_300 not in read(STATIC_JS_MAIN)),
        'hugo_ok': hugo.returncode == 0,
    }
    log('CHECKS=' + json.dumps(checks, ensure_ascii=False, indent=2))
    ok = all(checks.values())
    log('VERIFIED_OK=' + str(ok))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write(REPORT, '\n'.join(lines) + '\n')
    sys.exit(0 if ok else 1)
except Exception as e:
    log('ERROR=' + type(e).__name__ + ': ' + str(e))
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        write(REPORT, '\n'.join(lines) + '\n')
    except Exception:
        pass
    sys.exit(1)
