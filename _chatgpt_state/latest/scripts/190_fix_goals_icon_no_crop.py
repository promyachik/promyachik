from pathlib import Path
from PIL import Image
import re
import shutil

root = Path.cwd()

png_path = root / "static" / "images" / "stats-icons-v184" / "goals.png"
partial_path = root / "layouts" / "partials" / "transfer-player-stats.html"

if not png_path.exists():
    raise FileNotFoundError(f"Не найден файл: {png_path}")

if not partial_path.exists():
    raise FileNotFoundError(f"Не найден файл: {partial_path}")

backup_png = png_path.with_name("goals_before_190.png")
if not backup_png.exists():
    shutil.copy2(png_path, backup_png)

img = Image.open(png_path).convert("RGBA")
w, h = img.size

bbox = img.getbbox()
if bbox is None:
    raise RuntimeError("goals.png пустой или полностью прозрачный")

# Берём существующий утверждённый мяч, дизайн не меняем.
ball = img.crop(bbox)

# Создаём новый прозрачный canvas того же размера.
# Смысл: мяч не должен упираться в правый край PNG.
canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

# Уменьшаем именно содержимое внутри canvas, чтобы появился воздух справа.
# Это НЕ замена дизайна мяча, а исправление области изображения.
max_ball_w = int(w * 0.82)
max_ball_h = int(h * 0.82)
ball.thumbnail((max_ball_w, max_ball_h), Image.Resampling.LANCZOS)

# Чуть сдвигаем мяч влево, чтобы правый край точно не резался.
x = max(0, (w - ball.width) // 2 - int(w * 0.035))
y = max(0, (h - ball.height) // 2)

canvas.alpha_composite(ball, (x, y))
canvas.save(png_path, optimize=True)

html = partial_path.read_text(encoding="utf-8")

old_css = '''body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals .pfb-stats-v184__icon {

 width: 78px !important;

 height: 78px !important;

}'''

new_css = '''body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals {
 overflow: visible !important;
}

body.transfer-page #pfb-stats-v184 .pfb-stats-v184__goals .pfb-stats-v184__icon {
 width: 74px !important;
 height: 74px !important;
 max-width: 74px !important;
 max-height: 74px !important;
 object-fit: contain !important;
 object-position: center center !important;
 transform: translateX(-1px) !important;
}'''

if old_css in html:
    html = html.replace(old_css, new_css)
else:
    html = re.sub(
        r'body\.transfer-page #pfb-stats-v184 \.pfb-stats-v184__goals \.pfb-stats-v184__icon\s*\{[^}]*\}',
        new_css,
        html,
        count=1
    )

html = re.sub(r'goals\.png"\s*\|\s*relURL\s*\}\}\?v=\d+', 'goals.png" | relURL }}?v=190', html)

partial_path.write_text(html, encoding="utf-8")

print("DONE: пакет 190 готов")
print("Изменены только:")
print("-", png_path)
print("-", partial_path)
print("Бэкап мяча:", backup_png)
