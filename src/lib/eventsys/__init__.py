# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`eventsys`
====================================================
An Event System including event types and device types for *Python.
"""

from collections import namedtuple

from micropython import const


def custom_type(types=None, classes=None):
    """
    Create new event types and classes for the events class.

    For example, to recreate the events for the keypad device:
    ```
    import eventsys

    types = [("KEYDOWN", 0x300), ("KEYUP", 0x301)]
    classes = {"Key": "type name key mod scancode window"}
    eventsys.custom_type(types, classes)

    # Optionally update the filter
    events.filter += [events.KEYDOWN, events.KEYUP]
    ```

    Args:
        types (dict[str, int] | list[tuple[str, int]]): Event type names and values.
            Pass a dict or a list of `(name, value)` tuples.
        classes (dict[str, str]): Event class names mapped to namedtuple field strings.
    """
    if classes is None:
        classes = {}
    if types is None:
        types = {}
    for type_name, value in types.items():
        type_name = type_name.upper()
        if hasattr(events, type_name):
            raise ValueError(f"Event type {type_name} already exists in events class.")
        else:
            setattr(events, type_name, value or events._USER_TYPE_BASE)
            if not value:
                events._USER_TYPE_BASE += 1

    for event_class_name, event_class_fields in classes.items():
        event_class_name = event_class_name[0].upper() + event_class_name[1:].lower()
        if hasattr(events, event_class_name):
            raise ValueError(f"Event class {event_class_name} already exists in events class.")
        else:
            event_class_fields = event_class_fields.lower()
            setattr(
                events,
                event_class_name,
                namedtuple(event_class_name, event_class_fields),  # noqa: PYI024
            )


class events:
    """
    A container for event types and classes.  Similar to a C enum and struct.
    """

    # Event types (from SDL2 / PyGame, not complete)
    QUIT = const(0x100)  # User clicked the window close button
    KEYDOWN = const(0x300)  # Key pressed
    KEYUP = const(0x301)  # Key released
    MOUSEMOTION = const(0x400)  # Mouse moved
    MOUSEBUTTONDOWN = const(0x401)  # Mouse button pressed
    MOUSEBUTTONUP = const(0x402)  # Mouse button released
    MOUSEWHEEL = const(0x403)  # Mouse wheel motion
    JOYAXISMOTION = const(0x600)  # Joystick axis motion
    JOYBALLMOTION = const(0x601)  # Joystick trackball motion
    JOYHATMOTION = const(0x602)  # Joystick hat position change
    JOYBUTTONDOWN = const(0x603)  # Joystick button pressed
    JOYBUTTONUP = const(0x604)  # Joystick button released
    _USER_TYPE_BASE = 0x8000

    filter = [
        QUIT,
        KEYDOWN,
        KEYUP,
        MOUSEMOTION,
        MOUSEBUTTONDOWN,
        MOUSEBUTTONUP,
        MOUSEWHEEL,
        JOYAXISMOTION,
        JOYBALLMOTION,
        JOYHATMOTION,
        JOYBUTTONDOWN,
        JOYBUTTONUP,
    ]

    # Event classes from PyGame
    Unknown = namedtuple("Common", "type")  # noqa: PYI024
    Motion = namedtuple("Motion", "type pos rel buttons touch window")  # noqa: PYI024
    Button = namedtuple("Button", "type pos button touch window")  # noqa: PYI024
    Wheel = namedtuple("Wheel", "type flipped x y precise_x precise_y touch window")  # noqa: PYI024
    Key = namedtuple("Key", "type name key mod scancode window")  # noqa: PYI024
    Quit = namedtuple("Quit", "type")  # noqa: PYI024
    Any = namedtuple("Any", "type")  # noqa: PYI024
    JoyAxisMotion = namedtuple("JoyAxisMotion", "type instance_id axis value")  # noqa: PYI024
    JoyButtonUp = namedtuple("JoyButtonUp", "type instance_id button")  # noqa: PYI024
    JoyButtonDown = namedtuple("JoyButtonDown", "type instance_id button")  # noqa: PYI024
    JoyHatMotion = namedtuple("JoyHatMotion", "type instance_id hat value")  # noqa: PYI024
    JoyBallMotion = namedtuple("JoyBallMotion", "type instance_id ball rel")  # noqa: PYI024
