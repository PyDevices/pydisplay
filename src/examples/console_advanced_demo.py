"""
console_advanced_demo.py - Advanced demo of the mpconsole module
"""

from board_config import display_drv
from palettes import get_palette
from console import Console
from sys import implementation, platform
from graphics import text16

SSID = "<ssid>"
PASSPHRASE = "<passphrase>"


pal = get_palette()

# Have to use a lambda to map the way Console calls char_writer to the way display_drv.text expects it
char_writer = lambda char, x, y, fg, bg: text16(display_drv, char, x, y, fg)  # noqa: E731
console = Console(display_drv, char_writer, cwidth=8, lheight=16)

maj, min, *_ = implementation.version
try:
    import wifi

    wifi.radio.connect(SSID, PASSPHRASE)
    console.label(
        Console.TITLE,
        f"{implementation.name} {maj}.{min} @ {wifi.radio.ipv4_address}",
        pal.BLACK,
    )
except ImportError:
    console.label(Console.TITLE, f"{implementation.name} {maj}.{min}", pal.BLACK)

try:
    import gc

    console.label(Console.RIGHT, lambda: f"mf={gc.mem_free():,}", pal.BLUE)
except ImportError:
    from psutil import virtual_memory

    console.label(Console.RIGHT, lambda: f"mf={virtual_memory().free:,}", pal.BLUE)

try:
    import os

    os.dupterm(console)
    help()
except ImportError:
    console.write("REPL not available.\n", pal.YELLOW)

console.label(Console.LEFT, platform, pal.RED)

display_drv.show()

#### Example commands
# console.cls()                   # Clear the console screen
# console.write("Hello, World!")  # Write text to the console
# console.hide()                  # Hide the console screen
# console.show()                  # Show the console screen after hiding it
