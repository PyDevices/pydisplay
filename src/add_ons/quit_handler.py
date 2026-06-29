# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Wire pydisplay display cleanup into ``broker.on_quit``."""


def wire_display_quit(broker, before=None, after=None):
    """Install a quit handler that cleans up registered display drivers.

    Scans registered devices for ``_data`` objects with ``deinit`` and ``quit``,
    calls ``data.quit()``, then ``os._exit(0)`` when a display was found — matching
    legacy pydisplay behavior now that eventsys no longer terminates the process.
    """

    def on_quit():
        if before is not None:
            try:
                before()
            except SystemExit:
                pass
        display_quit = False
        try:
            for device in broker.devices:
                data = getattr(device, "_data", None)
                if callable(getattr(data, "deinit", None)) and callable(
                    getattr(data, "quit", None)
                ):
                    display_quit = True
                    data.quit()
        except SystemExit:
            pass
        if display_quit:
            import os

            os._exit(0)
        if after is not None:
            try:
                after()
            except SystemExit:
                pass

    broker.on_quit = on_quit
