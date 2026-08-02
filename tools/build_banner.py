"""
build_banner.py — TerraByteGlobeLoop

Composites the 3D globe loop into the profile README's hero banner, and drives the
CRT sweep band down the frame.

Why composite rather than rebuild the banner in Blender: the hero
(`assets/hero-online.svg`) is hand-authored — a vectorised VT323 wordmark, a
spot-masked grid, a starfield, bloom filters, corner telemetry. Reproducing that
in Blender would lose fidelity for no gain. So the SVG stays the plate; only the
flat globe is swapped for the real one.

Geometry is taken from the SVG, not guessed: the flat mark is
`<circle cx="305" cy="210" r="152">` inside `<g class="screen">`, wrapped at prep
time in `<g class="flatglobe">` so it alone can be hidden. The 3D globe is scaled
so its rim radius lands on that same 152, at that same centre.

The sweep reproduces the SVG's own `.sweep` rect + `sweepY` keyframes: a 26 px
band with a 0 -> 0.5 -> 0 `#02EEAA` gradient, travelling y = -30 -> 420.

Loop maths: the globe loop is 36 frames. The banner runs N = 36 * CYCLES frames
so the globe's own loop still closes; the sweep completes exactly one pass over
the whole N. Both are therefore seamless together.

Usage
  python build_banner.py --plate plate_2x.png --glitch plate_glitch_2x.png \
      --globe <globe frames dir> --out <dir> [--cycles 2] [--width 1280]
"""

import argparse
import os

import numpy as np
from PIL import Image

# ── geometry, read off hero-online.svg (viewBox 0 0 1280 420) ────────────────
SVG_W, SVG_H = 1280.0, 420.0
GLOBE_CX, GLOBE_CY, GLOBE_R = 305.0, 210.0, 152.0
FRAMING = 1.22           # build_globe.py CFG: half-frame-height in rim radii
SWEEP_H = 26.0
SWEEP_FROM, SWEEP_TO = -30.0, 420.0
SWEEP_PEAK = 0.9         # sweepY holds opacity .9 between 8% and 92%
PHOSPHOR = (0x02, 0xEE, 0xAA)


