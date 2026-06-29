from pathlib import Path
import re
import json
from datetime import datetime

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

project = Path.cwd()
report_dir = project / "var"
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / "profutbik_205_goncalo_ramos_page_check.txt"

terms = [
    "goncalo", "gonçalo", "gonzalo", "ramos",
    "гонсалу", "гонзалу", "рамуш", "рамос"
]

content_dir = project / "content"
data_dir = project / "data"
layouts_dir = project / "layouts"
static_dir = project / "static"

def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return path.read_text(encoding="cp1251", errors="ignore")
        except Exception:
            return ""

def norm(s):
    return (s or "").lower()

def parse_front_matter(text):
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = text[3:end].strip()
            body = text[end+4:]
            for line in raw.splitlines():
                if ":" in line and not line.lstrip().startswith("#"):
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
    elif text.startswith("+++"):
        end = text.find("\n+++", 3)
        if end != -1:
            raw = text[3:end].strip()
            body = text[end+4:]
            for line in raw.splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body

def extract_image_refs(text, fm):
    refs = []
    image_keys = [
        "image", "images", "photo", "player_image", "playerPhoto",
        "cover", "thumbnail", "featured_image", "featuredImage",
        "hero", "hero_image", "concept_art", "conceptArt"
    ]
    for k, v in fm.items():
        lk = k.lower()
        if any(ik.lower() == lk for ik in image_keys) or "image" in lk or "photo" in lk or "cover" in lk:
            refs.append((k, v))
    # markdown images
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', text):
        refs.append(("markdown_image", m.group(1).strip()))
    # html src
    for m in re.finditer(r'src=["\']([^"\']+)["\']', text):
        refs.append(("html_src", m.group(1).strip()))
    return refs

def resolve_image(ref, page_path=None):
    ref_clean = ref.strip().strip('"').strip("'")
    if not ref_clean:
        return None, "empty"
    if ref_clean.startswith(("http://", "https://")):
        return None, "external"
    if "?" in ref_clean:
        ref_clean = ref_clean.split("?", 1)[0]
    if ref_clean.startswith("/promyachik/"):
        ref_clean = ref_clean[len("/promyachik/"):]
    if ref_clean.startswith("/"):
        ref_clean = ref_clean[1:]
    candidates = []
    candidates.append(project / ref_clean)
    candidates.append(static_dir / ref_clean)
    if ref_clean.startswith("images/"):
        candidates.append(static_dir / ref_clean)
    else:
        candidates.append(static_dir / "images" / ref_clean)
    if page_path is not None:
        candidates.append(page_path.parent / ref_clean)
    for c in candidates:
        if c.exists() and c.is_file():
            return c, "local"
    return candidates[0], "missing"

