#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Brad Barnett
# SPDX-License-Identifier: MIT
"""Vendor Adafruit CircuitPython display/touch drivers into pydisplay."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISPLAY_DRIVERS = {
    "sh1106": "Adafruit_CircuitPython_DisplayIO_SH1106",
    "sh1107": "Adafruit_CircuitPython_DisplayIO_SH1107",
    "ssd1305": "Adafruit_CircuitPython_DisplayIO_SSD1305",
    "ssd1306": "Adafruit_CircuitPython_DisplayIO_SSD1306",
    "ssd1322": "Adafruit_CircuitPython_SSD1322",
    "ssd1325": "Adafruit_CircuitPython_SSD1325",
    "ssd1327": "Adafruit_CircuitPython_SSD1327",
    "ssd1331": "Adafruit_CircuitPython_SSD1331",
    "ssd1351": "Adafruit_CircuitPython_SSD1351",
    "ssd1680": "Adafruit_CircuitPython_SSD1680",
    "ssd1681": "Adafruit_CircuitPython_SSD1681",
    "ssd1683": "Adafruit_CircuitPython_SSD1683",
    "ssd1675": "Adafruit_CircuitPython_SSD1675",
    "ssd1677": "Adafruit_CircuitPython_SSD1677",
    "ssd1608": "Adafruit_CircuitPython_SSD1608",
    "uc8151d": "Adafruit_CircuitPython_UC8151D",
    "uc8179": "Adafruit_CircuitPython_UC8179",
    "uc8253": "Adafruit_CircuitPython_UC8253",
    "il0373": "Adafruit_CircuitPython_IL0373",
    "il0398": "Adafruit_CircuitPython_IL0398",
    "il91874": "Adafruit_CircuitPython_IL91874",
    "ek79686": "Adafruit_CircuitPython_EK79686",
    "jd79661": "Adafruit_CircuitPython_JD79661",
    "jd79667": "Adafruit_CircuitPython_JD79667",
    "spd1656": "Adafruit_CircuitPython_SPD1656",
    "acep7in": "Adafruit_CircuitPython_ACeP7In",
    "ra8875": "Adafruit_CircuitPython_RA8875",
    "pcd8544": "Adafruit_CircuitPython_PCD8544",
}

TOUCH_DRIVERS = {
    "ft5336": "Adafruit_CircuitPython_FT5336",
    "tsc2007": "Adafruit_CircuitPython_TSC2007",
    "tt21100": "Adafruit_CircuitPython_TT21100",
    "stmpe610": "Adafruit_CircuitPython_STMPE610",
    "touchscreen": "Adafruit_CircuitPython_Touchscreen",
}

COMMUNITY_DISPLAY = {
    "community/st7565": ("mateusznowakdev/CircuitPython_DisplayIO_ST7565", "displayio_st7565.py"),
}

BUSDISPLAY_IMPORT = """try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay
"""

EPAPER_IMPORT = """try:
    from displaysys.epaperdisplay import EPaperDisplay as _EPaperDisplayBase
except ImportError:
    try:
        from epaperdisplay import EPaperDisplay as _EPaperDisplayBase
    except ImportError:
        _EPaperDisplayBase = object
"""


def clone_repo(repo: str, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/adafruit/{repo}.git", str(dest)],
        check=True,
        capture_output=True,
    )


def clone_repo_url(url: str, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/{url}.git", str(dest)],
        check=True,
        capture_output=True,
    )


def find_module_py(repo_dir: Path, stem: str) -> Path:
    for path in repo_dir.glob("adafruit_*.py"):
        return path
    pkg = repo_dir / f"adafruit_{stem}"
    if pkg.is_dir():
        candidate = pkg / f"{stem}.py"
        if candidate.exists():
            return candidate
    matches = list(repo_dir.glob(f"*{stem}*.py"))
    if not matches:
        raise FileNotFoundError(f"No module in {repo_dir} for {stem}")
    return matches[0]


def patch_busdisplay(content: str) -> str:
    content = re.sub(r"^from busdisplay import BusDisplay\s*$", "", content, flags=re.M)
    content = re.sub(
        r"^try:\s*\n\s*from displaysys\.busdisplay import BusDisplay.*?\nexcept ImportError:.*?\n\s*from busdisplay import BusDisplay\s*\n",
        "",
        content,
        flags=re.M | re.S,
    )
    if "from displaysys.busdisplay import BusDisplay" not in content:
        content = BUSDISPLAY_IMPORT + "\n" + content
    content = re.sub(r"^__version__ = .*$", "", content, flags=re.M)
    content = re.sub(r"^__repo__ = .*$", "", content, flags=re.M)
    return content


EPAPER_IMPORT = """try:
    import digitalio
