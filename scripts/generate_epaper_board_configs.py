#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Generate paired CP/MP e-paper board configs from a driver table."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "board_configs" / "epaperdisplay"

MP_BUS = """display_bus = SPIBus(
    id=0,
    baudrate=4_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    dc=9,
    cs=10,
    reset=6,
)
"""

CP_BUS = """display_bus = FourWire(
    board.SPI(),
    command=board.D9,
    chip_select=board.D10,
    reset=board.D6,
    baudrate=4_000_000,
)
"""

CONFIGS = [
    {
        "slug": "ssd1681_154_tricolor",
        "module": "ssd1681",
        "title": "SSD1681 1.54\" tri-color breakout",
        "width": 200,
        "height": 200,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "ssd1683_213_featherwing",
        "module": "ssd1683",
        "title": "SSD1683 2.13\" E-Ink FeatherWing",
        "width": 250,
        "height": 122,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "ssd1677_583_mono",
        "module": "ssd1677",
        "title": "SSD1677 5.83\" monochrome bare display",
        "width": 648,
        "height": 480,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "ssd1608_154_mono",
        "module": "ssd1608",
        "title": "SSD1608 1.54\" monochrome breakout",
        "width": 200,
        "height": 200,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "il0373_213_tricolor",
        "module": "il0373",
        "title": "IL0373 2.13\" tri-color FeatherWing",
        "width": 250,
        "height": 122,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "il0398_42_mono",
        "module": "il0398",
        "title": "IL0398 4.2\" monochrome E-Ink",
        "width": 400,
        "height": 300,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "il91874_27_tricolor",
        "module": "il91874",
        "title": "IL91874 2.7\" tri-color shield",
        "width": 264,
        "height": 176,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "uc8179_583_mono",
        "module": "uc8179",
        "title": "UC8179 5.83\" monochrome bare display",
        "width": 648,
        "height": 480,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "uc8253_37_mono",
        "module": "uc8253",
        "title": "UC8253 3.7\" monochrome bare display",
        "width": 416,
        "height": 240,
        "color_depth": 1,
        "chip_kwargs": {},
    },
    {
        "slug": "ek79686_27_tricolor",
        "module": "ek79686",
        "title": "EK79686 2.7\" tri-color breakout",
        "width": 176,
        "height": 264,
        "color_depth": 2,
        "chip_kwargs": {"highlight_color": True},
    },
    {
        "slug": "jd79661_213_4gray",
        "module": "jd79661",
        "title": "JD79661 2.13\" 4-gray E-Ink",
        "width": 128,
        "height": 250,
        "color_depth": 2,
        "chip_kwargs": {},
    },
    {
        "slug": "jd79667_391_4gray",
        "module": "jd79667",
        "title": "JD79667 3.91\" 4-gray E-Ink",
        "width": 200,
        "height": 384,
        "color_depth": 2,
        "chip_kwargs": {},
    },
    {
        "slug": "spd1656_154_acep",
        "module": "spd1656",
        "title": "SPD1656 1.54\" 6-color ACeP",
        "width": 152,
        "height": 152,
        "color_depth": 4,
        "chip_kwargs": {},
    },
]


def _chip_args(cfg: dict) -> str:
    lines = [
        f"    width={cfg['width']},",
        f"    height={cfg['height']},",
        "    busy_pin=Pin(7, Pin.IN),",
        "    rotation=0,",
    ]
    for key, value in cfg.get("chip_kwargs", {}).items():
        if isinstance(value, bool):
            lines.append(f"    {key}={value},")
        elif isinstance(value, str):
            lines.append(f"    {key}={value!r},")
        else:
            lines.append(f"    {key}={value},")
    return "\n".join(lines)


def _chip_args_cp(cfg: dict) -> str:
    lines = [
        f"    width={cfg['width']},",
        f"    height={cfg['height']},",
        "    busy_pin=board.D7,",
        "    rotation=0,",
    ]
    for key, value in cfg.get("chip_kwargs", {}).items():
        if isinstance(value, bool):
            lines.append(f"    {key}={value},")
        elif isinstance(value, str):
            lines.append(f"    {key}={value!r},")
        else:
            lines.append(f"    {key}={value},")
    return "\n".join(lines)


