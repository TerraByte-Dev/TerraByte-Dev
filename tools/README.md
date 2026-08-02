# tools/ — hero banner rebuild

`regen-hero.yml` runs these daily, right after `gen_hero.py` redraws the SVGs, to
rebuild the **dark** hero `assets/hero-globe.webp`.

```
gen_hero.py  ──►  assets/hero-online.svg      (fresh starfield / DAY / stars)
                        │
   prep_plates.py  ─────┴──►  plate + glitch plate     (Playwright, 3x = 3840x1260,
                                                        flat globe hidden)
                        │
   build_banner.py ─────┴──►  72 composited frames     (3D globe + travelling sweep)
                        │        needs the globe pack, see below
   encode_banner.py ────┴──►  assets/hero-globe.webp   (1920x630, 25 fps, q92)
```

**The globe pack** is a release asset, not a repo file:
`gh release download globe-pack-v1 -p globe-pack-1113.webp`. It is 36 pre-rendered
Blender frames (1113px, lossless RGBA). The globe never changes, so it is baked
once; keeping it out of the repo means re-baking replaces the asset instead of
adding another ~17 MB to git history.

Regenerating the pack itself needs Blender and lives in the Blender workspace:
`Blender/02-Assets/TerraByteGlobeLoop` → `build_globe.py`, then `make_globe_pack.py`.

## Things that will bite you

- `prep_plates.py` anchors on `<circle cx="305" cy="210" r="178" fill="url(#halo)"/>`
  and `<g class="wm">` to find the flat globe. Those come from `gen_hero.py`'s
  `gcx, gcy, R = 305, 210, 152` constants — if you move the globe there, update the
  anchor or the step fails loudly (it raises rather than silently shipping the flat one).
- **Never add grain before encoding.** It turns pure black into noise, quadruples
  the size, and gives the encoder something to smear into visible blocks.
- q92 is the quality floor; below ~q90 the black field visibly blocks.
- The banner step is `continue-on-error: true` on purpose — a Playwright hiccup
  must not stop the daily SVG redraw from committing.
