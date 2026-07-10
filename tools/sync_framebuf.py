#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Copy canonical ``src/add_ons/framebuf.py`` into ``graphics/`` for packaging.

``src/add_ons/framebuf.py`` is the only editable source. ``src/lib/graphics/framebuf.py``
is generated (gitignored) so the pydisplay-graphics wheel and standalone ``graphics``
copytree tests stay self-contained without maintaining two copies by hand.

Usage:
    .venv/bin/python tools/sync_framebuf.py          # write copy
    .venv/bin/python tools/sync_framebuf.py --check  # fail if missing or stale
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CANONICAL = _REPO_ROOT / "src" / "add_ons" / "framebuf.py"
_GENERATED = _REPO_ROOT / "src" / "lib" / "graphics" / "framebuf.py"


def sync_framebuf(*, check: bool = False) -> None:
    if not _CANONICAL.is_file():
        raise SystemExit(f"missing canonical framebuf module: {_CANONICAL}")

    canonical = _CANONICAL.read_bytes()

    if check:
        if not _GENERATED.is_file():
            raise SystemExit(
                f"missing {_GENERATED.relative_to(_REPO_ROOT)} — "
                "run: .venv/bin/python tools/sync_framebuf.py"
            )
        if _GENERATED.read_bytes() != canonical:
            raise SystemExit(
                f"{_GENERATED.relative_to(_REPO_ROOT)} is stale — "
                "edit src/add_ons/framebuf.py, then run tools/sync_framebuf.py"
            )
        return

    _GENERATED.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_CANONICAL, _GENERATED)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the generated copy is missing or differs from canonical",
    )
    args = parser.parse_args(argv)
    sync_framebuf(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