except ImportError:
    pass
try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from epaperdisplay_chip import EPaperDisplay
"""


def patch_epaper(content: str) -> str:
    content = re.sub(r"^import digitalio\s*$", "", content, flags=re.M)
    content = re.sub(r"^import epaperdisplay\s*$", "", content, flags=re.M)
    content = re.sub(r"^import displayio\s*$", "", content, flags=re.M)
    content = re.sub(
        r"^try:\s*\n\s*from epaperdisplay import EPaperDisplay.*?\nexcept ImportError:.*?\n(?:\s*from .*?\n)?",
        "",
        content,
        flags=re.M | re.S,
    )
    content = content.replace("epaperdisplay.EPaperDisplay", "EPaperDisplay")
    if "from epaperdisplay_chip import EPaperDisplay" not in content:
        match = re.search(r'^""".*?"""\s*\n', content, flags=re.S | re.M)
        if match:
            pos = match.end()
            content = content[:pos] + "\n" + EPAPER_IMPORT + "\n" + content[pos:]
        else:
            content = EPAPER_IMPORT + "\n" + content
    return content


def vendor_adafruit(name: str, repo: str, out_dir: Path, *, epaper: bool = False) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = Path(tmp) / repo
        clone_repo(repo, repo_dir)
        src = find_module_py(repo_dir, name.replace("_", ""))
        content = src.read_text(encoding="utf-8")
        if epaper or "EPaperDisplay" in content:
            content = patch_epaper(content)
        else:
            content = patch_busdisplay(content)
        dest = out_dir / f"{name}.py"
        dest.write_text(content, encoding="utf-8")
        print(f"vendored {dest.relative_to(ROOT)}")


def vendor_touch(name: str, repo: str, out_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = Path(tmp) / repo
        clone_repo(repo, repo_dir)
        src = find_module_py(repo_dir, name)
        dest = out_dir / "circuitpython" / f"adafruit_{name}.py"
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")
        content = re.sub(r"^__version__ = .*$", "", content, flags=re.M)
        content = re.sub(r"^__repo__ = .*$", "", content, flags=re.M)
        dest.write_text(content, encoding="utf-8")
        print(f"vendored {dest.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--touch", action="store_true")
    parser.add_argument("--community", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    run_all = args.all or not (args.display or args.touch or args.community)

    display_dir = ROOT / "drivers" / "display"
    touch_dir = ROOT / "drivers" / "touch"
    epaper_names = {
        "ssd1680",
        "ssd1681",
        "ssd1683",
        "ssd1675",
        "ssd1677",
        "ssd1608",
        "uc8151d",
        "uc8179",
        "uc8253",
        "il0373",
        "il0398",
        "il91874",
        "ek79686",
        "jd79661",
        "jd79667",
        "spd1656",
        "acep7in",
    }

    if run_all or args.display:
        for name, repo in DISPLAY_DRIVERS.items():
            try:
                vendor_adafruit(name, repo, display_dir, epaper=name in epaper_names)
            except Exception as exc:  # noqa: BLE001
                print(f"skip {name}: {exc}", file=sys.stderr)

    if run_all or args.touch:
        for name, repo in TOUCH_DRIVERS.items():
            try:
                vendor_touch(name, repo, touch_dir)
            except Exception as exc:  # noqa: BLE001
                print(f"skip touch {name}: {exc}", file=sys.stderr)

    if run_all or args.community:
        for out_name, (repo_url, module_file) in COMMUNITY_DISPLAY.items():
            with tempfile.TemporaryDirectory() as tmp:
                repo_dir = Path(tmp) / "repo"
                clone_repo_url(repo_url, repo_dir)
                src = repo_dir / module_file
                content = patch_busdisplay(src.read_text(encoding="utf-8"))
                dest = display_dir / f"{out_name}.py"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"vendored {dest.relative_to(ROOT)}")

    # Promote WIP OLED color drivers if vendored successfully
    for wip in ("ssd1331", "ssd1351"):
        src = display_dir / f"{wip}.py"
        wip_src = display_dir / "work_in_progress" / f"{wip}.py"
        if src.exists() and wip_src.exists():
            wip_src.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
