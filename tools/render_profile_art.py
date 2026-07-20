#!/usr/bin/env python3
"""Render the three animated SVGs used by the profile README.

  assets/avi-ascii.svg       self-typing ASCII portrait from the GitHub avatar
  assets/info-card.svg       neofetch-style key/value card
  assets/contrib-heatmap.svg live 53x7 contribution calendar

No API token: the avatar and the contribution calendar are both public HTML.
Run with no args; writes into assets/ next to this file's parent.
"""

import io
import os
import re
import urllib.request

USER = os.environ.get("PROFILE_USER", "MAqilNaufal")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# tokyo-night, to match the shields.io badges already in the README
BG = "#1a1b27"
FG = "#a9b1d6"
DIM = "#565f89"
BLUE = "#7aa2f7"
PURPLE = "#bb9af7"
GREEN = "#9ece6a"
YELLOW = "#e0af68"
HEAT = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

RAMP = " .`:-=+*cs#%@"  # bright -> dark


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-art/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- ascii portrait

def ascii_portrait(width=370, cols=72):
    from PIL import Image, ImageChops, ImageOps

    img = Image.open(io.BytesIO(get(f"https://github.com/{USER}.png", binary=True)))
    if img.mode == "RGBA":
        img = Image.alpha_composite(Image.new("RGBA", img.size, (26, 27, 39, 255)), img)
    img = img.convert("RGB")
    w, h = img.size

    corners = [img.getpixel(p) for p in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2))]
    flat_bg = all(sum(abs(a - b) for a, b in zip(c, corners[0])) < 30 for c in corners)

    # A flat-colour avatar (the current one is a cartoon on solid blue) can't be
    # separated by luminance alone - its background sits between the light and
    # dark parts of the subject. Key the background out by colour distance, then
    # shade what's left by darkness. Photos have no flat corners, so they take
    # the plain luminance path instead.
    if flat_bg:
        bg = Image.new("RGB", img.size, corners[0])
        dist = ImageChops.difference(img, bg).convert("L").point(
            lambda v: min(255, int(v * 255 / 48)))  # 48/255 tolerance, then saturate
    else:
        dist = Image.new("L", img.size, 255)

    dark = ImageOps.autocontrast(ImageOps.invert(img.convert("L")))

    # halve vertical resolution: character cells are ~2x taller than wide
    rows = max(1, round(cols * h / w * 0.5))
    cov = dist.resize((cols, rows), Image.LANCZOS).load()
    tone = dark.resize((cols, rows), Image.LANCZOS).load()

    advance = width / cols
    line_h = advance * 2  # undoes the 0.5 vertical sampling, so aspect is preserved
    height = round(rows * line_h)

    lines = []
    for y in range(rows):
        row = ""
        for x in range(cols):
            # coverage decides ink-or-nothing, darkness only picks how heavy the ink is
            d = (cov[x, y] / 255) * (0.35 + 0.65 * tone[x, y] / 255)
            row += RAMP[min(len(RAMP) - 1, int(d * len(RAMP)))]
        lines.append(row.rstrip() or " ")

    # each row wipes in left-to-right behind its own clip rect
    body, clips = [], []
    for i, line in enumerate(lines):
        y = (i + 0.85) * line_h
        clips.append(
            f'<clipPath id="c{i}"><rect x="0" y="{i * line_h:.2f}" width="0" height="{line_h:.2f}">'
            f'<animate attributeName="width" from="0" to="{width}" begin="{i * 0.045:.3f}s"'
            f' dur="0.34s" fill="freeze"/></rect></clipPath>')
        # textLength pins the row to an exact width, so alignment holds whatever
        # monospace font the viewer actually resolves
        body.append(
            f'<text x="0" y="{y:.2f}" textLength="{len(line) * advance:.2f}" lengthAdjust="spacing"'
            f' clip-path="url(#c{i})" xml:space="preserve">{esc(line)}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait of {USER}">
<style>text{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:{advance / 0.6:.2f}px;fill:{FG}}}</style>
<defs>{"".join(clips)}</defs>
<rect width="100%" height="100%" fill="{BG}"/>
{chr(10).join(body)}
</svg>'''


# ---------------------------------------------------------------- info card

def info_card(stats, width=490, height=370):
    rows = [
        ("name", "Muhamad Aqil Naufal", BLUE),
        ("role", "System Analyst / Digital Marketing", FG),
        ("focus", "AI-driven internal tooling", FG),
        ("stack", "Python · TypeScript · SQL · Next.js", FG),
        ("data", "BigQuery · Power BI · Supabase", FG),
        ("infra", "Docker · n8n · GitHub Actions", FG),
        ("", "", None),
        ("commits", f"{stats['total']} in the last year", GREEN),
        ("active", f"{stats['active']} days · {stats['streak']} day streak", GREEN),
        ("busiest", f"{stats['best']} contributions in one day", GREEN),
        ("", "", None),
        ("web", "maqilnaufal.my.id", PURPLE),
        ("linkedin", "in/maqilnaufal", PURPLE),
    ]

    # height is pinned to the portrait's so the two panels line up side by side
    pad, top = 22, 58
    line_h = (height - top - pad - 16) / len(rows)

    body = [
        f'<text class="p" x="{pad}" y="28">{USER}@github <tspan fill="{DIM}">~ $</tspan> '
        f'<tspan fill="{YELLOW}">neofetch</tspan></text>',
        f'<line x1="{pad}" y1="36" x2="{width - pad}" y2="36" stroke="{DIM}" stroke-opacity=".35"/>',
    ]
    for i, (k, v, color) in enumerate(rows):
        if not k:
            continue
        y = round(top + i * line_h, 2)
        body.append(
            f'<g class="r" style="animation-delay:{0.35 + i * 0.06:.2f}s">'
            f'<text class="k" x="{pad}" y="{y}">{esc(k)}</text>'
            f'<text class="v" x="{pad + 92}" y="{y}" fill="{color}">{esc(v)}</text></g>')

    swatch = "".join(
        f'<rect x="{pad + i * 26}" y="{height - pad - 12}" width="18" height="9" rx="2" fill="{c}"/>'
        for i, c in enumerate([BLUE, PURPLE, GREEN, YELLOW, "#f7768e", FG, DIM]))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Profile summary for {USER}">
<style>
text{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:13px}}
.p{{fill:{GREEN};font-size:13px}}
.k{{fill:{DIM}}}
.r{{opacity:0;animation:in .5s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:translateX(0)}}}}
</style>
<rect width="100%" height="100%" rx="8" fill="{BG}"/>
{chr(10).join(body)}
{swatch}
</svg>'''


