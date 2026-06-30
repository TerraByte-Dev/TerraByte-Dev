#!/usr/bin/env python3
"""Parametric TERRABYTE hero generator.

Two realities from one geometry:
  --mode online     neon phosphor system, powered ON (dark theme)
  --mode blueprint  technical drawing of the same machine (light theme)

Self-rewriting inputs (the GitHub Action passes these so the hero evolves):
  --seed N      generative starfield (unique per day)
  --uptime N    DAY counter
  --date STR    stamp / blueprint revision
  --featured S  current focus project

Self-contained animated SVG, GitHub <img>-safe (SMIL + internal CSS).
Honors prefers-reduced-motion.  Run with no args to build both at today's values.
"""
import json, math, argparse, random, datetime, subprocess, sys

W, H = 1280, 420
wm = json.load(open("assets/wordmarks.json", encoding="utf-8"))
terr = wm["strings"]["TERRABYTE"]            # monospace, sum_adv 3600
S = 0.197
wm_w = terr["sum_adv"] * S
RX0, RX1 = 470, 1250
ox = round(RX0 + ((RX1 - RX0) - wm_w) / 2, 1)
by = 220
gcx, gcy, R = 305, 210, 152
START = datetime.date(2025, 7, 12)           # account birthday -> uptime

PAL = {
    "online":    dict(bg="#000000", line="#02EEAA", ink="#9BF5B8", faint="#2f6f4e",
                      star="#7CFFCB", glow=True),
    "blueprint": dict(bg="#eef3f7", line="#1c5475", ink="#274b5f", faint="#86a8bf",
                      star="#a9c4d6", glow=False),
}

# ---------- geometry helpers ----------
def meridians(col, glow):
    K, NS, T = 7, 37, 11.0
    parts = []
    for i in range(K):
        phase = i * math.pi / K
        rx, op = [], []
        for j in range(NS):
            c = math.cos(2 * math.pi * j / (NS - 1) + phase)
            rx.append(str(round(R * abs(c), 1)))
            op.append(str(round((0.22 if glow else 0.35) + 0.6 * abs(c), 3)))
        dash = ' stroke-dasharray="2 7"' if i == 0 else ''
        parts.append(
            f'<ellipse cx="{gcx}" cy="{gcy}" rx="{R}" ry="{R}" fill="none" stroke="{col}" stroke-width="1.5"{dash}>'
            f'<animate attributeName="rx" values="{";".join(rx)}" dur="{T}s" repeatCount="indefinite"/>'
            f'<animate attributeName="stroke-opacity" values="{";".join(op)}" dur="{T}s" repeatCount="indefinite"/></ellipse>')
    return "\n      ".join(parts)

def latitudes(col, glow):
    out = []
    for f in [-0.82, -0.55, -0.28, 0, 0.28, 0.55, 0.82]:
        dy = f * R
        rxx = math.sqrt(max(R * R - dy * dy, 0))
        op = (0.85 if glow else 0.7) if abs(f) < 0.01 else (0.5 if glow else 0.45)
        out.append(f'<ellipse cx="{gcx}" cy="{round(gcy+dy,1)}" rx="{round(rxx,1)}" ry="{round(rxx*0.20,1)}" '
                   f'fill="none" stroke="{col}" stroke-width="1.3" stroke-opacity="{op}"/>')
    return "\n      ".join(out)

def core_T(col):
    cx, cy = gcx, gcy
    return (f'<g fill="{col}">'
            f'<circle cx="{cx-23}" cy="{cy-82}" r="8.5"/><circle cx="{cx+23}" cy="{cy-82}" r="8.5"/>'
            f'<rect x="{cx-26}" y="{cy-80}" width="6" height="34" rx="3"/>'
            f'<rect x="{cx+20}" y="{cy-80}" width="6" height="34" rx="3"/>'
            f'<path d="M {cx-10} {cy-46} L {cx+10} {cy-46} L {cx+13} {cy+12} L {cx} {cy+106} L {cx-13} {cy+12} Z"/></g>'
            f'<path d="M {cx-84} {cy-16} C {cx-64} {cy-50} {cx-26} {cy-52} {cx} {cy-51} '
            f'C {cx+26} {cy-52} {cx+64} {cy-50} {cx+84} {cy-16}" fill="none" stroke="{col}" stroke-width="15" stroke-linecap="round"/>')