def analyze_image(path):
    if not PIL_AVAILABLE:
        return {"ok": False, "note": "Pillow not available, cannot analyze image background"}
    try:
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        px = img.load()
        sample = []
        margin = max(1, min(w, h) // 20)
        coords = []
        for x in range(0, margin):
            for y in range(0, margin):
                coords.append((x, y))
                coords.append((w-1-x, y))
                coords.append((x, h-1-y))
                coords.append((w-1-x, h-1-y))
        for x, y in coords[:5000]:
            r, g, b, a = px[x, y]
            sample.append((r, g, b, a))
        if not sample:
            return {"ok": True, "size": f"{w}x{h}", "note": "no sample"}
        avg_r = sum(p[0] for p in sample) / len(sample)
        avg_g = sum(p[1] for p in sample) / len(sample)
        avg_b = sum(p[2] for p in sample) / len(sample)
        avg_a = sum(p[3] for p in sample) / len(sample)
        near_white = sum(1 for r,g,b,a in sample if a > 220 and r > 235 and g > 235 and b > 235) / len(sample)
        near_black = sum(1 for r,g,b,a in sample if a > 220 and r < 25 and g < 25 and b < 25) / len(sample)
        transparent = sum(1 for r,g,b,a in sample if a < 20) / len(sample)
        warning = None
        if near_white > 0.45:
            warning = "POSSIBLE WHITE BACKGROUND: many corner pixels are near-white"
        elif transparent > 0.45:
            warning = "transparent/alpha background detected"
        elif near_black > 0.45:
            warning = "black background detected"
        return {
            "ok": True,
            "size": f"{w}x{h}",
            "corner_avg_rgba": [round(avg_r), round(avg_g), round(avg_b), round(avg_a)],
            "corner_near_white_ratio": round(near_white, 3),
            "corner_near_black_ratio": round(near_black, 3),
            "corner_transparent_ratio": round(transparent, 3),
            "warning": warning
        }
    except Exception as e:
        return {"ok": False, "note": str(e)}

# Search candidate pages
candidates = []
if content_dir.exists():
    for p in content_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in [".md", ".html"]:
            txt = read_text(p)
            hay = norm(str(p.relative_to(project)) + "\n" + txt)
            hits = [t for t in terms if t in hay]
            if hits:
                score = len(hits)
                if "transfers" in str(p).lower():
                    score += 5
                if "ramos" in hay or "рамуш" in hay:
                    score += 3
                candidates.append((score, p, hits))

candidates.sort(key=lambda x: (-x[0], str(x[1])))

selected = candidates[0][1] if candidates else None
selected_text = read_text(selected) if selected else ""
selected_fm, selected_body = parse_front_matter(selected_text) if selected else ({}, "")

# Template stats check
stats_partial = layouts_dir / "partials" / "transfer-player-stats.html"
template_hits = []
if layouts_dir.exists():
    for p in layouts_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in [".html", ".htm"]:
            txt = read_text(p)
            if "transfer-player-stats" in txt:
                template_hits.append(p)

# Homepage / featured check
homepage_refs = []
for rel in ["layouts/index.html", "content/_index.md", "content/posts/test.md"]:
    p = project / rel
    if p.exists():
        txt = read_text(p)
        hay = norm(txt)
        if any(t in hay for t in ["ramos", "рамуш", "гонсалу", "goncalo", "gonçalo"]):
            homepage_refs.append(p)

# Build report
lines = []
lines.append("PROFUTBIK 205 - GONCALO RAMOS PAGE CHECK")
lines.append("=" * 60)
lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"Project: {project}")
lines.append("")
lines.append("IMPORTANT")
lines.append("- This report only checks local files.")
lines.append("- It does not open the site.")
lines.append("- It does not push.")
lines.append("")

lines.append("1) FOUND CANDIDATE PAGES")
lines.append("-" * 60)
if not candidates:
    lines.append("NO candidate page found for Goncalo/Gonçalo/Ramos/Гонсалу/Рамуш in content/.")
else:
    for score, p, hits in candidates[:20]:
        lines.append(f"[score {score}] {p.relative_to(project)} | hits: {', '.join(hits)}")
lines.append("")

warnings = []
fixes = []

