"""Adafruit CLUE — CircuitPython built-in display via board.DISPLAY"""

from displaysys.boarddisplay import BoardDisplay
import eventsys

display_drv = BoardDisplay(width=240, height=240, color_depth=16)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
