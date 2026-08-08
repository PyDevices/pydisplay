# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Soft rotary-encoder emulator for LVGL on non-MCU runtimes.

Stand-in for hardware ``machine.Encoder`` / ``rotaryio`` while developing on
desktop (SDL/PG), PyScript, or Jupyter. Each :class:`EncoderEmu` owns:

* a :class:`SoftEncoder` (position + pushbutton state)
* an eventsys :class:`~eventsys.EncoderDevice` registered on ``runtime``
* an LVGL emulator UI (← / Enter / →) on a secondary displaysys surface,
  in a private focus group (not the app default)

Multiple emulators may coexist in one app (one window/canvas each)::

    from board_config import runtime
    import display_driver  # primary LVGL first
    from lv_encoder_emu import EncoderEmu

    emu_a = EncoderEmu(runtime, title="Enc A")
    emu_b = EncoderEmu(runtime, title="Enc B")
    # emu_a.device / emu_b.device are LVGL encoder indevs on the primary display
"""

from board_config import display_drv

# Matches display_driver._encoder_cb (MOUSEBUTTON* button 3 → encoder press).
DEFAULT_ENCODER_BUTTON = 3


class SoftEncoder:
    """Position / button state for ``runtime.add_encoder`` read callbacks.

    Same contract apps use with MCU ``machine.Encoder`` / ``rotaryio``: a
    wrapping position integer and a boolean pushbutton.
    """

    def __init__(self, pos=0):
        self.pos = int(pos)
        self.pressed = False

    def inc(self, n=1):
        self.pos += int(n)

    def dec(self, n=1):
        self.pos -= int(n)

    def push(self):
        self.pressed = True

    def release(self):
        self.pressed = False

    def read_pos(self):
        """Zero-arg callable for ``runtime.add_encoder(read=...)``."""
        return self.pos

    def read_button(self):
        """Zero-arg callable for ``runtime.add_encoder(button_read=...)``."""
        return self.pressed


def make_emu_display(
    primary=None,
    *,
    width=240,
    height=80,
    title="Encoder",
    scale=1,
    canvas_id=None,
):
    """Create a same-backend secondary display for an encoder emulator.

    Args:
        primary: Primary displaysys driver (default: ``board_config.display_drv``).
        width, height: Emulator panel size in pixels.
        title: Window title (SDL/PG).
        scale: PGDisplay scale (ignored by other backends).
        canvas_id: PyScript canvas DOM id (default ``aux_canvas``). Each emulator
            needs a distinct id when using more than one PS surface.

    Returns:
        tuple: ``(display, attach_devices)`` where ``attach_devices`` is
        ``None`` (desktop reuses ``runtime.host_dev``) or a list of host
        devices for PyScript/Jupyter.
    """
    if primary is None:
        primary = display_drv
    name = type(primary).__name__
    if name == "SDLDisplay":
        from displaysys.sdldisplay import SDLDisplay

        return SDLDisplay(width=width, height=height, title=title, quiet=True), None
    if name == "PGDisplay":
        from displaysys.pgdisplay import PGDisplay

        return (
            PGDisplay(width=width, height=height, title=title, scale=scale, quiet=True),
            None,
        )
    if name == "PSDisplay":
        from displaysys.psdisplay import PSDisplay
        import eventsys

        # Per-canvas drain (PSDisplay owns PSDevices). Separate HostEventsDevice
        # from the primary — not a second PG/SDL-style shared pump.
        cid = canvas_id if canvas_id is not None else "aux_canvas"
        dd = PSDisplay(cid, width, height)
        host = eventsys.HostEventsDevice(host_read=dd.get_events, display=dd)
        return dd, [host]
    if name == "JNDisplay":
        from displaysys.jndisplay import JNDisplay
        import eventsys

        dd = JNDisplay(width, height)
        # Eagerly create JNDevices (widget) before LVGL attach; drain stays
        # on the display for the aux HostEventsDevice.
        dd.get_events()
        host = eventsys.HostEventsDevice(host_read=dd.get_events, display=dd)
        return dd, [host]
    raise ValueError(f"lv_encoder_emu: unsupported backend {name!r}")


def _mk_emu_button(parent, symbol, group, *, on_short=None, on_repeat=None, press_release=None):
    import lvgl as lv

    b = lv.button(parent)
    b.set_size(64, 64)
    lab = lv.label(b)
    lab.set_text(symbol)
    lab.center()
    # Keep clicks working, but never take group focus (avoids stealing / resetting
    # the app's default encoder group when the pointer hits the emulator).
    b.remove_flag(lv.OBJ_FLAG.CLICK_FOCUSABLE)
    lv.group_remove_obj(b)
    group.add_obj(b)
    if press_release is not None:
        soft = press_release
        b.add_event_cb(lambda e, s=soft: s.push(), lv.EVENT.PRESSED, None)
        b.add_event_cb(lambda e, s=soft: s.release(), lv.EVENT.RELEASED, None)
    else:
        if on_short is not None:
            cb = on_short
            b.add_event_cb(lambda e, c=cb: c(), lv.EVENT.SHORT_CLICKED, None)
        if on_repeat is not None:
            cb = on_repeat
            b.add_event_cb(lambda e, c=cb: c(), lv.EVENT.LONG_PRESSED_REPEAT, None)
    return b


class EncoderEmu:
    """One emulated encoder: secondary surface + LVGL UI + eventsys device.

    Call after ``import display_driver`` so the primary LVGL display exists.
    The encoder indev is attached to ``target_lv_display`` (default: primary).

    Args:
        runtime: ``board_config.runtime`` (or any :class:`eventsys.Runtime`).
        display: Existing secondary displaysys driver, or ``None`` to create one.
        attach_devices: Host devices for ``display_driver.attach`` (PS/JN);
            ignored when ``display`` is created by :func:`make_emu_display`.
        title, width, height, scale, canvas_id: Forwarded to :func:`make_emu_display`
            when creating a display.
        button: Mouse button index for the encoder switch (default ``3``, matching
            ``display_driver._encoder_cb``).
        target_lv_display: LVGL display that receives the encoder indev; default
            is the primary LVGL display.
        soft: Optional existing :class:`SoftEncoder`; created when omitted.
    """

    def __init__(
        self,
        runtime,
        *,
        display=None,
        attach_devices=None,
        title="Encoder",
        width=240,
        height=80,
        scale=1,
        canvas_id=None,
        button=DEFAULT_ENCODER_BUTTON,
        target_lv_display=None,
        soft=None,
    ):
        import display_driver
        import lvgl as lv

        host_devs = attach_devices
        if display is None:
            display, host_devs = make_emu_display(
                runtime.primary,
                width=width,
                height=height,
                title=title,
                scale=scale,
                canvas_id=canvas_id,
            )
        if display not in runtime.displays:
            runtime.add_display(display)

        self._display = display
        self._soft = soft if soft is not None else SoftEncoder()
        self._device = runtime.add_encoder(
            read=self._soft.read_pos,
            button_read=self._soft.read_button,
            button=button,
        )
        self._bridge = display_driver.attach(display, host_devs)
        display_driver.attach_devices([self._device], lv_display=target_lv_display)
        # Private group so ←/Enter/→ never join the app's default encoder group.
        self._group = lv.group_create()
        self._bind_surface_indevs(lv)
        self._root = self._build_ui(lv)

    @property
    def soft(self):
        """:class:`SoftEncoder` state (position / button)."""
        return self._soft

    @property
    def device(self):
        """Registered eventsys :class:`~eventsys.EncoderDevice`."""
        return self._device

    @property
    def display(self):
        """Secondary displaysys driver for the emulator surface."""
        return self._display

    @property
    def bridge(self):
        """``display_driver.DisplayDriver`` for the emulator LVGL display."""
        return self._bridge

    @property
    def group(self):
        """LVGL group owning the emulator buttons (not the app default)."""
        return self._group

    @property
    def root(self):
        """Root LVGL object of the emulator UI."""
        return self._root

    def _bind_surface_indevs(self, lv):
        """Point secondary-surface indevs at the emu group, not the app default."""
        for vd in getattr(self._bridge, "virtual_devices", ()):
            for dev in getattr(vd, "devices", ()):
                indev = getattr(dev, "user_data", None)
                if indev is not None and hasattr(indev, "set_group"):
                    indev.set_group(self._group)

    def _build_ui(self, lv):
        scr = self._bridge.lv_display.get_screen_active()
        row = lv.obj(scr)
        row.set_size(lv.pct(100), lv.pct(100))
        row.set_flex_flow(lv.FLEX_FLOW.ROW)
        row.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        row.set_style_pad_all(4, 0)
        row.set_style_border_width(0, 0)
        soft = self._soft
        grp = self._group
        _mk_emu_button(row, lv.SYMBOL.LEFT, grp, on_short=soft.dec, on_repeat=soft.dec)
        _mk_emu_button(row, lv.SYMBOL.NEW_LINE, grp, press_release=soft)
        _mk_emu_button(row, lv.SYMBOL.RIGHT, grp, on_short=soft.inc, on_repeat=soft.inc)
        return row
