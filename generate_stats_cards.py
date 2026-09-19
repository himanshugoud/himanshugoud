"""
Generates two GitHub stats SVG cards (stats.svg, top-langs.svg) at identical
480x220 dimensions, using GitHub's own REST API and public contributions page.
No third-party rendering service involved -- guarantees the two cards always
match in size, since this script controls both directly.
"""
import urllib.request
import json
import re
import sys
import html as htmlmod

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "himanshugoud"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return json.loads(urllib.request.urlopen(req).read().decode())


def esc(s):
    return htmlmod.escape(str(s))


user = get(f"https://api.github.com/users/{USERNAME}")
repos = get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")

total_stars = sum(r.get("stargazers_count", 0) for r in repos)
public_repos = user.get("public_repos", len(repos))
followers = user.get("followers", 0)

lang_bytes = {}
for r in repos:
    if r.get("fork"):
        continue
    try:
        langs = get(r["languages_url"])
    except Exception:
        continue
    for lang, b in langs.items():
        lang_bytes[lang] = lang_bytes.get(lang, 0) + b

total_bytes = sum(lang_bytes.values()) or 1
lang_pct = sorted(
    [(lang, b / total_bytes * 100) for lang, b in lang_bytes.items()],
    key=lambda x: -x[1],
)[:6]

contrib_url = f"https://github.com/users/{USERNAME}/contributions"
req = urllib.request.Request(contrib_url, headers={"User-Agent": "Mozilla/5.0"})
contrib_html = urllib.request.urlopen(req).read().decode("utf-8")
pattern = re.compile(r'(No contributions|\d+ contributions?) on ([A-Za-z]+ \d+)\w{0,2}\.')
matches = pattern.findall(contrib_html)
total_commits = sum(0 if c.startswith("No") else int(c.split()[0]) for c, _ in matches)

BG = "#0d1117"
BORDER = "#2d3348"
PURPLE = "#A78BFA"
CYAN = "#7DD3FC"
GREEN = "#4ADE80"
WHITE = "#e6e6f0"
GRAY = "#8b8fa3"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "CSS": "#563d7c",
    "HTML": "#e34c26", "Python": "#3572A5", "C": "#555555",
    "Java": "#b07219", "Shell": "#89e051",
}

W, H = 480, 220

# ---- Card 1: Stats ----
rows = [
    ("Total Stars Earned", total_stars),
    ("Public Repositories", public_repos),
    ("Commits (last year)", total_commits),
    ("Followers", followers),
]

row_y0 = 78
row_h = 32
stats_rows_svg = ""
for i, (label, value) in enumerate(rows):
    y = row_y0 + i * row_h
    stats_rows_svg += f'<text x="30" y="{y}" font-family="Fira Code, monospace" font-size="14">'
    stats_rows_svg += f'<tspan fill="{CYAN}">. {esc(label)}:</tspan></text>'
    stats_rows_svg += f'<text x="{W-30}" y="{y}" font-family="Fira Code, monospace" font-size="14" font-weight="bold" fill="{GREEN}" text-anchor="end">{esc(value)}</text>'

stats_svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
<text x="30" y="38" fill="{PURPLE}" font-family="Fira Code, monospace" font-size="17" font-weight="bold">{esc(user.get("name") or USERNAME)}'s GitHub Stats</text>
<line x1="30" y1="50" x2="{W-30}" y2="50" stroke="{BORDER}" stroke-width="1"/>
{stats_rows_svg}
</svg>'''

with open("profile/stats.svg", "w") as f:
    f.write(stats_svg)

# ---- Card 2: Top Languages ----
bar_x, bar_y, bar_w, bar_h = 30, 70, W - 60, 14
seg_x = bar_x
bar_segments = ""
for lang, pct in lang_pct:
    seg_w = bar_w * (pct / 100)
    color = LANG_COLORS.get(lang, "#888888")
    bar_segments += f'<rect x="{seg_x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{color}"/>'
    seg_x += seg_w

legend_svg = ""
col_w = (W - 60) / 2
for i, (lang, pct) in enumerate(lang_pct):
    col = i % 2
    row = i // 2
    lx = 30 + col * col_w
    ly = 112 + row * 26
    color = LANG_COLORS.get(lang, "#888888")
    legend_svg += f'<circle cx="{lx+5}" cy="{ly-4}" r="5" fill="{color}"/>'
    legend_svg += f'<text x="{lx+18}" y="{ly}" font-family="Fira Code, monospace" font-size="13" fill="{WHITE}">{esc(lang)} <tspan fill="{GRAY}">{pct:.2f}%</tspan></text>'

langs_svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
<text x="30" y="38" fill="{PURPLE}" font-family="Fira Code, monospace" font-size="17" font-weight="bold">Most Used Languages</text>
<line x1="30" y1="50" x2="{W-30}" y2="50" stroke="{BORDER}" stroke-width="1"/>
<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7" fill="#1c2130"/>
{bar_segments}
{legend_svg}
</svg>'''

with open("profile/top-langs.svg", "w") as f:
    f.write(langs_svg)

print(f"wrote profile/stats.svg and profile/top-langs.svg, both {W}x{H}")
