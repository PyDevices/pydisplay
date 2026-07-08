#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Generate board_config.py and package.json from TOML manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = ROOT / "board_configs" / "manifests"
BOARD_ROOT = ROOT / "board_configs"
GITHUB = "github:PyDevices/pydisplay"

PACKAGE_URLS = {
    "displaysys": f"{GITHUB}/packages/displaysys.json",
    "epaperdisplay": f"{GITHUB}/packages/epaperdisplay.json",
    "epaper_chip": f"{GITHUB}/packages/epaper_chip.json",
    "spibus": f"{GITHUB}/packages/spibus.json",
    "i2cbus": f"{GITHUB}/packages/i2cbus.json",
    "i80bus": f"{GITHUB}/packages/i80bus.json",
}

CP_TOUCH_URLS = {
    "focaltouch": (
        "adafruit_focaltouch.py",
        f"{GITHUB}/drivers/touch/circuitpython/adafruit_focaltouch.py",
    ),
    "tt21100": (
        "adafruit_tt21100.py",
        f"{GITHUB}/drivers/touch/circuitpython/adafruit_tt21100.py",
    ),
}

EPAPER_CLASSES = {
    "ssd1681": "SSD1681",
    "ssd1683": "SSD1683",
    "ssd1677": "SSD1677",
    "ssd1680": "SSD1680",
    "ssd1675": "SSD1675",
    "ssd1608": "SSD1608",
    "il0373": "IL0373",
    "il0398": "IL0398",
    "il91874": "IL91874",
    "uc8179": "UC8179",
    "uc8253": "UC8253",
    "uc8151d": "UC8151D",
    "ek79686": "EK79686",
    "jd79661": "JD79661",
    "jd79667": "JD79667",
    "spd1656": "SPD1656",
    "acep7in": "ACeP7In",
}

EPAPER_NO_BUSY = frozenset({"acep7in"})

DEFAULT_MP_EPAPER_BUS = {
    "id": 0,
    "baudrate": 4_000_000,
    "sck": 18,
    "mosi": 19,
    "miso": -1,
    "dc": 9,
    "cs": 10,
    "reset": 6,
}

DEFAULT_CP_EPAPER_BUS = {
    "command": "board.D9",
    "chip_select": "board.D10",
    "reset": "board.D6",
    "baudrate": 4_000_000,
}

