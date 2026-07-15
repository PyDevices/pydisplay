#!/usr/bin/env python3
"""
Generate a small set of color RGB565 (BMP565) status icons for pdwidgets.

Material Design icons are monochrome black glyphs on transparency. This tool
fetches a few individual PNGs from ``google/material-design-icons`` (via the
GitHub Contents API — no clone), colorizes each glyph with a chosen accent, and
writes a BMP565 file into ``src/pdwidgets/icons/`` in a local pdwidgets
checkout. Non-glyph pixels are set to a magenta chroma key so
``pdwidgets.Icon(chroma=CHROMA_565)`` can render them with a transparent
background. No PNG is shipped or decoded at runtime.

Usage::

    .venv/bin/python scripts/assets_make_color_icons.py
    .venv/bin/python scripts/assets_make_color_icons.py --pdwidgets-root ../pdwidgets

Requires: Pillow (dev dependency) and network access. This is a build-time
authoring tool; the generated .bmp assets are committed in the pdwidgets repo.
"""

import argparse
import io
import os
from pathlib import Path
import sys
import urllib.request

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src" / "lib"))

from PIL import Image  # noqa: E402

import graphics  # noqa: E402

# Magenta chroma key (non-swapped RGB565): (255, 0, 255).
CHROMA_RGB = (255, 0, 255)

# (github category, icon name, size dp, accent RGB, output basename)
ICONS = [
    ("device", "battery_full", 24, (94, 158, 110), "battery_full_color"),
    ("device", "bluetooth", 24, (74, 144, 226), "bluetooth_color"),
    ("social", "notifications", 24, (230, 178, 76), "notifications_color"),
]

API = "https://api.github.com/repos/google/material-design-icons/contents/png/{cat}/{name}/materialicons/{dp}dp/1x"


def resolve_pdwidgets_root(explicit: str | None) -> Path:
    """Return a local checkout of https://github.com/PyDevices/pdwidgets."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_root = os.environ.get("PDWIDGETS_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        (
            _ROOT.parent / "pdwidgets",
            Path("/agent/repos/pdwidgets"),
            Path.home() / "gh" / "pydevices" / "pdwidgets",
        )
    )
    for root in candidates:
        if (root / "src" / "pdwidgets").is_dir():
            return root.resolve()
    tried = ", ".join(str(p) for p in candidates)
    raise SystemExit(
        "pdwidgets checkout not found. Clone https://github.com/PyDevices/pdwidgets "
        f"or pass --pdwidgets-root. Tried: {tried}"
    )


def color565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def fetch_png(cat, name, dp):
    url = API.format(cat=cat, name=name, dp=dp)
    req = urllib.request.Request(url, headers={"User-Agent": "pdwidgets-icon-tool"})
    import json

    with urllib.request.urlopen(req, timeout=30) as resp:
        listing = json.load(resp)
    # Prefer the baseline black PNG.
    entry = next((e for e in listing if e["name"].endswith(".png")), None)
    if entry is None:
        raise RuntimeError(f"no PNG found for {cat}/{name}")
    dl = entry["download_url"]
    dreq = urllib.request.Request(dl, headers={"User-Agent": "pdwidgets-icon-tool"})
    with urllib.request.urlopen(dreq, timeout=30) as resp:
        return resp.read()


def convert(png_bytes, accent):
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    w, h = img.size
    px = img.load()
    chroma = color565(*CHROMA_RGB)
    accent565 = color565(*accent)
    fb = graphics.FrameBuffer(bytearray(w * h * 2), w, h, graphics.RGB565)
    for y in range(h):
        for x in range(w):
            _, _, _, a = px[x, y]
            fb.pixel(x, y, accent565 if a >= 128 else chroma)
    return fb, w, h


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdwidgets-root",
        default=None,
        help="Local checkout of PyDevices/pdwidgets (default: PDWIDGETS_ROOT, ../pdwidgets, …)",
    )
    args = parser.parse_args()

    icon_dir = resolve_pdwidgets_root(args.pdwidgets_root) / "src" / "pdwidgets" / "icons"

    print(f"chroma RGB565 = 0x{color565(*CHROMA_RGB):04X}")
    for cat, name, dp, accent, base in ICONS:
        print(f"fetching {cat}/{name} {dp}dp ...", end=" ", flush=True)
        png = fetch_png(cat, name, dp)
        fb, w, h = convert(png, accent)
        out = icon_dir / f"{base}_{dp}dp.bmp"
        out.parent.mkdir(parents=True, exist_ok=True)
        graphics.save_image(fb, str(out))
        print(f"wrote {out} ({w}x{h})")


if __name__ == "__main__":
    main()
