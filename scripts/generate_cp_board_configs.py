#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Brad Barnett
# SPDX-License-Identifier: MIT
"""Generate CircuitPython board_config siblings from MicroPython configs."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD_ROOT = ROOT / "board_configs" / "busdisplay"

# Map MP driver imports to CP patterns (display chip module stays same name)
CP_HEADER = '''"""CircuitPython variant — see paired MicroPython config in sibling directory."""

import board
from displayio import release_displays
'''

SPI_CP_TEMPLATE = CP_HEADER + '''from fourwire import FourWire
from {display_module} import {display_class}
{touch_imports}
import eventsys

release_displays()

{display_bus_setup}

{display_drv_setup}
{touch_setup}
broker = eventsys.Broker()
{touch_broker}
broker.register_quit_cleanup(display_drv)
'''

# Per-config overrides: (display_module, display_class, bus_setup, display_kwargs, touch)
SPI_OVERRIDES: dict[str, dict] = {
    "ili9341_eyespi_qtpy_esp32s3": {
        "bus": """display_bus = FourWire(
    board.SPI(),
    command=board.TX,
    chip_select=board.RX,
    baudrate=40_000_000,
)""",
        "display": """display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
)""",
        "touch": "focaltouch",
        "touch_rotation": "(6, 3, 0, 5)",
    },
}


def parse_mp_spi_bus(text: str) -> str | None:
    """Build CircuitPython FourWire setup from MicroPython SPIBus pin numbers."""
    dc = re.search(r"\bdc=(\d+)", text)
    cs = re.search(r"\bcs=(\d+)", text)
    if not dc or not cs:
        return None
    reset = re.search(r"\breset=(\d+)", text)
    baud = re.search(r"baudrate=([\d_]+)", text)
    baudrate = baud.group(1) if baud else "40_000_000"
    lines = [
        "display_bus = FourWire(",
        "    board.SPI(),",
        f"    command=board.D{dc.group(1)},",
        f"    chip_select=board.D{cs.group(1)},",
    ]
    if reset:
        lines.append(f"    reset=board.D{reset.group(1)},")
    lines.append(f"    baudrate={baudrate},")
    lines.append(")")
    return "\n".join(lines)


def parse_mp_display_drv(text: str, display_class: str) -> str | None:
    """Extract display_drv = Class(...) block from MP config when present."""
    m = re.search(
        rf"(display_drv = {re.escape(display_class)}\([\s\S]*?\n\))",
        text,
    )
    return m.group(1) if m else None


def parse_mp_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    info: dict = {}
    m = re.search(r"from (\w+) import (\w+)", text)
    if m and m.group(1) not in ("machine", "spibus", "i80bus", "ft6x36", "xpt2046"):
        info["display_module"] = m.group(1)
        info["display_class"] = m.group(2)
    if "SPIBus" in text:
        info["bus_type"] = "spi"
    elif "I80Bus" in text:
        info["bus_type"] = "i80"
    if "FT6x36" in text:
        info["touch"] = "ft6x36"
    elif "XPT2046" in text or "xpt2046" in text:
        info["touch"] = "xpt2046"
    elif "broker = None" in text:
        info["touch"] = None
    return info


def focaltouch_block(rotation: str = "(0, 0, 0, 0)") -> str:
    return f'''
from adafruit_focaltouch import Adafruit_FocalTouch

i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = {rotation}

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)
'''


def ft6x36_cp_block(rotation: str = "(0, 0, 0, 0)") -> str:
    return f'''
from adafruit_focaltouch import Adafruit_FocalTouch

i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = {rotation}

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)
'''


def generate_cp_package(mp_dir: Path) -> None:
    slug = mp_dir.name
    if slug.startswith("cp_") or slug.startswith("wokwi"):
        return
    cp_dir = mp_dir.parent / f"cp_{slug}"
    if cp_dir.exists():
        return

    mp_config = mp_dir / "board_config.py"
    if not mp_config.exists():
        return

    mp_pkg = mp_dir / "package.json"
    if not mp_pkg.exists():
        return

    override = SPI_OVERRIDES.get(slug, {})
    parsed = parse_mp_config(mp_config)
    mp_text = mp_config.read_text(encoding="utf-8")

    # Skip I80 for now unless override exists — manual configs preferred
    if parsed.get("bus_type") == "i80" and slug not in SPI_OVERRIDES:
        cp_dir.mkdir(parents=True, exist_ok=True)
        readme = cp_dir / "README.md"
        readme.write_text(
            f"# cp_{slug}\n\n"
            "CircuitPython config pending — use `paralleldisplaybus.ParallelBus` "
            f"with pins from the MicroPython config in `{slug}/`.\n",
            encoding="utf-8",
        )
        return

    display_module = override.get("display_module") or parsed.get("display_module", "st7789")
    display_class = override.get("display_class") or parsed.get("display_class", "ST7789")

    bus_setup = override.get("bus") or parse_mp_spi_bus(mp_text)
    if bus_setup is None:
        bus_setup = """display_bus = FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
    baudrate=40_000_000,
)"""
    display_setup = override.get("display") or parse_mp_display_drv(
        mp_text, display_class
    )
    if display_setup is None:
        display_setup = f"""display_drv = {display_class}(
    display_bus,
    width=240,
    height=320,
    rotation=0,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
)"""

    touch = override.get("touch", parsed.get("touch"))
    touch_setup = ""
    touch_broker = ""
    if touch in ("ft6x36", "focaltouch"):
        rot = override.get("touch_rotation", "(0, 0, 0, 0)")
        touch_setup = (
            "from adafruit_focaltouch import Adafruit_FocalTouch\n\n"
            "i2c = board.I2C()\n"
            "touch_drv = Adafruit_FocalTouch(i2c)\n\n\n"
            "def touch_read_func():\n"
            "    touches = touch_drv.touches\n"
            "    if len(touches):\n"
            "        return touches[0][\"x\"], touches[0][\"y\"]\n"
            "    return None\n\n\n"
            f"touch_rotation_table = {rot}\n"
        )
        touch_broker = (
            "touch_dev = broker.create(\n"
            "    type=eventsys.TOUCH,\n"
            "    read=touch_read_func,\n"
            "    data=display_drv,\n"
            "    data2=touch_rotation_table,\n"
            ")\n"
        )

    content = SPI_CP_TEMPLATE.format(
        display_module=display_module,
        display_class=display_class,
        touch_imports="",
        display_bus_setup=bus_setup,
        display_drv_setup=display_setup,
        touch_setup=touch_setup,
        touch_broker=touch_broker,
    )

    cp_dir.mkdir(parents=True, exist_ok=True)
    (cp_dir / "board_config.py").write_text(content, encoding="utf-8")

    pkg = json.loads(mp_pkg.read_text(encoding="utf-8"))
    urls = pkg.get("urls", [])
    new_urls = [
        ["board_config.py", f"github:PyDevices/pydisplay/board_configs/busdisplay/{mp_dir.parent.name}/cp_{slug}/board_config.py"]
    ]
    for url in urls:
        if url[0] != "board_config.py":
            new_urls.append(url)
    new_urls.append(
        [
            "adafruit_focaltouch.py",
            "github:PyDevices/pydisplay/drivers/touch/circuitpython/adafruit_focaltouch.py",
        ]
    )
    deps = pkg.get("deps", [])
    if not any("displaysys" in str(d) for d in deps):
        deps.append(["github:PyDevices/pydisplay/packages/displaysys.json", "main"])
    (cp_dir / "package.json").write_text(
        json.dumps({"urls": new_urls, "deps": deps, "version": "0.1"}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"created {cp_dir.relative_to(ROOT)}")


def main() -> None:
    for bus in ("spi", "i80"):
        bus_dir = BOARD_ROOT / bus
        if not bus_dir.is_dir():
            continue
        for mp_dir in sorted(bus_dir.iterdir()):
            if mp_dir.is_dir() and not mp_dir.name.startswith("cp_"):
                generate_cp_package(mp_dir)


if __name__ == "__main__":
    main()