MP_EPAPER_BUS = """display_bus = SPIBus(
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

CP_EPAPER_BUS = """display_bus = FourWire(
    board.SPI(),
    command=board.D9,
    chip_select=board.D10,
    reset=board.D6,
    baudrate=4_000_000,
)
"""


def _py_literal(value) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) >= 1000:
            s = str(value)
            parts = []
            while s:
                parts.insert(0, s[-3:])
                s = s[:-3]
            return "_".join(parts)
        return repr(value)
    if isinstance(value, (list, tuple)):
        inner = ", ".join(_py_literal(v) for v in value)
        return f"({inner})" if isinstance(value, tuple) else f"[{inner}]"
    if isinstance(value, dict):
        inner = ", ".join(f"{k!r}: {_py_literal(v)}" for k, v in value.items())
        return "{" + inner + "}"
    return repr(value)


def _display_value_literal(value) -> str:
    if isinstance(value, str):
        if value.startswith("board.") or value.startswith("Pin("):
            return value
        if value == "None":
            return "None"
        if value.startswith("0x"):
            return value
    return _py_literal(value)


def _display_kwargs(display: dict, *, skip: frozenset[str] | None = None) -> str:
    omit = {"module", "class", "cp"} | (skip or frozenset())
    lines = []
    for key, value in display.items():
        if key in omit:
            continue
        lines.append(f"    {key}={_display_value_literal(value)},")
    if lines:
        return "\n".join(lines) + "\n"
    return ""


def _cp_mirror_line(display: dict) -> str:
    cp = display.get("cp")
    if not cp:
        return ""
    inner = _py_literal({k: v for k, v in cp.items() if k not in ("module", "class")})
    return f"    cp={inner},\n"


def _mp_spi_bus(bus: dict) -> str:
    lines = [
        "display_bus = SPIBus(",
        f"    id={bus['id']},",
        f"    baudrate={_py_literal(bus['baudrate'])},",
        f"    sck={bus['sck']},",
        f"    mosi={bus['mosi']},",
    ]
    if "miso" in bus:
        lines.append(f"    miso={bus['miso']},")
    lines.extend(
        [
            f"    dc={bus['dc']},",
            f"    cs={bus['cs']},",
        ]
    )
    if "reset" in bus:
        lines.append(f"    reset={bus['reset']},")
    lines.append(")")
    return "\n".join(lines)


def _cp_fourwire_bus(fw: dict) -> str:
    lines = [
        "display_bus = FourWire(",
        "    board.SPI(),",
        f"    command={fw['command']},",
        f"    chip_select={fw['chip_select']},",
        f"    baudrate={_py_literal(fw['baudrate'])},",
        ")",
    ]
    if "reset" in fw:
        lines.insert(-1, f"    reset={fw['reset']},")
    return "\n".join(lines)


def _cp_spi_bus_from_mp(bus: dict) -> str:
    """Default CP bus from MP pin numbers (D<n> mapping)."""
    dc = bus["dc"]
    cs = bus["cs"]
    lines = [
        "display_bus = FourWire(",
        "    board.SPI(),",
        f"    command=board.D{dc},",
        f"    chip_select=board.D{cs},",
        f"    baudrate={_py_literal(bus['baudrate'])},",
        ")",
    ]
    if "reset" in bus:
        lines.insert(-1, f"    reset=board.D{bus['reset']},")
    return "\n".join(lines)


def _touch_rotation_literal(touch: dict) -> str:
    if touch.get("rotation_null"):
        return "None"
    rot = touch.get("rotation_table", [0, 0, 0, 0])
    return _py_literal(tuple(rot) if isinstance(rot, list) else rot)


def _touch_chip_ctor(touch: dict, *, cp: bool) -> str:
    if cp:
        cp_touch = touch.get("cp", {})
        driver = cp_touch.get("driver", "focaltouch")
        if driver == "tt21100":
            return "TT21100(i2c)"
        return "Adafruit_FocalTouch(i2c)"
    cls = touch["class"]
    chip = touch.get("chip") or {}
    if not chip:
        return f"{cls}(i2c)"
    inner = ", ".join(f"{k}={_display_value_literal(v)}" for k, v in chip.items())
    return f"{cls}(i2c, {inner})"


def _mp_touch_block(touch: dict) -> str:
    i2c = touch["mp"]["i2c"]
    read = touch.get("read", "get_positions")
    rot_lit = _touch_rotation_literal(touch)
    setup = f"""i2c = I2C({i2c["id"]}, sda=Pin({i2c["sda"]}), scl=Pin({i2c["scl"]}), freq={_py_literal(i2c["freq"])})
touch_drv = {_touch_chip_ctor(touch, cp=False)}
"""
    if touch.get("read_wrapper"):
        setup += """
def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


"""
    else:
        setup += f"touch_read_func = touch_drv.{read}\n"
    setup += f"touch_rotation_table = {rot_lit}\n\n"
    runtime = """runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
"""
    return setup + runtime


def _cp_touch_block(touch: dict) -> str:
    rot_lit = _touch_rotation_literal(touch)
    cp_touch = touch.get("cp", {})
    driver = cp_touch.get("driver", "focaltouch")
    if driver == "tt21100":
        setup = f"""i2c = board.I2C()
touch_drv = {_touch_chip_ctor(touch, cp=True)}


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = {rot_lit}

"""
    else:
        setup = f"""i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = {rot_lit}

"""
    runtime = """runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
