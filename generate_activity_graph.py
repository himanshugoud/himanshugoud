"""
Generates a small SVG line chart of daily contributions for the last 90 days,
using GitHub's own public contributions page (github.com/users/<name>/contributions)
as the data source. No third-party rendering service involved.
"""
import re
import sys
import urllib.request

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "himanshugoud"

url = f"https://github.com/users/{USERNAME}/contributions"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8")

pattern = re.compile(r'(No contributions|\d+ contributions?) on ([A-Za-z]+ \d+)\w{0,2}\.')
matches = pattern.findall(html)

counts = []
for count_str, _ in matches:
    if count_str.startswith("No"):
        counts.append(0)
    else:
        counts.append(int(count_str.split()[0]))

N = 90
counts = counts[-N:]


def build_svg(values, width=760, height=200, pad_l=20, pad_r=20, pad_t=34, pad_b=20):
    n = len(values)
    maxv = max(values) if max(values) else 1
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def x(i):
        return pad_l + (i / (n - 1)) * plot_w

    def y(v):
        return pad_t + plot_h - (v / maxv) * plot_h

    points = [(x(i), y(v)) for i, v in enumerate(values)]
    path_d = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in points)
    area_d = path_d + f" L {points[-1][0]:.1f},{pad_t+plot_h} L {points[0][0]:.1f},{pad_t+plot_h} Z"

    grid = ""
    for gy in range(0, 5):
        yy = pad_t + plot_h * gy / 4
        grid += f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" stroke="#2d3348" stroke-width="1"/>'

    total = sum(values)
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#0d1117" rx="8"/>
  <text x="{pad_l}" y="20" fill="#A78BFA" font-family="Fira Code, monospace" font-size="13" font-weight="bold">Daily Contributions -- last {n} days ({total} total)</text>
  {grid}
  <defs>
    <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8E2DE2" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#8E2DE2" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <path d="{area_d}" fill="url(#fillGrad)"/>
  <path d="{path_d}" fill="none" stroke="#A78BFA" stroke-width="2"/>
</svg>'''


svg = build_svg(counts)
with open("profile/activity.svg", "w") as f:
    f.write(svg)
print(f"wrote profile/activity.svg from {len(counts)} days of real data")
