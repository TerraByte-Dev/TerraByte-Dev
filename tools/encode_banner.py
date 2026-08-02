"""
encode_banner.py — TerraByteGlobeLoop

Encodes composited banner frames to an animated WebP using Pillow only.

Deliberately not ffmpeg: this runs in GitHub Actions as part of `regen-hero.yml`,
and Pillow is already required for the composite. Measured on the real frames,
PIL q92 lands at 3,997 KB vs ffmpeg's 4,094 KB — the same file for one fewer
dependency.

Quality notes, all measured on this content:
  * q92 is the floor. The banner is a saturated green graphic on pure black, and
    lossy WebP rings around high-contrast edges. Below ~q90 that ringing reads as
    grey blocks in the black field — the exact "low bitrate" look this project
    had to fix once already.
  * NEVER add film grain before this step. Grain turns every pure-black pixel
    into noise: it quadrupled the lossless size and gave the lossy encoder
    something to smear. The frames must come in with a genuinely flat black.

Usage
  python encode_banner.py --in <frames dir> --out hero-globe.webp [--fps 25] [--quality 92]
"""

import argparse
import glob
import os

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--quality", type=int, default=92)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.src, "*.png")))
    if not files:
        raise SystemExit(f"no frames in {a.src}")
    ims = [Image.open(f).convert("RGB") for f in files]

    # 25 fps: GIF delays are centisecond-quantised and WebP/APNG are exact at 40 ms,
    # so 25 is the one rate that is clean everywhere. Keep it even though this is WebP.
    ims[0].save(a.out, save_all=True, append_images=ims[1:],
                quality=a.quality, method=6, minimize_size=True,
                duration=int(round(1000 / a.fps)), loop=0)

    mb = os.path.getsize(a.out) / 1024 / 1024
    print(f"encoded {len(ims)} frames @ {a.fps} fps q{a.quality} -> {a.out}  ({mb:.2f} MB)")


if __name__ == "__main__":
    main()