if selected:
    lines.append("2) SELECTED PAGE")
    lines.append("-" * 60)
    lines.append(str(selected.relative_to(project)))
    lines.append("")
    lines.append("Front matter:")
    if selected_fm:
        for k in sorted(selected_fm.keys()):
            lines.append(f"- {k}: {selected_fm[k]}")
    else:
        lines.append("- No front matter detected.")
        warnings.append("Selected page has no front matter.")
        fixes.append("Add SEO front matter: title, description, date, slug/url, image/photo fields.")
    lines.append("")

    title = selected_fm.get("title") or selected_fm.get("seoTitle") or selected_fm.get("seo_title")
    desc = selected_fm.get("description") or selected_fm.get("meta_description") or selected_fm.get("summary")
    slug = selected_fm.get("slug") or selected_fm.get("url")
    draft = selected_fm.get("draft")
    h1_count = len(re.findall(r"(?m)^#\s+", selected_body))
    word_count = len(re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", selected_body))

    lines.append("3) SEO CHECK")
    lines.append("-" * 60)
    lines.append(f"title: {'OK' if title else 'MISSING'}" + (f" | length {len(title)} | {title}" if title else ""))
    lines.append(f"description/meta: {'OK' if desc else 'MISSING'}" + (f" | length {len(desc)} | {desc}" if desc else ""))
    lines.append(f"slug/url: {'OK' if slug else 'not explicit / may be folder slug'}" + (f" | {slug}" if slug else ""))
    lines.append(f"draft: {draft if draft is not None else 'not set'}")
    lines.append(f"H1 count in body: {h1_count}")
    lines.append(f"Approx text tokens/words: {word_count}")
    if not title:
        warnings.append("SEO title is missing.")
        fixes.append("Add SEO title for Goncalo Ramos transfer page.")
    if not desc:
        warnings.append("Meta description is missing.")
        fixes.append("Add 120-160 character meta description.")
    if word_count < 350:
        warnings.append("Text looks short for SEO transfer page.")
        fixes.append("Expand page with SEO intro, transfer facts, clubs, position, value/context, internal links.")
    lines.append("")

    lines.append("4) IMAGE / PHOTO CHECK")
    lines.append("-" * 60)
    refs = extract_image_refs(selected_text, selected_fm)
    if not refs:
        lines.append("NO image/photo references found in selected page.")
        warnings.append("No photo/image reference found on selected page.")
        fixes.append("Add/repair player photo reference and process white background.")
    else:
        for k, ref in refs:
            path, status = resolve_image(ref, selected)
            lines.append(f"- {k}: {ref}")
            lines.append(f"  status: {status}")
            if path:
                try:
                    lines.append(f"  resolved: {path.relative_to(project)}")
                except Exception:
                    lines.append(f"  resolved: {path}")
            if status == "local" and path and path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                info = analyze_image(path)
                lines.append(f"  image_analysis: {json.dumps(info, ensure_ascii=False)}")
                if info.get("warning") and "WHITE" in info.get("warning", ""):
                    warnings.append(f"Possible white background in image: {path.relative_to(project)}")
                    fixes.append("Replace/prepare player photo with black background #000000 or real alpha, depending on page design.")
            elif status == "missing":
                warnings.append(f"Image file missing: {ref}")
                fixes.append(f"Fix image path or add missing file: {ref}")
    lines.append("")
else:
    warnings.append("No Goncalo Ramos page found.")
    fixes.append("Create or locate Goncalo Ramos transfer page under content/transfers/.")

lines.append("5) APPROVED STATS BLOCK CHECK")
lines.append("-" * 60)
lines.append(f"stats partial exists: {'YES' if stats_partial.exists() else 'NO'} | {stats_partial.relative_to(project) if stats_partial.exists() else stats_partial}")
if template_hits:
    lines.append("templates containing transfer-player-stats:")
    for p in template_hits:
        lines.append(f"- {p.relative_to(project)}")
else:
    lines.append("NO template contains transfer-player-stats partial.")
    warnings.append("Approved stats block is not found in templates.")
    fixes.append("Connect layouts/partials/transfer-player-stats.html through transfer/default template for all players.")
goals_png = static_dir / "images" / "stats-icons-v184" / "goals.png"
lines.append(f"goals icon exists: {'YES' if goals_png.exists() else 'NO'} | {goals_png.relative_to(project) if goals_png.exists() else goals_png}")
if goals_png.exists():
    info = analyze_image(goals_png)
    lines.append(f"goals icon analysis: {json.dumps(info, ensure_ascii=False)}")
lines.append("")

lines.append("6) MAIN PAGE / FEATURED TRANSFER CHECK")
lines.append("-" * 60)
if homepage_refs:
    lines.append("Ramos appears in homepage-related files:")
    for p in homepage_refs:
        lines.append(f"- {p.relative_to(project)}")
    lines.append("If this is a featured/main transfer, concept art should exist and be referenced.")
    fixes.append("If Ramos is featured on main page, prepare concept art in site style and reference it.")
else:
    lines.append("No direct Ramos reference found in common homepage files checked.")
lines.append("")

lines.append("7) WARNINGS")
lines.append("-" * 60)
if warnings:
    for w in warnings:
        lines.append(f"- {w}")
else:
    lines.append("No obvious warnings detected by static file scan.")
lines.append("")

lines.append("8) NEXT FIX CHECKLIST")
lines.append("-" * 60)
if fixes:
    seen = set()
    for f in fixes:
        if f not in seen:
            lines.append(f"- {f}")
            seen.add(f)
else:
    lines.append("- Page looks basically OK by static scan; inspect browser layout manually.")
lines.append("")

lines.append("9) PACKAGE RULE REMINDER")
lines.append("-" * 60)
lines.append("- Next fix package should be ZIP only.")
lines.append("- No auto site opening.")
lines.append("- No Y/N.")
lines.append("- No auto push.")
lines.append("- Make backup and show touched files.")
lines.append("")

report_path.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
