#!/usr/bin/env python3
"""Render assets/info-card.svg - a neofetch-style card for the profile README.

Live numbers come from the public contribution calendar at
https://github.com/users/<user>/contributions, so no API token is needed.
Run with no args.
"""

import os
import re
import urllib.request

USER = os.environ.get("PROFILE_USER", "MAqilNaufal")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# tokyo-night, matching the shields.io badges in the README
BG = "#1a1b27"
FG = "#a9b1d6"
DIM = "#565f89"
BLUE = "#7aa2f7"
PURPLE = "#bb9af7"
GREEN = "#9ece6a"
YELLOW = "#e0af68"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fetch_stats():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-art/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")

    days = {}
    for td in re.findall(r"<td\b[^>]*class=\"[^\"]*ContributionCalendar-day[^\"]*\"[^>]*>", html):
        cid = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
        lvl = re.search(r'data-level="(\d+)"', td)
        if cid and lvl:
            days[(int(cid.group(2)), int(cid.group(1)))] = int(lvl.group(1))  # (week, weekday)

    if not days:
        raise SystemExit("no contribution cells parsed - GitHub markup changed")

    counts = [int(m) for m in re.findall(r">(\d+) contributions? on", html)]
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)

    # longest run of consecutive active days, walked in calendar order
    best = run = 0
    for key in sorted(days, key=lambda k: (k[0], k[1])):
        run = run + 1 if days[key] > 0 else 0
        best = max(best, run)

    return {
        "total": total.group(1) if total else str(sum(counts)),
        "active": sum(1 for v in days.values() if v > 0),
        "streak": best,
        "busiest": max(counts) if counts else 0,
    }


def render(stats, width=520):
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
        ("busiest", f"{stats['busiest']} contributions in one day", GREEN),
        ("", "", None),
        ("web", "maqilnaufal.my.id", PURPLE),
        ("linkedin", "in/maqilnaufal", PURPLE),
        ("", "", None),  # spacer before the trailing prompt
    ]

    pad, top, line_h = 24, 62, 24
    height = round(top + len(rows) * line_h + pad)

    body = [
        f'<text class="p" x="{pad}" y="30">{USER}@github <tspan fill="{DIM}">~ $</tspan> '
        f'<tspan fill="{YELLOW}">neofetch</tspan></text>',
        f'<line x1="{pad}" y1="40" x2="{width - pad}" y2="40" stroke="{DIM}" stroke-opacity=".35"/>',
    ]
    for i, (k, v, color) in enumerate(rows):
        if not k:
            continue
        y = top + i * line_h
        body.append(
            f'<g class="r" style="animation-delay:{0.3 + i * 0.07:.2f}s">'
            f'<text class="k" x="{pad}" y="{y}">{esc(k)}</text>'
            f'<text x="{pad + 96}" y="{y}" fill="{color}">{esc(v)}</text></g>')

    # trailing prompt, so the card ends on a live terminal rather than dead space.
    # The cursor is a tspan in the text flow, which sidesteps guessing glyph widths.
    body.append(
        f'<g class="r" style="animation-delay:{0.3 + len(rows) * 0.07:.2f}s">'
        f'<text class="p" x="{pad}" y="{top + len(rows) * line_h}">{USER}@github '
        f'<tspan fill="{DIM}">~ $</tspan> <tspan class="cur" fill="{FG}">█</tspan></text></g>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Profile summary for {USER}">
<style>
text{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:13px}}
.p{{fill:{GREEN}}}
.k{{fill:{DIM}}}
.r{{opacity:0;animation:in .5s ease-out forwards}}
.cur{{animation:blink 1.1s steps(1) infinite}}
@keyframes in{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes blink{{0%,50%{{opacity:1}}50.01%,100%{{opacity:0}}}}
</style>
<rect width="100%" height="100%" rx="8" fill="{BG}"/>
{chr(10).join(body)}
</svg>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    stats = fetch_stats()
    svg = render(stats)
    with open(os.path.join(OUT, "info-card.svg"), "w") as f:
        f.write(svg)
    print(f"wrote info-card.svg ({len(svg)} bytes) {stats}")


if __name__ == "__main__":
    main()
