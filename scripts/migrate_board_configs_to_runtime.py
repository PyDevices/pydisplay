#!/usr/bin/env python3
"""Migrate board_config.py files from Broker idiom to Runtime."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "board_configs"

TOUCH_BLOCK = re.compile(
    r"""
    broker\s*=\s*eventsys\.Broker\(\)\s*\n+
    (?P<dev>\w+)\s*=\s*broker\.create\(\s*\n
    \s*type=eventsys\.TOUCH,\s*\n
    \s*read=(?P<read>[^,\n]+),\s*\n
    \s*data=display_drv,\s*\n
    \s*data2=(?P<data2>[^,\n]+),\s*\n
    \)\s*\n+
    broker\.register_quit_cleanup\(display_drv\)
    """,
    re.VERBOSE,
)

KEYPAD_BLOCK = re.compile(
    r"""
    broker\s*=\s*eventsys\.Broker\(\)\s*\n+
    (?P<dev>\w+)\s*=\s*broker\.create\(\s*\n
    \s*type=eventsys\.KEYPAD,\s*\n
    \s*read=(?P<read>[^,\n]+),\s*\n
    \)\s*\n+
    broker\.register_quit_cleanup\(display_drv\)
    """,
    re.VERBOSE,
)

JOYSTICK_BLOCK = re.compile(
    r"""
    broker\s*=\s*eventsys\.Broker\(\)\s*\n+
    (?P<dev>\w+)\s*=\s*broker\.create\(\s*\n
    \s*type=eventsys\.JOYSTICK,\s*\n
    (?P<body>.*?)
    \)\s*\n+
    broker\.register_quit_cleanup\(display_drv\)
    """,
    re.VERBOSE | re.DOTALL,
)

HOSTED_BLOCK = re.compile(
    r"broker\s*=\s*eventsys\.Broker\(\)\s*\n+"
    r"events_dev\s*=\s*broker\.create\(\s*\n"
    r"\s*type=eventsys\.QUEUE,\s*\n"
    r"\s*read=(?P<read>[^,\n]+),\s*\n"
    r"\s*data=display_drv,[^\n]*\n"
    r"(?:\s*#[^\n]*\n)*"
    r"\)\s*\n+"
    r"broker\.display_refresh\s*=\s*broker\.on_tick\(display_drv\.show,\s*period=\d+"
    r"(?:,\s*async_=(?P<async>[^\n)]+))?\)\s*\n"
    r"broker\.register_quit_cleanup\(display_drv,\s*after=broker\.stop_timer\)",
    re.MULTILINE,
)

SIMPLE_QUIT = re.compile(
    r"broker\s*=\s*eventsys\.Broker\(\)\s*\n+broker\.register_quit_cleanup\(display_drv\)"
)


def _runtime_touch(read: str, data2: str) -> str:
    read = read.strip()
    data2 = data2.strip()
    if data2 in ("None", "touch_rotation_table"):
        if data2 == "None":
            return (
                f"runtime = eventsys.Runtime(\n    display=display_drv,\n    touch_read={read},\n)"
            )
        return (
            "runtime = eventsys.Runtime(\n"
            "    display=display_drv,\n"
            f"    touch_read={read},\n"
            "    touch_rotation_table=touch_rotation_table,\n"
            ")"
        )
    return (
        "runtime = eventsys.Runtime(\n"
        "    display=display_drv,\n"
        f"    touch_read={read},\n"
        f"    touch_rotation_table={data2},\n"
        ")"
    )


def migrate_text(text: str, path: Path) -> str:
    if "eventsys.Broker" not in text and "broker = None" not in text:
        return text

    text = text.replace("broker = None", "runtime = None")

    m = HOSTED_BLOCK.search(text)
    if m:
        async_kw = ""
        if m.group("async"):
            async_val = m.group("async").strip()
            if async_val not in ("False", "TIMER_ASYNC"):
                async_kw = f",\n    timer_async={async_val}"
            elif async_val == "TIMER_ASYNC":
                async_kw = ",\n    timer_async=True"
        replacement = (
            "runtime = eventsys.Runtime(\n"
            "    display=display_drv,\n"
            f"    host_read={m.group('read').strip()},{async_kw}\n"
            ")"
        )
        text = HOSTED_BLOCK.sub(replacement, text, count=1)
        text = re.sub(r"^TIMER_ASYNC\s*=\s*True\s*\n", "", text, flags=re.MULTILINE)
        return text

    m = TOUCH_BLOCK.search(text)
    if m:
        text = TOUCH_BLOCK.sub(_runtime_touch(m.group("read"), m.group("data2")), text, count=1)
        return text

    m = KEYPAD_BLOCK.search(text)
    if m:
        replacement = (
            "runtime = eventsys.Runtime(display=display_drv)\n"
            f"runtime.add_keypad(read={m.group('read').strip()})"
        )
        text = KEYPAD_BLOCK.sub(replacement, text, count=1)
        return text

    m = JOYSTICK_BLOCK.search(text)
    if m:
        body = m.group("body").strip()
        replacement = (
            "runtime = eventsys.Runtime(display=display_drv)\n"
            f"runtime.add_joystick(\n    {body}\n)"
        )
        text = JOYSTICK_BLOCK.sub(replacement, text, count=1)
        return text

    if SIMPLE_QUIT.search(text):
        text = SIMPLE_QUIT.sub("runtime = None", text)
        return text

    if "eventsys.Broker" in text:
        print(f"WARN: unmigrated Broker in {path}")
    return text


def main() -> None:
    changed = 0
    for path in sorted(CONFIG_ROOT.rglob("board_config.py")):
        original = path.read_text(encoding="utf-8")
        updated = migrate_text(original, path)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    # lib board_config already hand-migrated
    print(f"Updated {changed} board_config.py files")


if __name__ == "__main__":
    main()
