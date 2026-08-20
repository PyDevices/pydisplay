# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Unit tests for ``lib/utils/fetch_ph_gui.py`` interpreter patches."""

import asyncio
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "lib" / "utils"
if str(UTILS) not in sys.path:
    sys.path.insert(0, str(UTILS))

import fetch_ph_gui  # noqa: E402


class FetchPhGuiPatchTests(unittest.TestCase):
    def test_patch_uasyncio_registers_sys_modules(self):
        sys.modules.pop("uasyncio", None)
        fetch_ph_gui._patch_uasyncio()
        self.assertIn("uasyncio", sys.modules)
        self.assertIn("asyncio", sys.modules)
        self.assertIs(sys.modules["uasyncio"], sys.modules["asyncio"])
        self.assertTrue(hasattr(sys.modules["uasyncio"], "sleep_ms"))

    def test_uasyncio_sleep_ms_execution(self):
        fetch_ph_gui._patch_uasyncio()
        import uasyncio

        async def _test():
            await uasyncio.sleep_ms(1)

        asyncio.run(_test())

    def test_asyncio_compat_run_and_new_event_loop(self):
        fetch_ph_gui._patch_uasyncio()
        compat = sys.modules["asyncio"]

        # Outside running loop, run and new_event_loop behave standardly
        async def sample():
            return 42

        res = compat.run(sample())
        self.assertEqual(res, 42)

    def test_apply_patches_calls_patch_uasyncio(self):
        sys.modules.pop("uasyncio", None)
        fetch_ph_gui._apply_patches("micropython-touch")
        self.assertIn("uasyncio", sys.modules)

        sys.modules.pop("uasyncio", None)
        fetch_ph_gui._apply_patches("micropython-micro-gui")
        self.assertIn("uasyncio", sys.modules)

        sys.modules.pop("uasyncio", None)
        fetch_ph_gui._apply_patches("micropython-nano-gui")
        self.assertIn("uasyncio", sys.modules)
