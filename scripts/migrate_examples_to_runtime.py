#!/usr/bin/env python3
"""Migrate examples and tools from broker to runtime."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "src" / "examples",
    ROOT / "src" / "add_ons",
    ROOT / "tools",
    ROOT / "tests",
]

REPLACEMENTS = [
    (
        re.compile(r"\bfrom board_config import TIMER_ASYNC, broker, display_drv\b"),
        "from board_config import display_drv, runtime",
    ),
    (
        re.compile(r"\bfrom board_config import broker, display_drv\b"),
        "from board_config import display_drv, runtime",
    ),
    (
        re.compile(r"\bfrom board_config import display_drv, broker\b"),
        "from board_config import display_drv, runtime",
    ),
    (re.compile(r"\bfrom board_config import broker\b"), "from board_config import runtime"),
    (re.compile(r"\bimport eventsys\b[\s\S]*?poll_quit_discarding_others"), "import eventsys"),
    (
        re.compile(r"\beventsys\.poll_quit_discarding_others\(runtime\)"),
        "False  # use runtime.quit_requested",
    ),
    (re.compile(r"\bpoll_quit_discarding_others\(runtime\)"), "runtime.quit_requested"),
    (
        re.compile(r"\bpoll_quit_discarding_others\(broker\)"),
        "runtime.quit_requested if runtime else False",
    ),
    (
        re.compile(r"\bwhile not poll_quit_discarding_others\(runtime\):"),
        "while runtime is None or not runtime.quit_requested:",
    ),
    (
        re.compile(r"\bwhile not poll_quit_discarding_others\(broker\):"),
        "while runtime is None or not runtime.quit_requested:",
    ),
    (re.compile(r"\bboard_config\.TIMER_ASYNC\b"), "runtime.timer_async if runtime else False"),
    (re.compile(r"\bTIMER_ASYNC\b"), "runtime.timer_async"),
    (re.compile(r"\bbroker\b"), "runtime"),
    (re.compile(r"\beventsys\.QUEUE\b"), "eventsys.HOST"),
    (re.compile(r"\beventsys\.Broker\b"), "eventsys.Runtime"),
    (re.compile(r"\bQueueDevice\b"), "HostEventsDevice"),
    (re.compile(r"\bregister_quit_cleanup\b"), "before_quit  # removed"),
]


def migrate_file(path: Path) -> bool:
    if path.name == "migrate_examples_to_runtime.py":
        return False
    text = path.read_text(encoding="utf-8")
    original = text
    for pattern, repl in REPLACEMENTS:
        text = pattern.sub(repl, text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for base in TARGETS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if migrate_file(path):
                changed += 1
    print(f"Updated {changed} Python files")


if __name__ == "__main__":
    main()