def starfield(seed, col, n=64):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        x, y = round(rng.uniform(8, W - 8), 1), round(rng.uniform(8, H - 8), 1)
        if (x - gcx) ** 2 + (y - gcy) ** 2 < (R - 6) ** 2:   # keep the globe interior clear
            continue
        r = round(rng.uniform(0.5, 1.7), 2)
        b = round(rng.uniform(0.12, 0.55), 2)
        d = round(rng.uniform(2.6, 6.0), 1)
        bg = round(-rng.uniform(0, d), 1)
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" opacity="{b}">'
                   f'<animate attributeName="opacity" values="{b};{round(b*0.18,2)};{b}" dur="{d}s" begin="{bg}s" repeatCount="indefinite"/></circle>')
    return "\n      ".join(out)

def orbit_sat(col):
    ry = round(R * 0.20, 1)
    d = (f"M {gcx-R} {gcy} A {R} {ry} 0 1 1 {gcx+R} {gcy} A {R} {ry} 0 1 1 {gcx-R} {gcy} Z")
    return (f'<circle r="5.5" fill="{col}"><animateMotion dur="11s" repeatCount="indefinite" rotate="auto" path="{d}"/>'
            f'<animate attributeName="opacity" values="1;1;0.35;0.35;1" keyTimes="0;0.25;0.5;0.75;1" dur="11s" repeatCount="indefinite"/></circle>')

# ---------- blueprint drafting annotations ----------
def dim_h(x1, x2, y, label, col):
    return (f'<g stroke="{col}" stroke-width="1" fill="{col}" font-size="13" letter-spacing="1">'
            f'<line x1="{x1}" y1="{y-5}" x2="{x1}" y2="{y+5}"/><line x1="{x2}" y1="{y-5}" x2="{x2}" y2="{y+5}"/>'
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'
            f'<path d="M{x1} {y} l8 -3 v6 z"/><path d="M{x2} {y} l-8 -3 v6 z"/>'
            f'<rect x="{(x1+x2)//2-30}" y="{y-10}" width="60" height="20" fill="{PAL["blueprint"]["bg"]}" stroke="none"/>'
            f'<text x="{(x1+x2)//2}" y="{y+4}" text-anchor="middle" stroke="none">{label}</text></g>')

def callout(x1, y1, x2, y2, label, col, anchor="start"):
    return (f'<g stroke="{col}" stroke-width="1" fill="{col}" font-size="12" letter-spacing="1.5">'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/><circle cx="{x1}" cy="{y1}" r="2.5" stroke="none"/>'
            f'<text x="{x2 + (6 if anchor=="start" else -6)}" y="{y2+4}" text-anchor="{anchor}" stroke="none">{label}</text></g>')

# ---------- CSS (literal braces; injected, not f-parsed) ----------
STYLE = """
  @keyframes blink { 0%,46%{opacity:1} 47%,100%{opacity:0} }
  @keyframes flick { 0%,100%{opacity:1} 92%{opacity:1} 94%{opacity:.8} 96%{opacity:1} 97%{opacity:.88} 98%{opacity:1} }
  @keyframes glitch { 0%,89%,100%{transform:translate(0,0)} 90%{transform:translate(-2px,0)} 91%{transform:translate(2px,0)} 92%{transform:translate(-1px,0)} 93%{transform:translate(0,0)} }
  @keyframes ghostR { 0%,89%,100%{opacity:0} 90.5%,92%{opacity:.45} }
  @keyframes ghostC { 0%,89%,100%{opacity:0} 90.5%,92%{opacity:.4} }
  @keyframes sweepY { 0%{transform:translateY(-30px);opacity:0} 8%{opacity:.9} 92%{opacity:.9} 100%{transform:translateY(420px);opacity:0} }
  @keyframes pulse { 0%,100%{opacity:.85} 50%{opacity:1} }
  @keyframes drawline { from{stroke-dashoffset:300} to{stroke-dashoffset:0} }
  @keyframes dash { to { stroke-dashoffset: -16 } }
  .screen{animation:flick 7s steps(1) infinite}
  .wm{animation:glitch 6.5s ease-in-out infinite}
  .wm-r{animation:ghostR 6.5s ease-in-out infinite}
  .wm-c{animation:ghostC 6.5s ease-in-out infinite}
  .sweep{animation:sweepY 5.5s linear infinite}
  .core{animation:pulse 3.2s ease-in-out infinite}
  .rule{stroke-dasharray:300;animation:drawline 1.6s ease-out forwards, pulse 3.2s ease-in-out 1.6s infinite}
  .march{stroke-dasharray:6 4;animation:dash 1.4s linear infinite}
  @media (prefers-reduced-motion: reduce){
    .screen,.wm,.wm-r,.wm-c,.sweep,.core,.rule,.march{animation:none}
    .wm-r,.wm-c,.sweep{opacity:0}.rule{stroke-dashoffset:0}
  }
"""

