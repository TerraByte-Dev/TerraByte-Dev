# Credits — TERRABYTE.SYS profile

This profile uses the README format in a few ways most don't:

- **Two realities** — `<picture>` + prefers-color-scheme swaps the whole hero by viewer theme.
  Dark = the neon system (`hero-online.svg`); light = a technical blueprint of the same machine
  (`hero-blueprint.svg`).
- **Self-rewriting** — `.github/workflows/regen-hero.yml` re-runs `gen_hero.py` daily, so the
  generative starfield reseeds, the DAY counter ticks, and the blueprint REV date updates. The
  profile is never the same twice.
- **Hero geometry** — one rotating phosphor wireframe globe (the TerraByte mark) with a glowing
  trident-T core, orbiting satellite, CRT scan-sweep + glitch (online) / dimensioned drafting
  callouts (blueprint). Pure animated SVG (SMIL + CSS); honors prefers-reduced-motion.
- **Wordmark** — [VT323](https://fonts.google.com/specimen/VT323) (SIL OFL 1.1) vectorized to SVG
  `<path>` data (`assets/wordmarks.json`) for sandbox-safe rendering. No font binary redistributed.
- **Mint** `#02EEAA`, sampled from the official TerraByte logo. UI/mono: IBM Plex Mono (OFL).
