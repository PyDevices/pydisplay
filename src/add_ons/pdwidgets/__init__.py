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
    tick: Calls the tick method of all Display objects.
    init_timer: Records the desired tick period (compatibility shim).
    pump: Processes one widget frame during setup bursts.
    run_forever: Drives the cooperative widget loop until quit.

Optional add-on dependency:
    ``Label`` (and widgets built on it) gains proportional-font rendering when a
    ``font`` module is supplied. That path lazily imports **``add_ons/tft_write``**
    (the russhughes ``write_font_converter`` renderer) — the only ``add_ons/*``
    module pdwidgets touches, and only when a proportional font is actually
    used. The default romfont path has no such dependency.

Timer architecture:
    pdwidgets owns **no** timer of its own. Frames are driven cooperatively from
    a single poll function that ``multimer.loop.run_forever`` runs either in a
    plain ``while`` loop (sync) or on the shared ``asyncio`` loop (async),
    selected automatically from ``board_config.runtime.timer_async``. This is the
    ``apollo.py`` pattern: own no timer, poll ``tick()`` from the loop callback.

    An earlier design created a plain sync ``multimer.Timer`` inside
    ``init_timer`` even when ``runtime.timer_async`` was ``True``, which raced the
    asyncio loop with a background sync timer — exactly the "competing timer"
    the repo forbids once ``timer_async`` is ``True``. Driving ticks from the
    loop instead means ``Display.timer`` is always ``None`` and there is never a
    sync timer running alongside the async loop, on any runtime (desktop SDL/PG,
    MicroPython/CircuitPython unix, ``micropython.exe``, PyScript, Jupyter). It
    also keeps ``multimer`` untouched — only its public loop helpers are used.
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
    Call the ``tick`` method of every registered :class:`Display`.

    Args:
        _ (Any): Ignored positional argument so this may also be used as a
            timer/``on_tick`` callback signature.
    """
    for display in Display.displays:
        display.tick()


def init_timer(period=10):
    """
    Record the desired widget tick period (compatibility shim).

    pdwidgets no longer owns a timer (see the module "Timer architecture"
    note): frames are driven cooperatively by :func:`run_forever` / :func:`pump`.
    This function is retained so existing examples that call
    ``pd.init_timer(10)`` keep working; it only stores ``period`` as the poll
    delay used by :func:`run_forever`.

    Args:
        period (int): The desired inter-frame period in milliseconds.
    """
    Display.tick_period = period


def _poll_widgets():
    """Poll all widget displays; return True when quit is requested."""
    for display in list(Display.displays):
        runtime = display.runtime
        if runtime is not None and runtime.quit_requested:
            return True
        if runtime is None:
            continue
        if elist := runtime.poll():
            for e in elist:
                if e.type == events.QUIT:
                    return True
                if e.type in events.filter:
                    display.handle_event(e)
    return False


def pump():
    """
    Process one widget frame during setup bursts (before :func:`run_forever`).

    Because pdwidgets owns no timer, this always calls :func:`tick` so drawing
    performed while building the UI (e.g. a ``Console`` writing in a ``while``
    loop) is flushed to the display.
    """
    tick()


def run_forever():
    """
    Drive the cooperative widget loop until quit is requested.

    Uses ``multimer.loop.run_forever``, which selects a plain ``while`` loop
    (sync) or the shared ``asyncio`` loop (async) based on
    ``board_config.runtime.timer_async``. The poll callback calls :func:`tick`
    (flush dirty regions, run tasks, redraw) then polls the runtime for events.
    No timer is created, so an async loop never coexists with a sync timer.
    """
    from multimer.loop import run_forever as multimer_run_forever

    def poll():
        tick()
        return _poll_widgets()

    multimer_run_forever(poll, delay_ms=Display.tick_period)


_POINTER_EVENTS = (events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP, events.MOUSEMOTION)


def _cond_pointer(child, event, point):
    """Event condition: child's padded area contains the (translated) pointer."""
    return child.padded_area.contains(point)


def _cond_always(child, event, point):
    """Event condition: always deliver (non-pointer events)."""
    return True


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
        """
        Remove a previously registered event callback.

        Args:
            event_type (int): ``eventsys.events`` constant the callback was
                registered for.
            callback (callable): The callback to remove. No error if absent.
        """
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].pop(callback, None)

    def handle_event(self, event, condition=None, point=None):
        """
        Handle an event and propagate it to child widgets.

        Subclasses that need to handle events should override this method and
        call it to propagate the event to children.

        The default ``condition`` is a module-level function (not a per-call
        closure), and for pointer events the pointer is translated to display
        coordinates once per dispatch rather than once per child.

        Args:
            event (Event): The event to handle.
            condition (callable): ``condition(child, event, point)`` returning
                True when the event should be delivered to ``child``. Defaults
                to a pointer-hit test for mouse events, else always True.
            point (tuple): Pre-translated pointer position, shared across the
                recursion for pointer events.
        """
        if condition is None:
            if event.type in _POINTER_EVENTS:
                condition = _cond_pointer
                point = self.display.translate_point(event.pos)
            else:
                condition = _cond_always
        for child in self.children:
            if child.visible:
                if condition(child, event, point):
                    for callback, data in child._event_callbacks.get(event.type, {}).items():
                        callback(data, event)
                child.handle_event(event, condition, point)

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
        """
        Show or hide the widget.

        Args:
            hide (bool): ``True`` to hide, ``False`` to show.
        """
        self.visible = not hide

    def invalidate(self):
        """Mark this widget (and its descendants) as needing a redraw."""
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
        """
        Set the callback invoked when the widget's value changes.

        Args:
            callback (callable): Called as ``callback(widget)`` on change.
        """
        self._change_callback = callback

    def set_position(self, x=None, y=None, w=None, h=None, align=None, align_to=None):
        """
        Update any subset of the widget's geometry and re-layout.

        Only the arguments that are not ``None`` are changed. Changing geometry
        invalidates the parent so the affected area is redrawn.

        Args:
            x (int): New relative x-coordinate.
            y (int): New relative y-coordinate.
            w (int): New width.
            h (int): New height.
            align (int): New ``ALIGN`` constant.
            align_to (Widget): New widget to align against.
        """
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
        """Redraw this widget if invalidated, then clear its dirty flags."""
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
        """
        Set the widget's value (equivalent to assigning ``widget.value``).

        Args:
            value: The new value; triggers ``changed`` when it differs.
        """
        self.value = value

    def set_modal(self, modal=True):
        """
        Grab or release modal pointer capture for this widget.

        While a widget is modal, the :class:`Display` routes all pointer events
        (mouse/touch) through this widget's branch only, so widgets elsewhere in
        the tree do not receive them. Non-pointer events (e.g. key events) are
        unaffected. This is used by :class:`Dialog` and :class:`Dropdown` to
        implement modal overlays without a separate event layer. Modality nests:
        the most recently grabbed widget wins, and releasing restores the
        previous one.

        Args:
            modal (bool): ``True`` to grab modal capture, ``False`` to release.
        """
        modals = self.display._modals
        if modal:
            if self not in modals:
                modals.append(self)
        elif self in modals:
            modals.remove(self)


class Display(Widget):
    displays = []
    timer = None  # pdwidgets owns no timer; kept as None for API/back-compat.
    tick_period = 10  # Poll delay (ms) used by run_forever; set via init_timer.

    def __init__(self, display_drv, runtime, tfa=0, bfa=0, format=RGB565):
        """
        Initialize a Display object to manage the display and child widgets.

        Args:
            display_drv (DisplayDriver): The display driver object that manages the display hardware.
            runtime (Runtime): The event runtime object that manages the event system.
            tfa (int): The top fixed area of the display.
            bfa (int): The bottom fixed area of the display.
            format (int): The color format of the display (default is RGB565).

        Usage:
            from board_config import display_drv, runtime
            display = Display(display_drv, runtime)
        """
        self.display_drv = display_drv
        super().__init__(
            None, 0, 0, display_drv.width, display_drv.height, fg=-1, bg=0, padding=(0, 0, 0, 0)
        )
        display_drv.set_vscroll(tfa, bfa)
        display_drv.vscroll = 0
        self.runtime = runtime
        self._buffer = memoryview(
            bytearray(display_drv.width * display_drv.height * display_drv.color_depth // 8)
        )
        self.framebuf = FrameBuffer(self._buffer, display_drv.width, display_drv.height, format)
        self._dirty_areas = []
        self._tasks = []
        self._tick_busy = False
        self._modals = []  # modal-capture stack (see Widget.set_modal)
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
    def _modal(self):
        """The widget currently holding modal pointer capture, or None."""
        return self._modals[-1] if self._modals else None

    def handle_event(self, event, condition=None, point=None):
        """
        Dispatch an event, honoring modal pointer capture.

        When a widget has grabbed modal capture (see :meth:`Widget.set_modal`)
        and the event is a pointer event, it is routed only through that
        widget's branch — everything else on screen is inert. All other events
        (and the non-modal case) fall through to the normal
        :meth:`Widget.handle_event` traversal.
        """
        modal = self._modal
        if modal is not None and modal.visible and event.type in _POINTER_EVENTS:
            point = self.translate_point(event.pos)
            for callback, data in modal._event_callbacks.get(event.type, {}).items():
                callback(data, event)
            modal.handle_event(event, _cond_pointer, point)
            return
        super().handle_event(event, condition, point)

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
        """
        Schedule a repeating task run from :meth:`tick`.

        Args:
            callback (callable): Zero-argument callable to run.
            delay (int): Interval between runs, in milliseconds.

        Returns:
            Task: The created task (pass to :meth:`remove_task` to cancel).
        """
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
        self.display_drv.show()

    def remove_task(self, task):
        """
        Cancel a scheduled task.

        Args:
            task (Task): A task previously returned by :meth:`add_task`.
        """
        self._tasks.remove(task)

    def quit(self):
        """Remove this display from the active list (called on QUIT)."""
        if self in Display.displays:
            Display.displays.remove(self)

    def tick(self):
        """
        Run one frame of the widget event loop.

        Flushes dirty areas to the display, otherwise polls ``runtime`` for events,
        runs scheduled tasks, and re-renders invalidated widgets. Call from a timer
        (see ``init_timer``) or your main loop.
        """
        if self._tick_busy:
            return
        self._tick_busy = True

        if self._dirty_areas:
            # Coalesce touching/overlapping dirty rectangles before flushing.
            # Take ownership of the pending list up front so we never mutate a
            # list while iterating it, and merge transitively (a freshly merged
            # area may now touch one merged earlier).
            pending = self._dirty_areas
            self._dirty_areas = []
            merged = []
            for area in pending:
                i = 0
                while i < len(merged):
                    if area.touches_or_intersects(merged[i]):
                        area += merged.pop(i)
                        i = 0
                    else:
                        i += 1
                merged.append(area)

            for dirty in merged:
                self.refresh(dirty)
        else:
            t = ticks_ms()
            for task in self._tasks:
                if t >= task.next_run:
                    task.run(t)

            self.render_dirty_widgets()
        self._tick_busy = False

    def render_dirty_widgets(self):
        """Redraw all invalidated widgets, breadth-first, without recursion."""
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
        shadow=0,
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
            shadow (int): Fake drop-shadow offset in pixels drawn behind the
                button in ``color_theme.shadow`` (0 disables; the default).
        """
        self.radius = radius
        self.pressed_offset = pressed_offset
        self.shadow = shadow
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
        Draw the button background and shape (with an optional drop shadow).
        """
        self.parent.draw(self.area)
        pa = self.padded_area
        if self.shadow:
            # Cheap fake drop shadow: a shape-colored round_rect offset behind
            # the button. Two fills, no alpha blending.
            self.display.framebuf.round_rect(
                pa.x + self.shadow,
                pa.y + self.shadow,
                pa.w,
                pa.h,
                self.radius,
                self.color_theme.shadow,
                f=True,
            )
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)

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
        font=None,
    ):
        """
        Initialize a Label widget to display text.

        By default the built-in 8-pixel-wide romfont is used. Passing ``font``
        (a proportional bitmap font module from the ``write_font_converter``
        pipeline, e.g. ``chango_32``) renders the text with the optional
        ``add_ons/tft_write`` renderer instead — see the module docstring note
        on that dependency. Proportional text is opaque, so a solid ``bg`` is
        used (the parent's ``bg`` when none is given).

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
            text_height (int): The height of the romfont text (default TEXT_SIZE.LARGE).
            scale (int): The scale of the romfont text (default is 1).
            inverted (bool): Invert the romfont text (default is False).
            font_data (str): Alternate romfont file/memoryview for the text.
            font (module): Proportional bitmap font module (``tft_write`` style);
                when given, overrides romfont rendering and sizing.
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        padding = padding if padding is not None else (0, 0, 0, 0)
        value = value if value is not None else ""
        self._font = font
        if font is not None:
            from tft_write import write_width

            w = w or write_width(font, value) + padding[0] + padding[2]
            h = h or font.HEIGHT + padding[1] + padding[3]
            bg = bg if bg is not None else parent.bg
        else:
            w = w or len(value) * TEXT_WIDTH * scale + padding[0] + padding[2]
            h = h or text_height * scale + padding[1] + padding[3]
        align = align if align is not None else ALIGN.CENTER
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
        x, y, _, _ = self.padded_area
        if self._font is not None:
            # Proportional font: tft_write fills each glyph's background itself.
            from tft_write import write as _tft_write

            bg = self.bg if self.bg is not self.parent.color_theme.transparent else self.parent.bg
            self.display.framebuf.fill_rect(*self.padded_area, bg)
            _tft_write(self.display.framebuf, self._font, self.value, x, y, self.fg, bg)
            return
        if self.bg is not self.parent.color_theme.transparent:
            self.display.framebuf.fill_rect(
                *self.padded_area, self.bg
            )  # Draw background if bg is specified
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
    # Reusable 2-entry (bg, fg) palette. Rewritten on every draw, so a single
    # shared buffer avoids allocating a 4-byte FrameBuffer per draw call.
    _palette = FrameBuffer(memoryview(bytearray(4)), 2, 1, RGB565)

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
        chroma=None,
    ):
        """
        Initialize an Icon widget to display an icon.

        Two asset kinds are supported, both loaded via ``FrameBuffer.from_file``:

        * **Monochrome ``.pbm``** (1 bit-per-pixel) — recolored to the icon's
          ``fg``/``bg`` at draw time via a 2-entry palette (the default).
        * **Color RGB565 ``.bmp`` (BMP565)** — blitted as-is; pass ``chroma`` to
          treat one color as transparent. No PNG is used anywhere.

        Args:
            parent (Widget): The parent widget or screen that contains this icon.
            x (int): The x-coordinate of the icon.
            y (int): The y-coordinate of the icon.
            w (int): The width of the icon.
            h (int): The height of the icon.
            align (int): The alignment of the icon.
            align_to (Widget): The widget to align to.
            fg (int): The color of the icon (monochrome assets only).
            bg (int): The background color of the icon.
            visible (bool): The visibility of the icon.
            value (str): The icon file to display (``.pbm`` or BMP565 ``.bmp``).
            padding (tuple): The padding on each side of the icon.
            chroma (int): Transparent color key for color (BMP565) icons.

        Usage:
            icon = Icon(screen, value="icon.pbm")
            status = Icon(bar, value="battery_color_24dp.bmp")
        """
        if not value:
            raise ValueError("Icon value must be set to the filename with path.")
        self.chroma = chroma
        self.load_icon(value)
        padding = padding if padding is not None else DEFAULT_PADDING
        w = w or self._icon_width + padding[0] + padding[2]
        h = h or self._icon_height + padding[1] + padding[3]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def load_icon(self, value):
        """Load icon file, cache it, and record whether it is a color asset."""
        if value in Icon.cache:
            self._fbuf = Icon.cache[value]
        else:
            self._fbuf = FrameBuffer.from_file(value)
            Icon.cache[value] = self._fbuf
        self._icon_width, self._icon_height = self._fbuf.width, self._fbuf.height
        self._is_color = self._fbuf.format == RGB565
        self._swapped = None

    def _swapped_color(self):
        """Return (byteswapped color FrameBuffer, swapped chroma), cached."""
        if self._swapped is None:
            src = self._fbuf.buffer
            swp = bytearray(len(src))
            swp[0::2] = src[1::2]
            swp[1::2] = src[0::2]
            fbuf = FrameBuffer(memoryview(swp), self._fbuf.width, self._fbuf.height, RGB565)
            chroma = self.chroma
            if chroma is not None:
                chroma = ((chroma & 0xFF) << 8) | (chroma >> 8)
            self._swapped = (fbuf, chroma)
        return self._swapped

    def changed(self):
        """Update the icon when the value (file) changes."""
        self.display.framebuf.fill_rect(*self.padded_area, self.bg)
        self.load_icon(self.value)
        super().changed()

    def draw(self, _=None):
        """
        Draw the icon on the screen.

        Color (BMP565) icons are blitted directly (with ``chroma`` as the
        transparent key when set); monochrome icons are recolored to
        ``fg``/``bg`` via the shared 2-entry palette buffer.
        """
        px, py = self.padded_area.x, self.padded_area.y
        if self._is_color:
            fbuf = self._fbuf
            chroma = self.chroma
            # BMP565 assets are stored non-swapped; match the display's byte
            # order when it draws pre-swapped colors (swapped MCU panels).
            if self.display.needs_swap:
                fbuf, chroma = self._swapped_color()
            if chroma is not None:
                self.display.framebuf.blit(fbuf, px, py, chroma)
            else:
                self.display.framebuf.blit(fbuf, px, py)
            return
        pal = Icon._palette
        if self.bg is self.parent.color_theme.transparent:
            key = ~self.fg
            pal.pixel(0, 0, key)
        else:
            key = -1
            pal.pixel(0, 0, self.bg)
        pal.pixel(1, 0, self.fg)
        self.display.framebuf.blit(self._fbuf, px, py, key, pal)


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


class RadioGroup(Widget):
    def __init__(self, parent: Widget):
        """
        Initialize a RadioGroup to manage a group of RadioButtons.

        RadioGroup is a real (but invisible, zero-size) :class:`Widget` so it
        participates in the widget tree for lifecycle consistency with every
        other widget. It draws nothing and is skipped by the dirty-rect render
        pass (``invalidate`` and ``draw`` are no-ops). The member RadioButtons
        are normal children of their own parent; the group only tracks them for
        mutual exclusion.

        Args:
            parent (Widget): The parent widget or screen that owns this group.

        See Also:
            RadioButton
        """
        self.radio_buttons = []
        super().__init__(parent, x=0, y=0, w=0, h=0, visible=False)
        self._w = self._h = 0

    def invalidate(self):
        """No-op: an invisible, zero-size group never needs redrawing."""

    def draw(self, area=None):
        """No-op: the group draws nothing."""

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


def _root_screen(widget):
    """Return the top-level screen ancestor of ``widget`` (child of the Display)."""
    node = widget
    while node.parent is not None and node.parent.parent is not None:
        node = node.parent
    return node


class Card(Widget):
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
        radius=8,
        shadow=2,
        title=None,
        font=None,
    ):
        """
        Initialize a Card: a rounded, optionally-shadowed container for grouping
        other widgets.

        The card paints a rounded ``surface`` rectangle (with a cheap fake drop
        shadow) and, optionally, a title along its top. Add child widgets to it
        exactly like any other container.

        Args:
            parent (Widget): The parent widget or screen that contains this card.
            x (int): The x-coordinate of the card.
            y (int): The y-coordinate of the card.
            w (int): The width of the card.
            h (int): The height of the card.
            align (int): The alignment of the card.
            align_to (Widget): The widget to align to.
            fg (int): The foreground (text) color; defaults to ``on_surface``.
            bg (int): The card surface color; defaults to ``surface``.
            visible (bool): The visibility of the card.
            value (Any): User-assigned value of the card.
            padding (tuple): The padding on each side of the card.
            radius (int): The corner radius of the card (default is 8).
            shadow (int): Fake drop-shadow offset in pixels (0 disables).
            title (str): Optional title drawn along the top of the card.
            font (module): Optional proportional font module for the title.

        Usage:
            card = Card(screen, w=200, h=120, title="Settings")
            Switch(card, align=pd.ALIGN.CENTER)
        """
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.radius = radius
        self.shadow = shadow
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.title_label = None
        if title:
            self.title_label = Label(
                self,
                value=title,
                x=radius,
                y=PAD,
                align=ALIGN.TOP_LEFT,
                fg=fg,
                bg=bg,
                font=font,
            )

    def draw(self, _=None):
        """Draw the card's shadow and rounded surface."""
        self.parent.draw(self.area)
        pa = self.padded_area
        if self.shadow:
            self.display.framebuf.round_rect(
                pa.x + self.shadow,
                pa.y + self.shadow,
                pa.w,
                pa.h,
                self.radius,
                self.color_theme.shadow,
                f=True,
            )
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)


class _Layout(Widget):
    """
    Base for :class:`Row` / :class:`Column`: stacks children with fixed spacing.

    Not a full flexbox engine — children are laid out in insertion order along
    one axis (with a constant gap between them); the cross axis is left to each
    child's own alignment. Re-layout happens automatically whenever a child is
    added or removed.
    """

    _vertical = True

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
        spacing=PAD,
    ):
        self.spacing = spacing
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def add_child(self, child):
        """Add a child widget, then re-flow the layout."""
        self.children.append(child)
        self._layout()
        child.invalidate()

    def remove_child(self, child):
        """Remove a child widget, then re-flow the layout."""
        self.children.remove(child)
        self._layout()
        self.invalidate()

    def _layout(self):
        """Position children sequentially along the layout axis."""
        offset = 0
        for child in self.children:
            if self._vertical:
                child.set_position(x=0, y=offset, align=ALIGN.TOP_LEFT, align_to=self)
                offset += child.height + self.spacing
            else:
                child.set_position(x=offset, y=0, align=ALIGN.TOP_LEFT, align_to=self)
                offset += child.width + self.spacing


class Row(_Layout):
    """
    A container that lays its children out left-to-right with fixed spacing.

    Args:
        parent (Widget): The parent widget or screen that contains this row.
        x (int): The x-coordinate of the row.
        y (int): The y-coordinate of the row.
        w (int): The width of the row.
        h (int): The height of the row.
        align (int): The alignment of the row.
        align_to (Widget): The widget to align to.
        fg (int): The foreground color of the row.
        bg (int): The background color of the row.
        visible (bool): The visibility of the row.
        value (Any): User-assigned value of the row.
        padding (tuple): The padding on each side of the row.
        spacing (int): Gap in pixels inserted between children (default PAD).

    Usage:
        row = Row(screen, spacing=6)
        Button(row, label="A")
        Button(row, label="B")
    """

    _vertical = False


class Column(_Layout):
    """
    A container that stacks its children top-to-bottom with fixed spacing.

    Args:
        parent (Widget): The parent widget or screen that contains this column.
        x (int): The x-coordinate of the column.
        y (int): The y-coordinate of the column.
        w (int): The width of the column.
        h (int): The height of the column.
        align (int): The alignment of the column.
        align_to (Widget): The widget to align to.
        fg (int): The foreground color of the column.
        bg (int): The background color of the column.
        visible (bool): The visibility of the column.
        value (Any): User-assigned value of the column.
        padding (tuple): The padding on each side of the column.
        spacing (int): Gap in pixels inserted between children (default PAD).

    Usage:
        col = Column(screen, spacing=6)
        Label(col, value="One")
        Label(col, value="Two")
    """

    _vertical = True


class Badge(Widget):
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
        size=12,
    ):
        """
        Initialize a Badge: a small colored status dot or count pill.

        With no ``value`` the badge is a filled dot (useful as a connection or
        status indicator); with a short ``value`` (e.g. a notification count) it
        becomes a rounded pill containing the text.

        Args:
            parent (Widget): The parent widget or screen that contains this badge.
            x (int): The x-coordinate of the badge.
            y (int): The y-coordinate of the badge.
            w (int): The width of the badge (auto-sized when omitted).
            h (int): The height of the badge (auto-sized when omitted).
            align (int): The alignment of the badge.
            align_to (Widget): The widget to align to.
            fg (int): The text color; defaults to ``on_error``.
            bg (int): The badge color; defaults to ``error``.
            visible (bool): The visibility of the badge.
            value (Any): Optional short text/count; ``None`` draws a plain dot.
            padding (tuple): The padding on each side of the badge.
            size (int): Diameter (dot) or height (pill) in pixels (default 12).

        Usage:
            online = Badge(bar, bg=screen.color_theme.success)  # status dot
            unread = Badge(icon, value=3, align=pd.ALIGN.OUTER_TOP_RIGHT)  # pill
        """
        bg = bg if bg is not None else parent.color_theme.error
        fg = fg if fg is not None else parent.color_theme.on_error
        padding = padding if padding is not None else (0, 0, 0, 0)
        self.size = size
        text = "" if value is None else str(value)
        if text:
            w = w or max(size, len(text) * TEXT_WIDTH + PAD * 3)
            h = h or size
        else:
            w = w or size
            h = h or size
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """Draw the badge as a dot (no value) or a rounded pill (with text)."""
        self.parent.draw(self.area)
        pa = self.padded_area
        text = "" if self._value is None else str(self._value)
        if text:
            self.display.framebuf.round_rect(*pa, pa.h // 2, self.bg, f=True)
            tx = pa.x + (pa.w - len(text) * TEXT_WIDTH) // 2
            ty = pa.y + (pa.h - TEXT_SIZE.SMALL) // 2
            self.display.framebuf.text(text, tx, ty, self.fg, height=TEXT_SIZE.SMALL)
        else:
            r = pa.h // 2
            self.display.framebuf.circle(pa.x + r, pa.y + r, r, self.bg, f=True)


class Switch(Widget):
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
        value=False,
        padding=None,
        on_color=None,
        off_color=None,
        knob_color=None,
    ):
        """
        Initialize a Switch: an iOS-style sliding on/off toggle.

        A rounded "pill" track with a circular knob that sits left (off) or
        right (on); tapping anywhere on it flips the state. This is a visual
        alternative to the icon-swapping :class:`ToggleButton`, built from the
        same cheap ``round_rect`` + ``circle`` primitives as :class:`Slider`.

        Args:
            parent (Widget): The parent widget or screen that contains this switch.
            x (int): The x-coordinate of the switch.
            y (int): The y-coordinate of the switch.
            w (int): The width of the switch (defaults to twice the height).
            h (int): The height of the switch.
            align (int): The alignment of the switch.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the switch.
            bg (int): The background color behind the switch.
            visible (bool): The visibility of the switch.
            value (bool): The initial state (default False / off).
            padding (tuple): The padding on each side of the switch.
            on_color (int): Track color when on; defaults to ``success``.
            off_color (int): Track color when off; defaults to ``tertiary``.
            knob_color (int): Knob color; defaults to ``on_primary``.

        Usage:
            wifi = Switch(card, align=pd.ALIGN.RIGHT, value=True)
            wifi.set_change_cb(lambda s: print("wifi", s.value))
        """
        h = h or ICON_SIZE.MEDIUM
        w = w or h * 2
        self.on_color = on_color if on_color is not None else parent.color_theme.success
        self.off_color = off_color if off_color is not None else parent.color_theme.tertiary
        self.knob_color = knob_color if knob_color is not None else parent.color_theme.on_primary
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.toggle)

    def toggle(self, data=None, event=None):
        """Flip the switch between on and off."""
        self.value = not self.value

    def draw(self, _=None):
        """Draw the pill track and the knob at the on/off position."""
        self.parent.draw(self.area)
        pa = self.padded_area
        r = pa.h // 2
        track = self.on_color if self.value else self.off_color
        self.display.framebuf.round_rect(*pa, r, track, f=True)
        knob_x = pa.x + pa.w - r if self.value else pa.x + r
        knob_r = r - 2 if r > 2 else r
        self.display.framebuf.circle(knob_x, pa.y + r, knob_r, self.knob_color, f=True)


class NumberStepper(Widget):
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
        value=0,
        padding=None,
        step=1,
        minimum=None,
        maximum=None,
        number_format="{}",
    ):
        """
        Initialize a NumberStepper: a ``-`` button, a value display and a ``+``
        button for adjusting a bounded number.

        This generalizes the ad-hoc ``+``/``-`` :class:`IconButton` pattern into
        a reusable widget. Pressing a button changes ``value`` by ``step``,
        clamped to ``[minimum, maximum]`` when those are given, and fires the
        change callback.

        Args:
            parent (Widget): The parent widget or screen that contains this stepper.
            x (int): The x-coordinate of the stepper.
            y (int): The y-coordinate of the stepper.
            w (int): The width of the stepper.
            h (int): The height of the stepper.
            align (int): The alignment of the stepper.
            align_to (Widget): The widget to align to.
            fg (int): The value-text color; defaults to ``on_surface``.
            bg (int): The background color; defaults to ``surface_variant``.
            visible (bool): The visibility of the stepper.
            value (int | float): The initial value (default 0).
            padding (tuple): The padding on each side of the stepper.
            step (int | float): Amount added/subtracted per press (default 1).
            minimum (int | float): Lower clamp bound, or ``None`` for unbounded.
            maximum (int | float): Upper clamp bound, or ``None`` for unbounded.
            number_format (str): ``str.format`` spec for the value display.

        Usage:
            temp = NumberStepper(card, value=20, minimum=15, maximum=30)
            temp.set_change_cb(lambda s: print("set", s.value))
        """
        h = h or ICON_SIZE.LARGE + 2 * PAD
        w = w or ICON_SIZE.LARGE * 4
        bg = bg if bg is not None else parent.color_theme.surface_variant
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.step = step
        self.minimum = minimum
        self.maximum = maximum
        self._number_format = number_format
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        btn_w = self.padded_area.h
        btn_h = self.padded_area.h
        self.neg_button = IconButton(
            self,
            w=btn_w,
            h=btn_h,
            align=ALIGN.LEFT,
            icon_file=icon_theme.remove(ICON_SIZE.SMALL),
            fg=parent.color_theme.on_primary,
            bg=parent.color_theme.primary_variant,
        )
        self.pos_button = IconButton(
            self,
            w=btn_w,
            h=btn_h,
            align=ALIGN.RIGHT,
            icon_file=icon_theme.add(ICON_SIZE.SMALL),
            fg=parent.color_theme.on_primary,
            bg=parent.color_theme.primary_variant,
        )
        self.box = TextBox(
            self,
            w=self.width - 2 * btn_w,
            align=ALIGN.CENTER,
            value=number_format.format(value),
            fg=fg,
            bg=bg,
            format="^",
        )
        self.neg_button.add_event_cb(events.MOUSEBUTTONDOWN, lambda d, e: self._step(-1))
        self.pos_button.add_event_cb(events.MOUSEBUTTONDOWN, lambda d, e: self._step(1))

    def _step(self, direction):
        """Adjust the value by ``step`` in the given direction (+1 / -1)."""
        self.value = self._value + self.step * direction

    def changed(self):
        """Clamp the value to the configured bounds and refresh the display."""
        v = self._value
        if self.minimum is not None and v < self.minimum:
            v = self.minimum
        if self.maximum is not None and v > self.maximum:
            v = self.maximum
        self._value = v
        self.box.value = self._number_format.format(v)
        super().changed()


class TextInput(Widget):
    _focused = None  # the TextInput currently receiving key events, if any

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
        hint="",
        text_height=TEXT_SIZE.LARGE,
        radius=6,
        max_length=None,
    ):
        """
        Initialize a TextInput: a single-line editable text field.

        Tap the field to focus it (a text cursor appears and the border
        highlights); typing appends printable characters, Backspace deletes, and
        Enter releases focus. Only the focused field consumes key events, so
        several inputs can coexist on one screen.

        Args:
            parent (Widget): The parent widget or screen that contains this input.
            x (int): The x-coordinate of the input.
            y (int): The y-coordinate of the input.
            w (int): The width of the input (defaults to the parent width).
            h (int): The height of the input.
            align (int): The alignment of the input.
            align_to (Widget): The widget to align to.
            fg (int): The text color; defaults to ``on_surface``.
            bg (int): The field color; defaults to ``surface``.
            visible (bool): The visibility of the input.
            value (str): The initial text content.
            padding (tuple): The padding on each side of the input.
            hint (str): Placeholder text shown (dimmed) while empty.
            text_height (int): The romfont text height (default TEXT_SIZE.LARGE).
            radius (int): The corner radius of the field (default 6).
            max_length (int): Maximum number of characters, or ``None``.

        Usage:
            name = TextInput(card, hint="Your name", max_length=16)
            name.set_change_cb(lambda s: print(s.value))
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        value = value if value is not None else ""
        w = w or parent.width
        h = h or text_height + 3 * PAD
        self.hint = hint
        self.text_height = text_height
        self.radius = radius
        self.max_length = max_length
        self.focused = False
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._focus)
        self.add_event_cb(events.KEYDOWN, self._key)

    def _focus(self, data=None, event=None):
        """Take keyboard focus (releasing any previously focused input)."""
        prev = TextInput._focused
        if prev is not None and prev is not self:
            prev.focused = False
            prev.invalidate()
        TextInput._focused = self
        if not self.focused:
            self.focused = True
            self.invalidate()

    def _key(self, data=None, event=None):
        """Edit the text on key press, but only when this input is focused."""
        if not self.focused or TextInput._focused is not self:
            return
        key = event.key
        if key == 8:  # Backspace
            if self._value:
                self.value = self._value[:-1]
        elif key == 13:  # Enter / Return releases focus
            self.focused = False
            TextInput._focused = None
            self.invalidate()
        elif 32 <= key < 127 and (self.max_length is None or len(self._value) < self.max_length):
            self.value = self._value + chr(key)

    def draw(self, _=None):
        """Draw the field box, its text or hint, and the cursor when focused."""
        self.parent.draw(self.area)
        pa = self.padded_area
        border = self.color_theme.primary if self.focused else self.color_theme.outline
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)
        self.display.framebuf.round_rect(*pa, self.radius, border, f=False)
        tx = pa.x + PAD + self.radius
        ty = pa.y + (pa.h - self.text_height) // 2
        text = self._value or ""
        if text:
            self.display.framebuf.text(text, tx, ty, self.fg, height=self.text_height)
        elif self.hint:
            self.display.framebuf.text(
                self.hint, tx, ty, self.color_theme.tertiary, height=self.text_height
            )
        if self.focused:
            cx = tx + len(text) * TEXT_WIDTH
            self.display.framebuf.fill_rect(cx, ty, 1, self.text_height, self.fg)


class Dropdown(Widget):
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
        options=None,
        radius=6,
    ):
        """
        Initialize a Dropdown: a header button that reveals a popup option list.

        Tapping the header opens a small popup (a shadowed :class:`Card` of
        option buttons) over the screen; tapping an option selects it, updates
        ``value`` and closes the popup; tapping anywhere else also closes it. The
        popup uses modal pointer capture (see :meth:`Widget.set_modal`) so the
        rest of the UI is inert while it is open.

        Args:
            parent (Widget): The parent widget or screen that contains this dropdown.
            x (int): The x-coordinate of the dropdown.
            y (int): The y-coordinate of the dropdown.
            w (int): The width of the dropdown header.
            h (int): The height of the dropdown header.
            align (int): The alignment of the dropdown.
            align_to (Widget): The widget to align to.
            fg (int): The text/arrow color; defaults to ``on_surface``.
            bg (int): The header color; defaults to ``surface``.
            visible (bool): The visibility of the dropdown.
            value (str): The initially selected option (defaults to the first).
            padding (tuple): The padding on each side of the dropdown.
            options (list): The list of option strings.
            radius (int): The corner radius of the header/popup (default 6).

        Usage:
            dd = Dropdown(card, options=["Low", "Medium", "High"])
            dd.set_change_cb(lambda s: print("chose", s.value))
        """
        self.options = list(options) if options else []
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        w = w or ICON_SIZE.LARGE * 4
        h = h or ICON_SIZE.LARGE
        self.radius = radius
        if value is None and self.options:
            value = self.options[0]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self._open = False
        self._open_event = None
        self._arrow = Icon(
            self,
            align=ALIGN.RIGHT,
            fg=fg,
            bg=bg,
            value=icon_theme.dropdown(ICON_SIZE.SMALL),
        )
        self._sel_label = Label(
            self, value=str(value or ""), x=PAD + radius, align=ALIGN.LEFT, fg=fg, bg=bg
        )
        # A full-screen, transparent overlay on the root screen grabs modal
        # pointer capture while open; the option Card lives inside it.
        screen = _root_screen(self)
        self._overlay = Widget(
            screen, 0, 0, self.display.width, self.display.height, bg=None, visible=False
        )
        self._overlay.add_event_cb(events.MOUSEBUTTONDOWN, self._on_overlay)
        option_h = ICON_SIZE.LARGE
        self._panel = Card(
            self._overlay,
            w=self.width,
            h=option_h * max(len(self.options), 1),
            align=ALIGN.OUTER_BOTTOM,
            align_to=self,
            radius=radius,
            shadow=3,
        )
        self._option_buttons = []
        for i, opt in enumerate(self.options):
            btn = Button(
                self._panel,
                w=self.width,
                h=option_h,
                y=i * option_h,
                align=ALIGN.TOP_LEFT,
                align_to=self._panel,
                label=str(opt),
                radius=0,
                bg=self._panel.bg,
                text_color=fg,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_select(opt))
            self._option_buttons.append(btn)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._toggle_open)

    def _make_select(self, option):
        """Return a callback that selects ``option`` and closes the popup."""

        def select(data=None, event=None):
            self.value = option
            self._close()

        return select

    def _toggle_open(self, data=None, event=None):
        """Open the popup when closed (tapping the header)."""
        if not self._open:
            self._open = True
            # Remember the opening event so the overlay's close-on-outside
            # handler ignores this same click (modal capture only kicks in on
            # the next event; without this the opening click would immediately
            # reach the now-visible overlay and close the popup).
            self._open_event = event
            self._overlay.visible = True
            self._overlay.set_modal(True)

    def _close(self):
        """Hide the popup and release modal capture."""
        if self._open:
            self._open = False
            self._overlay.set_modal(False)
            self._overlay.visible = False

    def _on_overlay(self, data=None, event=None):
        """Close the popup when the tap lands outside the option panel."""
        if event is self._open_event:
            return
        point = self.display.translate_point(event.pos)
        if not self._panel.area.contains(point):
            self._close()

    def changed(self):
        """Update the header label to the selected option."""
        self._sel_label.value = str(self._value or "")
        super().changed()

    def draw(self, _=None):
        """Draw the dropdown header (rounded surface)."""
        self.parent.draw(self.area)
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=True)
        self.display.framebuf.round_rect(
            *self.padded_area, self.radius, self.color_theme.outline, f=False
        )


class Dialog(Widget):
    def __init__(
        self,
        parent: Widget,
        message="",
        title=None,
        buttons=None,
        on_result=None,
        fg=None,
        bg=None,
        w=None,
        h=None,
        font=None,
        scrim=None,
    ):
        """
        Initialize a Dialog: a modal message box centered over the screen.

        The dialog is a full-screen overlay (painted with an opaque ``scrim`` —
        the pure-Python framebuffer has no alpha blending, so the backdrop is a
        solid muted color rather than a translucent dim) holding a centered
        :class:`Card` with a title, a message and one or more action buttons.
        While shown it grabs modal pointer capture so the underlying UI is inert.
        Clicking a button closes the dialog and invokes ``on_result`` with that
        button's label.

        Args:
            parent (Widget): The parent widget or screen; the overlay is attached
                to the root screen so it covers the whole display.
            message (str): The message body text.
            title (str): Optional title shown at the top of the card.
            buttons (list): Button labels (default ``["OK"]``).
            on_result (callable): Called as ``on_result(label)`` when a button is
                pressed (also fired before the dialog hides).
            fg (int): Text color; defaults to ``on_surface``.
            bg (int): Card color; defaults to ``surface``.
            w (int): Card width (auto-sized when omitted).
            h (int): Card height (auto-sized when omitted).
            font (module): Optional proportional font module for the title.
            scrim (int): Backdrop fill color; defaults to ``color_theme.shadow``.

        Usage:
            dlg = Dialog(screen, "Power off?", title="Confirm",
                         buttons=["Cancel", "OK"], on_result=handle)
            dlg.show()
        """
        screen = _root_screen(parent)
        display = parent.display
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.scrim = scrim if scrim is not None else parent.color_theme.shadow
        self.on_result = on_result
        super().__init__(
            screen, 0, 0, display.width, display.height, fg=fg, bg=None, visible=False
        )
        w = w or min(display.width - 2 * ICON_SIZE.LARGE, ICON_SIZE.LARGE * 8)
        h = h or min(display.height - 2 * ICON_SIZE.LARGE, ICON_SIZE.LARGE * 5)
        self.card = Card(
            self, w=w, h=h, align=ALIGN.CENTER, fg=fg, bg=bg, title=title, font=font, shadow=4
        )
        Label(
            self.card,
            value=message,
            align=ALIGN.CENTER,
            y=-ICON_SIZE.SMALL,
            fg=fg,
            bg=bg,
        )
        labels = list(buttons) if buttons else ["OK"]
        btn_w = (w - PAD * (len(labels) + 2)) // len(labels)
        prev = None
        for lbl in labels:
            btn = Button(
                self.card,
                w=btn_w,
                y=-PAD * 2,
                align=ALIGN.BOTTOM if prev is None else ALIGN.OUTER_RIGHT,
                align_to=self.card if prev is None else prev,
                label=lbl,
                radius=6,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_result(lbl))
            prev = btn

    def _make_result(self, label):
        """Return a callback that reports ``label`` and closes the dialog."""

        def result(data=None, event=None):
            if self.on_result:
                self.on_result(label)
            self.hide_dialog()

        return result

    def show(self):
        """Show the dialog and grab modal pointer capture."""
        self.visible = True
        self.set_modal(True)
        self.invalidate()

    def hide_dialog(self):
        """Hide the dialog and release modal pointer capture."""
        self.set_modal(False)
        self.visible = False

    def draw(self, _=None):
        """Paint the opaque scrim across the screen behind the card."""
        self.display.framebuf.fill_rect(*self.area, self.scrim)
