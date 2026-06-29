from pathlib import Path
from PIL import Image
import shutil
import re
from datetime import datetime

project = Path.cwd()
png_target = project / 'static' / 'images' / 'stats-icons-v184' / 'goals.png'
partial_path = project / 'layouts' / 'partials' / 'transfer-player-stats.html'
backup_dir = project / '_backup_195_restore_approved_goals_ball_no_crop'
backup_dir.mkdir(parents=True, exist_ok=True)

print('PROFUTBIK 195 - restore approved goals ball and remove crop')
print(f'Project: {project}')
print('Time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

if not png_target.exists():
    raise FileNotFoundError(f'Missing target icon: {png_target}')
if not partial_path.exists():
    raise FileNotFoundError(f'Missing partial: {partial_path}')

backup_png = backup_dir / 'goals_before_195.png'
backup_partial = backup_dir / 'transfer-player-stats_before_195.html'
if not backup_png.exists():
    shutil.copy2(png_target, backup_png)
    print('Backup saved:', backup_png.relative_to(project))
if not backup_partial.exists():
    shutil.copy2(partial_path, backup_partial)
    print('Backup saved:', backup_partial.relative_to(project))

candidates = [
    project / '_backup_186_restore_approved_goals_icon' / 'static' / 'images' / 'stats-icons-v184' / 'goals.png',
    project / '_backup_172_restore_approved_goals_icon' / 'static' / 'images' / 'stats-icons-v184' / 'goals.png',
    project / '_backup_188_fix_approved_goals_icon_right_edge' / 'static' / 'images' / 'stats-icons-v184' / 'goals.png',
    project / '_backup_189_fix_goals_icon_full_right_padding' / 'static' / 'images' / 'stats-icons-v184' / 'goals.png',
    project / 'static' / 'images' / 'stats-icons-v184' / 'goals_before_191.png',
    project / 'static' / 'images' / 'stats-icons-v184' / 'goals_before_190.png',
    project / 'static' / 'images' / 'stats-icons-v184' / 'goals_before_194.png',
    backup_png,
]
source = None
for c in candidates:
    if c.exists():
        source = c
        break
if source is None:
    raise FileNotFoundError('Could not find any approved goals icon source candidate.')
print('Approved design source:', source.relative_to(project))

img = Image.open(source).convert('RGBA')
bbox = img.getbbox()
if bbox is None:
    raise RuntimeError('Source icon is fully transparent.')
ball = img.crop(bbox)
orig_w, orig_h = img.size
canvas_w = max(orig_w, int(ball.width * 1.42))
canvas_h = max(orig_h, int(ball.height * 1.22))
out = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
max_ball_w = int(canvas_w * 0.78)
max_ball_h = int(canvas_h * 0.78)
ball_copy = ball.copy()
ball_copy.thumbnail((max_ball_w, max_ball_h), Image.Resampling.LANCZOS)
x = max(0, (canvas_w - ball_copy.width) // 2 - int(canvas_w * 0.06))
y = max(0, (canvas_h - ball_copy.height) // 2)
out.alpha_composite(ball_copy, (x, y))
out.save(png_target)
print('Restored approved design and added safe transparent canvas:', png_target.relative_to(project))

html = partial_path.read_text(encoding='utf-8')
html_new = re.sub(r'goals\.png"\s*\|\s*relURL\s*\}\}\?v=\d+', 'goals.png" | relURL }}?v=195', html)
marker = '/* 195 goals icon approved design no crop fix */'
css_block = marker + """
body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals,
body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals *,
body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals .pfb-stats-v184__icon {
  overflow: visible !important;
  clip-path: none !important;
  -webkit-clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
}

body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals .pfb-stats-v184__icon {
  width: 72px !important;
  height: 72px !important;
  max-width: 72px !important;
  max-height: 72px !important;
  object-fit: contain !important;
  object-position: center center !important;
  transform: translateX(-2px) !important;
}
"""
if marker not in html_new:
    if '</style>' in html_new:
        html_new = html_new.replace('</style>', '\n' + css_block + '\n</style>', 1)
    else:
        html_new += '\n<style>\n' + css_block + '\n</style>\n'
if html_new != html:
    partial_path.write_text(html_new, encoding='utf-8')
    print('Patched partial CSS/cache:', partial_path.relative_to(project))
else:
    print('Partial already had expected patch or no change was needed:', partial_path.relative_to(project))

self_copy_target = project / 'scripts' / '195_restore_approved_goals_ball_no_crop.py'
self_copy_target.parent.mkdir(parents=True, exist_ok=True)
try:
    shutil.copy2(__file__, self_copy_target)
except Exception:
    pass

print()
print('Touched files:')
print('-', partial_path.relative_to(project))
print('-', png_target.relative_to(project))
print()
print('DONE 195. Open the De Ligt page and press Ctrl+F5.')
