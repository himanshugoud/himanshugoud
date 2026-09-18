"""
Generates an SVG line chart of daily contributions for the last 90 days,
using GitHub's own public contributions page (github.com/users/<name>/contributions)
as the data source. No third-party rendering service involved.
"""
import re
import math
import sys
import urllib.request

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "himanshugoud"

url = f"https://github.com/users/{USERNAME}/contributions"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8")

td_pattern = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="(contribution-day-component-[^"]+)"')
tds = dict((b, a) for a, b in td_pattern.findall(html))  # id -> date

tip_pattern = re.compile(r'for="(contribution-day-component-[^"]+)"[^>]*>\s*(No contributions|\d+ contributions?) on', re.DOTALL)
tips = tip_pattern.findall(html)

records = []
for cell_id, count_str in tips:
    date = tds.get(cell_id)
    if not date:
        continue
    count = 0 if count_str.startswith("No") else int(count_str.split()[0])
    records.append((date, count))

records.sort(key=lambda r: r[0])  # ISO dates sort correctly as strings

N = 90
records = records[-N:]
counts = [c for _, c in records]
dates = [d for d, _ in records]


def fmt_label(iso_date):
    _, m, d = iso_date.split("-")
    months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[int(m)]} {int(d)}"


def build_svg(values, dates, width=760, height=220, pad_l=36, pad_r=20, pad_t=34, pad_b=34):
    n = len(values)
    maxv = max(values) if max(values) else 1
    step = max(1, math.ceil(maxv / 4))
    maxv_rounded = step * 4

    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def x(i):
        return pad_l + (i / (n - 1)) * plot_w

    def y(v):
        return pad_t + plot_h - (v / maxv_rounded) * plot_h

    points = [(x(i), y(v)) for i, v in enumerate(values)]
    path_d = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    area_d = path_d + f" L {points[-1][0]:.1f},{pad_t+plot_h} L {points[0][0]:.1f},{pad_t+plot_h} Z"

    grid = ""
    ylabels = ""
    for gy in range(0, 5):
        yy = pad_t + plot_h * gy / 4
        val = maxv_rounded - step * gy
        grid += f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" stroke="#2d3348" stroke-width="1"/>'
        ylabels += f'<text x="{pad_l-8}" y="{yy+4:.1f}" fill="#8b8fa3" font-family="Fira Code, monospace" font-size="10" text-anchor="end">{val}</text>'

    xlabels = ""
    tick_count = 6
    for t in range(tick_count):
        idx = int(t * (n - 1) / (tick_count - 1))
        xx = x(idx)
        xlabels += f'<text x="{xx:.1f}" y="{height-pad_b+16}" fill="#8b8fa3" font-family="Fira Code, monospace" font-size="10" text-anchor="middle">{fmt_label(dates[idx])}</text>'
        xlabels += f'<line x1="{xx:.1f}" y1="{pad_t+plot_h}" x2="{xx:.1f}" y2="{pad_t+plot_h+4}" stroke="#8b8fa3" stroke-width="1"/>'

    total = sum(values)
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#0d1117" rx="8"/>
  <text x="{width/2}" y="20" fill="#A78BFA" font-family="Fira Code, monospace" font-size="13" font-weight="bold" text-anchor="middle">Himanshu Goud's Contribution Graph -- last {n} days ({total} total)</text>
  {grid}
  {ylabels}
  {xlabels}
  <defs>
    <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8E2DE2" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#8E2DE2" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <path d="{area_d}" fill="url(#fillGrad)"/>
  <path d="{path_d}" fill="none" stroke="#A78BFA" stroke-width="2"/>
</svg>'''


svg = build_svg(counts, dates)
with open("profile/activity.svg", "w") as f:
    f.write(svg)
print(f"wrote profile/activity.svg: {dates[0]} to {dates[-1]}, total {sum(counts)}")
