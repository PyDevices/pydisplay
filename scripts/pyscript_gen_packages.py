#!/usr/bin/env python3
"""Deprecated alias — use gallery_generator.py."""

from __future__ import annotations

from pathlib import Path
import sys

print(
    "warning: scripts/pyscript_gen_packages.py is deprecated; use scripts/gallery_generator.py",
    file=sys.stderr,
)
# Avoid importing as package — exec the sibling module as __main__.
target = Path(__file__).resolve().with_name("gallery_generator.py")
sys.argv[0] = str(target)
code = compile(target.read_text(encoding="utf-8"), str(target), "exec")
globs = {"__name__": "__main__", "__file__": str(target)}
exec(code, globs)
