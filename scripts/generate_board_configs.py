#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Generate board_config.py and package.json from TOML manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import tomllib

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "scripts" / "board_config"
MANIFEST_ROOT = SOURCE_ROOT / "manifests"
HAND_MAINTAINED_ROOT = SOURCE_ROOT / "hand_maintained"
BOARD_ROOT = ROOT / "board_configs"
ALLOWED_BOARD_FILES = frozenset({"board_config.py", "package.json"})
GITHUB = "github:PyDevices/pydisplay"

PACKAGE_URLS = {
    "displaysys": f"{GITHUB}/packages/displaysys.json",
    "epaperdisplay": f"{GITHUB}/packages/epaperdisplay.json",
    "epaper_chip": f"{GITHUB}/packages/epaper_chip.json",
    "spibus": f"{GITHUB}/packages/spibus.json",
    "i2cbus": f"{GITHUB}/packages/i2cbus.json",
    "i80bus": f"{GITHUB}/packages/i80bus.json",
    "mipidsi": f"{GITHUB}/packages/mipidsi.json",
    "picodvi": f"{GITHUB}/packages/picodvi.json",
    "rgbframebuffer": f"{GITHUB}/packages/rgbframebuffer.json",
    "pixeldisplay": f"{GITHUB}/packages/pixeldisplay.json",
    "graphics": f"{GITHUB}/packages/graphics.json",
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
    "touchscreen": (
        "adafruit_touchscreen.py",
        f"{GITHUB}/drivers/touch/circuitpython/adafruit_touchscreen.py",
    ),
    "stmpe610": (
        "adafruit_stmpe610.py",
        f"{GITHUB}/drivers/touch/circuitpython/adafruit_stmpe610.py",
    ),
}

