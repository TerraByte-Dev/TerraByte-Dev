#!/usr/bin/env python3
"""Bespoke body components for the TERRABYTE profile — replaces stock shields/table
with custom phosphor SVG: a stack panel and clickable project cards. Each card is an
<img> wrapped in a markdown link, so it's custom-looking AND clickable.
Self-contained animated SVG, GitHub <img>-safe; honors prefers-reduced-motion."""
import json

MINT = "#02EEAA"; INK = "#9BF5B8"; FAINT = "#2f6f4e"; BG = "#020503"; PANEL = "#04090a"

DEFS = f'''<defs>
    <style>
      @keyframes p {{ 0%,100%{{opacity:.5}} 50%{{opacity:1}} }}
      .dot {{ animation:p 1.8s ease-in-out infinite }}
      @keyframes bar {{ 0%,100%{{opacity:.6}} 50%{{opacity:1}} }}
      .accent {{ animation:bar 2.6s ease-in-out infinite }}
      @media (prefers-reduced-motion: reduce){{ .dot,.accent{{animation:none}} }}
    </style>
    <filter id="g" x="-40%" y="-40%" width="180%" height="180%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1" result="a"/><feGaussianBlur in="SourceGraphic" stdDeviation="3.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="sc" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" fill-opacity="0.30"/></pattern>
  </defs>'''

def card(idx, name, desc, lang):
    W, H = 900, 116
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,'IBM Plex Mono',SFMono-Regular,Menlo,Consolas,monospace" role="img" aria-label="{name} — {desc}">
  {DEFS}
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="3" fill="{BG}" stroke="{MINT}" stroke-width="1" stroke-opacity="0.28"/>
  <rect class="accent" x="1" y="1" width="5" height="{H-2}" rx="2" fill="{MINT}" filter="url(#g)"/>
  <text x="30" y="38" fill="{FAINT}" font-size="14" letter-spacing="3">{idx:02d}</text>
  <circle class="dot" cx="34" cy="80" r="4" fill="{MINT}" filter="url(#g)"/>
  <text x="74" y="48" fill="{MINT}" font-size="27" letter-spacing="1.5" filter="url(#g)">{name}</text>
  <text x="74" y="80" fill="{INK}" font-size="15.5" letter-spacing="0.4">{desc}</text>
  <g transform="translate({W-150},34)">
    <rect x="0" y="0" width="118" height="26" rx="3" fill="{PANEL}" stroke="{MINT}" stroke-width="1" stroke-opacity="0.35"/>
    <text x="59" y="18" text-anchor="middle" fill="{INK}" font-size="13" letter-spacing="2">{lang}</text>
  </g>
  <text x="{W-30}" y="92" text-anchor="end" fill="{MINT}" font-size="18" filter="url(#g)" opacity="0.9">&#8599;</text>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="3" fill="url(#sc)"/>
</svg>
'''

def stack_panel(groups):
    W = 900
    rowh, padtop = 40, 56
    H = padtop + rowh * len(groups) + 16
    rows = []
    for i, (label, items) in enumerate(groups):
        y = padtop + i * rowh
        rows.append(f'<text x="34" y="{y}" fill="{FAINT}" font-size="13" letter-spacing="3">{label}</text>')
        x = 190
        for it in items:
            w = 16 + len(it) * 9.2
            rows.append(f'<g transform="translate({round(x)},{y-19})">'
                        f'<rect width="{round(w)}" height="27" rx="3" fill="{PANEL}" stroke="{MINT}" stroke-width="1" stroke-opacity="0.30"/>'
                        f'<text x="{round(w/2)}" y="18" text-anchor="middle" fill="{INK}" font-size="13.5" letter-spacing="1">{it}</text></g>')
            x += w + 12
    rows_xml = "\n  ".join(rows)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,'IBM Plex Mono',SFMono-Regular,Menlo,Consolas,monospace" role="img" aria-label="stack">
  {DEFS}
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="3" fill="{BG}" stroke="{MINT}" stroke-width="1" stroke-opacity="0.22"/>
  <rect class="accent" x="1" y="1" width="5" height="{H-2}" rx="2" fill="{MINT}" filter="url(#g)"/>
  <text x="30" y="32" fill="{MINT}" font-size="16" letter-spacing="4" filter="url(#g)">STACK</text>
  <line x1="30" y1="42" x2="{W-30}" y2="42" stroke="{MINT}" stroke-width="1" stroke-opacity="0.18"/>
  {rows_xml}
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="3" fill="url(#sc)"/>
</svg>
'''

CARDS = [
    (1, "OpenEdu",     "Open-source AI tutoring platform — learn anything from absolute zero.", "TypeScript"),
    (2, "RADAR",       "Local-first project radar — every project is a blip on a CRT scope.",   "TypeScript"),
    (3, "TerraPlayer", "Offline desktop music player — no internet required.",                  "TypeScript"),
    (4, "hinge-auto",  "Emulator + ADB + vision-LLM that judges profiles against a rubric.",        "Python"),
]
SLUG = {"OpenEdu": "openedu", "RADAR": "radar", "TerraPlayer": "terraplayer", "hinge-auto": "hinge-auto"}
STACK = [
    ("LANGUAGES", ["TypeScript", "Python", "Lua", "C#"]),
    ("FRAMEWORKS", ["Astro", "React", "Node.js", "Electron", "Tailwind"]),
    ("INFRA / AI", ["Vercel", "Cloudflare", "PostgreSQL", "n8n", "LLMs"]),
]

for idx, name, desc, lang in CARDS:
    open(f"assets/card-{SLUG[name]}.svg", "w", encoding="utf-8").write(card(idx, name, desc, lang))
open("assets/stack.svg", "w", encoding="utf-8").write(stack_panel(STACK))
print("wrote assets/stack.svg + 4 project cards")