def build(mode, seed, uptime, date, featured):
    p = PAL[mode]; col = p["line"]; ink = p["ink"]; faint = p["faint"]
    bloom = ' filter="url(#bloom)"' if p["glow"] else ''
    soft = ' filter="url(#soft)"' if p["glow"] else ''
    screen_cls = ""
    flash_rect = ""   # cinematic boot dropped: CSS overlays/effects are unreliable in SVG-as-img

    # backgrounds / overlays differ per mode
    if mode == "online":
        bg = f'''<rect width="{W}" height="{H}" fill="{p['bg']}"/>
    <rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#spotmask)"/>
    <g>{starfield(seed, p['star'])}</g>'''
        deco_back = f'<circle cx="{gcx}" cy="{gcy}" r="{R+26}" fill="url(#halo)"/>'
        stamp = (f'<text x="40" y="{H-26}" fill="{faint}" font-size="13" letter-spacing="3">DAY {uptime:04d}</text>'
                 f'<text x="{W-40}" y="{H-26}" text-anchor="end" fill="{faint}" font-size="13" letter-spacing="3">{date}</text>')
        sweep = f'<rect class="sweep" x="0" y="0" width="{W}" height="26" fill="url(#sweepg)"/>'
        overlays = f'<rect width="{W}" height="{H}" fill="url(#scan)"/><rect width="{W}" height="{H}" fill="url(#vig)"/>'
        wm_block = f'''<g class="wm"{bloom}>
      <g class="wm-c" fill="#00c8ff"><g transform="translate({ox+3},{by}) scale({S},-{S})">{terr['inner']}</g></g>
      <g class="wm-r" fill="#ff2e6a"><g transform="translate({ox-3},{by}) scale({S},-{S})">{terr['inner']}</g></g>
      <g transform="translate({ox},{by}) scale({S},-{S})" fill="{col}">{terr['inner']}</g></g>'''
        rule = f'<line class="rule" x1="{ox+12}" y1="{by+24}" x2="{ox+round(wm_w)-12}" y2="{by+24}" stroke="url(#rule)" stroke-width="2.5"{soft}/>'
        tagline = f'<g{soft}><text x="{round(ox+wm_w/2)}" y="{by+58}" text-anchor="middle" fill="{ink}" font-size="21" letter-spacing="2">technologist &#183; builder &#183; jack of all trades</text></g>'
        extra = ""
    else:  # blueprint
        bg = f'''<rect width="{W}" height="{H}" fill="{p['bg']}"/>
    <rect width="{W}" height="{H}" fill="url(#paper)"/>
    <rect width="{W}" height="{H}" fill="url(#paper2)"/>'''
        deco_back = ""
        stamp = ""  # title block carries the date
        sweep = ""
        overlays = f'<rect x="6" y="6" width="{W-12}" height="{H-12}" fill="none" stroke="{col}" stroke-width="1.5"/><rect x="12" y="12" width="{W-24}" height="{H-24}" fill="none" stroke="{col}" stroke-width="0.6" stroke-opacity="0.5"/>'
        wm_block = f'<g transform="translate({ox},{by}) scale({S},-{S})" fill="none" stroke="{col}" stroke-width="3">{terr["inner"]}</g>'
        rule = f'<line class="march" x1="{ox+12}" y1="{by+24}" x2="{ox+round(wm_w)-12}" y2="{by+24}" stroke="{col}" stroke-width="1.4"/>'
        tagline = f'<text x="{round(ox+wm_w/2)}" y="{by+58}" text-anchor="middle" fill="{ink}" font-size="18" letter-spacing="4">TECHNOLOGIST &#183; BUILDER &#183; JACK OF ALL TRADES</text>'
        # drafting annotations + title block
        tb_x, tb_y, tb_w, tb_h = W - 372, H - 92, 360, 80
        extra = f'''
    {dim_h(gcx-R, gcx+R, gcy+R+34, f"&#216;{2*R}", col)}
    {callout(gcx-2, gcy-78, gcx-150, gcy-104, "ANTENNA NODE", col, "end")}
    {callout(gcx+R*0.72, gcy-R*0.5, gcx+150, gcy-118, "MERIDIAN &#215;7", col, "start")}
    {callout(gcx, gcy+40, gcx-150, gcy+92, "CORE-T", col, "end")}
    {callout(gcx+R*0.96, gcy, gcx+150, gcy+30, "EQUATOR", col, "start")}
    <g font-size="12" letter-spacing="1" fill="{col}">
      <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" fill="none" stroke="{col}" stroke-width="1.4"/>
      <line x1="{tb_x}" y1="{tb_y+28}" x2="{tb_x+tb_w}" y2="{tb_y+28}" stroke="{col}" stroke-width="0.8"/>
      <line x1="{tb_x+tb_w-120}" y1="{tb_y}" x2="{tb_x+tb_w-120}" y2="{tb_y+tb_h}" stroke="{col}" stroke-width="0.8"/>
      <text x="{tb_x+12}" y="{tb_y+19}" font-size="15" letter-spacing="2">FIG.1 &#8212; TERRABYTE MK.II</text>
      <text x="{tb_x+12}" y="{tb_y+46}">PROJECTION: ORTHO</text>
      <text x="{tb_x+12}" y="{tb_y+66}">SCALE 1:1</text>
      <text x="{tb_x+tb_w-108}" y="{tb_y+46}">REV {date}</text>
      <text x="{tb_x+tb_w-108}" y="{tb_y+66}">DAY {uptime:04d}</text>
    </g>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="ui-monospace,'IBM Plex Mono',SFMono-Regular,Menlo,Consolas,monospace" role="img" aria-label="TERRABYTE — technologist, builder, jack of all trades">
  <defs>
    <style>{STYLE}</style>
    <filter id="bloom" x="-70%" y="-70%" width="240%" height="240%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1.1" result="g1"/><feGaussianBlur in="SourceGraphic" stdDeviation="4" result="g2"/><feGaussianBlur in="SourceGraphic" stdDeviation="12" result="g3"/>
      <feMerge><feMergeNode in="g3"/><feMergeNode in="g2"/><feMergeNode in="g1"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="soft" x="-60%" y="-60%" width="220%" height="220%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <radialGradient id="vig" cx="50%" cy="42%" r="75%"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="0.7" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.7"/></radialGradient>
    <radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{col}" stop-opacity="0.16"/><stop offset="0.6" stop-color="{col}" stop-opacity="0.04"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{col}" stop-opacity="0"/><stop offset="0.5" stop-color="{col}" stop-opacity="1"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient>
    <linearGradient id="sweepg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity="0"/><stop offset="0.5" stop-color="{col}" stop-opacity="0.5"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="{col}" stroke-width="1" stroke-opacity="0.05"/></pattern>
    <pattern id="paper" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="{PAL['blueprint']['faint']}" stroke-width="0.6" stroke-opacity="0.5"/></pattern>
    <pattern id="paper2" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M100 0H0V100" fill="none" stroke="{PAL['blueprint']['line']}" stroke-width="0.8" stroke-opacity="0.25"/></pattern>
    <pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" fill-opacity="0.34"/></pattern>
    <radialGradient id="spot" cx="50%" cy="45%" r="62%"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="spotmask"><rect width="{W}" height="{H}" fill="url(#spot)"/></mask>
  </defs>
  {bg}
  <g class="screen{screen_cls}">
    {deco_back}
    <g{bloom}>
      <circle cx="{gcx}" cy="{gcy}" r="{R}" fill="none" stroke="{col}" stroke-width="2"/>
      {latitudes(col, p['glow'])}
      {meridians(col, p['glow'])}
      <g class="core"{soft}>{core_T(col)}</g>
      {orbit_sat(col)}
    </g>
    {extra}
    {wm_block}
    {rule}
    {tagline}
    {stamp}
    {sweep}
  </g>
  {overlays}
  {flash_rect}
</svg>
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["online", "blueprint", "both"], default="both")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--uptime", type=int, default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--featured", default="")
    a = ap.parse_args()
    today = datetime.date.today()
    seed = a.seed if a.seed is not None else today.toordinal()
    uptime = a.uptime if a.uptime is not None else (today - START).days
    date = a.date or today.strftime("%Y.%m.%d")
    modes = ["online", "blueprint"] if a.mode == "both" else [a.mode]
    for m in modes:
        svg = build(m, seed, uptime, date, a.featured)
        path = f"assets/hero-{m}.svg"
        open(path, "w", encoding="utf-8").write(svg)
        print(f"wrote {path} ({len(svg)} bytes)  seed={seed} uptime={uptime} date={date}")

if __name__ == "__main__":
    main()
