#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Audit MicroPython / CircuitPython board_config sibling pairs."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BOARD_ROOT = ROOT / "board_configs"


def _pairs(root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for mp_config in sorted(root.rglob("board_config.py")):
        mp_dir = mp_config.parent
        if mp_dir.name.startswith("cp_"):
            continue
        cp_dir = mp_dir.parent / f"cp_{mp_dir.name}"
        cp_config = cp_dir / "board_config.py"
        if cp_config.is_file():
            pairs.append((mp_config, cp_config))
    return pairs


def _has_broker(text: str) -> bool:
    return bool(re.search(r"\bbroker\s*=|eventsys\.Broker|broker\.create", text))


def _has_runtime(text: str) -> bool:
    return "runtime" in text


def _touch_kind(text: str) -> str:
    if "touch_read_func" in text or "touch_read=" in text:
        return "touch"
    if "add_keypad" in text:
        return "keypad"
    return "none"


def _epaper_dims(text: str) -> tuple[int, int, int] | None:
    m = re.search(
        r"EPaperDisplay\([^)]*width=(\d+),\s*height=(\d+),\s*color_depth=(\d+)",
        text,
    )
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def _display_dims(text: str) -> tuple[int | None, int | None, int | None]:
    dims = _epaper_dims(text)
    if dims:
        return dims[0], dims[1], dims[2]
    width = re.search(r"\bwidth=(\d+)", text)
    height = re.search(r"\bheight=(\d+)", text)
    depth = re.search(r"\bcolor_depth=(\d+)", text)
    return (
        int(width.group(1)) if width else None,
        int(height.group(1)) if height else None,
        int(depth.group(1)) if depth else None,
    )


def _dims_issues(rel: Path, mp_dims, cp_dims) -> list[str]:
    issues: list[str] = []
    mp_w, mp_h, mp_d = mp_dims
    cp_w, cp_h, cp_d = cp_dims
    if mp_w is None and cp_w is None:
        return issues
    if mp_w is None or cp_w is None:
        issues.append(f"{rel}: missing width on {'MP' if mp_w is None else 'CP'}")
    elif mp_w != cp_w:
        issues.append(f"{rel}: width mismatch MP={mp_w} CP={cp_w}")
    if mp_h is None and cp_h is None:
        pass
    elif mp_h is None or cp_h is None:
        issues.append(f"{rel}: missing height on {'MP' if mp_h is None else 'CP'}")
    elif mp_h != cp_h:
        issues.append(f"{rel}: height mismatch MP={mp_h} CP={cp_h}")
    if mp_d is not None and cp_d is not None and mp_d != cp_d:
        issues.append(f"{rel}: color_depth mismatch MP={mp_d} CP={cp_d}")
    return issues


def audit_pair(mp_path: Path, cp_path: Path) -> list[str]:
    issues: list[str] = []
    rel = mp_path.parent.relative_to(BOARD_ROOT)
    mp_text = mp_path.read_text(encoding="utf-8")
    cp_text = cp_path.read_text(encoding="utf-8")

    for label, text in (("MP", mp_text), ("CP", cp_text)):
        if _has_broker(text):
            issues.append(f"{rel}: {label} still uses Broker API")
        if not _has_runtime(text):
            issues.append(f"{rel}: {label} missing runtime export")

    mp_touch = _touch_kind(mp_text)
    cp_touch = _touch_kind(cp_text)
    if mp_touch != cp_touch:
        issues.append(f"{rel}: input mismatch (MP={mp_touch}, CP={cp_touch})")

    mp_dims = _display_dims(mp_text)
    cp_dims = _display_dims(cp_text)
    issues.extend(_dims_issues(rel, mp_dims, cp_dims))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="board_configs subtree to scan (default: busdisplay, epaperdisplay, fbdisplay)",
    )
    args = parser.parse_args()
    roots = [
        BOARD_ROOT / name for name in (args.root or ["busdisplay", "epaperdisplay", "fbdisplay"])
    ]

    all_issues: list[str] = []
    pair_count = 0
    for root in roots:
        if not root.is_dir():
            continue
        for mp_path, cp_path in _pairs(root):
            pair_count += 1
            all_issues.extend(audit_pair(mp_path, cp_path))

    if all_issues:
        for issue in all_issues:
            print(issue, file=sys.stderr)
        print(f"\n{len(all_issues)} issue(s) in {pair_count} pair(s)", file=sys.stderr)
        return 1

    print(f"OK ({pair_count} CP/MP pair(s) audited)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
