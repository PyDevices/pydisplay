from _typeshed import Incomplete
from typing import NamedTuple

class events:
    QUIT: Incomplete
    KEYDOWN: Incomplete
    KEYUP: Incomplete
    MOUSEMOTION: Incomplete
    MOUSEBUTTONDOWN: Incomplete
    MOUSEBUTTONUP: Incomplete
    MOUSEWHEEL: Incomplete
    JOYAXISMOTION: Incomplete
    JOYBALLMOTION: Incomplete
    JOYHATMOTION: Incomplete
    JOYBUTTONDOWN: Incomplete
    JOYBUTTONUP: Incomplete
    FINGERDOWN: Incomplete
    FINGERUP: Incomplete
    FINGERMOTION: Incomplete
    filter: Incomplete

    class Unknown(NamedTuple):
        type: Incomplete

    class Motion(NamedTuple):
        type: Incomplete
        pos: Incomplete
        rel: Incomplete
        buttons: Incomplete
        touch: Incomplete
        window: Incomplete

    class Button(NamedTuple):
        type: Incomplete
        pos: Incomplete
        button: Incomplete
        touch: Incomplete
        window: Incomplete

    class Wheel(NamedTuple):
        type: Incomplete
        flipped: Incomplete
        x: Incomplete
        y: Incomplete
        precise_x: Incomplete
        precise_y: Incomplete
        touch: Incomplete
        window: Incomplete

    class Key(NamedTuple):
        type: Incomplete
        name: Incomplete
        key: Incomplete
        mod: Incomplete
        scancode: Incomplete
        window: Incomplete

    class Quit(NamedTuple):
        type: Incomplete

    class Any(NamedTuple):
        type: Incomplete

    class JoyAxisMotion(NamedTuple):
        type: Incomplete
        instance_id: Incomplete
        axis: Incomplete
        value: Incomplete

    class JoyButtonUp(NamedTuple):
        type: Incomplete
        instance_id: Incomplete
        button: Incomplete

    class JoyButtonDown(NamedTuple):
        type: Incomplete
        instance_id: Incomplete
        button: Incomplete

    class JoyHatMotion(NamedTuple):
        type: Incomplete
        instance_id: Incomplete
        hat: Incomplete
        value: Incomplete

    class JoyBallMotion(NamedTuple):
        type: Incomplete
        instance_id: Incomplete
        ball: Incomplete
        rel: Incomplete

    class Finger(NamedTuple):
        type: Incomplete
        pos: Incomplete
        finger_id: Incomplete
        window: Incomplete

def register_event(name=None, value=None, *, fields=None, types=None, classes=None) -> None: ...
