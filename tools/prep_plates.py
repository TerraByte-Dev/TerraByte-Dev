"""
prep_plates.py — TerraByteGlobeLoop

Turns the profile README's hero SVG into the two raster PLATES that
`build_banner.py` composites the 3D globe into.

Two jobs, and both are fiddly enough to be worth a script:

1. HIDE ONLY THE FLAT GLOBE. The hero's `<g class="screen">` wraps the *entire*
   banner - globe, wordmark, tagline - so hiding `.screen` blanks the whole thing.
   The globe is an unclassed subtree inside it. This script wraps exactly that
   subtree (from the halo circle's sibling through to `<g class="wm">`) in
   `<g class="flatglobe">` so it alone can be hidden. The halo circle itself is
   deliberately left OUTSIDE the wrapper, so the SVG's own soft glow stays under
   the 3D globe.

2. FREEZE THE ANIMATIONS. The plate must be a still, so `*{animation:none}`. But
   the wordmark's RGB ghost layers (`.wm-r` / `.wm-c`) rest at opacity 0 only
   *because* their keyframes put them there - freezing animations reveals them at
   full strength. They have to be pinned to 0 explicitly.

Produces a normal plate and a glitch plate (the `.wm` kick + ghosts that their
`glitch`/`ghostR`/`ghostC` keyframes fire); `build_banner.py` swaps to the glitch
plate for the last couple of frames of the loop.

Requires Playwright (`pip install playwright && playwright install chromium`).
cairosvg is NOT a substitute here - it needs libcairo, and it would not run the
CSS anyway.

Usage
  python prep_plates.py --svg <hero-online.svg> --out <dir> [--scale 2]
"""

import argparse
import asyncio
import os

BASE_CSS = (
    "html,body{margin:0;padding:0;background:#000}"
    "svg{display:block}"
    ".flatglobe{display:none !important}"   # the 3D globe takes this slot
    ".sweep{display:none !important}"       # build_banner.py drives its own
    "*{animation:none !important}"          # freeze to the resting state
)
REST_CSS   = ".wm-r,.wm-c{opacity:0 !important}"
GLITCH_CSS = (".wm{transform:translate(-2px,0)}"
              ".wm-r{opacity:.45 !important}.wm-c{opacity:.4 !important}")

VIEW_W, VIEW_H = 1280, 420


def tag_flatglobe(svg_text):
    """Wrap the flat globe subtree so it can be hidden on its own."""
    halo = '<circle cx="305" cy="210" r="178" fill="url(#halo)"/>'
    a = svg_text.find(halo)
    if a < 0:
        raise SystemExit("halo circle not found - the hero SVG has changed; "
                         "re-check the globe subtree boundaries")
    a += len(halo)                       # keep the halo visible
    b = svg_text.find('<g class="wm"')
    if b < a:
        raise SystemExit('<g class="wm"> not found after the halo')
    return svg_text[:a] + '<g class="flatglobe">' + svg_text[a:b] + "</g>" + svg_text[b:]


async def shoot(svg_text, out, scale, extra_css):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": VIEW_W, "height": VIEW_H},
                                      device_scale_factor=scale)
        await page.set_content(f"<style>{BASE_CSS}{extra_css}</style>" + svg_text)
        await page.wait_for_timeout(300)
        # `animation:none` only stops CSS animations. The starfield twinkle is SMIL
        # (<animate> elements), which keeps running - so without this the plate
        # catches a random star state and is not reproducible. Only ~0.1% of pixels,
        # but a byte-identical rebuild is worth two lines.
        await page.evaluate("""() => {
            const s = document.querySelector('svg');
            if (s && s.pauseAnimations) { s.setCurrentTime(0); s.pauseAnimations(); }
        }""")
        await page.wait_for_timeout(80)
        await page.screenshot(path=out, clip={"x": 0, "y": 0, "width": VIEW_W, "height": VIEW_H})
        await browser.close()
    print(f"  {os.path.basename(out)}  {os.path.getsize(out)//1024} KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", required=True, help="the profile repo's assets/hero-online.svg")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=float, default=2.0,
                    help="supersample; build_banner.py downscales after compositing")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    svg = tag_flatglobe(open(a.svg, encoding="utf-8").read())
    with open(os.path.join(a.out, "hero_tagged.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg)

    print(f"plates at {int(VIEW_W*a.scale)}x{int(VIEW_H*a.scale)}:")
    asyncio.run(shoot(svg, os.path.join(a.out, "plate_2x.png"), a.scale, REST_CSS))
    asyncio.run(shoot(svg, os.path.join(a.out, "plate_glitch_2x.png"), a.scale, GLITCH_CSS))


if __name__ == "__main__":
    main()
