#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Generate paired CP/MP e-paper board configs.

Board definitions live in ``board_configs/manifests/epaperdisplay.toml``.
This script delegates to ``generate_board_configs.py`` for output; ``CONFIGS``
is retained for reference and one-off manifest bootstrap only.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "generate_board_configs.py"

# Retained for manifest bootstrap — edit epaperdisplay.toml, not this list.
CONFIGS = [
    {
        "slug": "ssd1681_154_tricolor",
        "module": "ssd1681",
        "title": 'SSD1681 1.54" tri-color breakout',
        "width": 200,
        "height": 200,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "ssd1683_213_featherwing",
        "module": "ssd1683",
        "title": 'SSD1683 2.13" E-Ink FeatherWing',
        "width": 250,
        "height": 122,
        "color_depth": 1,
    },
    {
        "slug": "ssd1677_583_mono",
        "module": "ssd1677",
        "title": 'SSD1677 5.83" monochrome bare display',
        "width": 648,
        "height": 480,
        "color_depth": 1,
    },
    {
        "slug": "ssd1608_154_mono",
        "module": "ssd1608",
        "title": 'SSD1608 1.54" monochrome breakout',
        "width": 200,
        "height": 200,
        "color_depth": 1,
    },
    {
        "slug": "il0373_213_tricolor",
        "module": "il0373",
        "title": 'IL0373 2.13" tri-color FeatherWing',
        "width": 250,
        "height": 122,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "il0398_42_mono",
        "module": "il0398",
        "title": 'IL0398 4.2" monochrome E-Ink',
        "width": 400,
        "height": 300,
        "color_depth": 1,
    },
    {
        "slug": "il91874_27_tricolor",
        "module": "il91874",
        "title": 'IL91874 2.7" tri-color shield',
        "width": 264,
        "height": 176,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "uc8179_583_mono",
        "module": "uc8179",
        "title": 'UC8179 5.83" monochrome bare display',
        "width": 648,
        "height": 480,
        "color_depth": 1,
    },
    {
        "slug": "uc8253_37_mono",
        "module": "uc8253",
        "title": 'UC8253 3.7" monochrome bare display',
        "width": 416,
        "height": 240,
        "color_depth": 1,
    },
    {
        "slug": "ek79686_27_tricolor",
        "module": "ek79686",
        "title": 'EK79686 2.7" tri-color breakout',
        "width": 176,
        "height": 264,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "jd79661_213_4gray",
        "module": "jd79661",
        "title": 'JD79661 2.13" 4-gray E-Ink',
        "width": 128,
        "height": 250,
        "color_depth": 2,
    },
    {
        "slug": "jd79667_391_4gray",
        "module": "jd79667",
        "title": 'JD79667 3.91" 4-gray E-Ink',
        "width": 200,
        "height": 384,
        "color_depth": 2,
    },
    {
        "slug": "spd1656_154_acep",
        "module": "spd1656",
        "title": 'SPD1656 1.54" 6-color ACeP',
        "width": 152,
        "height": 152,
        "color_depth": 4,
    },
]


def main() -> int:
    cmd = [sys.executable, str(GEN), "--kind", "epaper", *sys.argv[1:]]
    return subprocess.run(cmd, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
