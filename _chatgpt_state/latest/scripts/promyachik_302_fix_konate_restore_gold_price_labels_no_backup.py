from pathlib import Path
import re, subprocess, sys, datetime, json
ROOT = Path(r'C:\Users\Dmitrii\Promyachik')
REPORT = ROOT / 'var' / 'promyachik_302_fix_konate_restore_gold_price_labels_no_backup_report.txt'
REPORT.parent.mkdir(parents=True, exist_ok=True)
log=[]
def w(s):
    log.append(str(s))

def read(p):
    return p.read_text(encoding='utf-8', errors='ignore')
def write(p,t):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding='utf-8')

try:
    w('PROMYACHIK 302 - FIX KONATE RESTORE GOLD PRICE LABELS - NO BACKUP')
    w('Started: '+datetime.datetime.now().isoformat(timespec='seconds'))
    partial = ROOT/'layouts'/'partials'/'transfer-player-market-value-chart.html'
    css = ROOT/'static'/'css'/'transfer-player-market-value-chart.css'
    jsdir = ROOT/'static'/'js'
    jsfile = jsdir/'promyachik-konate-price-overlay-302.js'
    for p in [partial, css]:
        w(f'exists {p}: {p.exists()}')
        if not p.exists():
            raise FileNotFoundError(str(p))

    # Remove only our later broken/hacky blocks if present by numbered markers.
    css_text = read(css)
    for n in ['300','301','302']:
        css_text = re.sub(r'/\*\s*PROMYACHIK\s+'+n+r'[^*]*START\s*\*/.*?/\*\s*PROMYACHIK\s+'+n+r'[^*]*END\s*\*/', '', css_text, flags=re.S|re.I)
    css_text = re.sub(r'/\*\s*PROMYACHIK\s+302[^*]*START\s*\*/.*?/\*\s*PROMYACHIK\s+302[^*]*END\s*\*/', '', css_text, flags=re.S|re.I)
    add_css = r'''
/* PROMYACHIK 302 KONATE PRICE OVERLAY STABILITY START */
body.transfer-page .player-market-chart[data-promyachik-konate-302="1"] {
  position: relative !important;
}
body.transfer-page .player-market-chart[data-promyachik-konate-302="1"] .player-market-chart__point strong,
body.transfer-page .player-market-chart[data-promyachik-konate-302="1"] .player-market-chart__point small {
  visibility: hidden !important;
}
body.transfer-page .player-market-chart[data-promyachik-konate-302="1"] .promyachik-konate-price-layer-302 {
  position: absolute !important;
  inset: 0 !important;
  z-index: 6 !important;
  pointer-events: none !important;
}
body.transfer-page .player-market-chart[data-promyachik-konate-302="1"] .promyachik-konate-price-label-302 {
  position: absolute !important;
  transform: translate(-50%, 8px) !important;
  color: #f3cf55 !important;
  font-family: "Russo One", "Montserrat", Arial, sans-serif !important;
  font-size: 10px !important;
  font-weight: 400 !important;
  line-height: 1 !important;
  letter-spacing: 0.01em !important;
  white-space: nowrap !important;
  text-shadow: 0 0 8px rgba(231,198,91,.28) !important;
  background: transparent !important;
  border: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}
/* PROMYACHIK 302 KONATE PRICE OVERLAY STABILITY END */
'''
    if 'PROMYACHIK 302 KONATE PRICE OVERLAY STABILITY START' not in css_text:
        css_text = css_text.rstrip()+"\n"+add_css+"\n"
    write(css, css_text)
    w('css updated')

    jsdir.mkdir(parents=True, exist_ok=True)
    js_code = r'''
(function () {
  'use strict';
  var PATH_RE = /ibrahima-konate-real-madrid/i;
  var VALUES = ['€300K', '€35 млн', '€60 млн', '€45 млн'];

  function isKonatePage() {
    return PATH_RE.test(window.location.pathname || '') || PATH_RE.test(document.body && document.body.innerHTML ? document.body.innerHTML.slice(0, 6000) : '');
  }

  function textOf(el) {
    return (el && (el.textContent || '') || '').replace(/\s+/g, ' ').trim();
  }

  function normalize(v) {
    return String(v || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function hideOnlyWhiteDuplicate(chart) {
    var wanted = normalize('€45 млн');
    var parent = chart.closest('.transfer-side-column, .player-brief, article, main, body') || document.body;
    Array.prototype.forEach.call(parent.querySelectorAll('h1,h2,h3,h4,p,div,span,strong'), function (el) {
      if (chart.contains(el)) return;
      if (el.closest('.promyachik-konate-price-layer-302')) return;
      if (normalize(el.textContent) !== wanted) return;
      var r = el.getBoundingClientRect();
      var cr = chart.getBoundingClientRect();
      if (r.top >= cr.bottom - 4 && r.top <= cr.bottom + 90) {
        el.setAttribute('data-promyachik-hidden-white-current-price-302', '1');
        el.style.setProperty('display', 'none', 'important');
      }
    });
  }

  function buildOverlay() {
    if (!isKonatePage()) return;
    var chart = document.querySelector('.player-market-chart');
    if (!chart) return;
    chart.setAttribute('data-promyachik-konate-302', '1');
    var canvas = chart.querySelector('.player-market-chart__canvas');
    if (!canvas) return;

    var dots = Array.prototype.slice.call(chart.querySelectorAll('.player-market-chart__dot'));
    var pointStrong = Array.prototype.slice.call(chart.querySelectorAll('.player-market-chart__point strong'));
    var values = pointStrong.map(textOf).filter(Boolean);
    if (values.length < 2) values = VALUES.slice();
    var count = Math.min(values.length, dots.length || values.length);
    if (!count) return;

    var layer = chart.querySelector('.promyachik-konate-price-layer-302');
    if (!layer) {
      layer = document.createElement('div');
      layer.className = 'promyachik-konate-price-layer-302';
      canvas.appendChild(layer);
    }
    layer.innerHTML = '';

    var canvasRect = canvas.getBoundingClientRect();
    for (var i = 0; i < count; i++) {
      var label = document.createElement('span');
      label.className = 'promyachik-konate-price-label-302';
      label.textContent = values[i] || VALUES[i] || '';
      var x, y;
      if (dots[i]) {
        var dotRect = dots[i].getBoundingClientRect();
        x = dotRect.left + dotRect.width / 2 - canvasRect.left;
        y = dotRect.top + dotRect.height / 2 - canvasRect.top;
      } else {
        x = ((i + 0.5) / count) * canvasRect.width;
        y = canvasRect.height * 0.7;
      }
      label.style.left = Math.round(x) + 'px';
      label.style.top = Math.round(y) + 'px';
      layer.appendChild(label);
    }
    hideOnlyWhiteDuplicate(chart);
  }

  function schedule() {
    buildOverlay();
    setTimeout(buildOverlay, 80);
    setTimeout(buildOverlay, 300);
    setTimeout(buildOverlay, 900);
    setTimeout(buildOverlay, 1600);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule);
  } else {
    schedule();
  }
  window.addEventListener('load', schedule);
  window.addEventListener('resize', schedule);
})();
'''.strip()+"\n"
    write(jsfile, js_code)
    w('js overlay written: '+str(jsfile))

    # Include script in chart partial exactly once.
    part = read(partial)
    # remove broken includes from 300/301/302 if any
    part = re.sub(r'\s*<script[^>]+promyachik-konate-price-overlay-302\.js[^>]*></script>\s*', '\n', part, flags=re.I)
    include = '{{ if in (lower .RelPermalink) "ibrahima-konate-real-madrid" }}<script src="{{ "js/promyachik-konate-price-overlay-302.js" | relURL }}?v=302" defer></script>{{ end }}'
    if '</script>' in part or '{{- end -}}' in part:
        part = part.rstrip()+"\n"+include+"\n"
    else:
        part = part.rstrip()+"\n"+include+"\n"
    write(partial, part)
    w('partial updated')

    # optional sync public static if exists
    pubjs = ROOT/'public'/'js'
    if pubjs.exists():
        write(pubjs/'promyachik-konate-price-overlay-302.js', js_code)
        w('public js synced')

    # Hugo build validation
    proc = subprocess.run(['hugo','-D'], cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=60)
    w('hugo exit_code: '+str(proc.returncode))
    if proc.stdout.strip(): w('hugo stdout:\n'+proc.stdout[-2000:])
    if proc.stderr.strip(): w('hugo stderr:\n'+proc.stderr[-4000:])

    target = ROOT/'public'/'transfers'/'ibrahima-konate-real-madrid'/'index.html'
    html = read(target) if target.exists() else ''
    checks = {
        'target_exists': target.exists(),
        'has_overlay_script': 'promyachik-konate-price-overlay-302.js' in html,
        'css_has_302': 'PROMYACHIK 302 KONATE PRICE OVERLAY STABILITY START' in read(css),
        'js_exists': jsfile.exists(),
        'hugo_ok': proc.returncode == 0,
    }
    w('CHECKS: '+json.dumps(checks, ensure_ascii=False, indent=2))
    ok = all(checks.values())
    w('VERIFIED_OK: '+str(ok))
    write(REPORT, '\n'.join(log))
    sys.exit(0 if ok else 1)
except Exception as e:
    w('ERROR: '+repr(e))
    write(REPORT, '\n'.join(log))
    sys.exit(1)
