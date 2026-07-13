# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ..widget import Widget


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