# ---------------------------------------------------------------- heatmap

def fetch_contributions():
    html = get(f"https://github.com/users/{USER}/contributions")
    days = {}
    for td in re.findall(r"<td\b[^>]*class=\"[^\"]*ContributionCalendar-day[^\"]*\"[^>]*>", html):
        cid = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
        lvl = re.search(r'data-level="(\d+)"', td)
        if not (cid and lvl):
            continue
        days[(int(cid.group(2)), int(cid.group(1)))] = int(lvl.group(1))  # (week, weekday)

    if not days:
        raise SystemExit("no contribution cells parsed - GitHub markup changed")

    counts = [int(m) for m in re.findall(r">(\d+) contributions? on", html)]
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    active = sum(1 for v in days.values() if v > 0)

    # longest run of consecutive active days, walked in calendar order
    best_streak = run = 0
    for wk, wd in sorted(days, key=lambda k: (k[0], k[1])):
        run = run + 1 if days[(wk, wd)] > 0 else 0
        best_streak = max(best_streak, run)

    return days, {
        "total": total.group(1) if total else str(sum(counts)),
        "active": active,
        "streak": best_streak,
        "best": max(counts) if counts else 0,
    }


def heatmap(days, width=860):
    weeks = max(w for w, _ in days) + 1
    gap, pad, top = 3, 14, 26
    cell = (width - pad * 2 - (weeks - 1) * gap) / weeks
    height = round(top + 7 * (cell + gap) - gap + pad)

    rects = []
    for (wk, wd), lvl in sorted(days.items()):
        x = pad + wk * (cell + gap)
        y = top + wd * (cell + gap)
        rects.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="2"'
            f' fill="{HEAT[min(lvl, 4)]}" style="animation-delay:{(wk + wd) * 0.012:.3f}s"/>')

    legend_x = width - pad - 5 * (cell + gap) - 2
    legend = "".join(
        f'<rect class="lg" x="{legend_x + i * (cell + gap):.2f}" y="{top - cell - 8:.2f}"'
        f' width="{cell:.2f}" height="{cell:.2f}" rx="2" fill="{c}"/>'
        for i, c in enumerate(HEAT))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution calendar for the last year">
<style>
text{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:12px;fill:{DIM}}}
rect.d{{opacity:0;animation:pop .45s ease-out forwards}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
</style>
<rect width="100%" height="100%" rx="8" fill="{BG}"/>
<text x="{pad}" y="{top - 10}">last 12 months</text>
<g class="cells">{"".join(r.replace("<rect ", '<rect class="d" ') for r in rects)}</g>
{legend}
</svg>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    days, stats = fetch_contributions()
    for name, svg in [
        ("avi-ascii.svg", ascii_portrait()),
        ("info-card.svg", info_card(stats)),
        ("contrib-heatmap.svg", heatmap(days)),
    ]:
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg)
        print(f"wrote {name} ({len(svg)} bytes)")
    print(stats)


if __name__ == "__main__":
    main()
