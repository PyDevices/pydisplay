# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
# pyscript skip: binaries
"""
widgets_device_panel
====================================================
A fictional "Aurora Synth" control panel built entirely from pdwidgets.

Showcases the Phase 5 widgets — ``Card``, ``Switch``, ``NumberStepper`` and a
modal ``Dialog`` — alongside the classic ``Slider``/``Button``. Every control is
wired to a simulated "send control signal" action that appends to a scrolling
status log (a ``TextBox``); the Power Off button raises a modal confirmation
``Dialog`` before logging the (simulated) shutdown. No real hardware or network
is touched.

Runs under both ``timer_async`` modes; the UI is driven by ``runtime.run_forever()``.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

W = screen.width
margin = max(6, W // 40)


class Header(pd.Widget):
    """
    A vertical gradient title bar.

    Drawn as a handful of ``fill_rect`` bands whose color is interpolated with
    ``display.pal.color565`` — MCU-safe (the native cmod ``FrameBuffer`` has no
    ``gradient_rect``) and only a few fills per redraw.
    """

    _top = (0x3A, 0x53, 0x6B)
    _bottom = (0x5E, 0x7E, 0x9E)

    def draw(self, _=None):
        pa = self.padded_area
        bands = 8
        band_h = max(1, pa.h // bands)
        for i in range(bands):
            t = i / (bands - 1)
            rgb = tuple(int(a + (b - a) * t) for a, b in zip(self._top, self._bottom))
            color = display.pal.color565(*rgb)
            self.display.framebuf.fill_rect(pa.x, pa.y + i * band_h, pa.w, band_h + 1, color)


header = Header(screen, w=W, h=max(34, screen.height // 12), align=pd.ALIGN.TOP)
pd.Label(
    header,
    value="Aurora Synth",
    align=pd.ALIGN.LEFT,
    x=margin,
    fg=theme.on_primary,
    bg=theme.primary,
    scale=2,
)

# Status log along the bottom.
status = pd.TextBox(
    screen,
    w=W,
    align=pd.ALIGN.BOTTOM,
    scale=1,
    fg=theme.on_surface,
    bg=theme.surface_variant,
    value="Ready.",
)


def log(msg):
    status.set_value(msg)


# Control card between the header and the status bar.
card_h = status.y - header.height - 2 * margin
panel = pd.Card(
    screen,
    w=W - 2 * margin,
    h=card_h,
    y=header.height + margin,
    align=pd.ALIGN.TOP,
    title="Controls",
)
pad = margin + 4
inner_w = panel.width - 2 * pad

y = 26
row = pd.FormRow(panel, label="Power", x=pad, y=y, w=inner_w)
power_sw = pd.Switch(row, value=True)
power_sw.set_change_cb(lambda s: log("Power %s" % ("on" if s.value else "off")))

y += row.height + 4
pd.Divider(panel, x=pad, y=y, w=inner_w)

y += 12
pd.Label(panel, value="Volume", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
y += 18
volume = pd.Slider(panel, x=pad, y=y, w=inner_w, align=pd.ALIGN.TOP_LEFT, value=0.6, step=0.05)
volume.set_change_cb(lambda s: log("Volume %d%%" % int(s.value * 100)))

y += 28
pd.Label(panel, value="Cutoff", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
y += 18
cutoff = pd.Slider(panel, x=pad, y=y, w=inner_w, align=pd.ALIGN.TOP_LEFT, value=0.4, step=0.05)
cutoff.set_change_cb(lambda s: log("Cutoff %d%%" % int(s.value * 100)))

y += 30
pd.Label(panel, value="Voices", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
y += 18
voices = pd.NumberStepper(
    panel, x=pad, y=y, w=inner_w, align=pd.ALIGN.TOP_LEFT, value=4, minimum=1, maximum=8
)
voices.set_change_cb(lambda s: log("Voices: %s" % s.value))

power_off = pd.Button(
    panel,
    label="Power Off",
    align=pd.ALIGN.BOTTOM,
    y=-pad,
    radius=6,
    shadow=2,
    bg=theme.error,
    text_color=theme.on_error,
)

confirm = pd.Dialog(
    screen,
    "Power off the synth?",
    title="Confirm",
    buttons=["Cancel", "Power Off"],
    on_result=lambda label: log("Powered off." if label == "Power Off" else "Cancelled."),
)
power_off.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda s, e: confirm.show())

screen.visible = True

board_config.runtime.run_forever()