INPUT_DRIVER_URLS = {
    "keypad_shift": (
        "keypad_shift.py",
        f"{GITHUB}/drivers/input/keypad_shift.py",
    ),
    "keypad_gpio": (
        "keypad_gpio.py",
        f"{GITHUB}/drivers/input/keypad_gpio.py",
    ),
    "gpiojoystick": (
        "gpiojoystick.py",
        f"{GITHUB}/drivers/joystick/gpiojoystick.py",
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


def _ruff_cmd() -> list[str]:
    venv_ruff = ROOT / ".venv" / "bin" / "ruff"
    if venv_ruff.is_file():
        return [str(venv_ruff)]
    return [sys.executable, "-m", "ruff"]


def _ruff_format_board_config(source: str, *, rel_path: Path) -> str:
    """Apply ruff isort fix + format so generated output matches pre-commit hooks."""
    stdin_name = str(rel_path).replace("\\", "/")
    cmd = _ruff_cmd()
    isort = subprocess.run(
        [*cmd, "check", "--select", "I", "--fix-only", f"--stdin-filename={stdin_name}", "-"],
        input=source,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    if isort.returncode != 0:
        raise RuntimeError(
            f"ruff isort fix failed for {stdin_name}:\n{isort.stderr or isort.stdout}"
        )
    fmt = subprocess.run(
        [*cmd, "format", f"--stdin-filename={stdin_name}", "-"],
        input=isort.stdout,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    if fmt.returncode != 0:
        raise RuntimeError(f"ruff format failed for {stdin_name}:\n{fmt.stderr or fmt.stdout}")
    return fmt.stdout


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
        if value.startswith("GPIO_"):
            return repr(value)
        if value.isidentifier() and value.isupper():
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
    ]
    if "baudrate" in bus:
        lines.append(f"    baudrate={_py_literal(bus['baudrate'])},")
    lines.extend(
        [
            f"    sck={bus['sck']},",
            f"    mosi={bus['mosi']},",
        ]
    )
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


def _touch_type(touch: dict) -> str:
    return touch.get("type") or "i2c"


def _calibration_literal(calibration: list) -> str:
    pairs = [tuple(pair) for pair in calibration]
    return _py_literal(tuple(pairs))


def _display_dim_expr(value) -> str:
    if isinstance(value, str):
        return value
    return str(value)


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


def _mp_i2c_touch_setup(touch: dict) -> str:
    i2c = touch["mp"]["i2c"]
    read = touch.get("read", "get_positions")
    rot_lit = _touch_rotation_literal(touch)
    if "sda" in i2c:
        i2c_line = (
            f"i2c = I2C({i2c['id']}, sda=Pin({i2c['sda']}), scl=Pin({i2c['scl']}), "
            f"freq={_py_literal(i2c['freq'])})"
        )
    else:
        i2c_line = f"i2c = I2C({i2c['id']}, freq={_py_literal(i2c['freq'])})"
    if i2c.get("reuse_i2c"):
        i2c_line = ""
    setup = f"""{i2c_line}
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
    setup += f"touch_rotation_table = {rot_lit}\n"
    return setup


def _mp_xpt2046_touch_setup(touch: dict) -> str:
    spi = touch["mp"]["spi"]
    rot_lit = _touch_rotation_literal(touch)
    if "sck" in spi:
        spi_line = (
            f"spi = SPI({spi['id']}, baudrate={spi['baudrate']}, "
            f"sck=Pin({spi['sck']}), mosi=Pin({spi['mosi']}), miso=Pin({spi['miso']}))"
        )
    else:
        spi_line = f"spi = SPI({spi['id']}, baudrate={spi['baudrate']})"
    setup = f"""{spi_line}
touch_drv = {touch["class"]}(
    spi=spi,
    cs=Pin({spi["cs"]}),
"""
    if int_pin := spi.get("int_pin"):
        setup += f"    int_pin=Pin({int_pin}),\n"
    setup += ")\n"
    if cal := touch.get("calibrate"):
        setup += f"""
touch_drv.calibrate(
    xmin={cal["xmin"]},
    xmax={cal["xmax"]},
    ymin={cal["ymin"]},
    ymax={cal["ymax"]},
    width={_display_dim_expr(cal.get("width", "display_drv.width"))},
    height={_display_dim_expr(cal.get("height", "display_drv.height"))},
    orientation={cal["orientation"]},
)

"""
    read = touch.get("read", "get_touch")
    setup += f"touch_read_func = touch_drv.{read}\n"
    setup += f"touch_rotation_table = {rot_lit}\n"
    return setup


def _mp_stmpe610_touch_setup(touch: dict) -> str:
    spi = touch["mp"]["spi"]
    chip = touch.get("chip") or {}
    cal_name = touch.get("calibration_name", "_TOUCH_CALIBRATION")
    cal_lit = _calibration_literal(touch["calibration"])
    cs = chip["cs"]
    setup = f"""touch_spi = SPI(
    {spi["id"]},
    baudrate={spi["baudrate"]},
    sck=Pin({spi["sck"]}),
    mosi=Pin({spi["mosi"]}),
    miso=Pin({spi["miso"]}),
)
{cal_name} = {cal_lit}
touch_drv = {touch["class"]}(
    touch_spi,
    cs={cs},
    width={chip["width"]},
    height={chip["height"]},
    rotation={chip["rotation"]},
    calibration={cal_name},
)

"""
    if touch.get("read_wrapper") == "stmpe610":
        setup += """
def touch_read_func():
    if touch_drv.touched:
        point = touch_drv.touch_point
        if point is not None:
            return point
    return None


"""
    else:
        read = touch.get("read", "get_positions")
        setup += f"touch_read_func = touch_drv.{read}\n"
    setup += f"touch_rotation_table = {_touch_rotation_literal(touch)}\n"
    return setup


def _mp_touch_setup(touch: dict) -> str:
    ttype = _touch_type(touch)
    if ttype == "xpt2046":
        return _mp_xpt2046_touch_setup(touch)
    if ttype == "stmpe610":
        return _mp_stmpe610_touch_setup(touch)
    return _mp_i2c_touch_setup(touch)


def _cp_i2c_touch_setup(touch: dict) -> str:
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
    return setup


def _cp_xpt2046_touch_setup(touch: dict) -> str:
    cp = touch.get("cp", {})
    pins = cp["pins"]
    rot_lit = _touch_rotation_literal(touch)
    pin_args = ",\n    ".join(pins)
    x_res = cp.get("x_resistance", 400)
    return f"""touchscreen = Touchscreen(
    {pin_args},
    x_resistance={x_res},
)


def touch_read_func():
    point = touchscreen.touch_point
    if point:
        return point[0], point[1]
    return None

touch_rotation_table = {rot_lit}
"""


def _cp_stmpe610_touch_setup(touch: dict) -> str:
    cp = touch.get("cp", {})
    cal_name = touch.get("calibration_name", "_TOUCH_CALIBRATION")
    cal_lit = _calibration_literal(touch["calibration"])
    rot_lit = _touch_rotation_literal(touch)
    return f"""{cal_name} = {cal_lit}

touch_drv = Adafruit_STMPE610_SPI(
    board.SPI(),
    {cp["chip_select"]},
    baudrate={cp.get("baudrate", 1_000_000)},
    calibration={cal_name},
    size=(display_drv.width, display_drv.height),
    disp_rotation=display_drv.rotation,
)


def touch_read_func():
    if touch_drv.touched:
        point = touch_drv.touch_point
        if point is not None:
            return point[0], point[1]
    return None


touch_rotation_table = {rot_lit}
"""


def _cp_touch_setup(touch: dict) -> str:
    ttype = _touch_type(touch)
    if ttype == "xpt2046":
        return _cp_xpt2046_touch_setup(touch)
    if ttype == "stmpe610":
        return _cp_stmpe610_touch_setup(touch)
    return _cp_i2c_touch_setup(touch)


def _mp_encoder_setup(enc: dict) -> str:
    kwargs = []
    if enc.get("pull_up", True):
        kwargs.append("pull_up=True")
    if enc.get("half_step"):
        kwargs.append("half_step=True")
    kw = ", ".join(kwargs)
    if kw:
        kw = ", " + kw
    active_low = enc.get("button_active_low", True)
    button_expr = "not encoder_button.value()" if active_low else "encoder_button.value()"
    return f"""encoder_drv = {enc["class"]}({enc["pin_a"]}, {enc["pin_b"]}{kw})
encoder_read_func = encoder_drv.value
encoder_button = Pin({enc["button_pin"]}, Pin.IN, Pin.PULL_UP)


def encoder_button_func():
    return {button_expr}


"""


def _mp_keypad_shift_setup(kps: dict) -> str:
    mapping = kps.get("mapping", "PYBADGE_BUTTON_MAP")
    return f"""buttons = ShiftRegisterButtons(
    clock={kps["clock"]},
    latch={kps["latch"]},
    data={kps["data"]},
    mapping={mapping},
)

"""


def _mp_joystick_setup(joy: dict) -> str:
    axes_lines = []
    for axis in joy["axes"]:
        atten = axis.get("atten", "ADC.ATTN_11DB")
        axes_lines.append(f"        ADC(Pin({axis['pin']}), atten={atten}),")
    axes_body = "\n".join(axes_lines)
    buttons = ", ".join(f"Pin({pin}, Pin.IN, Pin.PULL_UP)" for pin in joy["buttons"])
    return f"""joystick_driver = {joy["class"]}(
    instance_id={joy.get("instance_id", 0)},
    axes=[
{axes_body}
    ],
    buttons=[
        {buttons},
    ],
)

"""


def _cp_keypad_gpio_setup(kpg: dict) -> str:
    keys = kpg.get("keys", "MAGTAG_BUTTON_KEYS")
    lines = ["buttons = GPIOButtons({"]
    for name, pin in kpg["buttons"].items():
        idx = list(kpg["buttons"].keys()).index(name)
        lines.append(f'        "{name}": ({pin}, {keys}[{idx}]),')
    lines.append("    })")
    lines.append("")
    return "\n".join(lines) + "\n"


def _mp_input_setup(manifest: dict) -> str:
    input_cfg = manifest.get("input") or {}
    blocks: list[str] = []
    if enc := input_cfg.get("encoder"):
        blocks.append(_mp_encoder_setup(enc))
    if kps := input_cfg.get("keypad_shift"):
        blocks.append(_mp_keypad_shift_setup(kps))
    if joy := input_cfg.get("joystick"):
        blocks.append(_mp_joystick_setup(joy))
    return "".join(blocks)


def _cp_input_setup(manifest: dict) -> str:
    input_cfg = manifest.get("input") or {}
    if kpg := input_cfg.get("keypad_gpio"):
        return _cp_keypad_gpio_setup(kpg)
    return ""


def _runtime_block(manifest: dict, *, cp: bool) -> str:
    touch = manifest.get("touch")
    input_cfg = manifest.get("input") or {}
    has_touch = touch is not None
    has_input = bool(
        input_cfg.get("encoder")
        or input_cfg.get("keypad_shift")
        or input_cfg.get("joystick")
        or (cp and input_cfg.get("keypad_gpio"))
    )

    if not has_touch and not has_input:
        return "runtime = None\n"

    if has_touch and not has_input:
        return """runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
"""

    lines = ["runtime = eventsys.Runtime(display=display_drv)"]
    if not cp:
        if input_cfg.get("encoder"):
            lines.append(
                "runtime.add_encoder(read=encoder_read_func, button_read=encoder_button_func)"
            )
        if input_cfg.get("keypad_shift"):
            lines.append("runtime.add_keypad(read=buttons.read)")
        if joy := input_cfg.get("joystick"):
            emulate = joy.get("emulate_digital", [])
            lines.append(
                f"runtime.add_joystick(joystick_driver=joystick_driver, emulate_digital={_py_literal(emulate)})"
            )
    elif input_cfg.get("keypad_gpio"):
        lines.append("runtime.add_keypad(read=buttons.read)")
    return "\n".join(lines) + "\n"


def _mp_touch_block(touch: dict) -> str:
    return _mp_touch_setup(touch) + "\n" + _runtime_block({"touch": touch}, cp=False)


def _cp_touch_block(touch: dict) -> str:
    return _cp_touch_setup(touch) + "\n" + _runtime_block({"touch": touch}, cp=True)


def _cp_touch_import(touch: dict) -> str:
    ttype = _touch_type(touch)
    if ttype == "xpt2046":
        return "from adafruit_touchscreen import Touchscreen\n"
    if ttype == "stmpe610":
        return "from adafruit_stmpe610 import Adafruit_STMPE610_SPI\n"
    driver = touch.get("cp", {}).get("driver", "focaltouch")
    if driver == "tt21100":
        return "from adafruit_tt21100 import TT21100\n"
    return "from adafruit_focaltouch import Adafruit_FocalTouch\n"


def _collect_mp_imports(manifest: dict, *, bus_import: str) -> list[str]:
    imports: list[str] = []
    if manifest.get("mp_gc_collect"):
        imports.append("import gc")
    preamble = manifest.get("mp_preamble", "")
    if "sleep_ms" in preamble and "from time import sleep_ms" not in preamble:
        imports.append("from time import sleep_ms")

    touch = manifest.get("touch")
    if touch:
        imports.append(f"from {touch['module']} import {touch['class']}")
        ttype = _touch_type(touch)
        if ttype == "i2c":
            imports.append("from machine import I2C, Pin")
        else:
            imports.append("from machine import Pin, SPI")

    input_cfg = manifest.get("input") or {}
    preamble_pin = "Pin(" in manifest.get("mp_preamble", "")
    display_pin = any(
        isinstance(v, str) and v.startswith("Pin(") for v in manifest["display"].values()
    )
    need_pin = bool(input_cfg) or preamble_pin or display_pin
    if input_cfg.get("encoder"):
        imports.append(
            f"from {input_cfg['encoder']['module']} import {input_cfg['encoder']['class']}"
        )
    if input_cfg.get("keypad_shift"):
        imports.append("from keypad_shift import PYBADGE_BUTTON_MAP, ShiftRegisterButtons")
    if input_cfg.get("joystick"):
        imports.append("from gpiojoystick import GPIOJoystick")
        imports.append("from machine import ADC, Pin")
        need_pin = False
    if need_pin and "Pin" not in "\n".join(imports):
        imports.append("from machine import Pin")

    display = manifest["display"]
    imports.append(f"from {display['module']} import {display['class']}")
    imports.append(bus_import)
    imports.append("")
    imports.append("import eventsys")
    return imports


def _collect_cp_imports(manifest: dict) -> list[str]:
    imports: list[str] = []
    if touch := manifest.get("touch"):
        imports.append(_cp_touch_import(touch).rstrip())
    input_cfg = manifest.get("input") or {}
    if input_cfg.get("keypad_gpio"):
        keys = input_cfg["keypad_gpio"].get("keys", "MAGTAG_BUTTON_KEYS")
        imports.append(f"from keypad_gpio import GPIOButtons, {keys}")
    display = manifest["display"]
    imports.append("import board")
    imports.append("from displayio import release_displays")
    if manifest["kind"] == "busdisplay_i80":
        imports.append("from paralleldisplaybus import ParallelBus")
    else:
        imports.append("from fourwire import FourWire")
    imports.append(f"from {display['module']} import {display['class']}")
    imports.append("import eventsys")
    return imports


def _post_display_block(manifest: dict, *, cp: bool) -> str:
    blocks: list[str] = []
    if touch := manifest.get("touch"):
        if cp:
            blocks.append(_cp_touch_setup(touch))
        else:
            blocks.append(_mp_touch_setup(touch))
    if cp:
        blocks.append(_cp_input_setup(manifest))
    else:
        blocks.append(_mp_input_setup(manifest))
    blocks.append(_runtime_block(manifest, cp=cp))
    return "\n".join(block for block in blocks if block)


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


MIPIDSI_MP_PORT_MSG = {
    "esp32p4": "MIPI DSI requires displayif mipidsi cmod (esp32p4 port)",
    "mimxrt1176": "MIPI DSI requires displayif mipidsi cmod (mimxrt1176 port)",
}


def _mipidsi_init_name(display: dict) -> str:
    return display.get("init_sequence_name", "PANEL_INIT_SEQUENCE")


def _mipidsi_init_setup(display: dict) -> str:
    name = _mipidsi_init_name(display)
    if display.get("init_sequence_empty"):
        return f'{name} = b""\n\n'
    if display.get("init_sequence_ref"):
        return ""
    hex_chunks = display.get("init_sequence_hex")
    if hex_chunks:
        lines = [f"{name} = ("]
        for hex_str in hex_chunks:
            data = bytes.fromhex(hex_str)
            inner = "".join(f"\\x{b:02x}" for b in data)
            lines.append(f'    b"{inner}"')
        lines.append(")")
        return "\n".join(lines) + "\n\n"
    chunks = display.get("init_sequence_chunks")
    if chunks:
        lines = [f"{name} = ("]
        lines.extend(f"    {chunk}" for chunk in chunks)
        lines.append(")")
        return "\n".join(lines) + "\n\n"
    return f'{name} = b""\n\n'


def _mipidsi_bus_mp(bus: dict) -> str:
    parts = [
        f"frequency={_py_literal(bus['frequency'])}",
        f"num_lanes={bus.get('num_lanes', 2)}",
    ]
    if "ldo_chan" in bus:
        parts.append(f"ldo_chan={bus['ldo_chan']}")
    if "ldo_voltage_mv" in bus:
        parts.append(f"ldo_voltage_mv={bus['ldo_voltage_mv']}")
    return f"bus = Bus({', '.join(parts)})\n"


def _mipidsi_display_kwargs(display: dict, *, init_name: str) -> str:
    lines = [f"    init_sequence={init_name},"]
    for key in (
        "width",
        "height",
        "color_depth",
        "pixel_clock_frequency",
        "hsync_pulse_width",
        "hsync_front_porch",
        "hsync_back_porch",
        "vsync_pulse_width",
        "vsync_front_porch",
        "vsync_back_porch",
        "reset_pin",
        "backlight_pin",
        "backlight_on_high",
    ):
        if key in display:
            lines.append(f"    {key}={_display_value_literal(display[key])},")
    return "\n".join(lines)


def _mp_pin_constants(pins: dict) -> str:
    return "\n".join(f"{name} = {value}" for name, value in pins.items()) + "\n\n"


def _mp_mipidsi_gt911_i2c_setup(touch: dict) -> str:
    i2c = touch["mp"]["i2c"]
    if "scl" not in i2c:
        return f"i2c = I2C({i2c['id']}, freq={_py_literal(i2c['freq'])})\n"
    scl = _display_value_literal(i2c["scl"])
    sda = _display_value_literal(i2c["sda"])
    return (
        f"i2c = I2C({i2c['id']}, scl=Pin({scl}), sda=Pin({sda}), "
        f"freq={_py_literal(i2c['freq'])})\n"
    )


def _mp_mipidsi_touch_setup(touch: dict) -> str:
    cls = touch.get("class", "GT911")
    chip = touch.get("chip", {})
    i2c_line = ""
    if not touch.get("mp", {}).get("i2c", {}).get("reuse_i2c"):
        i2c_line = _mp_mipidsi_gt911_i2c_setup(touch)
    parts = [i2c_line, f"touch_drv = {cls}(\n    i2c,"]
    for key, value in chip.items():
        if value is None:
            parts.append(f"    {key}=None,")
        else:
            parts.append(f"    {key}={_display_value_literal(value)},")
    parts.append(")\n")
    return "\n".join(parts) + "\n"


def _mp_mipidsi_touch_tail(touch: dict) -> str:
    rot = _touch_rotation_literal(touch)
    return f"""
def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


touch_rotation_table = {rot}

display_drv = FBDisplay(fb)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
"""


def _mp_mipidsi_touch(touch: dict) -> str:
    return _mp_mipidsi_touch_setup(touch) + _mp_mipidsi_touch_tail(touch)


def _mp_mipidsi_gt911_touch(touch: dict) -> str:
    return _mp_mipidsi_touch(touch)


def emit_fbdisplay_mipidsi_mp(manifest: dict) -> str:
    display = manifest["display"]
    bus = manifest["bus"]
    title = manifest.get("title", manifest["slug"])
    port = manifest.get("port", "esp32p4")
    port_msg = MIPIDSI_MP_PORT_MSG.get(port, MIPIDSI_MP_PORT_MSG["esp32p4"])
    init_name = _mipidsi_init_name(display)

    imports = ["from displaysys.fbdisplay import FBDisplay", "import eventsys"]
    for extra in manifest.get("mp_imports", []):
        if extra not in imports:
            imports.insert(0, extra)
    if display.get("init_sequence_ref") and (mod := display.get("init_sequence_module")):
        init_import = f"from {mod} import {init_name}"
        if init_import not in imports:
            imports.insert(0, init_import)

    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    preamble_after_pins = manifest.get("mp_preamble_after_pins", "")
    if preamble_after_pins and not preamble_after_pins.endswith("\n"):
        preamble_after_pins += "\n"
    pin_block = ""
    if pins := manifest.get("pins", {}).get("mp"):
        pin_block = _mp_pin_constants(pins)

    needs_time = manifest.get("mp_lcd_reset_pulse", False) or "import time" in manifest.get(
        "mp_imports", []
    )
    needs_pin = manifest.get("mp_lcd_reset_pulse", False)
    needs_machine = (
        manifest.get("mp_lcd_reset_pulse")
        or manifest.get("touch")
        or preamble_after_pins
        or pin_block
    )
    if touch := manifest.get("touch"):
        touch_import = f"from {touch['module']} import {touch['class']}"
        if touch_import not in imports:
            imports.insert(0, touch_import)
    if needs_machine and "from machine import I2C, Pin" not in "\n".join(imports):
        imports.insert(0, "from machine import I2C, Pin")
    elif needs_pin and "from machine import Pin" not in "\n".join(imports):
        imports.insert(0, "from machine import Pin")
    if needs_time and "import time" not in imports:
        imports.insert(0, "import time")

    init_block = _mipidsi_init_setup(display)
    reset_block = ""
    if manifest.get("mp_lcd_reset_pulse"):
        pins = manifest.get("pins", {}).get("mp", {})
        reset_pin = "LCD_RESET" if "LCD_RESET" in pins else display.get("reset_pin")
        reset_block = f"""lcd_reset = Pin({reset_pin}, Pin.OUT, value=1)
lcd_reset.value(0)
time.sleep_ms(100)
lcd_reset.value(1)
time.sleep_ms(200)

"""

    touch_setup = ""
    touch_tail = ""
    runtime_tail = "display_drv = FBDisplay(fb)\n\nruntime = None\n"
    if touch := manifest.get("touch"):
        touch_setup = _mp_mipidsi_touch_setup(touch)
        touch_tail = _mp_mipidsi_touch_tail(touch)
        runtime_tail = ""

    bus_display = f"""{_mipidsi_bus_mp(bus)}
fb = Display(
    bus,
{_mipidsi_display_kwargs(display, init_name=init_name)}
)
"""
    if manifest.get("touch_before_display") and touch_setup:
        body = f"{touch_setup}{bus_display}{touch_tail}"
    else:
        body = f"{bus_display}{touch_setup}{touch_tail}"

    return f'''"""{title}"""

{chr(10).join(imports)}

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError("{port_msg}") from exc

{preamble}{pin_block}{preamble_after_pins}{init_block}{reset_block}{body}{runtime_tail}'''


def _cp_mipidsi_gt911_touch(touch: dict) -> str:
    cp = touch.get("cp", {})
    rot = _touch_rotation_literal(touch)
    i2c_scl = cp.get("i2c_scl", "board.SCL")
    i2c_sda = cp.get("i2c_sda", "board.SDA")
    address = cp.get("address", "0x5D")
    setup = f"""i2c = busio.I2C({i2c_scl}, {i2c_sda})
"""
    reset_pin = cp.get("reset_pin")
    if reset_pin:
        setup += f"""touch_rst = digitalio.DigitalInOut({reset_pin})
touch_rst.direction = digitalio.Direction.OUTPUT
touch_drv = gt911.GT911(i2c, i2c_address={address}, rst_pin=touch_rst)

"""
    else:
        setup += f"touch_drv = gt911.GT911(i2c, i2c_address={address})\n\n"
    setup += """
def touch_read_func():
    touches = touch_drv.touches
    if touches:
        return touches[0][0], touches[0][1]
    return None


"""
    setup += f"""touch_rotation_table = {rot}

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
"""
    return setup


def emit_fbdisplay_mipidsi_cp(manifest: dict) -> str:
    display = dict(manifest["display"])
    if cp_display := display.pop("cp", None):
        display.update(cp_display)
    bus = manifest["bus"]
    title = manifest.get("title_cp", f"{manifest.get('title', manifest['slug'])} — CircuitPython")
    init_name = _mipidsi_init_name(display)
    use_fb_disp = manifest.get("cp_framebuffer_display", False)

    imports = [
        "import board",
        "import busio",
        "import displayio",
        "import mipidsi",
        "from displaysys.fbdisplay import FBDisplay",
        "import eventsys",
    ]
    for extra in manifest.get("cp_imports", []):
        if extra not in imports:
            imports.insert(3, extra)
    if display.get("init_sequence_ref") and (mod := display.get("init_sequence_module")):
        init_import = f"from {mod} import {init_name}"
        if init_import not in imports:
            imports.insert(3, init_import)
    if touch := manifest.get("touch"):
        if touch.get("cp", {}).get("driver") == "gt911":
            imports.insert(4, "import gt911")
        if touch.get("cp", {}).get("reset_pin") and "digitalio" not in imports:
            imports.insert(3, "import digitalio")
    if manifest.get("cp_lcd_reset_pulse"):
        if "import time" not in imports:
            imports.insert(0, "import time")
        if "import digitalio" not in imports:
            imports.insert(3, "import digitalio")

    if use_fb_disp:
        imports.insert(4, "import framebufferio")

    preamble = manifest.get("cp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    pin_block = ""
    if pins := manifest.get("pins", {}).get("cp"):
        pin_lines = [f"{name} = {value}" for name, value in pins.items()]
        pin_block = "\n".join(pin_lines) + "\n\n"

    init_block = _mipidsi_init_setup(display)
    reset_block = ""
    if manifest.get("cp_lcd_reset_pulse"):
        reset_block = f"""reset_pin = digitalio.DigitalInOut({manifest["pins"]["cp"].get("LCD_RESET", "board.IO27")})
reset_pin.direction = digitalio.Direction.OUTPUT
reset_pin.value = False
time.sleep(0.1)
reset_pin.value = True
time.sleep(0.2)

"""

    bus_line = _mipidsi_bus_mp(bus).replace("bus = Bus", "bus = mipidsi.Bus")
    display_block = f"""{bus_line}
fb = mipidsi.Display(
    bus,
{_mipidsi_display_kwargs(display, init_name=init_name)}
)
"""
    if use_fb_disp:
        display_block += """
display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

"""

    fbdisplay_line = "display_drv = FBDisplay(fb)\n\n"
    runtime_tail = fbdisplay_line + "runtime = None\n"
    touch_block = ""
    if touch := manifest.get("touch"):
        touch_block = _cp_mipidsi_gt911_touch(touch)
        runtime_tail = ""

    return f'''"""{title}"""

{chr(10).join(imports)}

displayio.release_displays()

{preamble}{pin_block}{init_block}{reset_block}{display_block}{fbdisplay_line}{touch_block}{runtime_tail}'''


def package_json_fbdisplay_mipidsi(manifest: dict, *, cp: bool) -> dict:
    slug = manifest["slug"]
    out = manifest.get("out", "fbdisplay")
    prefix = f"cp_{slug}" if cp else slug
    path = f"board_configs/{out}/{prefix}/board_config.py"
    urls = [["board_config.py", f"{GITHUB}/{path}"]]
    pkg = manifest.get("package", {})
    if touch_drv := pkg.get("touch_driver"):
        urls.append([f"{touch_drv}.py", f"{GITHUB}/drivers/touch/{touch_drv}.py"])
    for extra in pkg.get("urls_mp" if not cp else "urls_cp", []):
        urls.append([extra["name"], extra["url"]])
    deps = [[PACKAGE_URLS["displaysys"], "main"]]
    if not cp and pkg.get("include_mipidsi", True):
        deps.append([PACKAGE_URLS["mipidsi"], "main"])
    for name in pkg.get("deps_mp" if not cp else "deps_cp", []):
        if name in PACKAGE_URLS:
            deps.append([PACKAGE_URLS[name], "main"])
    result = {"urls": urls, "deps": deps, "version": "0.1"}
    if notes := pkg.get("notes_cp" if cp else "notes_mp"):
        result["notes"] = notes
    return result


PICODVI_MP_PORT_MSG = {
    "rp2040": "DVI output requires displayif picodvi cmod (rp2 PIO)",
    "rp2350": "DVI output requires displayif picodvi cmod (rp2350 HSTX)",
}

RGBFB_MP_PORT_MSG = {
    "esp32": "Parallel RGB scanout requires displayif rgbframebuffer cmod (esp32 port)",
    "mimxrt1062": "Parallel RGB scanout requires displayif rgbframebuffer cmod (mimxrt eLCDIF)",
}


def _package_json_fbdisplay(
    manifest: dict,
    *,
    cp: bool,
    include_module: str | None = None,
    include_default: bool = True,
) -> dict:
    slug = manifest["slug"]
    out = manifest.get("out", "fbdisplay")
    prefix = f"cp_{slug}" if cp else slug
    path = f"board_configs/{out}/{prefix}/board_config.py"
    urls = [["board_config.py", f"{GITHUB}/{path}"]]
    pkg = manifest.get("package", {})
    if touch_drv := pkg.get("touch_driver"):
        urls.append([f"{touch_drv}.py", f"{GITHUB}/drivers/touch/{touch_drv}.py"])
    for extra in pkg.get("urls_mp" if not cp else "urls_cp", []):
        urls.append([extra["name"], extra["url"]])
    deps = [[PACKAGE_URLS["displaysys"], "main"]]
    if (
        include_module
        and not cp
        and pkg.get(f"include_{include_module}", include_default)
        and include_module in PACKAGE_URLS
    ):
        deps.append([PACKAGE_URLS[include_module], "main"])
    for name in pkg.get("deps_mp" if not cp else "deps_cp", []):
        if name in PACKAGE_URLS:
            deps.append([PACKAGE_URLS[name], "main"])
    result = {"urls": urls, "deps": deps, "version": "0.1"}
    if notes := pkg.get("notes_cp" if cp else "notes_mp"):
        result["notes"] = notes
    return result


def _fb_pin_literal(value, *, cp: bool, pin_wrap: bool = True) -> str:
    if cp:
        return str(value)
    if isinstance(value, int) and not pin_wrap:
        return str(value)
    if isinstance(value, int):
        return f"Pin({value})"
    if isinstance(value, str):
        if value.startswith("Pin(") or value.startswith("board."):
            return value
        if value.startswith("GPIO_"):
            return repr(value) if cp else f'Pin("{value}")'
        if value.isidentifier() and value.isupper():
            return value
    return _py_literal(value)


def _fb_pin_seq_literal(values, *, cp: bool, pin_wrap: bool = True, as_list: bool = False) -> str:
    inner = ", ".join(_fb_pin_literal(v, cp=cp, pin_wrap=pin_wrap) for v in values)
    if as_list:
        return f"[{inner}]"
    return f"({inner})"


def _dict_assign(name: str, mapping: dict, *, cp: bool, pin_wrap: bool = True) -> str:
    lines = [f"{name} = {{"]
    for key, value in mapping.items():
        if key in ("red", "green", "blue", "data") and isinstance(value, list):
            lit = _fb_pin_seq_literal(value, cp=cp, pin_wrap=pin_wrap)
        elif key in (
            "de",
            "vsync",
            "hsync",
            "dclk",
            "clock_pin",
            "latch_pin",
            "output_enable_pin",
        ):
            lit = _fb_pin_literal(value, cp=cp, pin_wrap=pin_wrap)
        elif key in ("rgb_pins", "addr_pins") and isinstance(value, list):
            lit = _fb_pin_seq_literal(value, cp=cp, pin_wrap=pin_wrap, as_list=cp)
        else:
            lit = _display_value_literal(value)
        lines.append(f'    "{key}": {lit},')
    lines.append("}")
    return "\n".join(lines)


def _picodvi_pin_kwargs(pins: dict, *, cp: bool) -> str:
    lines = []
    for key in (
        "clk_dp",
        "clk_dn",
        "red_dp",
        "red_dn",
        "green_dp",
        "green_dn",
        "blue_dp",
        "blue_dn",
    ):
        lines.append(f"    {key}={_fb_pin_literal(pins[key], cp=cp)},")
    return "\n".join(lines)


def emit_fbdisplay_picodvi_mp(manifest: dict) -> str:
    fb = manifest["fb"]
    pins = manifest["pins"]["mp"]
    title = manifest.get("title", manifest["slug"])
    port = manifest.get("port", "rp2040")
    port_msg = PICODVI_MP_PORT_MSG.get(port, PICODVI_MP_PORT_MSG["rp2040"])
    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    fb_kwargs = "\n".join(f"    {key}={_py_literal(value)}," for key, value in fb.items())
    return f'''"""{title}"""

from machine import Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from picodvi import Framebuffer
except ImportError as exc:
    raise NotImplementedError("{port_msg}") from exc

{preamble}fb = Framebuffer(
{fb_kwargs}
{_picodvi_pin_kwargs(pins, cp=False)}
)

display_drv = FBDisplay(fb)

runtime = None
'''


def emit_fbdisplay_picodvi_cp(manifest: dict) -> str:
    fb = manifest["fb"]
    pins = manifest["pins"]["cp"]
    title = manifest.get("title_cp", f"{manifest.get('title', manifest['slug'])} — CircuitPython")
    preamble = manifest.get("cp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    fb_kwargs = "\n".join(f"    {key}={_py_literal(value)}," for key, value in fb.items())
    return f'''"""{title}"""

import board
import displayio
import picodvi

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

{preamble}fb = picodvi.Framebuffer(
{fb_kwargs}
{_picodvi_pin_kwargs(pins, cp=True)}
)

display_drv = FBDisplay(fb)

runtime = None
'''


def package_json_fbdisplay_picodvi(manifest: dict, *, cp: bool) -> dict:
    return _package_json_fbdisplay(manifest, cp=cp, include_module="picodvi")


def _rgbmatrix_kwargs(matrix: dict, *, cp: bool) -> str:
    pin_keys = {"rgb_pins", "addr_pins", "clock_pin", "latch_pin", "output_enable_pin"}
    lines = []
    for key, value in matrix.items():
        if key in pin_keys:
            if isinstance(value, list):
                lines.append(
                    f"    {key}={_fb_pin_seq_literal(value, cp=cp, pin_wrap=not cp, as_list=cp)},"
                )
            else:
                lines.append(f"    {key}={_fb_pin_literal(value, cp=cp, pin_wrap=not cp)},")
        else:
            lines.append(f"    {key}={_display_value_literal(value)},")
    return "\n".join(lines)


def _fbdisplay_wrap_expr(manifest: dict, fb_name: str = "matrix") -> str:
    matrix = manifest.get("matrix", manifest.get("fb", {}))
    fb = manifest.get("fbdisplay", {})
    width = fb.get("width", matrix.get("width"))
    height = fb.get("height", matrix.get("height"))
    if width and height:
        return f"display_drv = FBDisplay({fb_name}, width={width}, height={height})\n"
    return f"display_drv = FBDisplay({fb_name})\n"


def _matrix_config(manifest: dict, *, cp: bool) -> dict:
    matrix = dict(manifest.get("matrix", {}))
    if cp:
        matrix.update(matrix.pop("cp", {}))
    else:
        matrix.pop("cp", None)
    return matrix


def emit_fbdisplay_rgbmatrix_mp(manifest: dict) -> str:
    matrix = _matrix_config(manifest, cp=False)
    title = manifest.get("title", manifest["slug"])
    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    kwargs = _rgbmatrix_kwargs(matrix, cp=False)
    imports = ["import rgbmatrix", "from displaysys.fbdisplay import FBDisplay", "import eventsys"]
    if "Pin(" in kwargs:
        imports.insert(0, "from machine import Pin")
    return f'''"""{title}"""

{chr(10).join(imports)}

{preamble}matrix = rgbmatrix.RGBMatrix(
{kwargs}
)

{_fbdisplay_wrap_expr(manifest)}
runtime = None
'''


def emit_fbdisplay_rgbmatrix_cp(manifest: dict) -> str:
    matrix = _matrix_config(manifest, cp=True)
    title = manifest.get("title_cp", f"{manifest.get('title', manifest['slug'])} — CircuitPython")
    preamble = manifest.get("cp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    if manifest.get("cp_matrix_alias"):
        tail = f"fb = matrix\n\n{_fbdisplay_wrap_expr(manifest, fb_name='fb')}"
    else:
        tail = _fbdisplay_wrap_expr(manifest)
    return f'''"""{title}"""

import board
import displayio
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

{preamble}matrix = rgbmatrix.RGBMatrix(
{_rgbmatrix_kwargs(matrix, cp=True)}
)

{tail}runtime = None
'''


def package_json_fbdisplay_rgbmatrix(manifest: dict, *, cp: bool) -> dict:
    return _package_json_fbdisplay(
        manifest, cp=cp, include_module="rgbmatrix", include_default=False
    )


def _rgbfb_timing_keys() -> tuple[str, ...]:
    return (
        "frequency",
        "width",
        "height",
        "hsync_pulse_width",
        "hsync_front_porch",
        "hsync_back_porch",
        "vsync_pulse_width",
        "vsync_front_porch",
        "vsync_back_porch",
        "hsync_idle_low",
        "vsync_idle_low",
        "de_idle_high",
        "pclk_active_high",
        "pclk_idle_high",
        "overscan_left",
    )


def _mp_rgbfb_reset_block(manifest: dict) -> str:
    if not manifest.get("mp_lcd_reset_pulse"):
        return ""
    pins = manifest.get("pins", {}).get("mp", {})
    reset = pins.get("LCD_RESET", "LCD_RESET")
    return f"""{reset}.value(0)
time.sleep_ms(10)
{reset}.value(1)
time.sleep_ms(120)

"""


def emit_fbdisplay_rgbframebuffer_mp(manifest: dict) -> str:
    pin_wrap = manifest.get("mp_pin_wrap", manifest.get("port") == "mimxrt1062")
    pins_name = manifest.get("tft_pins_var", "tft_pins")
    timings_name = manifest.get("tft_timings_var", "tft_timings")
    tft_pins_raw = manifest.get("tft_pins", {})
    tft_pins = tft_pins_raw.get("mp", tft_pins_raw)
    tft_timings = manifest["tft_timings"]
    title = manifest.get("title", manifest["slug"])
    port = manifest.get("port", "esp32")
    port_msg = RGBFB_MP_PORT_MSG.get(port, RGBFB_MP_PORT_MSG["esp32"])
    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    preamble_after = manifest.get("mp_preamble_after", "")
    if preamble_after and not preamble_after.endswith("\n"):
        preamble_after += "\n"
    post_fb = manifest.get("mp_post_fb", "")
    if post_fb and not post_fb.endswith("\n"):
        post_fb += "\n"

    imports = ["from displaysys.fbdisplay import FBDisplay", "import eventsys"]
    for extra in manifest.get("mp_imports", []):
        imports.insert(0, extra)
    needs_machine = (
        manifest.get("mp_lcd_reset_pulse")
        or manifest.get("touch")
        or pin_wrap
        or preamble
        or preamble_after
    )
    if (
        needs_machine
        and "from machine import I2C, Pin" not in imports
        and "from machine import Pin" not in imports
    ):
        if manifest.get("touch") or "I2C(" in preamble or "I2C(" in preamble_after:
            imports.insert(0, "from machine import I2C, Pin")
        else:
            imports.insert(0, "from machine import Pin")
    if manifest.get("mp_lcd_reset_pulse") and "import time" not in imports:
        imports.insert(0, "import time")
    if touch := manifest.get("touch"):
        touch_import = f"from {touch['module']} import {touch['class']}"
        if touch_import not in imports:
            imports.insert(0, touch_import)

    pin_constants = ""
    if mp_pins := manifest.get("pins", {}).get("mp"):
        pin_constants = _mp_pin_constants(mp_pins)

    pins_dict = _dict_assign(pins_name, tft_pins, cp=False, pin_wrap=pin_wrap)
    timings_dict = _dict_assign(timings_name, tft_timings, cp=False, pin_wrap=False)
    reset_block = _mp_rgbfb_reset_block(manifest)

    after_fb = ""
    runtime_tail = "display_drv = FBDisplay(fb)\n\nruntime = None\n"
    if manifest.get("touch"):
        after_fb = "display_drv = FBDisplay(fb)\n\n" + _post_display_block(manifest, cp=False)
        runtime_tail = ""

    return f'''"""{title}"""

{chr(10).join(imports)}

try:
    from rgbframebuffer import RGBFrameBuffer
except ImportError as exc:
    raise NotImplementedError("{port_msg}") from exc

{preamble}{pin_constants}{reset_block}{pins_dict}

{timings_dict}

{preamble_after}fb = RGBFrameBuffer(**{pins_name}, **{timings_name})

{post_fb}{runtime_tail}{after_fb}'''


def emit_fbdisplay_rgbframebuffer_cp(manifest: dict) -> str:
    title = manifest.get("title_cp", f"{manifest.get('title', manifest['slug'])} — CircuitPython")
    preamble = manifest.get("cp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    cp_module = manifest.get("cp_module", "dotclockframebuffer")
    cp_class = manifest.get("cp_class", "DotClockFramebuffer")
    use_native = manifest.get("cp_native_rgbframebuffer", False)

    imports = [
        "import board",
        "import displayio",
        "from displaysys.fbdisplay import FBDisplay",
        "import eventsys",
    ]
    if manifest.get("cp_framebuffer_display"):
        imports.insert(3, "import framebufferio")
    if use_native:
        imports.insert(3, "import rgbframebuffer")
    else:
        imports.insert(3, f"import {cp_module}")
    if manifest.get("cp_lcd_reset_pulse") or manifest.get("touch", {}).get("cp", {}).get(
        "reset_pin"
    ):
        imports.insert(0, "import time")
        imports.insert(4, "import digitalio")
    if touch := manifest.get("touch"):
        cp_touch = touch.get("cp", {})
        if cp_touch.get("driver") == "gt911":
            imports.insert(5, "import busio")
            imports.insert(5, "import gt911")
        elif cp_touch.get("driver") == "focaltouch":
            imports.insert(5, "from adafruit_focaltouch import Adafruit_FocalTouch")

    tft_timings = manifest["tft_timings"]
    display_block = ""
    setup_prefix = preamble
    if use_native:
        cp_pins = manifest.get("tft_pins", {}).get("cp", manifest.get("cp_tft_pins"))
        timing_lines = [
            f"    {key}={_display_value_literal(value)}," for key, value in tft_timings.items()
        ]
        if isinstance(cp_pins, str):
            display_block = (
                f"fb = rgbframebuffer.RGBFrameBuffer(\n    **{cp_pins},\n"
                + "\n".join(timing_lines)
                + "\n)\n\n"
            )
        else:
            pin_lines = []
            for key, value in cp_pins.items():
                if key in ("red", "green", "blue", "data") and isinstance(value, list):
                    lit = _fb_pin_seq_literal(value, cp=True, as_list=False)
                else:
                    lit = _fb_pin_literal(value, cp=True)
                pin_lines.append(f"    {key}={lit},")
            display_block = (
                "fb = rgbframebuffer.RGBFrameBuffer(\n"
                + "\n".join(pin_lines + timing_lines)
                + "\n)\n\n"
            )
    else:
        pins_name = manifest.get("tft_pins_var", "tft_pins")
        cp_pins = manifest.get("tft_pins", {}).get("cp")
        if cp_pins_expr := manifest.get("cp_tft_pins_expr"):
            pins_dict = f"{pins_name} = {cp_pins_expr}\n\n"
        elif cp_pins:
            pins_dict = _dict_assign(pins_name, cp_pins, cp=True) + "\n\n"
        else:
            pins_dict = f"{pins_name} = dict(board.TFT_PINS)\n\n"
        timings_name = manifest.get("tft_timings_var", "tft_timings")
        timings_dict = _dict_assign(timings_name, tft_timings, cp=True) + "\n\n"
        setup_prefix = f"{pins_dict}{timings_dict}{preamble}"
        display_block = f"fb = {cp_module}.{cp_class}(**{pins_name}, **{timings_name})\n\n"

    for extra in manifest.get("cp_imports", []):
        if extra not in imports:
            imports.insert(3, extra)

    fb_disp_block = ""
    if manifest.get("cp_framebuffer_display"):
        fb_disp_block = """display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)
display.root_group = None

"""

    runtime_tail = "display_drv = FBDisplay(fb)\n\nruntime = None\n"
    touch_block = ""
    if touch := manifest.get("touch"):
        if touch.get("cp", {}).get("driver") == "gt911":
            touch_setup = _cp_mipidsi_gt911_touch(touch)
        else:
            touch_setup = _post_display_block(manifest, cp=True)
        touch_block = "display_drv = FBDisplay(fb)\n\n" + touch_setup
        runtime_tail = ""

    return f'''"""{title}"""

{chr(10).join(imports)}

{setup_prefix}displayio.release_displays()

{display_block}{fb_disp_block}{runtime_tail}{touch_block}'''


def package_json_fbdisplay_rgbframebuffer(manifest: dict, *, cp: bool) -> dict:
    return _package_json_fbdisplay(manifest, cp=cp, include_module="rgbframebuffer")


def emit_busdisplay_spi_mp(manifest: dict) -> str:
    display = manifest["display"]
    cls = display["class"]
    bus = manifest["bus"]["mp"]["spi"]
    title = manifest.get("title", manifest["slug"])

    imports = _collect_mp_imports(manifest, bus_import="from spibus import SPIBus")

    preamble = manifest.get("mp_preamble", "")
    if manifest.get("mp_gc_collect"):
        preamble = (preamble + "\n\n" if preamble else "") + "gc.collect()\n"

    cp_line = _cp_mirror_line(display)
    post_display = _mp_gc_snippet(manifest) if manifest.get("mp_gc_collect") else ""
    tail_gc = "gc.collect()\n" if manifest.get("mp_gc_collect") and "touch" in manifest else ""
    after_display = _post_display_block(manifest, cp=False)

    return f'''"""{title}"""

{chr(10).join(imports)}

{preamble}
{_mp_spi_bus(bus)}

{post_display}display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}{cp_line})
{post_display}{after_display}{tail_gc}'''


def emit_busdisplay_spi_cp(manifest: dict) -> str:
    base_display = manifest["display"]
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

    slug = manifest["slug"]
    title = manifest.get(
        "title_cp",
        f"{manifest.get('title', slug)} — CircuitPython",
    )
    imports = _collect_cp_imports(manifest)
    after_display = _post_display_block(manifest, cp=True)

    return f'''"""{title}"""

{chr(10).join(imports)}

release_displays()

{bus_setup}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}
)
{after_display}'''


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
    cls = display["class"]
    bus = manifest["bus"]["mp"]["i80"]
    title = manifest.get("title", manifest["slug"])

    imports = _collect_mp_imports(manifest, bus_import="from i80bus import I80Bus")

    preamble = manifest.get("mp_preamble", "")
    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    after_display = _post_display_block(manifest, cp=False)

    return f'''"""{title}"""

{chr(10).join(imports)}

{preamble}{_mp_i80_bus(bus)}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)})
{after_display}'''


def emit_busdisplay_i80_cp(manifest: dict) -> str:
    base_display = manifest["display"]
    cls = base_display["class"]
    if "cp" in base_display:
        display = dict(base_display["cp"])
        for key in ("width", "height"):
            if key not in display and key in base_display:
                display[key] = base_display[key]
    else:
        display = {k: v for k, v in base_display.items() if k not in ("module", "class", "cp")}

    pins = manifest["bus"]["cp"]["parallel"]["pins"]
    title = manifest.get(
        "title_cp",
        f"{manifest.get('title', manifest['slug'])} — CircuitPython",
    )
    imports = _collect_cp_imports(manifest)
    after_display = _post_display_block(manifest, cp=True)

    return f'''"""{title}"""

{chr(10).join(imports)}

release_displays()

{_cp_parallel_bus(pins)}

display_drv = {cls}(
    display_bus,
{_display_kwargs(display)}
)
{after_display}'''


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
        driver = manifest["touch"].get("cp", {}).get("driver")
        if not driver:
            driver = {
                "xpt2046": "touchscreen",
                "stmpe610": "stmpe610",
            }.get(_touch_type(manifest["touch"]), "focaltouch")
        name, url = CP_TOUCH_URLS.get(driver, CP_TOUCH_URLS["focaltouch"])
        urls.append([name, url])
    input_cfg = manifest.get("input") or {}
    if not cp:
        if input_cfg.get("encoder"):
            urls.extend(
                [
                    ["rotary.py", "github:miketeachman/micropython-rotary/rotary.py"],
                    [
                        "rotary_irq_esp.py",
                        "github:miketeachman/micropython-rotary/rotary_irq_esp.py",
                    ],
                ]
            )
        if input_cfg.get("keypad_shift"):
            name, url = INPUT_DRIVER_URLS["keypad_shift"]
            urls.append([name, url])
        if input_cfg.get("joystick"):
            name, url = INPUT_DRIVER_URLS["gpiojoystick"]
            urls.append([name, url])
    elif input_cfg.get("keypad_gpio"):
        name, url = INPUT_DRIVER_URLS["keypad_gpio"]
        urls.append([name, url])
    for extra in pkg.get("urls_cp" if cp else "urls_mp", []):
        urls.append([extra["name"], extra["url"]])
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


def _grid_kwargs(manifest: dict) -> str:
    grid = manifest.get("grid", {})
    parts = []
    for key in (
        "alternating",
        "orientation",
        "reverse_x",
        "reverse_y",
        "top",
        "bottom",
        "rotation",
    ):
        if key in grid:
            parts.append(f"{key}={grid[key]}")
    return ", ".join(parts)


def emit_pixeldisplay_cp(manifest: dict) -> str:
    grid = manifest["grid"]
    strip = manifest["strip"]
    w = grid["width"]
    h = grid["height"]
    grid_args = _grid_kwargs(manifest)
    grid_tail = f", {grid_args}" if grid_args else ""

    if strip == "neopixel":
        cfg = manifest["cp"]["neopixel"]
        pin = cfg["pin"]
        brightness = cfg.get("brightness", 0.1)
        return f'''"""{manifest.get("title", manifest["slug"])} — CircuitPython NeoPixel grid"""

import board
import neopixel

from adafruit_pixel_framebuf import PixelFramebuffer
from displaysys.pixeldisplay import PixelDisplay

pixel_width = {w}
pixel_height = {h}

pixels = neopixel.NeoPixel(
    {pin},
    pixel_width * pixel_height,
    brightness={brightness},
    auto_write=False,
)

_pixel_framebuf = PixelFramebuffer(
    pixels,
    pixel_width,
    pixel_height{grid_tail},
)

display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
'''

    cfg = manifest["cp"]["dotstar"]
    clock = cfg["clock"]
    data = cfg["data"]
    brightness = cfg.get("brightness", 0.3)
    return f'''"""{manifest.get("title", manifest["slug"])} — CircuitPython DotStar grid"""

import adafruit_dotstar
import board

from adafruit_pixel_framebuf import PixelFramebuffer
from displaysys.pixeldisplay import PixelDisplay

pixel_width = {w}
pixel_height = {h}

pixels = adafruit_dotstar.DotStar(
    {clock},
    {data},
    pixel_width * pixel_height,
    brightness={brightness},
    auto_write=False,
)

_pixel_framebuf = PixelFramebuffer(
    pixels,
    pixel_width,
    pixel_height{grid_tail},
)

display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
'''


def emit_pixeldisplay_mp(manifest: dict) -> str:
    grid = manifest["grid"]
    strip = manifest["strip"]
    w = grid["width"]
    h = grid["height"]
    grid_args = _grid_kwargs(manifest)
    grid_tail = f", {grid_args}" if grid_args else ""

    if strip == "neopixel":
        cfg = manifest["mp"]["neopixel"]
        pin = cfg["pin"]
        bpp = cfg.get("bpp", 3)
        timing = cfg.get("timing", 1)
        return f'''"""{manifest.get("title", manifest["slug"])} — MicroPython NeoPixel grid"""

from machine import Pin
import neopixel

from displaysys.pixeldisplay import PixelFramebuffer, PixelDisplay

pixel_width = {w}
pixel_height = {h}

pixels = neopixel.NeoPixel(Pin({pin}), pixel_width * pixel_height, bpp={bpp}, timing={timing})

_pixel_framebuf = PixelFramebuffer(pixels, pixel_width, pixel_height{grid_tail})
display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
'''

    cfg = manifest["mp"]["dotstar"]
    clock = cfg["clock"]
    data = cfg["data"]
    bpp = cfg.get("bpp", 3)
    return f'''"""{manifest.get("title", manifest["slug"])} — MicroPython DotStar grid"""

from machine import Pin
import dotstar

from displaysys.pixeldisplay import PixelFramebuffer, PixelDisplay

pixel_width = {w}
pixel_height = {h}

pixels = dotstar.DotStar(Pin({clock}), Pin({data}), pixel_width * pixel_height, bpp={bpp})

_pixel_framebuf = PixelFramebuffer(pixels, pixel_width, pixel_height{grid_tail})
display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
'''


def package_json_pixeldisplay(manifest: dict, *, cp: bool) -> dict:
    slug = manifest["slug"]
    out = manifest.get("out", "pixeldisplay")
    prefix = f"cp_{slug}" if cp else slug
    path = f"board_configs/{out}/{prefix}/board_config.py"
    urls = [["board_config.py", f"{GITHUB}/{path}"]]
    deps = [
        [PACKAGE_URLS["displaysys"], "main"],
        [PACKAGE_URLS["pixeldisplay"], "main"],
    ]
    if not cp:
        deps.append([PACKAGE_URLS["graphics"], "main"])
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

    elif kind == "fbdisplay_mipidsi":
        out_rel = manifest.get("out", "fbdisplay")
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_fbdisplay_mipidsi_mp(manifest)
        mp_pkg = json.dumps(package_json_fbdisplay_mipidsi(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_fbdisplay_mipidsi_cp(manifest)
            cp_pkg = json.dumps(package_json_fbdisplay_mipidsi(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "fbdisplay_picodvi":
        out_rel = manifest.get("out", "fbdisplay")
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_fbdisplay_picodvi_mp(manifest)
        mp_pkg = json.dumps(package_json_fbdisplay_picodvi(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_fbdisplay_picodvi_cp(manifest)
            cp_pkg = json.dumps(package_json_fbdisplay_picodvi(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "fbdisplay_rgbmatrix":
        out_rel = manifest.get("out", "fbdisplay")
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_fbdisplay_rgbmatrix_mp(manifest)
        mp_pkg = json.dumps(package_json_fbdisplay_rgbmatrix(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_fbdisplay_rgbmatrix_cp(manifest)
            cp_pkg = (
                json.dumps(package_json_fbdisplay_rgbmatrix(manifest, cp=True), indent=2) + "\n"
            )
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "fbdisplay_rgbframebuffer":
        out_rel = manifest.get("out", "fbdisplay")
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_fbdisplay_rgbframebuffer_mp(manifest)
        mp_pkg = (
            json.dumps(package_json_fbdisplay_rgbframebuffer(manifest, cp=False), indent=2) + "\n"
        )
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython"):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_fbdisplay_rgbframebuffer_cp(manifest)
            cp_pkg = (
                json.dumps(package_json_fbdisplay_rgbframebuffer(manifest, cp=True), indent=2)
                + "\n"
            )
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    elif kind == "pixeldisplay":
        out_rel = manifest.get("out", "pixeldisplay")
        mp_dir = BOARD_ROOT / out_rel / slug
        mp_py = emit_pixeldisplay_mp(manifest)
        mp_pkg = json.dumps(package_json_pixeldisplay(manifest, cp=False), indent=2) + "\n"
        errors.extend(_write_pair(mp_dir, mp_py, mp_pkg, check=check))
        if manifest.get("circuitpython", True):
            cp_dir = BOARD_ROOT / out_rel / f"cp_{slug}"
            cp_py = emit_pixeldisplay_cp(manifest)
            cp_pkg = json.dumps(package_json_pixeldisplay(manifest, cp=True), indent=2) + "\n"
            errors.extend(_write_pair(cp_dir, cp_py, cp_pkg, check=check))

    else:
        errors.append(f"{slug}: unknown kind {kind!r}")
    return errors


def _write_pair(directory: Path, board_py: str, package: str, *, check: bool) -> list[str]:
    errors: list[str] = []
    rel_bc = directory.relative_to(ROOT) / "board_config.py"
    board_py = _ruff_format_board_config(board_py, rel_path=rel_bc)
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


def install_hand_maintained(*, check: bool) -> list[str]:
    errors: list[str] = []
    for src_config in sorted(HAND_MAINTAINED_ROOT.rglob("board_config.py")):
        rel_dir = src_config.parent.relative_to(HAND_MAINTAINED_ROOT)
        dest_dir = BOARD_ROOT / rel_dir
        for name in ALLOWED_BOARD_FILES:
            src = src_config.parent / name
            if not src.is_file():
                continue
            content = src.read_text(encoding="utf-8")
            dest = dest_dir / name
            if check:
                if not dest.exists():
                    errors.append(f"missing {dest.relative_to(ROOT)}")
                elif dest.read_text(encoding="utf-8") != content:
                    errors.append(f"drift {dest.relative_to(ROOT)}")
            else:
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
        if not check:
            print(f"wrote {dest_dir.relative_to(ROOT)}")
    return errors


def check_board_root_clean() -> list[str]:
    errors: list[str] = []
    if not BOARD_ROOT.is_dir():
        return errors
    for path in sorted(BOARD_ROOT.rglob("*")):
        if path.is_dir():
            if path.name == "__pycache__":
                errors.append(f"stray directory {path.relative_to(ROOT)}")
            continue
        if path.name not in ALLOWED_BOARD_FILES:
            errors.append(f"stray file {path.relative_to(ROOT)}")
    return errors


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
        help="filter by manifest kind (busdisplay_spi, busdisplay_i2c, busdisplay_i80, busdisplay_verbatim, fbdisplay_mipidsi, fbdisplay_picodvi, fbdisplay_rgbmatrix, fbdisplay_rgbframebuffer, epaper, pixeldisplay)",
    )
    parser.add_argument(
        "--hand-maintained-only",
        action="store_true",
        help="install hand-maintained board configs without regenerating manifests",
    )
    args = parser.parse_args()

    errors: list[str] = []
    manifest_count = 0

    if args.hand_maintained_only:
        if args.only or args.kind:
            print(
                "--hand-maintained-only cannot be combined with --only or --kind", file=sys.stderr
            )
            return 1
        errors.extend(install_hand_maintained(check=args.check))
    else:
        manifests = load_manifests(args.only, kind=args.kind)
        if args.only and not manifests:
            print(f"No manifest for slug {args.only!r}", file=sys.stderr)
            return 1
        manifest_count = len(manifests)
        for manifest in manifests:
            errors.extend(write_outputs(manifest, check=args.check))
        errors.extend(install_hand_maintained(check=args.check))

    if args.check:
        errors.extend(check_board_root_clean())

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    if args.check and not args.hand_maintained_only:
        print(f"OK ({manifest_count} manifest(s))")
    elif args.check:
        print("OK (hand-maintained)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
