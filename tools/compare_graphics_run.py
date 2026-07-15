#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Subprocess entry point for one graphics cmod vs python parity run."""

import sys


def _dir_of(file: str) -> str:
    p = file.replace("\\", "/")
    i = p.rfind("/")
    return p[:i] if i >= 0 else "."


_TOOLS = _dir_of(__file__)
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

from compare_graphics import main  # noqa: E402

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
