# deps: lvgl
# modules: roku_engine, roku_lvgl
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_remote
====================================================
Launcher for the Roku remote stack.

Loads prefs (``frontend``, MRU host/serial, saved TVs), resumes the last TV
when its serial still matches, then starts the chosen front end:

* :mod:`roku_engine`   -- ECP client + discovery + prefs (no UI)
* :mod:`roku_lvgl`     -- LVGL front end (default)
* :mod:`roku_widgets`  -- ``pdwidgets`` front end
* :mod:`roku_graphics` -- ``graphics.FrameBuffer`` front end

Switching front ends from MORE writes prefs and asks you to restart the app
(exit / re-run ``roku_remote``). PyScript and Jupyter: leave the page / restart
the kernel the same way. Soft-reset is not relied on (it does not re-run
``main.py``).

Requires Roku **Control by mobile apps -> Enabled**; join WiFi before running
on a microcontroller. Optional fixed target: ``ROKU_HOST`` in :mod:`roku_engine`.
"""

import lib.path  # noqa: F401 — adds lib/, add_ons/, examples/

import roku_engine
from roku_engine import (
    DEFAULT_FRONTEND,
    RokuEngine,
    get_frontend,
)


def _import_frontend(name):
    """Import one front-end module by prefs id."""
    if name == "widgets":
        import roku_widgets as mod

        return mod
    if name == "graphics":
        import roku_graphics as mod

        return mod
    import roku_lvgl as mod

    return mod


def main():
    # Suppress front-end auto-start on import; we call ``run()`` below.
    roku_engine._LAUNCHER_OWNS_RUN = True

    engine = RokuEngine()
    start_page = "devices"
    try:
        if engine.resume_last_host():
            start_page = "remote"
    except Exception:
        start_page = "devices"

    name = get_frontend()
    try:
        mod = _import_frontend(name)
    except Exception as err:
        # Fall back for this session only — do not rewrite prefs, or a
        # transient import failure (missing pdwidgets path, etc.) would erase
        # the user's chosen front end and always reopen LVGL after restart.
        print(
            "roku_remote: %s front end unavailable (%s); using %s"
            % (name, err, DEFAULT_FRONTEND)
        )
        mod = _import_frontend(DEFAULT_FRONTEND)

    mod.run(engine=engine, start_page=start_page)


main()