"""
    return setup + runtime


def _cp_touch_import(touch: dict) -> str:
    driver = touch.get("cp", {}).get("driver", "focaltouch")
    if driver == "tt21100":
        return "from adafruit_tt21100 import TT21100\n"
    return "from adafruit_focaltouch import Adafruit_FocalTouch\n"


def _mp_gc_snippet(manifest: dict) -> str:
    return "gc.collect()\n\n" if manifest.get("mp_gc_collect") else ""


def _mp_i80_bus(bus: dict) -> str:
    data = bus["data"]
    data_lit = ", ".join(str(p) for p in data)
    return f"""display_bus = I80Bus(
    dc={bus["dc"]},
    cs={bus["cs"]},
    wr={bus["wr"]},
    data=[{data_lit}],
)"""


def _cp_parallel_bus(pins: list[str]) -> str:
    args = ",\n    ".join(pins)
    return f"""display_bus = ParallelBus(
    {args},
)"""


def emit_busdisplay_spi_mp(manifest: dict) -> str:
    display = manifest["display"]
    mod = display["module"]
    cls = display["class"]
    bus = manifest["bus"]["mp"]["spi"]
    title = manifest.get("title", manifest["slug"])

    imports = []
    if manifest.get("mp_gc_collect"):
        imports.append("import gc")
    if "touch" in manifest:
        touch = manifest["touch"]
        imports.append(f"from {touch['module']} import {touch['class']}")
        imports.append("from machine import I2C, Pin")
    imports.append(f"from {mod} import {cls}")
    imports.append("from spibus import SPIBus")
    imports.append("")
    imports.append("import eventsys")

    preamble = manifest.get("mp_preamble", "")
    if manifest.get("mp_gc_collect"):
        preamble = (preamble + "\n\n" if preamble else "") + "gc.collect()\n"

    touch_setup = ""
    runtime_block = "runtime = None\n"
    if "touch" in manifest:
        touch_setup = _mp_touch_block(manifest["touch"])
        if manifest.get("mp_gc_collect"):
            touch_setup = "gc.collect()\n\n" + touch_setup
        runtime_block = ""

    cp_line = _cp_mirror_line(display)
    post_display = _mp_gc_snippet(manifest) if manifest.get("mp_gc_collect") else ""
    tail_gc = "gc.collect()\n" if manifest.get("mp_gc_collect") and "touch" in manifest else ""

    return f'''"""{title}"""

{chr(10).join(imports)}

{preamble}
{_mp_spi_bus(bus)}

{post_display}display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}{cp_line})
{post_display}{touch_setup}{runtime_block}{tail_gc}'''


def emit_busdisplay_spi_cp(manifest: dict) -> str:
    base_display = manifest["display"]
    mod = base_display["module"]
    cls = base_display["class"]
    if "cp" in base_display:
        display = dict(base_display["cp"])
        for key in ("width", "height"):
            if key not in display and key in base_display:
                display[key] = base_display[key]
    else:
        display = {k: v for k, v in base_display.items() if k not in ("module", "class", "cp")}
    display = {k: v for k, v in display.items() if k not in ("module", "class")}

    bus = manifest["bus"]
    if "cp" in bus and "fourwire" in bus["cp"]:
        bus_setup = _cp_fourwire_bus(bus["cp"]["fourwire"])
    else:
        bus_setup = _cp_spi_bus_from_mp(bus["mp"]["spi"])

    touch_setup = ""
    runtime_block = "runtime = None\n"
    touch_import = ""
    if "touch" in manifest:
        touch_setup = _cp_touch_block(manifest["touch"])
        touch_import = _cp_touch_import(manifest["touch"])
        runtime_block = ""

    slug = manifest["slug"]
    title = manifest.get(
        "title_cp",
        f"{manifest.get('title', slug)} — CircuitPython",
    )

    return f'''"""{title}"""

{touch_import}import board
from displayio import release_displays
from fourwire import FourWire
from {mod} import {cls}
import eventsys

release_displays()

{bus_setup}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}
)
{touch_setup}{runtime_block}'''


def emit_busdisplay_i2c_mp(manifest: dict) -> str:
    display = manifest["display"]
    mod = display["module"]
    cls = display["class"]
    i2c = manifest["bus"]["mp"]["i2c"]
    addr = i2c.get("address", 0x3C)
    title = manifest.get("title", manifest["slug"])
    return f'''"""{title}"""

from machine import I2C, Pin
from i2cbus import I2CBus
from {mod} import {cls}

import eventsys

display_bus = I2CBus(I2C({i2c["id"]}, sda=Pin({i2c["sda"]}), scl=Pin({i2c["scl"]}), freq={_py_literal(i2c["freq"])}), address={_display_value_literal(addr)})

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)})
runtime = None
'''


def emit_busdisplay_i2c_cp(manifest: dict) -> str:
    display = manifest["display"]
    mod = display["module"]
    cls = display["class"]
    addr = manifest["bus"]["cp"].get("address", 0x3C)
    title = manifest.get(
        "title_cp",
        f"{manifest.get('title', manifest['slug'])} — CircuitPython",
    )
    return f'''"""{title}"""

import board
from displayio import release_displays
from i2cdisplaybus import I2CDisplayBus
from {mod} import {cls}

import eventsys

release_displays()

display_bus = I2CDisplayBus(board.I2C(), device_address={_display_value_literal(addr)})

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)})
runtime = None
'''


def emit_busdisplay_i80_mp(manifest: dict) -> str:
    display = manifest["display"]
    mod = display["module"]
    cls = display["class"]
    bus = manifest["bus"]["mp"]["i80"]
    title = manifest.get("title", manifest["slug"])

    imports: list[str] = []
    if manifest.get("mp_preamble", "").find("sleep_ms") >= 0:
        imports.append("from time import sleep_ms")
    imports.append("from i80bus import I80Bus")
    if "touch" in manifest:
        touch = manifest["touch"]
        imports.append(f"from {touch['module']} import {touch['class']}")
    imports.append(f"from {mod} import {cls}")
    if "touch" in manifest:
        imports.append("from machine import I2C, Pin")
    else:
        imports.append("from machine import Pin")
    imports.append("")
    imports.append("import eventsys")

    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    touch_setup = ""
    runtime_block = "runtime = None\n"
    if "touch" in manifest:
        touch_setup = _mp_touch_block(manifest["touch"])
        runtime_block = ""

    return f'''"""{title}"""

{chr(10).join(imports)}

{preamble}{_mp_i80_bus(bus)}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)})
{touch_setup}{runtime_block}'''


def emit_busdisplay_i80_cp(manifest: dict) -> str:
    base_display = manifest["display"]
    mod = base_display["module"]
    cls = base_display["class"]
    if "cp" in base_display:
        display = dict(base_display["cp"])
        for key in ("width", "height"):
            if key not in display and key in base_display:
                display[key] = base_display[key]
    else:
        display = {k: v for k, v in base_display.items() if k not in ("module", "class", "cp")}

    touch_import = ""
    touch_setup = ""
    runtime_block = "runtime = None\n"
    if "touch" in manifest:
        touch_import = _cp_touch_import(manifest["touch"])
        touch_setup = _cp_touch_block(manifest["touch"])
        runtime_block = ""

    pins = manifest["bus"]["cp"]["parallel"]["pins"]
    title = manifest.get(
        "title_cp",
        f"{manifest.get('title', manifest['slug'])} — CircuitPython",
    )

    return f'''"""{title}"""

{touch_import}import board
from displayio import release_displays
from paralleldisplaybus import ParallelBus
from {mod} import {cls}
import eventsys

release_displays()

{_cp_parallel_bus(pins)}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}
)
{touch_setup}{runtime_block}'''


def _epaper_class(manifest: dict) -> str:
    return manifest.get("class") or EPAPER_CLASSES[manifest["module"]]


def _mp_spi_bus_block(bus: dict) -> str:
    lines = [
        "display_bus = SPIBus(",
        f"    id={bus['id']},",
        f"    baudrate={_py_literal(bus['baudrate'])},",
        f"    sck={bus['sck']},",
        f"    mosi={bus['mosi']},",
        f"    miso={bus['miso']},",
        f"    dc={bus['dc']},",
        f"    cs={bus['cs']},",
    ]
    if "reset" in bus:
        lines.append(f"    reset={bus['reset']},")
    lines.append(")")
    return "\n".join(lines)


def _cp_fourwire_epaper_block(bus: dict) -> str:
    lines = [
        "display_bus = FourWire(",
        "    board.SPI(),",
        f"    command={bus['command']},",
        f"    chip_select={bus['chip_select']},",
    ]
    if "reset" in bus:
        lines.append(f"    reset={bus['reset']},")
    lines.append(f"    baudrate={_py_literal(bus['baudrate'])},")
    lines.append(")")
    return "\n".join(lines)


def _mp_epaper_bus(manifest: dict) -> str:
    bus = dict(DEFAULT_MP_EPAPER_BUS)
    bus.update(manifest.get("mp_bus") or {})
    return _mp_spi_bus_block(bus)


def _cp_epaper_bus(manifest: dict) -> str:
    bus = dict(DEFAULT_CP_EPAPER_BUS)
    bus.update(manifest.get("cp_bus") or {})
    return _cp_fourwire_epaper_block(bus)


def _epaper_chip_args(manifest: dict, *, cp: bool) -> str:
    mod = manifest["module"]
    lines = [
        f"    width={manifest['width']},",
        f"    height={manifest['height']},",
    ]
    if mod not in EPAPER_NO_BUSY:
        busy = (
            manifest.get("cp_chip", {}).get("busy_pin")
            if cp
            else manifest.get("mp_chip", {}).get("busy_pin")
        )
        if busy is None:
            busy = "board.D7" if cp else "Pin(7, Pin.IN)"
        lines.append(f"    busy_pin={busy},")
    lines.append("    rotation=0,")
    chip_kwargs = dict(manifest.get("chip_kwargs") or {})
    if cp:
        chip_kwargs.update(manifest.get("cp", {}) or {})
    for key, value in chip_kwargs.items():
        if key in ("busy_pin",):
            continue
        lines.append(f"    {key}={_py_literal(value)},")
    return "\n".join(lines)


def emit_epaper_mp(manifest: dict) -> str:
    if manifest.get("template") == "magtag":
        return emit_epaper_magtag_mp(manifest)
    mod = manifest["module"]
    cls = _epaper_class(manifest)
    title = manifest["title"]
    return f'''"""{title} — MicroPython (Feather SPI pinout)"""

from machine import Pin, SPI
from {mod} import {cls}
from spibus import SPIBus

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

{_mp_epaper_bus(manifest)}
_epaper = {cls}(
    display_bus,
{_epaper_chip_args(manifest, cp=False)}
)

display_drv = EPaperDisplay(_epaper, width={manifest["width"]}, height={manifest["height"]}, color_depth={manifest["color_depth"]})

runtime = None
'''


def emit_epaper_cp(manifest: dict) -> str:
    if manifest.get("template") == "magtag":
        return emit_epaper_magtag_cp(manifest)
    mod = manifest["module"]
    cls = _epaper_class(manifest)
    title = manifest["title"]
    return f'''"""Adafruit {title} — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from {mod} import {cls}

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

