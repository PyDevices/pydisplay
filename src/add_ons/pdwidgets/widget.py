# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from graphics import Area

from ._constants import ALIGN, DEFAULT_PADDING, POSITION
from ._themes import ColorTheme
from ._util import _POINTER_EVENTS, _cond_always, _cond_pointer, _log


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
