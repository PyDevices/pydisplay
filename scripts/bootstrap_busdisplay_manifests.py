#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Bootstrap busdisplay TOML manifests from existing board_config.py files.

Creates ``kind = "busdisplay_verbatim"`` manifests so ``generate_board_configs.py
--check`` guards against drift. Skips slugs that already have a manifest unless
``--force`` is passed. Structured manifests (``busdisplay_spi``) are left alone.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BOARD_ROOT = ROOT / "board_configs" / "busdisplay"
MANIFEST_ROOT = ROOT / "board_configs" / "manifests" / "busdisplay"


def _toml_string(value: str) -> str:
    if '"""' not in value:
        return f'"""\n{value}"""'
    if "'''" not in value:
        return f"'''\n{value}'''"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _docstring_title(text: str) -> str | None:
    m = re.match(r'^[\s\S]*?"""([^"]+)"""', text)
    if m:
        return m.group(1).split("\n")[0].strip()
    m = re.match(r"^[\s\S]*?'''([^']+)'''", text)
    if m:
        return m.group(1).split("\n")[0].strip()
    return None


def _read_pair(directory: Path) -> tuple[str, str] | None:
    bc = directory / "board_config.py"
    pj = directory / "package.json"
    if not bc.is_file() or not pj.is_file():
        return None
    return bc.read_text(encoding="utf-8"), pj.read_text(encoding="utf-8")


def _emit_manifest(
    *,
    slug: str,
    bus: str,
    mp: tuple[str, str],
    cp: tuple[str, str] | None,
    title: str | None,
) -> str:
    lines = [
        "# Bootstrapped from board_configs — edit here; run generate_board_configs.py",
        'kind = "busdisplay_verbatim"',
        f"slug = {slug!r}",
        f'out = "busdisplay/{bus}"',
        f"circuitpython = {'true' if cp else 'false'}",
    ]
    if title:
        lines.append(f"title = {title!r}")
    lines.append("")
    lines.append("[verbatim.mp]")
    lines.append(f"board_config = {_toml_string(mp[0])}")
    lines.append(f"package_json = {_toml_string(mp[1])}")
    if cp:
        lines.append("")
        lines.append("[verbatim.cp]")
        lines.append(f"board_config = {_toml_string(cp[0])}")
        lines.append(f"package_json = {_toml_string(cp[1])}")
    return "\n".join(lines) + "\n"


def bootstrap(*, force: bool) -> int:
    created = 0
    skipped = 0
    for bus in ("spi", "i80", "i2c"):
        bus_dir = BOARD_ROOT / bus
        if not bus_dir.is_dir():
            continue
        out_bus = MANIFEST_ROOT / bus
        out_bus.mkdir(parents=True, exist_ok=True)
        for mp_dir in sorted(bus_dir.iterdir()):
            if not mp_dir.is_dir() or mp_dir.name.startswith("cp_"):
                continue
            slug = mp_dir.name
            manifest_path = out_bus / f"{slug}.toml"
            if manifest_path.exists() and not force:
                skipped += 1
                continue
            mp = _read_pair(mp_dir)
            if mp is None:
                print(f"skip {slug}: missing board_config.py or package.json", file=sys.stderr)
                continue
            cp_dir = mp_dir.parent / f"cp_{slug}"
            cp = _read_pair(cp_dir) if cp_dir.is_dir() else None
            title = _docstring_title(mp[0])
            manifest_path.write_text(
                _emit_manifest(slug=slug, bus=bus, mp=mp, cp=cp, title=title),
                encoding="utf-8",
            )
            print(f"wrote {manifest_path.relative_to(ROOT)}")
            created += 1
    print(f"created {created}, skipped {skipped}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite existing manifests")
    args = parser.parse_args()
    return bootstrap(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
