# deps: graphics, eventsys
"""
Simon — classic memory game for round (and rectangular) displays.

Uses pydisplay ``graphics`` (not LVGL) plus ``eventsys`` touch. Designed as a
light-RAM display/touch driver demo: draws directly to the bus display with no
full-frame buffer.

On round panels the bezel clips the corners, so each pad is two ``fill_rect``
calls forming an L that leaves the center hub untouched (fast flashes).

Gameplay (Classic Simon): the device lights a growing sequence of colored pads;
the player repeats it by tapping. Wrong tap or timeout ends the round.
"""

from board_config import display_drv, runtime
from random import getrandbits
from time import sleep_ms

import eventsys
import graphics

try:
    from multimer import ticks_diff, ticks_ms
except ImportError:
    from time import ticks_diff, ticks_ms  # type: ignore

# RGB565 — match other busdisplay examples (driver handles byte order).
BLACK = 0x0000
WHITE = 0xFFFF
GREY = 0x8410
# Dim / bright pairs: green, red, yellow, blue (classic pad order).
DIM = (0x0320, 0x8000, 0x8400, 0x0010)
LIT = (0x07E0, 0xF800, 0xFFE0, 0x001F)

W = display_drv.width
H = display_drv.height
CX = W // 2
CY = H // 2
INNER_R = max(28, min(W, H) // 7)
GAP = 4
HALF_GAP = GAP // 2
# Each pad = two fill_rects forming an L that leaves the hub square untouched:
#   (1) main block stopping at the hub edge
#   (2) narrow strip along the outer side of the hub
# TL green, TR red, BL yellow, BR blue.
_STRIP = INNER_R - HALF_GAP  # width/height of the narrow arm
PADS = (
    (  # top-left
        (0, 0, CX - INNER_R, CY - HALF_GAP),
        (CX - INNER_R, 0, _STRIP, CY - INNER_R),
    ),
    (  # top-right
        (CX + INNER_R, 0, W - (CX + INNER_R), CY - HALF_GAP),
        (CX + HALF_GAP, 0, _STRIP, CY - INNER_R),
    ),
    (  # bottom-left
        (0, CY + HALF_GAP, CX - INNER_R, H - (CY + HALF_GAP)),
        (CX - INNER_R, CY + INNER_R, _STRIP, H - (CY + INNER_R)),
    ),
    (  # bottom-right
        (CX + INNER_R, CY + HALF_GAP, W - (CX + INNER_R), H - (CY + HALF_GAP)),
        (CX + HALF_GAP, CY + INNER_R, _STRIP, H - (CY + INNER_R)),
    ),
)
INPUT_MS = 5000
FLASH_MS = 280
GAP_MS = 80
MAX_LEN = 20

# Fixed-width hub lines (8px font). Longest labels: "SIMON", "watch", "best 20".
HUB_CHARS = 7
HUB_TEXT_W = HUB_CHARS * 8
HUB_Y0 = CY - 10
HUB_Y1 = CY + 6

IDLE, SHOW, INPUT, FAIL = 0, 1, 2, 3

state = IDLE
sequence = []
step = 0
deadline = 0
busy = False
best = 0


def _center_pad(msg, width=HUB_CHARS):
    s = str(msg)[:width]
    pad = width - len(s)
    left = pad // 2
    return (" " * left) + s + (" " * (pad - left))


def _hub_chrome():
    # Square hub frame once; text updates never redraw this.
    s = INNER_R * 2
    x = CX - INNER_R
    y = CY - INNER_R
    display_drv.fill_rect(x, y, s, s, BLACK)
    display_drv.fill_rect(x + 2, y + 2, s - 4, 1, GREY)
    display_drv.fill_rect(x + 2, y + s - 3, s - 4, 1, GREY)
    display_drv.fill_rect(x + 2, y + 2, 1, s - 4, GREY)
    display_drv.fill_rect(x + s - 3, y + 2, 1, s - 4, GREY)


def _hub_text(msg, sub=""):
    """Rewrite hub text only (space-padded so shorter labels clear longer ones)."""
    line0 = _center_pad(msg)
    line1 = _center_pad(sub)
    x = CX - HUB_TEXT_W // 2
    # Clear glyph rows then draw — spaces alone may not erase prior pixels.
    display_drv.fill_rect(x, HUB_Y0, HUB_TEXT_W, 8, BLACK)
    graphics.text(display_drv, line0, x, HUB_Y0, WHITE)
    display_drv.fill_rect(x, HUB_Y1, HUB_TEXT_W, 8, BLACK)
    graphics.text(display_drv, line1, x, HUB_Y1, GREY)


def _hub(msg, sub=""):
    _hub_chrome()
    _hub_text(msg, sub)


def _pad(i, lit=False):
    c = LIT[i] if lit else DIM[i]
    a, b = PADS[i]
    display_drv.fill_rect(a[0], a[1], a[2], a[3], c)
    display_drv.fill_rect(b[0], b[1], b[2], b[3], c)


def _gaps():
    # Cross only outside the hub so pad flashes never need a hub redraw.
    display_drv.fill_rect(CX - HALF_GAP, 0, GAP, CY - INNER_R, BLACK)
    display_drv.fill_rect(CX - HALF_GAP, CY + INNER_R, GAP, H - (CY + INNER_R), BLACK)
    display_drv.fill_rect(0, CY - HALF_GAP, CX - INNER_R, GAP, BLACK)
    display_drv.fill_rect(CX + INNER_R, CY - HALF_GAP, W - (CX + INNER_R), GAP, BLACK)


def draw_board(hub_msg="SIMON", hub_sub="tap"):
    for i in range(4):
        _pad(i, False)
    _gaps()
    _hub(hub_msg, hub_sub)
    display_drv.show()


def flash(i):
    # Pads leave the hub untouched — no hub refresh required.
    _pad(i, True)
    display_drv.show()
    sleep_ms(FLASH_MS)
    _pad(i, False)
    display_drv.show()
    sleep_ms(GAP_MS)


def hit_pad(x, y):
    dx = x - CX
    dy = y - CY
    if dx * dx + dy * dy < INNER_R * INNER_R:
        return -1
    if abs(dx) <= HALF_GAP or abs(dy) <= HALF_GAP:
        return -1
    if dy < 0:
        return 0 if dx < 0 else 1  # green / red
    return 2 if dx < 0 else 3  # yellow / blue


def play_sequence():
    global state, step, deadline, busy
    busy = True
    state = SHOW
    score = len(sequence)
    _hub_text(str(score), "watch")
    display_drv.show()
    sleep_ms(250)
    for pad in sequence:
        flash(pad)
    step = 0
    deadline = ticks_ms() + INPUT_MS
    state = INPUT
    _hub_text(str(score), "go")
    display_drv.show()
    busy = False


def new_game():
    global sequence, step
    sequence = [getrandbits(2)]
    step = 0
    draw_board(str(len(sequence)), "watch")
    play_sequence()


def fail():
    global state, busy, best
    busy = True
    state = FAIL
    score = max(0, len(sequence) - 1)
    if score > best:
        best = score
    for _ in range(2):
        display_drv.fill_rect(0, 0, W, H, 0x8000)
        display_drv.show()
        sleep_ms(100)
        display_drv.fill_rect(0, 0, W, H, BLACK)
        display_drv.show()
        sleep_ms(60)
    draw_board("OVER", "best %d" % best)
    state = IDLE
    busy = False


def advance():
    global sequence, step, deadline, state, best
    step += 1
    deadline = ticks_ms() + INPUT_MS
    if step < len(sequence):
        _hub_text(str(len(sequence)), "%d/%d" % (step, len(sequence)))
        display_drv.show()
        return
    if len(sequence) >= MAX_LEN:
        best = max(best, MAX_LEN)
        draw_board("WIN!", "best %d" % best)
        state = IDLE
        return
    sequence.append(getrandbits(2))
    play_sequence()


def _on_up(e):
    global busy
    if busy or state == SHOW or e.button != 1:
        return
    x, y = e.pos
    pad = hit_pad(x, y)
    if state == IDLE:
        if pad >= 0 or (x - CX) * (x - CX) + (y - CY) * (y - CY) <= INNER_R * INNER_R:
            new_game()
        return
    if state != INPUT or pad < 0:
        return
    busy = True
    try:
        flash(pad)
        if pad != sequence[step]:
            fail()
            return
        advance()
    finally:
        if state != FAIL:
            busy = False


def _on_tick(_=None):
    if state == INPUT and not busy and ticks_diff(ticks_ms(), deadline) > 0:
        fail()


draw_board()
runtime.on(eventsys.MOUSEBUTTONUP, _on_up)
runtime.on_tick(_on_tick, period=50, async_=getattr(runtime, "timer_async", False))
runtime.run_forever()
