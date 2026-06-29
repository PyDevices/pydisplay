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

Functions:
    tick: Calls the tick method of all Display objects.
    init_timer: Initializes the timer to call the tick function at regular intervals.
"""

from random import getrandbits  # for MARK_UPDATES
from time import localtime  # for DigitalClock

from eventsys import events
from graphics import RGB565, Area, FrameBuffer

from ._constants import ALIGN, DEFAULT_PADDING, ICON_SIZE, PAD, POSITION, TEXT_SIZE, TEXT_WIDTH
from ._themes import ColorTheme, get_palette, icon_theme

try:
    from time import ticks_add, ticks_ms
except ImportError:
    from multimer import ticks_add, ticks_ms


DEBUG = False
MARK_UPDATES = False


def _log(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def tick(_=None):
    """
    Function to call the tick method of all Display objects.
    """
    for display in Display.displays:
        display.tick()


def init_timer(period=10):
    """
    Initialize the timer to call the tick function at regular intervals.

    Args:
        period (int): The period in milliseconds to call the tick function.
    """
    if Display.timer is None:
        from multimer import periodic

        Display.timer = periodic(tick, period)


def pump():
    """
    Process one frame during setup bursts (before ``run_forever``).

    On queued backends, drains the multimer callback queue. In poll mode
    (no ``init_timer``), also calls ``tick()``.
    """
    from multimer import capabilities, needs_pump
    from multimer import pump as multimer_pump

    caps = capabilities()
    if caps["schedule_queue"] or needs_pump():
        multimer_pump()
    if Display.timer is None:
        tick()


def run_forever():
    """
    Keep the widget loop alive on all platforms.

    On queued/SDL backends, runs ``pump()`` forever. In poll mode
    (no ``init_timer``), also calls ``tick()`` each iteration. On sync
    MCU with an active timer, returns immediately (the timer drives
    ``tick()``).
    """
    from multimer import capabilities, needs_pump, sleep_ms
    from multimer import pump as multimer_pump

    caps = capabilities()
    timer_req = needs_pump()
    needs_queue_loop = caps["schedule_queue"] or timer_req
    # CPython linux ctypes: schedule queue active but timer fires on main thread;
    # drive tick from the main loop instead of the timer to avoid signal/reentrancy issues.
    cpython_main_loop_tick = caps["schedule_queue"] and not timer_req
    has_timer = Display.timer is not None
    if cpython_main_loop_tick and Display.timer:
        try:
            Display.timer.deinit()
        except Exception:
            pass
        Display.timer = None
        has_timer = False

    if needs_queue_loop:
        while Display.displays:
            pump()
            if not has_timer or cpython_main_loop_tick:
                tick()
            sleep_ms(1)
    elif not has_timer:
        while Display.displays:
            tick()


_display_drv_get_attrs = {
    "set_vscroll",
    "tfa",
    "bfa",
    "vsa",
    "vscroll",
    "tfa_area",
    "bfa_area",
    "vsa_area",
    "scroll_by",
    "scroll_to",
    "translate_point",
}
_display_drv_set_attrs = {"vscroll"}


class Task:
    """
    A task that runs a callback function after a specified delay.  Used
    by the Display object to run tasks at regular intervals, such as
    refreshing the display or updating the clock.

    Args:
        callback (callable): The function to run.
        delay (int): The delay in milliseconds before running the callback.

    Usage:
        def my_callback():
            print("Hello, world!")

        task = Task(my_callback, 1000)  # Run my_callback every second
        display.add_task(task)
    """

    def __init__(self, callback, delay):
        self.callback = callback
        self.delay = delay
        self.next_run = ticks_add(ticks_ms(), delay)

    def run(self, t):
        """
        Run the callback function and set the next run time.

        Args:
            t (int): The current time in milliseconds.
        """
        self.callback()
        self.next_run = ticks_add(t, self.delay)


class Widget:
    next_instance_id = 0

    def __init__(
        self,
        parent,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
    ):
        """
        The base Widget class for creating widgets.  May be used as a base class for custom widgets or
        as a container for other widgets.

        Args:
            parent (Widget): The parent widget that contains this widget.  All widgets except the Display
                widget must have a parent.
            x (int): The x-coordinate of the widget.
            y (int): The y-coordinate of the widget.
            w (int): The width of the widget.
            h (int): The height of the widget.
            align (int): The alignment of the widget (default is ALIGN.TOP_LEFT).
            align_to (Widget): The widget to align to (default is the parent widget).
            fg (int): The foreground color of the widget (default is the parent's foreground color).
            bg (int): The background color of the widget (default is the parent's background color).
            visible (bool): The visibility of the widget (default is True).
            value (str): The value of the widget (e.g., text of a label, value of a slider).
            padding (tuple): The padding on each side of the widget (default is (2, 2, 2, 2)).
        """
        self.id = Widget.next_instance_id  # Currently only used in debugging
        Widget.next_instance_id += 1

        self._parent: Widget = None
        self.fg = fg if fg is not None else parent.fg if parent else -1
        self.bg = bg if bg is not None else parent.bg if parent else 0
        self._visible = visible
        self._value = value  # Value of the widget (e.g., text of a label)
        self.padding = padding if padding is not None else DEFAULT_PADDING

        self.children: list[Widget] = []
        self.dirty_widgets = set()
        self.dirty_descendants = set()
        self.invalidated = False
        self._event_callbacks = {}
        self._change_callback = None

        self._x = self._y = self._w = self._h = self._align = self._align_to = None
        self.set_position(
            x,
            y,
            w or parent.width,
            h or parent.height,
            align if align is not None else ALIGN.TOP_LEFT,
            align_to or parent,
        )
        self.parent: Widget = parent
        self._register_callbacks()

    def __str__(self):
        return f"ID {self.id} {self.__class__.__name__}"

    def __format__(self, format_spec):
        return f"ID {self.id} {self.__class__.__name__:{format_spec}}"

    def _register_callbacks(self):
        """
        Register event callbacks for the widget.  Subclasses should override this method to register event callbacks.
        """

    def add_event_cb(self, event_type: int, callback: callable, data=None):
        """
        Register a callback for an event type on this widget.

        Args:
            event_type: ``eventsys.events`` constant (e.g. ``events.MOUSEBUTTONDOWN``).
            callback: Callable invoked as ``callback(event, data)``.
            data: User data passed to callback; defaults to this widget.
        """
        # Each item's key is the callback and value is the optional data.  If the event_type is not found,
        # add it to the dictionary with the callback and data.
        data = data or self
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = {}
        self._event_callbacks[event_type][callback] = data

    def remove_event_cb(self, event_type: int, callback: callable):
        # Look in self._event_callbacks for the event_type.  If found, remove the callback from the dictionary.
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].pop(callback, None)

    def handle_event(self, event, condition=None):
        """
        Handle an event and propagate it to child widgets.  Subclasses that need to handle events
        should override this method and call this method to propagate the event to children.

        Args:
            event (Event): The event to handle.
            condition (callable): A function that returns True if the event should be handled by the child widget.
        """
        if condition is None:
            if event.type in (events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP, events.MOUSEMOTION):
                condition = lambda child, e: child.padded_area.contains(  # noqa: E731
                    self.display.translate_point(e.pos)
                )
            else:
                condition = lambda child, e: True  # noqa: E731
        for child in self.children:
            if child.visible:
                if condition(child, event):
                    for callback, data in child._event_callbacks.get(event.type, {}).items():
                        callback(data, event)
                child.handle_event(event, condition)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if parent != self._parent:
            if self._parent:
                self._parent.remove_child(self)
            self._parent = parent
            if self._parent:
                self._parent.add_child(self)
                if self.align_to is None:
                    self.set_position(align_to=parent)

    @property
    def area(self):
        """
        Absolute bounding box of the widget on screen.

        Returns:
            Area: ``(x, y, width, height)`` in display coordinates.
        """
        return Area(self.x, self.y, self.width, self.height)

    @property
    def padded_area(self):
        return self.area.inset(*self.padding)

    @property
    def x(self):
        """Calculate the absolute x-coordinate of the widget based on align"""
        align = self.align
        align_to = self.align_to or self.display

        x = align_to.x + int(self._x)

        if align & POSITION.LEFT:
            if align & POSITION.OUTER:
                x -= self.width
        elif align & POSITION.RIGHT:
            x += align_to.width
            if not align & POSITION.OUTER:
                x -= self.width
        else:
            x += (align_to.width - self.width) // 2

        return x

    @x.setter
    def x(self, x):
        self.set_position(x=x)

    @property
    def y(self):
        """Calculate the absolute y-coordinate of the widget based on align"""
        align = self.align
        align_to = self.align_to or self.display

        y = align_to.y + int(self._y)

        if align & POSITION.TOP:
            if align & POSITION.OUTER:
                y -= self.height
        elif align & POSITION.BOTTOM:
            y += align_to.height
            if not align & POSITION.OUTER:
                y -= self.height
        else:
            y += (align_to.height - self.height) // 2

        return y

    @y.setter
    def y(self, y):
        self.set_position(y=y)

    @property
    def width(self):
        return int(self._w)

    @width.setter
    def width(self, w):
        self.set_position(w=w)

    @property
    def height(self):
        return int(self._h)

    @height.setter
    def height(self, h):
        self.set_position(h=h)

    @property
    def align(self):
        return self._align

    @align.setter
    def align(self, align):
        self.set_position(align=align)

    @property
    def align_to(self):
        return self._align_to

    @align_to.setter
    def align_to(self, align_to):
        self.set_position(align_to=align_to)

    @property
    def display(self):
        return self.parent.display

    @property
    def color_theme(self) -> ColorTheme:
        return self.display.color_theme

    @property
    def visible(self):
        """Get widget visibility."""
        return self._visible and self.parent.visible

    @visible.setter
    def visible(self, visible):
        """Set widget visibility."""
        if visible != self._visible:
            if not self.visible:
                self._visible = True
                self.invalidate()
            else:
                self._visible = False
                self.parent.invalidate()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._value = value
            self.changed()

    def add_child(self, child):
        """Adds a child widget to the current widget."""
        _log("Adding", child, "to", self)
        self.children.append(child)
        child.invalidate()

    def changed(self):
        """Called when the value of the widget changes.  May be overridden in subclasses.
        If overridden, the subclass should call this method to trigger the on_change_callback and invalidate.
        """
        if self.visible:
            if self._change_callback:
                self._change_callback(self)
            self.invalidate()

    def draw(self, area=None):
        """
        Draw the widget on the screen.  Subclasses should override this method to draw the widget unless the widget is
        a container widget (like a screen) that contains other widgets.  Subclasses may call this method to draw the
        background of the widget before drawing other elements.
        """
        if self.bg is not None:
            area = area or self.area
            self.display.framebuf.fill_rect(*area, self.bg)

    def hide(self, hide=True):
        self.visible = not hide

    def invalidate(self):
        if not self.invalidated:
            self.invalidated = True
            if self.parent:
                self.parent.add_dirty_widget(self)
            for child in self.children:
                child.invalidate()

    def remove_child(self, widget):
        """Removes a child widget from the current widget."""
        self.children.remove(widget)
        self.invalidate()

    def set_change_cb(self, callback):
        self._change_callback = callback

    def set_position(self, x=None, y=None, w=None, h=None, align=None, align_to=None):
        changed = False
        if x is not None:
            self._x = x
            changed = True
        if y is not None:
            self._y = y
            changed = True
        if w is not None:
            self._w = w
            changed = True
        if h is not None:
            self._h = h
            changed = True
        if align is not None:
            self._align = align
            changed = True
        if align_to is not None:
            self._align_to = align_to
            changed = True
        if changed and self.parent is not None:
            self.parent.invalidate()

    def add_dirty_widget(self, child):
        self.dirty_widgets.add(child)
        self.dirty_descendants.add(child)
        if self.parent:
            self.parent.add_dirty_descendant(self)

    def add_dirty_descendant(self, branch):
        self.dirty_descendants.add(branch)
        if self.parent:
            self.parent.add_dirty_descendant(self)

    def render(self):
        if self.invalidated:
            _log("Drawing", self, "on", self.parent, "at", self.area)
            self.draw()
            self.invalidated = False
            if self.parent:
                self.parent.remove_dirty_widget(self)

    def remove_dirty_widget(self, child):
        self.dirty_widgets.discard(child)
        if not self.dirty_widgets and not self.dirty_descendants and self.parent:
            self.parent.remove_dirty_descendant(self)

    def remove_dirty_descendant(self, branch):
        self.dirty_descendants.discard(branch)

    def set_value(self, value):
        self.value = value


class Display(Widget):
    displays = []
    timer = None

    def __init__(self, display_drv, broker, tfa=0, bfa=0, format=RGB565):
        """
        Initialize a Display object to manage the display and child widgets.

        Args:
            display_drv (DisplayDriver): The display driver object that manages the display hardware.
            broker (Broker): The event broker object that manages the event system.
            tfa (int): The top fixed area of the display.
            bfa (int): The bottom fixed area of the display.
            format (int): The color format of the display (default is RGB565).

        Usage:
            from board_config import display_drv, broker
            display = Display(display_drv, broker)
        """
        self.display_drv = display_drv
        super().__init__(
            None, 0, 0, display_drv.width, display_drv.height, fg=-1, bg=0, padding=(0, 0, 0, 0)
        )
        display_drv.set_vscroll(tfa, bfa)
        display_drv.vscroll = 0
        self.broker = broker
        broker.on_quit = self.quit
        self._buffer = memoryview(
            bytearray(display_drv.width * display_drv.height * display_drv.color_depth // 8)
        )
        self.framebuf = FrameBuffer(self._buffer, display_drv.width, display_drv.height, format)
        self._dirty_areas = []
        self._tasks = []
        self._tick_busy = False
        if display_drv.requires_byteswap:
            self.needs_swap = display_drv.disable_auto_byteswap(True)
        else:
            self.needs_swap = False
        self.pal = get_palette(
            "material_design", swapped=self.needs_swap, color_depth=display_drv.color_depth
        )
        self._color_theme = ColorTheme(self.pal)
        Display.displays.append(self)

    @property
    def parent(self):
        return None

    @parent.setter
    def parent(self, parent):
        if parent is not None:
            raise ValueError("Display object cannot have a parent.")

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def width(self):
        return self._w

    @property
    def height(self):
        return self._h

    @property
    def display(self):
        return self

    @property
    def color_theme(self):
        return self._color_theme

    @property
    def visible(self):
        return True

    @visible.setter
    def visible(self, visible):
        raise ValueError("Cannot set visibility of Display object.")

    @property
    def active_screen(self):
        if self.children:
            return self.children[0]
        return None

    @active_screen.setter
    def active_screen(self, screen):
        for child in self.children:
            self.remove_child(child)
        super().add_child(screen)

    def add_child(self, screen):
        self.active_screen = screen

    def set_position(self, *args, **kwargs):
        self._x = 0
        self._y = 0
        self._w = self.display_drv.width
        self._h = self.display_drv.height
        self._align = ALIGN.TOP_LEFT
        self._align_to = None

    def add_task(self, callback, delay):
        new_task = Task(callback, delay)
        self._tasks.append(new_task)
        return new_task

    def refresh(self, area: Area):
        """
        Copy a dirty region from the internal framebuffer to the physical display.

        Args:
            area: ``Area`` or ``(x, y, w, h)`` rectangle to flush.
        """
        area = area.clip(self.area)
        _log("Refreshing", area)
        x, y, w, h = area
        for row in range(y, y + h):
            buffer_begin = (row * self.width + x) * 2
            buffer_end = buffer_begin + w * 2
            self.display_drv.blit_rect(self._buffer[buffer_begin:buffer_end], x, row, w, 1)
        if MARK_UPDATES:
            c = getrandbits(16)
            self.display_drv.fill_rect(x, y, w, 2, c)
            self.display_drv.fill_rect(x, y + h - 2, w, 2, c)
            self.display_drv.fill_rect(x, y, 2, h, c)
            self.display_drv.fill_rect(x + w - 2, y, 2, h, c)
        from multimer import capabilities, needs_pump

        caps = capabilities()
        needs_show = caps["schedule_queue"] or needs_pump()
        if needs_show:
            self.display_drv.show()

    def remove_task(self, task):
        self._tasks.remove(task)

    def quit(self):
        Display.displays.remove(self)
        if Display.timer and not Display.displays:
            timer = Display.timer
            Display.timer = None
            if not getattr(timer, "_busy", False):
                try:
                    timer.deinit()
                except Exception:
                    pass
        # display_drv.quit() releases SDL resources, restores the TTY, and
        # performs a low-level process exit.  sys.exit() raised from a timer or
        # micropython.schedule callback is printed and swallowed on the unix port.
        self.display_drv.quit()

    def tick(self):
        """
        Run one frame of the widget event loop.

        Flushes dirty areas to the display, otherwise polls ``broker`` for events,
        runs scheduled tasks, and re-renders invalidated widgets. Call from a timer
        (see ``init_timer``) or your main loop.
        """
        if self._tick_busy:
            return
        self._tick_busy = True

        if self._dirty_areas:
            # combine overlapping areas in self._dirty_areas into a new list called dirty_areas
            dirty_areas = []
            while self._dirty_areas:
                area = self._dirty_areas.pop()
                for i, other in enumerate(self._dirty_areas):
                    if area.touches_or_intersects(other):
                        area += other
                        self._dirty_areas.pop(i)
                dirty_areas.append(area)

            for dirty in dirty_areas:
                self.refresh(dirty)
        else:
            if elist := self.broker.poll():
                for e in elist:
                    if e.type in events.filter:
                        self.handle_event(e)

            t = ticks_ms()
            for task in self._tasks:
                if t >= task.next_run:
                    task.run(t)

            self.render_dirty_widgets()
        self._tick_busy = False

    def render_dirty_widgets(self):
        # Non-recursive redraw traversal using an explicit stack
        # Use a stack to avoid recursion / stack overflow
        stack = list(self.dirty_descendants)

        while stack:
            # Collect all widgets at the current level
            current_level = []
            while stack:
                widget = stack.pop()
                if widget.invalidated and widget.visible:
                    widget.render()
                    self._dirty_areas.append(widget.area)
                current_level.append(widget)

            # Now process the next level of descendants from current_level
            for widget in current_level:
                stack.extend(reversed(list(widget.dirty_widgets)))
                stack.extend(reversed(list(widget.dirty_descendants)))

    def __getattr__(self, name):
        if name in _display_drv_get_attrs:
            return getattr(self.display_drv, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in _display_drv_set_attrs:
            return setattr(self.display_drv, name, value)
        super().__setattr__(name, value)


class Screen(Widget):
    def __init__(self, parent: Display | Widget, fg=None, bg=None, visible=True):
        """
        Initialize a Screen object to contain widgets.

        Args:
            parent (Display): The display object that contains the screen.
            fg (int): The foreground color of the screen.
            bg (int): The background color of the screen.
            visible (bool): The visibility of the screen.

        Usage:
            screen = Screen(display)
        """
        super().__init__(
            parent,
            0,
            0,
            parent.width,
            parent.height,
            fg=fg,
            bg=bg,
            visible=visible,
            padding=(0, 0, 0, 0),
        )
        self.partitioned = self.display.tfa > 0 or self.display.bfa > 0

        if self.partitioned:
            self.top = Widget(
                self,
                *Area(self.display.tfa_area),
                fg=parent.color_theme.on_primary,
                bg=parent.color_theme.primary,
            )
            self.main = Widget(self, *Area(self.display.vsa_area))
            self.bottom = Widget(
                self,
                *Area(self.display.bfa_area),
                fg=parent.color_theme.on_primary,
                bg=parent.color_theme.primary,
            )


class Button(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        radius=0,
        pressed_offset=2,
        pressed=False,
        label=None,
        text_color=None,
        text_height=TEXT_SIZE.LARGE,
        icon_file=None,
        icon_color=None,
    ):
        """
        Initialize a Button widget to display an icon and/or text.

        Args:
            parent (Widget): The parent widget or screen that contains this widget.
            x (int): The x-coordinate of the widget.
            y (int): The y-coordinate of the widget.
            w (int): The width of the widget.
            h (int): The height of the widget.
            align (int): The alignment of the widget.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the widget.
            bg (int): The background color of the widget.
            visible (bool): The visibility of the widget (default is True).
            value (Any): User-assigned value of the widget.
            padding (tuple): The padding on each side of the widget.
            radius (int): The corner radius of the widget (default is 0).
            pressed_offset (int): The offset of the widget when pressed (default is 2).
            pressed (bool): The state of the widget (default is False).
            label (str): The text label of the widget.
            text_color (int): The color of the text label.
            text_height (int): The height of the text label (default is TEXT_SIZE.LARGE).
            icon_file (str): The icon file to display on the widget.
            icon_color (int): The color of the icon.
        """
        self.radius = radius
        self.pressed_offset = pressed_offset
        self._pressed = pressed
        if w is None and label:
            w = (len(label) + 1) * TEXT_WIDTH + 2 * PAD
        w = w or ICON_SIZE.LARGE + 2 * PAD
        h = h or ICON_SIZE.LARGE + 2 * PAD
        bg = bg if bg is not None else parent.color_theme.primary_variant
        fg = fg if fg is not None else parent.color_theme.on_primary
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        if icon_file:
            icon_align = ALIGN.CENTER if not label else ALIGN.LEFT
            icon_color = icon_color if icon_color is not None else parent.color_theme.on_primary
            self.icon = Icon(self, align=icon_align, fg=icon_color, bg=self.bg, value=icon_file)
        if label:
            if text_height not in TEXT_SIZE:
                raise ValueError("Text height must be 8, 14 or 16 pixels.")
            label_align = ALIGN.CENTER if not icon_file else ALIGN.OUTER_RIGHT
            label_align_to = self.icon if icon_file else self
            text_color = text_color if text_color is not None else parent.color_theme.on_primary
            self.label = Label(
                self,
                value=label,
                align=label_align,
                align_to=label_align_to,
                fg=text_color,
                bg=self.bg,
                text_height=text_height,
            )
        else:
            self.label = None

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.press)
        self.add_event_cb(events.MOUSEBUTTONUP, self.release)

    def draw(self, _=None):
        """
        Draw the button background and shape only.
        """
        self.parent.draw(self.area)
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=True)

    def press(self, data=None, event=None):
        self._pressed = True
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.fg, f=False)
        self.display.refresh(self.area)

    def release(self, data=None, event=None):
        self._pressed = False
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=False)
        self.display.refresh(self.area)


class Label(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        text_height=TEXT_SIZE.LARGE,
        scale=1,
        inverted=False,
        font_data=None,
    ):
        """
        Initialize a Label widget to display text.

        Args:
            parent (Widget): The parent widget or screen that contains this label.
            x (int): The x-coordinate of the label.
            y (int): The y-coordinate of the label.
            w (int): The width of the label.
            h (int): The height of the label.
            align (int): The alignment of the label.
            align_to (Widget): The widget to align to.
            fg (int): The color of the text.
            bg (int): The background color of the label.
            visible (bool): The visibility of the label.
            value (str): The text content of the label.
            padding (tuple): The padding on each side of the label.
            text_height (int): The height of the text (default is TEXT_SIZE.LARGE).
            scale (int): The scale of the text (default is 1).
            inverted (bool): The inversion of the text (default is False).
            font_data (str): The font file to use for the text.
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        padding = padding if padding is not None else (0, 0, 0, 0)
        w = w or len(value) * TEXT_WIDTH * scale + padding[0] + padding[2]
        h = h or text_height * scale + padding[1] + padding[3]
        align = align if align is not None else ALIGN.CENTER
        value = value if value is not None else ""
        self.text_height = text_height
        self.scale = scale
        self._inverted = inverted
        self._font_data = font_data
        bg = bg if bg is not None else parent.color_theme.transparent
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """
        Draw the label's text on the screen, using absolute coordinates.
        Optionally fills the background first if `bg` is set.
        """
        if self.bg is not self.parent.color_theme.transparent:
            self.display.framebuf.fill_rect(
                *self.padded_area, self.bg
            )  # Draw background if bg is specified
        x, y, _, _ = self.padded_area
        self.display.framebuf.text(
            self.value,
            x,
            y,
            self.fg,
            height=self.text_height,
            scale=self.scale,
            inverted=self._inverted,
            font_data=self._font_data,
        )

    @property
    def char_width(self):
        return TEXT_WIDTH * self.scale

    @property
    def char_height(self):
        return self.text_height * self.scale


class TextBox(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        format="",
        text_height=TEXT_SIZE.LARGE,
        scale=1,
        inverted=False,
        font_data=None,
    ):
        """
        Initialize a TextBox widget to display formatted text.

        Args:
            parent (Widget): The parent widget or screen that contains this text box.
            x (int): The x-coordinate of the text box.
            y (int): The y-coordinate of the text box.
            w (int): The width of the text box.
            h (int): The height of the text box.
            align (int): The alignment of the text box.
            align_to (Widget): The widget to align to.
            fg (int): The color of the text.
            bg (int): The background color of the text box.
            visible (bool): The visibility of the text box.
            value (str): The text content of the text box.
            padding (tuple): The padding on each side of the text box.
            format (str): The format string for the text.
            text_height (int): The height of the text (default is TEXT_SIZE.LARGE).
            scale (int): The scale of the text (default is 1).
            inverted (bool): The inversion of the text (default is False).
            font_data (str): The font file to use for the text.

        Usage:
            text_box = TextBox(screen, value="Hello, world!", format="{:>20}", text_height=TEXT_SIZE.LARGE)
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        padding = padding if padding is not None else DEFAULT_PADDING
        w = w or parent.width if parent else 60
        h = h or text_height * scale + padding[1] + padding[3]
        value = value if value is not None else ""
        self.format = format
        self.text_height = text_height
        self.scale = scale
        self._inverted = inverted
        self._font_data = font_data
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """
        Draw the label's text on the screen, using absolute coordinates.
        """
        pa = self.padded_area
        self.display.framebuf.fill_rect(*pa, self.bg)
        y = pa.y + (pa.h - self.text_height * self.scale) // 2
        self.display.framebuf.text(
            f"{self.value:{self.format}}",
            pa.x + PAD,
            y,
            self.fg,
            height=self.text_height,
            scale=self.scale,
            inverted=self._inverted,
            font_data=self._font_data,
        )

    @property
    def char_width(self):
        return TEXT_WIDTH * self.scale

    @property
    def char_height(self):
        return self.text_height * self.scale


class Icon(Widget):
    cache = {}

    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
    ):
        """
        Initialize an Icon widget to display an icon.  Currently only supports PBM files.
        PBM files are monochrome (1 bit per pixel) bitmaps.

        Args:
            parent (Widget): The parent widget or screen that contains this icon.
            x (int): The x-coordinate of the icon.
            y (int): The y-coordinate of the icon.
            w (int): The width of the icon.
            h (int): The height of the icon.
            align (int): The alignment of the icon.
            align_to (Widget): The widget to align to.
            fg (int): The color of the icon.
            bg (int): The background color of the icon.
            visible (bool): The visibility of the icon.
            value (str): The icon file to display.
            padding (tuple): The padding on each side of the icon.

        Usage:
            icon = Icon(screen, value="icon.pbm")
        """
        if not value:
            raise ValueError("Icon value must be set to the filename with path.")
        self.load_icon(value)
        padding = padding if padding is not None else DEFAULT_PADDING
        w = w or self._icon_width + padding[0] + padding[2]
        h = h or self._icon_height + padding[1] + padding[3]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def load_icon(self, value):
        """Load icon file and store pixel data."""
        if value in Icon.cache:
            self._fbuf = Icon.cache[value]
        else:
            self._fbuf = FrameBuffer.from_file(value)
            Icon.cache[value] = self._fbuf
        self._icon_width, self._icon_height = self._fbuf.width, self._fbuf.height

    def changed(self):
        """Update the icon when the value (file) changes."""
        self.display.framebuf.fill_rect(*self.padded_area, self.bg)
        self.load_icon(self.value)
        super().changed()

    def draw(self, _=None):
        """
        Draw the icon on the screen.
        """
        pal = FrameBuffer(memoryview(bytearray(4)), 2, 1, RGB565)
        if self.bg is self.parent.color_theme.transparent:
            key = ~self.fg
            pal.pixel(0, 0, key)
        else:
            key = -1
            pal.pixel(0, 0, self.bg)
        pal.pixel(1, 0, self.fg)
        self.display.framebuf.blit(self._fbuf, self.padded_area.x, self.padded_area.y, key, pal)


class IconButton(Button):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        icon_file=None,
    ):
        """
        Initialize an IconButton widget to display an icon on a button.

        Args:
            parent (Widget): The parent widget or screen that contains this icon button.
            x (int): The x-coordinate of the icon button.
            y (int): The y-coordinate of the icon button.
            w (int): The width of the icon button.
            h (int): The height of the icon button.
            align (int): The alignment of the icon button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the icon button.
            bg (int): The background color of the icon button.
            visible (bool): The visibility of the icon button.
            value (str): The user-assigned value of the icon button.
            padding (tuple): The padding on each side of the icon button.
            icon_file (str): The icon file to display.

        Usage:
            icon_button = IconButton(screen, icon_file="icon.pbm")
        """
        fg = fg if fg is not None else parent.fg
        bg = bg if bg is not None else parent.bg
        self.icon = Icon(None, align=ALIGN.CENTER, fg=fg, bg=bg, value=icon_file)
        w = w or self.icon.width
        h = h or self.icon.height
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.icon.parent = self


class Toggle(IconButton):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=False,
        padding=None,
        on_file=None,
        off_file=None,
    ):
        """
        An IconButton that toggles between two states (on and off).  Serves as a base widget for
        ToggleButton, CheckBox, and RadioButton widgets but may be used on its own.  Requires an
        on_file and optionally an off_file.  If only a single file is provided, the widget will
        change colors when toggled, otherwise the icon will change.

        Args:
            parent (Widget): The parent widget or screen that contains this toggle button.
            x (int): The x-coordinate of the toggle button.
            y (int): The y-coordinate of the toggle button.
            w (int): The width of the toggle button.
            h (int): The height of the toggle button.
            align (int): The alignment of the toggle button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the toggle button.
            bg (int): The background color of the toggle button.
            visible (bool): The visibility of the toggle button.
            value (bool): The initial state of the toggle button.
            padding (tuple): The padding on each side of the toggle button.
            on_file (str): The icon file to display when the button is on.
            off_file (str): The icon file to display when the button is off.

        Usage:
            toggle = Toggle(screen, on_file="on.pbm", off_file="off.pbm")
        """
        if not on_file:
            raise ValueError("An on_file file must be provided.")
        self.on_file = on_file
        self.off_file = off_file
        icon_file = self.off_file if self.off_file and not value else self.on_file
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, icon_file
        )
        self.changed()

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.toggle)

    def toggle(self, data=None, event=None):
        """Toggle the on/off state of the button."""
        self.value = not self.value  # Invert the current state

    def changed(self):
        """Update the icon based on the current on/off state."""
        # Update the icon value based on the current toggle state
        if self.off_file:
            self.icon.value = self.on_file if self.value else self.off_file
        else:
            self.icon.fg = self.fg if self.value else self.color_theme.tertiary
        super().changed()  # Call the parent changed method


class ToggleButton(Toggle):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=False,
        padding=None,
        size=ICON_SIZE.LARGE,
    ):
        """
        Initialize a ToggleButton widget.

        Args:
            parent (Widget): The parent widget or screen that contains this toggle button.
            x (int): The x-coordinate of the toggle button.
            y (int): The y-coordinate of the toggle button.
            w (int): The width of the toggle button.
            h (int): The height of the toggle button.
            align (int): The alignment of the toggle button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the toggle button.
            bg (int): The background color of the toggle button.
            visible (bool): The visibility of the toggle button.
            value (bool): The initial state of the toggle button.
            padding (tuple): The padding on each side of the toggle button.
            size (int): The size of the toggle button (default is ICON_SIZE.LARGE).

        Usage:
            toggle_button = ToggleButton(screen, size=ICON_SIZE.LARGE)
        """
        on_file = icon_theme.toggle_on(size)
        off_file = icon_theme.toggle_off(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )


class CheckBox(Toggle):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=False,
        padding=None,
        size=ICON_SIZE.LARGE,
    ):
        """
        Initialize a CheckBox widget.

        Args:
            parent (Widget): The parent widget or screen that contains this check box.
            x (int): The x-coordinate of the check box.
            y (int): The y-coordinate of the check box.
            w (int): The width of the check box.
            h (int): The height of the check box.
            align (int): The alignment of the check box.
            align_to (Widget): The widget to align to.
            fg (int): The color of the check box.
            bg (int): The background color of the check box.
            visible (bool): The visibility of the check box.
            value (bool): The initial state of the check box.
            padding (tuple): The padding on each side of the check box.
            size (int): The size of the check box (default is ICON_SIZE.LARGE).

        Usage:
            check_box = CheckBox(screen, size=ICON_SIZE.LARGE)
        """
        on_file = icon_theme.check_box_checked(size)
        off_file = icon_theme.check_box_unchecked(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )


class RadioGroup:
    def __init__(self):
        """
        Initialize a RadioGroup to manage a group of RadioButtons.

        See Also:
            RadioButton
        """
        self.radio_buttons = []

    def add(self, radio_button):
        """
        Add a RadioButton to the group.

        Args:
            radio_button (RadioButton): The RadioButton to add to the group.
        """
        self.radio_buttons.append(radio_button)

    def set_checked(self, selected_button):
        """
        Ensure only the selected button is checked in the group.

        Args:
            selected_button (RadioButton): The RadioButton to check.
        """
        for radio_button in self.radio_buttons:
            radio_button.value = radio_button == selected_button


class RadioButton(Toggle):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=False,
        padding=None,
        size=ICON_SIZE.LARGE,
        group: RadioGroup = None,
    ):
        """
        Initialize a RadioButton widget.

        Args:
            parent (Widget): The parent widget or screen that contains this radio button.
            x (int): The x-coordinate of the radio button.
            y (int): The y-coordinate of the radio button.
            w (int): The width of the radio button.
            h (int): The height of the radio button.
            align (int): The alignment of the radio button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the radio button.
            bg (int): The background color of the radio button.
            visible (bool): The visibility of the radio button.
            value (bool): The initial state of the radio button.
            padding (tuple): The padding on each side of the radio button.
            size (int): The size of the radio button (default is ICON_SIZE.LARGE).
            group (RadioGroup): The RadioGroup to which this radio button belongs.

        Usage:
            radio_group = RadioGroup()
            radio_button = RadioButton(screen, group=radio_group)
        """
        if group is None:
            raise ValueError("RadioButton must be part of a RadioGroup.")
        self.group = group
        self.group.add(self)
        on_file = icon_theme.radio_button_checked(size)
        off_file = icon_theme.radio_button_unchecked(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )

    def toggle(self, data=None, event=None):
        """Toggle the checked state to true when clicked and uncheck other RadioButtons in the group."""
        if not self.value:  # Only toggle if not already checked
            self.group.set_checked(self)  # Uncheck all other buttons in the group


class ProgressBar(Widget):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=0.0,
        padding=None,
        vertical=False,
        reverse=False,
    ):
        """
        Initialize a ProgressBar widget to display a progress bar.

        Args:
            parent (Widget): The parent widget or screen that contains this progress bar.
            x (int): The x-coordinate of the progress bar.
            y (int): The y-coordinate of the progress bar.
            w (int): The width of the progress bar.
            h (int): The height of the progress bar.
            align (int): The alignment of the progress bar.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the progress bar.
            bg (int): The background color of the progress bar.
            visible (bool): The visibility of the progress bar.
            value (float): The initial value of the progress bar (0 to 1).
            padding (tuple): The padding on each side of the progress bar.
            vertical (bool): Whether the progress bar is vertical (True) or horizontal (False).
            reverse (bool): Whether the progress bar is reversed (True) or not (False).

        Usage:
            progress_bar = ProgressBar(screen)
        """
        w = w or (ICON_SIZE.SMALL if vertical else ICON_SIZE.SMALL * 4)
        h = h or (ICON_SIZE.SMALL if not vertical else ICON_SIZE.SMALL * 4)
        fg = fg if fg is not None else parent.color_theme.on_primary
        bg = bg if bg is not None else parent.color_theme.primary_variant
        self.vertical = vertical
        self.reverse = reverse
        self.end_radius = w // 2 if self.vertical else h // 2
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.end_radius = self.padded_area.w // 2 if self.vertical else self.padded_area.h // 2

    def draw_ends(self):
        """
        Draw the circular ends of the progress bar.
        """
        pa = self.padded_area
        if self.vertical:
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if self.reverse else self.bg,
                f=True,
            )
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + pa.h - self.end_radius,
                self.end_radius,
                self.fg if not self.reverse else self.bg,
                f=True,
            )
        else:
            self.display.framebuf.circle(
                pa.x + pa.w - self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if self.reverse else self.bg,
                f=True,
            )
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if not self.reverse else self.bg,
                f=True,
            )

    def draw(self, _=None):
        """
        Draw the progress bar on the screen.
        """
        self.draw_ends()
        x, y, w, h = self.padded_area
        if self.vertical:
            y += self.end_radius
            h -= w
        else:
            x += self.end_radius
            w -= h
        self.display.framebuf.fill_rect(x, y, w, h, self.bg)

        if self.value == 0:
            return

        if self.vertical:
            progress_height = int(self.value * h)
            if self.reverse:
                self.display.framebuf.fill_rect(x, y, w, progress_height, self.fg)
            else:
                self.display.framebuf.fill_rect(
                    x, y + h - progress_height, w, progress_height, self.fg
                )
        else:
            progress_width = int(self.value * w)
            if self.reverse:
                self.display.framebuf.fill_rect(
                    x + w - progress_width, y, progress_width, h, self.fg
                )
            else:
                self.display.framebuf.fill_rect(x, y, progress_width, h, self.fg)

    def changed(self):
        # Ensure value is between 0 and 1
        if self.value < 0:
            self.value = 0
        elif self.value > 1:
            self.value = 1
        super().changed()


class Slider(ProgressBar):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=0.0,
        padding=None,
        vertical=False,
        reverse=False,
        knob_color=None,
        step=0.1,
    ):
        """
        Initialize a Slider widget with a circular knob that can be dragged.

        Args:
            parent (Widget): The parent widget or screen that contains this slider.
            x (int): The x-coordinate of the slider.
            y (int): The y-coordinate of the slider.
            w (int): The width of the slider.
            h (int): The height of the slider.
            align (int): The alignment of the slider.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the slider.
            bg (int): The background color of the slider.
            visible (bool): The visibility of the slider.
            value (float): The initial value of the slider (0 to 1).
            padding (tuple): The padding on each side of the slider.
            vertical (bool): Whether the slider is vertical (True) or horizontal (False).
            reverse (bool): Whether the slider is reversed (True) or not (False).
            knob_color (int): The color of the knob.
            step (float): The step size for value adjustments.

        Usage:
            slider = Slider(screen, vertical=True, step=0.1)
        """
        if vertical:
            w = w or ICON_SIZE.SMALL
            h = h or parent.height if parent else 6 * ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.RIGHT
        else:
            w = w or parent.width if parent else 6 * ICON_SIZE.SMALL
            h = h or ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.BOTTOM
        self.knob_color = knob_color if knob_color is not None else parent.color_theme.secondary
        self.step = step  # Step size for value adjustments
        self.dragging = False  # Track whether the knob is being dragged
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, vertical, reverse
        )
        self.knob_radius = self.end_radius

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.event_callback)
        self.add_event_cb(events.MOUSEBUTTONUP, self.event_callback)
        self.add_event_cb(events.MOUSEMOTION, self.event_callback)

    def draw(self, _=None):
        """Draw the slider, including the progress bar and the circular knob."""
        super().draw()  # Draw the base progress bar

        # Calculate the position of the knob
        knob_center = self._get_knob_center()

        # Draw the knob as a filled circle with correct radius
        self.display.framebuf.circle(*knob_center, self.knob_radius, self.knob_color, f=True)

    def event_callback(self, data, event):
        """Handle user input events like clicks, dragging, and mouse movements."""
        if self.dragging:
            if event.type == events.MOUSEBUTTONUP:
                self.dragging = False
            elif event.type == events.MOUSEMOTION:
                # Adjust the value based on mouse movement while dragging
                if self.vertical:
                    relative_pos = (
                        self._get_knob_center()[1] - self.display.translate_point(event.pos)[1]
                    ) / self.height
                else:
                    relative_pos = (
                        self.display.translate_point(event.pos)[0] - self._get_knob_center()[0]
                    ) / self.width
                self.adjust_value(relative_pos)

        elif (
            self._point_in_knob(self.display.translate_point(event.pos))
            and event.type == events.MOUSEBUTTONDOWN
        ):
            self.dragging = True
        elif (
            self.area.contains(self.display.translate_point(event.pos))
            and event.type == events.MOUSEBUTTONDOWN
        ):
            # Clicking outside the knob moves the slider by one step
            positive = True
            if self.vertical:
                if self.display.translate_point(event.pos)[1] > self._get_knob_center()[1]:
                    positive = False
            else:
                if self.display.translate_point(event.pos)[0] < self._get_knob_center()[0]:
                    positive = False
            self.adjust_value(self.step if positive else -self.step)

        super().handle_event(event)

    def adjust_value(self, value):
        """Adjust the slider value by one step in the specified direction."""
        if self.reverse:
            value = -value
        self.value = max(0, min(1, self.value + value))

    def _get_knob_center(self):
        """Calculate the center coordinates for the knob based on the current value."""
        x, y, w, h = self.padded_area
        value = self.value if self.reverse == self.vertical else 1 - self.value
        if self.vertical:
            span = h - w
            knob_y = int(y + value * span) + self.knob_radius
            knob_center = (x + self.knob_radius, knob_y)
        else:
            span = w - h
            knob_x = int(x + value * span) + self.knob_radius
            knob_center = (knob_x, y + self.knob_radius)
        return knob_center

    def _point_in_knob(self, pos):
        """Check if the given point is within the knob's circular area."""
        knob_center = self._get_knob_center()
        distance = ((pos[0] - knob_center[0]) ** 2 + (pos[1] - knob_center[1]) ** 2) ** 0.5
        return distance <= self.knob_radius


class ScrollBar(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=0.0,
        padding=None,
        vertical=False,
        reverse=False,
        knob_color=None,
        step=0.1,
    ):
        """
        Initialize a ScrollBar widget with two arrow IconButtons and a Slider.

        Args:
            parent (Widget): The parent widget or screen that contains this scroll bar.
            x (int): The x-coordinate of the scroll bar.
            y (int): The y-coordinate of the scroll bar.
            w (int): The width of the scroll bar.
            h (int): The height of the scroll bar.
            align (int): The alignment of the scroll bar.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the scroll bar.
            bg (int): The background color of the scroll bar.
            visible (bool): The visibility of the scroll bar.
            value (float): The initial value of the scroll bar (0 to 1).
            padding (tuple): The padding on each side of the scroll bar.
            vertical (bool): Whether the scroll bar is vertical (True) or horizontal (False).
            reverse (bool): Whether the scroll bar is reversed (True) or not (False).
            knob_color (int): The color of the knob.
            step (float): The step size for value adjustments.

        Usage:
            scroll_bar = ScrollBar(screen, vertical=True, step=0.1)
        """

        if vertical:
            w = w or ICON_SIZE.SMALL
            h = h or parent.height if parent else 6 * ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.RIGHT
            icon_size = w
        else:
            w = w or parent.width if parent else 6 * ICON_SIZE.SMALL
            h = h or ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.BOTTOM
            icon_size = h
        reverse = (
            not reverse if vertical else reverse
        )  # Reverse the direction for vertical sliders
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

        # Add IconButton on each end and Slider in the middle
        if vertical:
            self.pos_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.up_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.TOP,
            )
            self.neg_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.down_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.BOTTOM,
            )
            self.slider = Slider(
                self,
                w=icon_size,
                h=h - 2 * icon_size,
                vertical=True,
                align=ALIGN.CENTER,
                value=value,
                step=step,
                reverse=reverse,
                knob_color=knob_color,
                fg=fg,
                bg=bg,
            )
        else:
            self.neg_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.left_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.LEFT,
            )
            self.pos_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.right_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.RIGHT,
            )
            self.slider = Slider(
                self,
                w=w - icon_size * 2,
                h=icon_size,
                vertical=False,
                align=ALIGN.CENTER,
                value=value,
                step=step,
                reverse=reverse,
                knob_color=knob_color,
                fg=fg,
                bg=bg,
            )

        # Set button callbacks to adjust slider value
        self.neg_button.add_event_cb(
            events.MOUSEBUTTONDOWN, lambda _, e: self.slider.adjust_value(-self.slider.step)
        )
        self.pos_button.add_event_cb(
            events.MOUSEBUTTONDOWN, lambda _, e: self.slider.adjust_value(self.slider.step)
        )