def to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def to_srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def load_linear(path, rgba=False):
    im = Image.open(path).convert("RGBA" if rgba else "RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0
    if rgba:
        return to_linear(a[..., :3]), a[..., 3:]
    return to_linear(a)


def resize_lin(rgb, alpha, size):
    """Premultiplied linear-light resize, per channel as mode 'F'.

    PIL's RGBA is 8-bit per channel, so a uint16 buffer handed to fromarray with
    mode='RGBA' silently produces garbage; and resampling in sRGB darkens the glow
    edges that are most of this image.
    """
    ch = [rgb[..., i] * alpha[..., 0] for i in range(3)] + [alpha[..., 0]]
    out = [np.asarray(Image.fromarray(c, mode="F").resize(size, Image.LANCZOS),
                      dtype=np.float32) for c in ch]
    return np.dstack(out[:3]), np.clip(out[3], 0, 1)[..., None]   # stays premultiplied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plate", required=True)
    ap.add_argument("--glitch", default=None)
    ap.add_argument("--globe", required=True, help="dir of 1080^2 RGBA globe frames")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cycles", type=int, default=2, help="globe loops per banner loop")
    ap.add_argument("--width", type=int, default=1280, help="delivered width")
    ap.add_argument("--scanline", type=float, default=0.0,
                    help="extra scanlines; the plate already carries the SVG's own")
    ap.add_argument("--grain", type=float, default=0.004)
    ap.add_argument("--glitch-frames", type=int, default=2)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    plate = load_linear(a.plate)                       # (H, W, 3) linear
    PH, PW = plate.shape[:2]
    ss = PW / SVG_W                                    # plate supersample factor
    glitch = load_linear(a.glitch) if a.glitch else None

    # --globe is either a directory of RGBA render frames, or a PACK: a single
    # lossless animated WebP holding the globe already PREMULTIPLIED onto black
    # with no alpha channel. The pack exists so CI can rebuild the banner daily
    # without running Blender - it is ~14 MB and never changes, so it lives as a
    # release asset rather than in the repo.
    pack = a.globe.lower().endswith(".webp")
    if pack:
        from PIL import ImageSequence
        src_frames = [f.convert("RGBA").copy()
                      for f in ImageSequence.Iterator(Image.open(a.globe))]
        G = len(src_frames)
        names = [f"pack[{i}]" for i in range(G)]
    else:
        names = sorted(f for f in os.listdir(a.globe) if f.lower().endswith(".png"))
        G = len(names)
    N = G * a.cycles
    print(f"plate {PW}x{PH} (ss={ss:g})  globe {G} frames  banner {N} frames "
          f"-> {a.width}x{int(a.width*SVG_H/SVG_W)}")

    # the globe frame is FRAMING rim-radii tall, so match rim radius to GLOBE_R
    box = int(round(GLOBE_R * FRAMING * 2 * ss))
    x0 = int(round(GLOBE_CX * ss - box / 2))
    y0 = int(round(GLOBE_CY * ss - box / 2))
    print(f"  globe box {box}px at ({x0},{y0})")

    # pre-scale the globe frames once
    globes = []
    if pack:
        # The pack stores STRAIGHT (non-premultiplied) sRGB RGBA, already resized
        # to `box` by make_globe_pack.py using the same linear-premultiplied
        # resize the frames path uses. Decoding mirrors that path exactly:
        # to_linear, then premultiply.
        #
        # libwebp discards RGB wherever alpha == 0 (that is what `exact` is meant
        # to prevent; PIL does not reliably pass it through for animations).
        # Harmless here - those pixels are multiplied by alpha = 0 - but the
        # multiply makes it explicit rather than relying on it.
        for im in src_frames:
            if im.size != (box, box):
                im = im.resize((box, box), Image.LANCZOS)
            v = np.asarray(im, dtype=np.float32) / 255.0
            al = v[..., 3:]
            globes.append((to_linear(v[..., :3]) * al, al))
    else:
        for n in names:
            rgb, al = load_linear(os.path.join(a.globe, n), rgba=True)
            globes.append(resize_lin(rgb, al, (box, box)))

    # sweep band profile, in plate pixels
    band = int(round(SWEEP_H * ss))
    prof = np.sin(np.linspace(0, np.pi, band, dtype=np.float32)) * 0.5   # 0 -> .5 -> 0
    phos_srgb = np.array(PHOSPHOR, dtype=np.float32) / 255.0

    rng = np.random.default_rng(20260802)
    outw = a.width
    outh = int(round(outw * SVG_H / SVG_W))

    for f in range(N):
        base = plate
        if glitch is not None and f >= N - a.glitch_frames:
            base = glitch                       # their .wm glitch beat, once per loop
        img = base.copy()

        # ── globe, added (both are emissive on black; additive keeps the plate's
        #    faint grid visible through the cage instead of punching a hole)
        g_rgb, g_a = globes[f % G]
        sub = img[y0:y0 + box, x0:x0 + box]
        img[y0:y0 + box, x0:x0 + box] = (sub + g_rgb) if g_a is None else (sub * (1.0 - g_a) + g_rgb)

        srgb = to_srgb(img)

        # ── sweep band, composited in sRGB
        # SVG compositing is sRGB-space by default, so adding the band in LINEAR
        # light overshoots badly: 0.45 linear over near-black reads as ~0.70 sRGB
        # instead of the 0.45 the source design specifies. Add it here, after the
        # transfer curve, and it matches the SVG exactly.
        t = f / N
        y = SWEEP_FROM + (SWEEP_TO - SWEEP_FROM) * t
        fade = min(1.0, t / 0.08) * min(1.0, (1.0 - t) / 0.08)
        yy = int(round(y * ss))
        lo, hi = max(0, yy), min(PH, yy + band)
        if hi > lo:
            seg = prof[lo - yy: hi - yy][:, None, None] * SWEEP_PEAK * fade
            srgb = srgb.copy()
            srgb[lo:hi] = np.clip(srgb[lo:hi] + seg * phos_srgb[None, None, :], 0, 1)

        # ── downscale (supersampled AA on both type and cage)
        arr = np.clip(np.dstack([
            np.asarray(Image.fromarray(srgb[..., i], mode="F")
                       .resize((outw, outh), Image.LANCZOS), dtype=np.float32)
            for i in range(3)]), 0.0, 1.0)

        if a.scanline > 0:
            rows = np.arange(outh)
            arr *= (1.0 - a.scanline * (rows % 2 == 1)).astype(np.float32)[:, None, None]
        if a.grain > 0:
            arr = np.clip(arr + rng.normal(0, a.grain, (outh, outw, 1)).astype(np.float32), 0, 1)

        Image.fromarray((arr * 255 + 0.5).astype(np.uint8), "RGB").save(
            os.path.join(a.out, f"c_{f + 1:04d}.png"))

    print("wrote", N, "frames ->", a.out)


if __name__ == "__main__":
    main()
