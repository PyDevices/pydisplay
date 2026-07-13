# pyscript packages: micropython-nano-gui
"""
nano_gui_simpletest.py - Copied from:
https://github.com/peterhinch/micropython-nano-gui/tree/master?tab=readme-ov-file#23-verifying-hardware-configuration

``color_setup`` fetches micropython-nano-gui into add_ons/gui/ when needed.
On PyScript the gallery loader pre-installs the package (see ``# pyscript packages:``).
"""

from board_config import runtime
from color_setup import ssd  # Create a display instance
from gui.core.colors import RED, BLUE, GREEN
from gui.core.nanogui import refresh

refresh(ssd, True)  # Initialise and clear display.
# Uncomment for ePaper displays; not supported by displaybuf or displaysys (yet).
# ssd.wait_until_ready()
ssd.fill(0)
ssd.line(0, 0, ssd.width - 1, ssd.height - 1, GREEN)  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, RED)  # Red square at top left
ssd.rect(ssd.width - 15, ssd.height - 15, 15, 15, BLUE)  # Blue square at bottom right
ssd.show()

runtime.run_forever()