{_cp_epaper_bus(manifest)}
_epaper = {cls}(
    display_bus,
{_epaper_chip_args(manifest, cp=True)}
)

display_drv = EPaperDisplay(_epaper, width={manifest["width"]}, height={manifest["height"]}, color_depth={manifest["color_depth"]})

runtime = None
'''


def emit_epaper_magtag_mp(manifest: dict) -> str:
    cls = _epaper_class(manifest)
    mod = manifest["module"]
    return f'''"""Adafruit MagTag SSD1680 E-Ink — MicroPython"""

from machine import Pin
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS
from spibus import SPIBus
from {mod} import {cls}

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=4_000_000,
    sck=36,
    mosi=35,
    miso=37,
    dc=7,
    cs=8,
    reset=6,
)

_epaper = {cls}(
    display_bus,
    width={manifest["width"]},
    height={manifest["height"]},
    busy_pin=Pin(5, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width={manifest["width"]}, height={manifest["height"]}, color_depth={manifest["color_depth"]})

buttons = GPIOButtons(
    {{
        "a": (Pin(15, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[0]),
        "b": (Pin(14, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[1]),
        "c": (Pin(12, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[2]),
        "d": (Pin(11, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[3]),
    }}
)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
'''


def emit_epaper_magtag_cp(manifest: dict) -> str:
    cls = _epaper_class(manifest)
    mod = manifest["module"]
    return f'''"""Adafruit MagTag 2.9\\" grayscale E-Ink (SSD1680) — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS
from {mod} import {cls}

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.EPD_DC,
    chip_select=board.EPD_CS,
    reset=board.EPD_RESET,
    baudrate=4_000_000,
)

_epaper = {cls}(
    display_bus,
    width={manifest["width"]},
    height={manifest["height"]},
    busy_pin=board.EPD_BUSY,
    rotation=0,
    ram_offset=1,
)

display_drv = EPaperDisplay(_epaper, width={manifest["width"]}, height={manifest["height"]}, color_depth={manifest["color_depth"]})

buttons = GPIOButtons(
    {{
        "a": (board.BUTTON_A, MAGTAG_BUTTON_KEYS[0]),
        "b": (board.BUTTON_B, MAGTAG_BUTTON_KEYS[1]),
        "c": (board.BUTTON_C, MAGTAG_BUTTON_KEYS[2]),
        "d": (board.BUTTON_D, MAGTAG_BUTTON_KEYS[3]),
    }}
)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
'''


def package_json_busdisplay(manifest: dict, *, cp: bool) -> dict:
    slug = manifest["slug"]
    out = manifest["out"]
    pkg = manifest.get("package", {})
    prefix = f"cp_{slug}" if cp else slug
    path = f"board_configs/{out}/{prefix}/board_config.py"
    urls = [["board_config.py", f"{GITHUB}/{path}"]]
    if drv := pkg.get("display_driver"):
        urls.append([f"{drv}.py", f"{GITHUB}/drivers/display/{drv}.py"])
    if not cp and (touch_drv := pkg.get("touch_driver")):
        urls.append([f"{touch_drv}.py", f"{GITHUB}/drivers/touch/{touch_drv}.py"])
    if cp and "touch" in manifest:
        driver = manifest["touch"].get("cp", {}).get("driver", "focaltouch")
        name, url = CP_TOUCH_URLS.get(driver, CP_TOUCH_URLS["focaltouch"])
        urls.append([name, url])
    deps: list[list[str]] = []
    if pkg.get("include_displaysys", True):
        deps.append([PACKAGE_URLS["displaysys"], "main"])
    for name in pkg.get("deps_mp" if not cp else "deps_cp", []):
        if name in PACKAGE_URLS:
            deps.append([PACKAGE_URLS[name], "main"])
    return {"urls": urls, "deps": deps, "version": "0.1"}


def package_json_busdisplay_i2c(manifest: dict, *, cp: bool) -> dict:
    pkg = package_json_busdisplay(manifest, cp=cp)
    if not cp:
        pkg["deps"].append([PACKAGE_URLS["i2cbus"], "main"])
    return pkg


def package_json_busdisplay_i80(manifest: dict, *, cp: bool) -> dict:
    pkg = package_json_busdisplay(manifest, cp=cp)
    if not cp:
        pkg["deps"].append([PACKAGE_URLS["i80bus"], "main"])
    return pkg


def package_json_epaper(manifest: dict, *, cp: bool) -> dict:
    slug = manifest["slug"]
    mod = manifest["module"]
    prefix = f"cp_{slug}" if cp else slug
    path = f"board_configs/epaperdisplay/{prefix}/board_config.py"
    urls = [
        ["board_config.py", f"{GITHUB}/{path}"],
        [f"{mod}.py", f"{GITHUB}/drivers/display/{mod}.py"],
    ]
    if manifest.get("template") == "magtag":
        urls.append(
            [
                "keypad_gpio.py",
                f"{GITHUB}/drivers/input/keypad_gpio.py",
            ]
        )
    deps = [
        [PACKAGE_URLS["displaysys"], "main"],
        [PACKAGE_URLS["epaperdisplay"], "main"],
    ]
    if not cp:
        deps.extend(
            [
                [PACKAGE_URLS["epaper_chip"], "main"],
                [PACKAGE_URLS["spibus"], "main"],
            ]
        )
    return {"urls": urls, "deps": deps, "version": "0.1"}


def write_outputs(manifest: dict, *, check: bool) -> list[str]:
    kind = manifest["kind"]
    slug = manifest["slug"]
    errors: list[str] = []

    if kind == "busdisplay_spi":
        out_rel = manifest["out"]
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_busdisplay_spi_mp(manifest)
        mp_pkg = json.dumps(package_json_busdisplay(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))

        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_busdisplay_spi_cp(manifest)
            cp_pkg = json.dumps(package_json_busdisplay(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "busdisplay_i2c":
        out_rel = manifest["out"]
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_busdisplay_i2c_mp(manifest)
        mp_pkg = json.dumps(package_json_busdisplay_i2c(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_busdisplay_i2c_cp(manifest)
            cp_pkg = json.dumps(package_json_busdisplay_i2c(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "busdisplay_i80":
        out_rel = manifest["out"]
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_busdisplay_i80_mp(manifest)
        mp_pkg = json.dumps(package_json_busdisplay_i80(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_busdisplay_i80_cp(manifest)
            cp_pkg = json.dumps(package_json_busdisplay_i80(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "busdisplay_verbatim":
        out_rel = manifest["out"]
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_files = manifest["verbatim"]["mp"]
        errors.extend(
            _write_pair(
                mp_dir,
                mp_files["board_config"],
                mp_files["package_json"],
                check=check,
            )
        )
        if manifest.get("circuitpython") and "cp" in manifest.get("verbatim", {}):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_files = manifest["verbatim"]["cp"]
            errors.extend(
                _write_pair(
                    cp_dir,
                    cp_files["board_config"],
                    cp_files["package_json"],
                    check=check,
                )
            )

    elif kind == "epaper":
        mp_dir = BOARD_ROOT / "epaperdisplay" / slug
        cp_dir = BOARD_ROOT / "epaperdisplay" / f"cp_{slug}"
        mp_py = emit_epaper_mp(manifest)
        cp_py = emit_epaper_cp(manifest)
        mp_pkg = json.dumps(package_json_epaper(manifest, cp=False), indent=2) + "\n"
        cp_pkg = json.dumps(package_json_epaper(manifest, cp=True), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))
    else:
        errors.append(f"{slug}: unknown kind {kind!r}")
    return errors


def _write_pair(directory: Path, board_py: str, package: str, *, check: bool) -> list[str]:
    errors: list[str] = []
    bc = directory / "board_config.py"
    pj = directory / "package.json"
    for path, content in ((bc, board_py), (pj, package)):
        if check:
            if not path.exists():
                errors.append(f"missing {path.relative_to(ROOT)}")
            elif path.read_text(encoding="utf-8") != content:
                errors.append(f"drift {path.relative_to(ROOT)}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if not check:
        print(f"wrote {directory.relative_to(ROOT)}")
    return errors


EPAPER_CHIP_KWARGS = frozenset({"highlight_color"})


def _normalize_epaper_row(row: dict) -> dict:
    chip_kwargs = {k: row[k] for k in EPAPER_CHIP_KWARGS if k in row}
    manifest = {
        "kind": "epaper",
        "slug": row["slug"],
        "module": row["module"],
        "title": row["title"],
        "width": row["width"],
        "height": row["height"],
        "color_depth": row["color_depth"],
        "chip_kwargs": chip_kwargs,
    }
    for key in ("class", "template", "mp_bus", "cp_bus", "cp", "mp_chip", "cp_chip"):
        if key in row:
            manifest[key] = row[key]
    return manifest


def load_manifests(only: str | None, *, kind: str | None = None) -> list[dict]:
    manifests: list[dict] = []
    for path in sorted(MANIFEST_ROOT.rglob("*.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        if "board" in data:
            for row in data["board"]:
                manifest = _normalize_epaper_row(row)
                if only and manifest.get("slug") != only:
                    continue
                if kind and manifest.get("kind") != kind:
                    continue
                manifests.append(manifest)
        elif "kind" in data:
            if only and data.get("slug") != only:
                continue
            if kind and data.get("kind") != kind:
                continue
            manifests.append(data)
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated output differs")
    parser.add_argument("--only", help="generate one board slug only")
    parser.add_argument(
        "--kind",
        help="filter by manifest kind (busdisplay_spi, busdisplay_i2c, busdisplay_i80, busdisplay_verbatim, epaper)",
    )
    args = parser.parse_args()

    manifests = load_manifests(args.only, kind=args.kind)
    if args.only and not manifests:
        print(f"No manifest for slug {args.only!r}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for manifest in manifests:
        errors.extend(write_outputs(manifest, check=args.check))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    if args.check:
        print(f"OK ({len(manifests)} manifest(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