class DigitalClock(Label):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        text_height=TEXT_SIZE.LARGE,
        scale=1,
    ):
        """
        Initialize a DigitalClock widget to display the current time.

        Args:
            parent (Widget): The parent widget or screen that contains this digital clock.
            x (int): The x-coordinate of the digital clock.
            y (int): The y-coordinate of the digital clock.
            w (int): The width of the digital clock.
            h (int): The height of the digital clock.
            align (int): The alignment of the digital clock.
            align_to (Widget): The widget to align to.
            fg (int): The color of the digital clock.
            bg (int): The background color of the digital clock.
            visible (bool): The visibility of the digital clock.
            value (str): The initial value of the digital clock.
            padding (tuple): The padding on each side of the digital clock.
            text_height (int): The height of the text (default is TEXT_SIZE.LARGE).
            scale (int): The scale of the text (default is 1).

        Usage:
            clock = DigitalClock(screen, text_height=TEXT_SIZE.LARGE, scale=2)
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        fg = fg if fg is not None else parent.fg
        bg = bg if bg is not None else parent.bg
        w = w or (TEXT_WIDTH) * 8 * scale
        super().__init__(
            parent,
            x,
            y,
            w,
            h,
            align,
            align_to,
            fg,
            bg,
            visible,
            value,
            padding,
            text_height,
            scale,
        )
        self.task = self.display.add_task(self.update_time, 1000)

    def update_time(self):
        if self.visible:
            _y, _m, _d, h, min, sec, *_ = localtime()
            self.value = f"{h:02}:{min:02}:{sec:02}"


class ListView(Widget):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        padding=None,
    ):
        """
        Initialize a ListView widget to display a list of items.

        Args:
            parent (Widget): The parent widget or screen that contains this list view.
            x (int): The x-coordinate of the list view.
            y (int): The y-coordinate of the list view.
            w (int): The width of the list view.
            h (int): The height of the list view.
            align (int): The alignment of the list view.
            align_to (Widget): The widget to align to.
            fg (int): The color of the list view.
            bg (int): The background color of the list view.
            visible (bool): The visibility of the list view.
            padding (tuple): The padding on each side of the list view.

        Usage:
            list_view = ListView(screen)
            button1 = Button(list_view, label="Button 1", value=1)
            button2 = Button(list_view, label="Button 2", value=2)
        """
        fg = fg if fg is not None else parent.color_theme.on_primary
        bg = bg if bg is not None else parent.color_theme.primary
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value=0, padding=padding
        )
        self.scrollbar = ScrollBar(
            parent,
            vertical=True,
            h=h,
            fg=fg,
            bg=bg,
            visible=False,
            align_to=self,
            align=ALIGN.OUTER_RIGHT,
        )
        self.scrollbar.slider.set_change_cb(self.scroll)

    def add_child(self, child: Widget):
        """Adds a child widget to the current widget."""
        self.children.append(child)
        self.reassign_positions()

    def remove_child(self, child: Widget):
        """Removes a child widget from the current widget."""
        self.children.remove(child)
        self.reassign_positions()

    def reassign_positions(self):
        """Reassign the positions of all children after one is removed."""
        self._value = min(self._value, len(self.children) - 1)
        for i, child in enumerate(self.children):
            child.visible = False
            if i == 0:
                child.set_position(0, 0, self.width, None, align=ALIGN.TOP_LEFT, align_to=self)
            else:
                child.set_position(
                    0,
                    child.height,
                    self.width,
                    None,
                    align=ALIGN.BOTTOM_LEFT,
                    align_to=self.children[i - 1],
                )
        self.config_scrollbar()

    def config_scrollbar(self):
        """Configure the scrollbar based on the number of children."""
        if len(self.children) > 1:
            self.scrollbar.slider.step = 1 / (len(self.children) - 1)
        self.changed()

    def scroll(self, sender):
        """Read the value of the scrollbar and scroll the list view accordingly."""
        self.value = int(self.scrollbar.slider.value * (len(self.children) - 1))

    def scroll_up(self):
        """Scroll the list view up by one item."""
        self.value -= 1

    def scroll_down(self):
        """Scroll the list view down by one item."""
        self.value += 1

    def changed(self):
        """Update the list view when the value changes."""
        if self.value < 0:
            self._value = 0
        elif self.value >= len(self.children):
            self._value = len(self.children) - 1

        for child in self.children:
            child.visible = False

        sb_visible = False
        if len(self.children):
            self.children[0].y = -sum([child.height for child in self.children[: self.value]])
            for child in self.children:
                if self.area.contains_area(child.area):
                    child.visible = True
                else:
                    sb_visible = True
        self.scrollbar.visible = sb_visible
        if sb_visible:
            self.scrollbar.slider.value = self.value / (len(self.children) - 1)
        super().changed()
