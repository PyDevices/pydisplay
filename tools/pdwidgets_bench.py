#!/usr/bin/env python3
"""
Relative micro-benchmark for the pdwidgets render / event / percent paths.

Runs on cpython-venv as a *relative* proxy for MCU cost (absolute numbers are
meaningless off-device; deltas before/after an optimization are what matter).

Usage (headless)::

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \\
        .venv/bin/python tools/pdwidgets_bench.py [iterations]

It builds a representative screen (a handful of each widget type) and times:

* ``render_dirty_widgets()`` after invalidating the whole tree
* ``Display.tick()`` (flush + tasks + render)
* pointer event dispatch (a synthetic ``MOUSEMOTION`` through the tree)
* ``pct.Width`` / ``pct.Height`` value computation
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "add_ons"))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from time import perf_counter

import board_config
import pdwidgets as pd
from pdwidgets import pct


def build_screen():
    display = pd.Display(board_config.display_drv, board_config.runtime)
    screen = pd.Screen(display, visible=False)

    # A representative mix of widgets.
    for i in range(4):
        b = pd.Button(screen, x=4, y=4 + i * 40, w=120, h=32, label=f"Btn {i}", radius=6)
        b.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda s, e: None)
    pd.CheckBox(screen, x=140, y=4)
    pd.ToggleButton(screen, x=140, y=44)
    grp = pd.RadioGroup(screen)
    pd.RadioButton(screen, group=grp, x=140, y=84, value=True)
    pd.RadioButton(screen, group=grp, x=140, y=124)
    pd.Slider(screen, x=4, y=180, w=200, h=18, value=0.4)
    pd.ProgressBar(screen, x=4, y=210, w=200, h=18, value=0.6)
    pd.Label(screen, x=4, y=240, value="Hello pdwidgets")
    pd.DigitalClock(screen, x=4, y=270)

    box = pd.Widget(screen, x=4, y=300, w=120, h=80, bg=screen.color_theme.primary)
    pct_w = pct.Width(50, box)
    pct_h = pct.Height(50, box)
    pd.Button(box, w=pct_w, h=pct_h, align=pd.ALIGN.CENTER)

    screen.visible = True
    return display, screen, box, pct_w, pct_h


def time_it(label, fn, iterations):
    fn()  # warm up
    start = perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = perf_counter() - start
    per = elapsed / iterations * 1e6
    print(f"  {label:<28} {per:10.3f} us/iter  ({iterations} iters)")
    return elapsed


def main():
    # Rendering/tick actually rasterize (pure-Python round_rect/text/blit) and
    # dominate wall-clock, so they use far fewer iterations than the pure-logic
    # event-dispatch and pct paths (the paths this rework optimizes).
    scale = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    heavy_iters = 200 * scale
    light_iters = 20000 * scale
    display, screen, box, pct_w, pct_h = build_screen()

    # Drain any pending work so we start from a clean state.
    for _ in range(4):
        display.tick()

    def invalidate_and_render():
        screen.invalidate()
        display.render_dirty_widgets()
        display._dirty_areas = []

    def tick():
        screen.invalidate()
        display.tick()

    motion = pd.events.Motion(pd.events.MOUSEMOTION, (60, 200), (1, 1), (0, 0, 0), False, 0)

    def dispatch():
        screen.handle_event(motion)

    def pct_eval():
        # Exercise the value + a couple of arithmetic ops (as real call sites do).
        int(pct_w)
        int(pct_h)
        _ = pct_w + 10
        _ = pct_h / 2

    print("pdwidgets benchmark")
    time_it("render_dirty_widgets", invalidate_and_render, heavy_iters)
    time_it("tick (flush+render)", tick, heavy_iters)
    time_it("event dispatch", dispatch, light_iters)
    time_it("pct compute", pct_eval, light_iters)


if __name__ == "__main__":
    main()
