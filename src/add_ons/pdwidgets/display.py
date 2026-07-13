# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from random import getrandbits

try:
    from time import ticks_ms
except ImportError:
    from multimer import ticks_ms

from graphics import RGB565, Area, FrameBuffer

from ._constants import ALIGN
from ._themes import ColorTheme, get_palette
from ._util import (
    _POINTER_EVENTS,
    _WIDGET_EVENTS,
    _cond_pointer,
    _display_drv_get_attrs,
    _display_drv_set_attrs,
    _log,
)
from .task import Task
from .widget import Widget


def _mark_updates_enabled():
    import sys

    mod = sys.modules.get("pdwidgets")
    return bool(mod is not None and getattr(mod, "MARK_UPDATES", False))


class Display(Widget):
    displays = []
    timer = None  # pdwidgets owns no timer; kept as None for API/back-compat.
    tick_period = 10  # Render tick period (ms) for the runtime on_tick subscription.

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
        self._tick_sub = None
        Display.displays.append(self)
        self._attach_to_runtime()

    def _attach_to_runtime(self):
        """Wire input dispatch and frame rendering into the shared runtime.

        The canonical idiom owns no loop: the runtime's auto-service tick polls
        devices and dispatches events to :meth:`handle_event`, while a shared-
        timer subscription drives :meth:`tick` (flush/redraw). ``async_`` tracks
        ``runtime.timer_async`` so a sync render timer never coexists with the
        async loop.
        """
        runtime = self.runtime
        if runtime is None:
            return
        runtime.subscribe(self.handle_event, event_types=list(_WIDGET_EVENTS))
        self._tick_sub = runtime.on_tick(
            self._render_tick,
            period=Display.tick_period,
            async_=getattr(runtime, "timer_async", False),
        )

    def _render_tick(self, _=None):
        """Shared-timer callback: render one widget frame."""
        self.tick()

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
        if _mark_updates_enabled():
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
        Render one widget frame.

        Flushes dirty areas to the display, otherwise runs scheduled tasks and
        re-renders invalidated widgets. Driven automatically by the runtime's
        shared timer (see :meth:`_attach_to_runtime`); may also be called
        manually (e.g. :func:`tick`) to force a frame.
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


def tick(_=None):
    """
    Call the ``tick`` method of every registered :class:`Display`.

    Args:
        _ (Any): Ignored positional argument so this may also be used as a
            timer/``on_tick`` callback signature.
    """
    for display in Display.displays:
        display.tick()
