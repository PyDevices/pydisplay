"""
console_simpletest.py

Call `console.hide()` to use the display for something else.
"""

from board_config import display_drv
from console import Console


console = Console(display_drv)

for x in range(60):
    console.write(f"Line {x}\n")
    display_drv.show()
