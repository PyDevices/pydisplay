# pyscript mip: palettes
# pyodide wheels: palettes
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
# Font.fill_rect per pixel directly on the display (slow — see font_simpletest per_pixel mode).
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

    if hasattr(gc, "mem_free"):
        console.label(Console.RIGHT, lambda: f"mf={gc.mem_free():,}", pal.BLUE)
    else:
        raise ImportError
except ImportError:
    try:
        from psutil import virtual_memory

        console.label(Console.RIGHT, lambda: f"mf={virtual_memory().free:,}", pal.BLUE)
    except ImportError:
        pass

try:
    import pydisplay_test_mode

    _test_mode = pydisplay_test_mode.ENABLED
except ImportError:
    _test_mode = False

if not _test_mode:
    try:
        import os

        if hasattr(os, "dupterm"):
            os.dupterm(console)
            help()
        else:
            console.write("REPL not available (no os.dupterm).\n", pal.YELLOW)
    except (ImportError, AttributeError):
        console.write("REPL not available.\n", pal.YELLOW)

console.label(Console.LEFT, platform, pal.RED)

display_drv.show()

if _test_mode:
    from board_config import runtime

    console.write("console_advanced_demo: smoke test\n", pal.GREEN)
    display_drv.show()

    # Quit is already serviced by Runtime's auto-service; just block until then.
    runtime.run_forever()

#### Example commands
# console.cls()                   # Clear the console screen
# console.write("Hello, World!")  # Write text to the console
# console.hide()                  # Hide the console screen
# console.show()                  # Show the console screen after hiding it
