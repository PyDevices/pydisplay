# multimer types: sync
"""
console_advanced_demo.py - Advanced demo of the mpconsole module
"""

from board_config import display_drv
from palettes import get_palette
from console import Console
from sys import implementation, platform

SSID = "<ssid>"
PASSPHRASE = "<passphrase>"


pal = get_palette()

# Default Console char path: render each glyph into an 8x8 FrameBuffer, then
# blit_rect once per character (fast). Custom text8/text16 writers draw with
# Font.fill_rect per pixel directly on the display (slow — see font_simpletest2).
console = Console(display_drv, cwidth=8, lheight=8)

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
    try:
        import pydisplay_test_mode

        if not pydisplay_test_mode.ENABLED:
            help()
    except ImportError:
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
