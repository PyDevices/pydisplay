# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Internal helpers for pdwidgets."""

from eventsys import events


def _log(*args, **kwargs):
    """Print when ``pdwidgets.DEBUG`` is truthy (checked at call time)."""
    import sys

    mod = sys.modules.get("pdwidgets")
    if mod is not None and getattr(mod, "DEBUG", False):
        print(*args, **kwargs)


def _cond_pointer(child, event, point):
    """Event condition: child's padded area contains the (translated) pointer."""
    return child.padded_area.contains(point)


def _cond_always(child, event, point):
    """Event condition: always deliver (non-pointer events)."""
    return True


# Input event types delivered to the widget tree (QUIT is handled by the
# runtime itself, so it is intentionally excluded).
_WIDGET_EVENTS = (
    events.KEYDOWN,
    events.KEYUP,
    events.MOUSEMOTION,
    events.MOUSEBUTTONDOWN,
    events.MOUSEBUTTONUP,
    events.MOUSEWHEEL,
)


_POINTER_EVENTS = (events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP, events.MOUSEMOTION)


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


def _root_screen(widget):
    """Return the top-level screen ancestor of ``widget`` (child of the Display)."""
    node = widget
    while node.parent is not None and node.parent.parent is not None:
        node = node.parent
    return node
