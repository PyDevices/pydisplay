"""
pixel_sim_reel.py — play every pixel_sim demo back to back on the simulator.

Runs the demo reel (``scroll`` -> ``plasma`` -> ``fire`` -> ``matrix`` ->
``starfield``) in succession, giving each ``SECONDS`` of screen time before
advancing.  All demos share the one ``pixel_sim`` backend and ``runtime``, so it
is **time-boxed** rather than close-to-advance: closing the window (or Ctrl-C)
ends the whole reel.

``scroll`` advances at cycle boundaries (its ``main()`` is one full
scroll+gradient cycle); the frame-based effects advance every frame.

Run it as the main program to loop the reel forever (closes with the window):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_reel.py', run_name='__main__')"

On MicroPython, launch ``micropython`` from ``src/``, then::

    import lib.path
    import pixel_sim_reel

Plain ``import pixel_sim_reel`` plays the reel once through and returns.
"""

from multimer import ticks_add, ticks_diff, ticks_ms
from pixel_sim import runtime

DEMOS = (
    "pixel_sim_scroll",
    "pixel_sim_plasma",
    "pixel_sim_fire",
    "pixel_sim_matrix",
    "pixel_sim_starfield",
)
SECONDS = 6  # screen time per demo before advancing

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None

_START = ticks_ms()


def _stop():
    """Poll input so the window closes; True when quitting or the test times out."""
    if runtime is not None:
        runtime.poll()
        if runtime.quit_requested:
            return True
    if _TEST_DURATION_S is not None and ticks_diff(ticks_ms(), _START) >= _TEST_DURATION_S * 1000:
        return True
    return False


def _play(module, seconds):
    """Run one demo for ``seconds``; True if the whole reel should stop."""
    deadline = ticks_add(ticks_ms(), int(seconds * 1000))
    while ticks_diff(deadline, ticks_ms()) > 0:
        module.main()
        if _stop():
            return True
    return False


def main():
    """Play every demo once, in order (returns early on quit)."""
    for name in DEMOS:
        module = __import__(name)
        if _play(module, SECONDS):
            return


main()  # play the reel once through; importing never loops forever

if __name__ == "__main__":
    try:
        while not _stop():
            main()
    except KeyboardInterrupt:
        pass
