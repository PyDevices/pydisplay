# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`pdwidgets`
====================================================
Provides a collection of widgets for creating graphical user interfaces on embedded systems.
It includes base classes for widgets, as well as specific widgets such as buttons, labels, sliders, and more.

Classes:
    Task: A task that runs a callback function after a specified delay.
    Widget: The base class for creating widgets.
    Display: Manages the display and child widgets.
    Screen: A container for widgets.
    Button: A widget that displays an icon and/or text.
    Label: A widget that displays text.
    TextBox: A widget that displays formatted text.
    Icon: A widget that displays an icon.
    IconButton: A button widget that displays an icon.
    Toggle: A button widget that toggles between two states.
    ToggleButton: A toggle button widget.
    CheckBox: A checkbox widget.
    RadioGroup: Manages a group of radio buttons.
    RadioButton: A radio button widget.
    ProgressBar: A widget that displays a progress bar.
    Slider: A widget that displays a slider with a circular knob.
    ScrollBar: A widget that displays a scroll bar with two arrow buttons and a slider.
    DigitalClock: A widget that displays the current time.
    ListView: A widget that displays a list of items.
    Card: A rounded, optionally-shadowed container for grouping widgets.
    Row: A container that lays children out left-to-right with spacing.
    Column: A container that stacks children top-to-bottom with spacing.
    Badge: A small colored status dot or count pill.
    Switch: An iOS-style sliding on/off toggle.
    NumberStepper: A ``-``/value/``+`` control for a bounded number.
    TextInput: A single-line editable text field with focus and a cursor.
    Dropdown: A header button that reveals a popup option list.
    Dialog: A modal message box centered over the screen.

Functions:
    tick: Calls the tick method of all Display objects (manual frame pump).

Optional add-on dependency:
    ``Label`` (and widgets built on it) gains proportional-font rendering when a
    ``font`` module is supplied. That path lazily imports **``add_ons/tft_write``**
    (the russhughes ``write_font_converter`` renderer) — the only ``add_ons/*``
    module pdwidgets touches, and only when a proportional font is actually
    used. The default romfont path has no such dependency.

Timer architecture:
    pdwidgets owns **no** timer of its own. Each :class:`Display` wires itself
    into the shared ``eventsys.Runtime`` at construction
    (:meth:`Display._attach_to_runtime`): the runtime's auto-service tick polls
    devices and dispatches input events to :meth:`Display.handle_event`, while a
    single ``runtime.on_tick`` subscription drives :meth:`Display.tick`
    (flush/redraw). The subscription's ``async_`` tracks ``runtime.timer_async``,
    so a sync render timer never coexists with the async loop on any runtime
    (desktop SDL/PG, MicroPython/CircuitPython unix, ``micropython.exe``,
    PyScript, Jupyter).

    Apps therefore need no pdwidgets-specific loop: build the UI, then keep the
    process alive with the canonical idiom
    ``if __name__ == "__main__": runtime.run_forever()`` (optional in an
    interactive REPL on signal-driven backends).
"""

from eventsys import events
from graphics import Area

from ._constants import ALIGN, DEFAULT_PADDING, ICON_SIZE, PAD, POSITION, TEXT_SIZE, TEXT_WIDTH
from ._themes import ColorTheme, IconTheme, get_palette, icon_theme
from .badge import Badge
from .button import Button
from .card import Card
from .check_box import CheckBox
from .column import Column
from .dialog import Dialog
from .digital_clock import DigitalClock
from .display import Display, tick
from .dropdown import Dropdown
from .icon import Icon
from .icon_button import IconButton
from .label import Label
from .list_view import ListView
from .number_stepper import NumberStepper
from .progress_bar import ProgressBar
from .radio_button import RadioButton
from .radio_group import RadioGroup
from .row import Row
from .screen import Screen
from .scroll_bar import ScrollBar
from .slider import Slider
from .switch import Switch
from .task import Task
from .text_box import TextBox
from .text_input import TextInput
from .toggle import Toggle
from .toggle_button import ToggleButton
from .widget import Widget

DEBUG = False
MARK_UPDATES = False

__all__ = [
    "ALIGN",
    "DEBUG",
    "DEFAULT_PADDING",
    "ICON_SIZE",
    "MARK_UPDATES",
    "PAD",
    "POSITION",
    "TEXT_SIZE",
    "TEXT_WIDTH",
    "Area",
    "Badge",
    "Button",
    "Card",
    "CheckBox",
    "ColorTheme",
    "Column",
    "Dialog",
    "DigitalClock",
    "Display",
    "Dropdown",
    "Icon",
    "IconButton",
    "IconTheme",
    "Label",
    "ListView",
    "NumberStepper",
    "ProgressBar",
    "RadioButton",
    "RadioGroup",
    "Row",
    "Screen",
    "ScrollBar",
    "Slider",
    "Switch",
    "Task",
    "TextBox",
    "TextInput",
    "Toggle",
    "ToggleButton",
    "Widget",
    "events",
    "get_palette",
    "icon_theme",
    "tick",
]
