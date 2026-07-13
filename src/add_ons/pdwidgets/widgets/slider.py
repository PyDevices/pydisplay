# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE
from ..widget import Widget
from .progress_bar import ProgressBar


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