def mp_board_config(cfg: dict) -> str:
    mod = cfg["module"]
    cls = mod if mod[0].isupper() else mod.upper()
    if mod == "ssd1681":
        cls = "SSD1681"
    elif mod == "ssd1683":
        cls = "SSD1683"
    elif mod == "ssd1677":
        cls = "SSD1677"
    elif mod == "ssd1608":
        cls = "SSD1608"
    elif mod == "il0373":
        cls = "IL0373"
    elif mod == "il0398":
        cls = "IL0398"
    elif mod == "il91874":
        cls = "IL91874"
    elif mod == "uc8179":
        cls = "UC8179"
    elif mod == "uc8253":
        cls = "UC8253"
    elif mod == "ek79686":
        cls = "EK79686"
    elif mod == "jd79661":
        cls = "JD79661"
    elif mod == "jd79667":
        cls = "JD79667"
    elif mod == "spd1656":
        cls = "SPD1656"
    return f'''"""{cfg["title"]} — MicroPython (Feather SPI pinout)"""

from machine import Pin, SPI
from {mod} import {cls}
from spibus import SPIBus

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

{MP_BUS}
_epaper = {cls}(
    display_bus,
{_chip_args(cfg)}
)

display_drv = EPaperDisplay(_epaper, width={cfg["width"]}, height={cfg["height"]}, color_depth={cfg["color_depth"]})

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
'''


def cp_board_config(cfg: dict) -> str:
    mod = cfg["module"]
    mapping = {
        "ssd1681": "SSD1681",
        "ssd1683": "SSD1683",
        "ssd1677": "SSD1677",
        "ssd1608": "SSD1608",
        "il0373": "IL0373",
        "il0398": "IL0398",
        "il91874": "IL91874",
        "uc8179": "UC8179",
        "uc8253": "UC8253",
        "ek79686": "EK79686",
        "jd79661": "JD79661",
        "jd79667": "JD79667",
        "spd1656": "SPD1656",
    }
    cls = mapping[mod]
    return f'''"""Adafruit {cfg["title"]} — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from {mod} import {cls}

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

{CP_BUS}
_epaper = {cls}(
    display_bus,
{_chip_args_cp(cfg)}
)

display_drv = EPaperDisplay(_epaper, width={cfg["width"]}, height={cfg["height"]}, color_depth={cfg["color_depth"]})

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
'''


def package_json(slug: str, module: str, *, cp: bool) -> dict:
    path = f"board_configs/epaperdisplay/{slug}/board_config.py"
    urls = [[ "board_config.py", f"github:PyDevices/pydisplay/{path}" ], [f"{module}.py", f"github:PyDevices/pydisplay/drivers/display/{module}.py"]]
    deps = [
        ["github:PyDevices/pydisplay/packages/displaysys.json", "main"],
        ["github:PyDevices/pydisplay/packages/epaperdisplay.json", "main"],
    ]
    if not cp:
        deps.extend(
            [
                ["github:PyDevices/pydisplay/packages/epaper_chip.json", "main"],
                ["github:PyDevices/pydisplay/packages/spibus.json", "main"],
            ]
        )
    return {"urls": urls, "deps": deps, "version": "0.1"}


def main() -> None:
    for cfg in CONFIGS:
        slug = cfg["slug"]
        mod = cfg["module"]
        mp_dir = OUT / slug
        cp_dir = OUT / f"cp_{slug}"
        mp_dir.mkdir(parents=True, exist_ok=True)
        cp_dir.mkdir(parents=True, exist_ok=True)
        (mp_dir / "board_config.py").write_text(mp_board_config(cfg))
        (cp_dir / "board_config.py").write_text(cp_board_config(cfg))
        (mp_dir / "package.json").write_text(json.dumps(package_json(slug, mod, cp=False), indent=2) + "\n")
        (cp_dir / "package.json").write_text(json.dumps(package_json(f"cp_{slug}", mod, cp=True), indent=2) + "\n")
        print("wrote", slug, "and cp_" + slug)


if __name__ == "__main__":
    main()
