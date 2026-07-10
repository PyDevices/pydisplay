#!/usr/bin/env python3
"""
Generate/complete the curated icon set used by `pdwidgets.icon_theme`
(`src/add_ons/pdwidgets/icons/`) from a local checkout of
https://github.com/google/material-design-icons (png/ tree), at
``~/material-design-icons`` by default.

Unlike `assets_convert_md_png_to_pbm.py` (which bulk-converts the *entire*
material-design-icons PNG tree into `assets/icons/` using the icons' own
upstream file names), this script produces the small, curated, renamed set
that `pdwidgets._themes.IconTheme` actually expects, at every `ICON_SIZE`
(18/24/36/48dp), using the "materialicons" (baseline/filled) family.

Run from the repo root:

    .venv/bin/python scripts/assets_generate_pdwidgets_icons.py

By default this only fills in *missing* files, leaving any existing curated
icon untouched. Pass --force to regenerate everything.
"""

import argparse
from pathlib import Path
import sys

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / "lib"))

from graphics import MONO_HLSB, FrameBuffer  # noqa: E402

SIZES = (18, 24, 36, 48)
THRESHOLD = 160
FAMILY = "materialicons"  # baseline/filled style, matches the existing curated set

DEST = REPO_ROOT / "src" / "add_ons" / "pdwidgets" / "icons"

# pdwidgets filename prefix -> (material-design-icons category, short_name)
# Filename on disk is f"{prefix}{size}dp.pbm" (see IconTheme._icon()).
ICON_MAP = {
    # Existing IconTheme methods (src/add_ons/pdwidgets/_themes.py)
    "home_filled_": ("action", "home"),
    "keyboard_arrow_up_": ("hardware", "keyboard_arrow_up"),
    "keyboard_arrow_down_": ("hardware", "keyboard_arrow_down"),
    "keyboard_arrow_left_": ("hardware", "keyboard_arrow_left"),
    "keyboard_arrow_right_": ("hardware", "keyboard_arrow_right"),
    "check_box_": ("toggle", "check_box"),
    "check_box_outline_blank_": ("toggle", "check_box_outline_blank"),
    "radio_button_checked_": ("toggle", "radio_button_checked"),
    "radio_button_unchecked_": ("toggle", "radio_button_unchecked"),
    "toggle_on_": ("toggle", "toggle_on"),
    "toggle_off_": ("toggle", "toggle_off"),
    # New icons for pdwidgets rework widgets (Dialog/MessageBox, Dropdown, NumberStepper, ...)
    "close_": ("navigation", "close"),
    "add_": ("content", "add"),
    "remove_": ("content", "remove"),
    "info_": ("action", "info"),
    "warning_": ("alert", "warning"),
    "error_": ("alert", "error"),
    "expand_more_": ("navigation", "expand_more"),
    "menu_": ("navigation", "menu"),
}


def find_source_png(md_root: Path, category: str, short_name: str, size: int) -> Path:
    in_dir = md_root / "png" / category / short_name / FAMILY / f"{size}dp" / "1x"
    candidates = sorted(in_dir.glob("*.png"))
    if not candidates:
        raise FileNotFoundError(f"No PNG found in {in_dir}")
    return candidates[0]


def png_to_pbm(src: Path, dest_file: Path, threshold: int = THRESHOLD) -> None:
    img = Image.open(src).convert("LA")
    width, height = img.size
    alpha = img.getchannel("A")
    lum = img.getchannel("L")

    bytes_per_row = (width + 7) // 8
    buffer = memoryview(bytearray(bytes_per_row * height))
    fbuf = FrameBuffer(buffer, width, height, MONO_HLSB)

    for y in range(height):
        for x in range(width):
            # Foreground where the pixel is opaque and dark (matches the
            # bulk-conversion threshold convention in assets_convert_md_png_to_pbm.py).
            opaque = alpha.getpixel((x, y)) > threshold
            dark = lum.getpixel((x, y)) < 255 - threshold
            fbuf.pixel(x, y, 1 if (opaque and dark) else 0)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    fbuf.save(str(dest_file))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--material-icons-root",
        default=str(Path.home() / "material-design-icons"),
        help="Local checkout of google/material-design-icons (default: ~/material-design-icons)",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate files that already exist")
    args = parser.parse_args()

    md_root = Path(args.material_icons_root)
    if not (md_root / "png").is_dir():
        print(f"material-design-icons png/ tree not found under {md_root}", file=sys.stderr)
        return 1

    generated = 0
    skipped = 0
    for prefix, (category, short_name) in sorted(ICON_MAP.items()):
        for size in SIZES:
            dest_file = DEST / f"{prefix}{size}dp.pbm"
            if dest_file.exists() and not args.force:
                skipped += 1
                continue
            try:
                src = find_source_png(md_root, category, short_name, size)
            except FileNotFoundError as e:
                print(f"  skip {dest_file.name}: {e}", file=sys.stderr)
                continue
            png_to_pbm(src, dest_file)
            print(f"  wrote {dest_file.relative_to(REPO_ROOT)}")
            generated += 1

    print(f"\nGenerated {generated} icon(s), skipped {skipped} existing file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
