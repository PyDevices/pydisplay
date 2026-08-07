# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Unit tests for ``displaysys.autodisplay`` host selection."""

import builtins
import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401

from displaysys import AutoDisplay, AutoDisplayResult, host_kind
from displaysys import autodisplay as ad


class TestHostKind(unittest.TestCase):
    def test_pyscript(self):
        fake = types.ModuleType("pyscript")
        with mock.patch.dict(sys.modules, {"pyscript": fake}):
            self.assertEqual(host_kind(), "pyscript")

    def test_jupyter(self):
        with mock.patch.dict(sys.modules, {"pyscript": None}), mock.patch.object(
            builtins, "get_ipython", create=True, return_value=object()
        ):
            self.assertEqual(host_kind(), "jupyter")

    def test_desktop(self):
        with mock.patch.dict(sys.modules, {"pyscript": None}), mock.patch.object(
            builtins, "get_ipython", create=True, side_effect=NameError
        ):
            self.assertEqual(host_kind(), "desktop")


class TestAutoDisplay(unittest.TestCase):
    def test_pyscript_branch(self):
        display = mock.Mock(name="PSDisplay")
        devices = mock.Mock()
        devices.read = mock.Mock(name="ps_read")
        ps_mod = types.ModuleType("displaysys.psdisplay")
        ps_mod.PSDisplay = mock.Mock(return_value=display)
        ps_mod.PSDevices = mock.Mock(return_value=devices)
        with mock.patch.object(ad, "host_kind", return_value="pyscript"), mock.patch.dict(
            sys.modules, {"displaysys.psdisplay": ps_mod}
        ):
            result = AutoDisplay(width=100, height=200, canvas_id="c1", quiet=True)
        self.assertIsInstance(result, AutoDisplayResult)
        self.assertIs(result.display, display)
        self.assertIs(result.host_read, devices.read)
        self.assertTrue(result.timer_async)
        self.assertEqual(result.host, "pyscript")
        ps_mod.PSDisplay.assert_called_once_with("c1", 100, 200, quiet=True)
        ps_mod.PSDevices.assert_called_once_with("c1", display)

    def test_jupyter_branch(self):
        display = mock.Mock(name="JNDisplay")
        devices = mock.Mock()
        devices.read = mock.Mock(name="jn_read")
        jn_mod = types.ModuleType("displaysys.jndisplay")
        jn_mod.JNDisplay = mock.Mock(return_value=display)
        jn_mod.JNDevices = mock.Mock(return_value=devices)
        with mock.patch.object(ad, "host_kind", return_value="jupyter"), mock.patch.dict(
            sys.modules, {"displaysys.jndisplay": jn_mod}
        ):
            result = AutoDisplay(width=80, height=60, quiet=True)
        self.assertIs(result.display, display)
        self.assertIs(result.host_read, devices.read)
        self.assertTrue(result.timer_async)
        self.assertEqual(result.host, "jupyter")
        jn_mod.JNDisplay.assert_called_once_with(80, 60, quiet=True)

    def test_desktop_pg_first(self):
        display = mock.Mock(name="PGDisplay")
        get_events = mock.Mock(name="pg_get_events")
        pg_mod = types.ModuleType("displaysys.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(return_value=display)
        pg_mod.get_events = get_events
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.dict(
            sys.modules, {"displaysys.pgdisplay": pg_mod}
        ):
            result = AutoDisplay(
                width=320,
                height=480,
                rotation=90,
                scale=2.0,
                title="t",
                quiet=True,
            )
        self.assertIs(result.display, display)
        self.assertIs(result.host_read, get_events)
        self.assertFalse(result.timer_async)
        self.assertEqual(result.host, "desktop")
        pg_mod.PGDisplay.assert_called_once_with(
            width=320,
            height=480,
            rotation=90,
            title="t",
            scale=2.0,
            quiet=True,
        )

    def test_desktop_falls_back_to_sdl(self):
        display = mock.Mock(name="SDLDisplay")
        get_events = mock.Mock(name="sdl_get_events")
        # ``sys.modules[name] is None`` → ImportError on import
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.dict(
            sys.modules, {"displaysys.pgdisplay": None}
        ), mock.patch(
            "displaysys.sdldisplay.SDLDisplay", return_value=display
        ) as sdl_cls, mock.patch("displaysys.sdldisplay.get_events", get_events):
            result = AutoDisplay(
                width=160,
                height=120,
                title="sdl",
                quiet=True,
            )
        self.assertIs(result.display, display)
        self.assertIs(result.host_read, get_events)
        self.assertFalse(result.timer_async)
        self.assertEqual(result.host, "desktop")
        sdl_cls.assert_called_once()
        kwargs = sdl_cls.call_args.kwargs
        self.assertEqual(kwargs["width"], 160)
        self.assertEqual(kwargs["height"], 120)
        self.assertEqual(kwargs["title"], "sdl")


if __name__ == "__main__":
    unittest.main()
