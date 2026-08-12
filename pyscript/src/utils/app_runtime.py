# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Opt this application into the optional ``eventsys`` traffic controller.

Board configs describe hardware and never create an event runtime. Non-LVGL
examples import this module to make that application-level choice explicit.
LVGL applications instead use the independent runtime exported by
``display_driver``.
"""

import board_config

import eventsys


class ExampleRuntime(eventsys.Runtime):
    """Runtime with gallery-harness behavior kept outside the product package."""

    def _perform_teardown(self):
        try:
            import pydisplay_test_mode

            testing = pydisplay_test_mode.ENABLED
        except ImportError:
            testing = False
        if not testing:
            return super()._perform_teardown()
        if self._teardown_done:
            return
        self._teardown_done = True
        self._quit_requested = True
        if self.before_quit is not None:
            self.before_quit()
        self.stop_timer()


try:
    import pydisplay_test_mode

    _options = {"refresh_period": 0} if pydisplay_test_mode.ENABLED else {}
except ImportError:
    _options = {}

runtime = ExampleRuntime.from_board_config(board_config, **_options)

__all__ = ["ExampleRuntime", "runtime"]
