# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Browser / DOM keyboard helpers for host display backends.

Translate values from a JavaScript ``KeyboardEvent`` (PyScript or ipyevents)
into SDL-style key codes and modifier masks from ``keys``.
"""

import keys

# ---------------------------------------------------------------------------
# Translate ``KeyboardEvent.key`` into ``keys.K_*`` codes so web/notebook
# backends emit the same ``events.Key`` records as desktop SDL2 / PyGame.
# ---------------------------------------------------------------------------

_DOM_NAMED_KEYS = {
    "Backspace": keys.K_BACKSPACE,
    "Tab": keys.K_TAB,
    "Enter": keys.K_RETURN,
    "Escape": keys.K_ESCAPE,
    "Delete": keys.K_DELETE,
    "ArrowUp": keys.K_UP,
    "ArrowDown": keys.K_DOWN,
    "ArrowLeft": keys.K_LEFT,
    "ArrowRight": keys.K_RIGHT,
    # Why BrowserBack/GoBack/Back → K_AC_BACK: webOS / Tizen / some Chromium TV
    # remotes emit these DOM key names for the Back button; match Android SDL
    # Back so the display quit_chord can turn them into QUIT.
    "BrowserBack": keys.K_AC_BACK,
    "GoBack": keys.K_AC_BACK,
    "Back": keys.K_AC_BACK,
    "Home": keys.K_HOME,
    "End": keys.K_END,
    "PageUp": keys.K_PAGEUP,
    "PageDown": keys.K_PAGEDOWN,
    "Insert": keys.K_INSERT,
    "CapsLock": keys.K_CAPSLOCK,
    "NumLock": keys.K_NUMLOCKCLEAR,
    "ScrollLock": keys.K_SCROLLLOCK,
    "Pause": keys.K_PAUSE,
    "PrintScreen": keys.K_PRINTSCREEN,
    "ContextMenu": keys.K_MENU,
    "Control": keys.K_LCTRL,
    "Shift": keys.K_LSHIFT,
    "Alt": keys.K_LALT,
    "Meta": keys.K_LGUI,
    "F1": keys.K_F1,
    "F2": keys.K_F2,
    "F3": keys.K_F3,
    "F4": keys.K_F4,
    "F5": keys.K_F5,
    "F6": keys.K_F6,
    "F7": keys.K_F7,
    "F8": keys.K_F8,
    "F9": keys.K_F9,
    "F10": keys.K_F10,
    "F11": keys.K_F11,
    "F12": keys.K_F12,
}

# Right-hand variants of modifier keys, selected when the DOM key event reports
# ``location == DOM_KEY_LOCATION_RIGHT`` (2).
_DOM_RIGHT_KEYS = {
    "Control": keys.K_RCTRL,
    "Shift": keys.K_RSHIFT,
    "Alt": keys.K_RALT,
    "Meta": keys.K_RGUI,
}

_MOD_KEY_BITS = {
    keys.K_LSHIFT: keys.KMOD_LSHIFT,
    keys.K_RSHIFT: keys.KMOD_RSHIFT,
    keys.K_LCTRL: keys.KMOD_LCTRL,
    keys.K_RCTRL: keys.KMOD_RCTRL,
    keys.K_LALT: keys.KMOD_LALT,
    keys.K_RALT: keys.KMOD_RALT,
    keys.K_LGUI: keys.KMOD_LGUI,
    keys.K_RGUI: keys.KMOD_RGUI,
}

_BROWSER_SCROLL_KEYCODES = frozenset(
    (
        keys.K_UP,
        keys.K_DOWN,
        keys.K_LEFT,
        keys.K_RIGHT,
        keys.K_SPACE,
        keys.K_PAGEUP,
        keys.K_PAGEDOWN,
        keys.K_HOME,
        keys.K_END,
    )
)


def key_to_keycode(key, location=0):
    """
    Map a DOM ``KeyboardEvent.key`` value to an SDL-style key code.

    Args:
        key (str): The ``KeyboardEvent.key`` value (e.g. ``"a"`` or ``"ArrowUp"``).
        location (int): The ``KeyboardEvent.location`` value.  ``2`` selects the
            right-hand variant of a modifier key (e.g. ``keys.K_RCTRL``).

    Returns:
        int: The matching ``keys.K_*`` code, or ``keys.K_UNKNOWN``.
    """
    if location == 2:
        code = _DOM_RIGHT_KEYS.get(key)
        if code is not None:
            return code
    code = _DOM_NAMED_KEYS.get(key)
    if code is not None:
        return code
    if key and len(key) == 1:
        o = ord(key)
        if 0x41 <= o <= 0x5A:  # 'A'-'Z' -> lowercase code, matching SDL
            return o + 0x20
        return o
    return keys.K_UNKNOWN


def mod_mask(ctrl, shift, alt, meta):
    """
    Build a modifier mask from DOM modifier flags.

    DOM only reports that a modifier *group* is held, not left vs right.
    This returns the **left-hand** ``KMOD_L*`` bits. Prefer matching with
    group masks (``keys.KMOD_SHIFT`` / ``keys.KMOD_CTRL`` / …) or
    :func:`keys.chord_matches`, or enrich with :func:`enrich_mod` when pressed
    keycodes are known.

    Args:
        ctrl (bool): Whether Ctrl is held.
        shift (bool): Whether Shift is held.
        alt (bool): Whether Alt is held.
        meta (bool): Whether Meta/GUI (Cmd/Win) is held.

    Returns:
        int: A mask of ``keys.KMOD_*`` bits.
    """
    mask = 0
    if shift:
        mask |= keys.KMOD_LSHIFT
    if ctrl:
        mask |= keys.KMOD_LCTRL
    if alt:
        mask |= keys.KMOD_LALT
    if meta:
        mask |= keys.KMOD_LGUI
    return mask


def enrich_mod(mod, pressed_keys):
    """OR left/right ``KMOD_*`` bits for modifier keycodes in ``pressed_keys``.

    Use on browser backends after updating the pressed-key set so ambient
    ``event.mod`` reflects Right Shift/Ctrl/… when those keys are down.

    Args:
        mod (int): Base modifier mask (e.g. from :func:`mod_mask`).
        pressed_keys: Iterable of currently pressed key codes.

    Returns:
        int: ``mod`` with bits from pressed modifier keys set.
    """
    mask = mod or 0
    if not pressed_keys:
        return mask
    for key in pressed_keys:
        bit = _MOD_KEY_BITS.get(key)
        if bit:
            mask |= bit
    return mask


def dom_key_scrolls_page(keycode):
    """
    Return True if the browser may scroll the page for this key code.

    Used by PyScript / notebook backends to suppress default scrolling while
    the game canvas is focused.
    """
    return keycode in _BROWSER_SCROLL_KEYCODES
