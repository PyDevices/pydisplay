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

from displaysys import AutoDisplay, host_kind
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
    def test_pyscript_returns_display(self):
        display = mock.Mock(name="PSDisplay")
        display.get_events = mock.Mock(name="ps_get_events")
        display.requires_async_timer = True
        ps_mod = types.ModuleType("displaysys.psdisplay")
        ps_mod.PSDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="pyscript"), mock.patch.dict(
            sys.modules, {"displaysys.psdisplay": ps_mod}
        ):
            result = AutoDisplay(width=100, height=200, canvas_id="c1", quiet=True)
        self.assertIs(result, display)
        self.assertTrue(result.requires_async_timer)
        self.assertIs(result.get_events, display.get_events)
        ps_mod.PSDisplay.assert_called_once_with("c1", 100, 200, quiet=True)

    def test_jupyter_returns_display(self):
        display = mock.Mock(name="JNDisplay")
        display.get_events = mock.Mock(name="jn_get_events")
        display.requires_async_timer = True
        jn_mod = types.ModuleType("displaysys.jndisplay")
        jn_mod.JNDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="jupyter"), mock.patch.dict(
            sys.modules, {"displaysys.jndisplay": jn_mod}
        ):
            result = AutoDisplay(width=80, height=60, quiet=True)
        self.assertIs(result, display)
        self.assertTrue(result.requires_async_timer)
        jn_mod.JNDisplay.assert_called_once_with(80, 60, quiet=True)

    def test_desktop_pg_first(self):
        display = mock.Mock(name="PGDisplay")
        display.get_events = mock.Mock(name="pg_get_events")
        display.requires_async_timer = False
        pg_mod = types.ModuleType("displaysys.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(return_value=display)
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
        self.assertIs(result, display)
        self.assertFalse(result.requires_async_timer)
        self.assertIs(result.get_events, display.get_events)
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
        display.get_events = mock.Mock(name="sdl_get_events")
        display.requires_async_timer = False
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.dict(
            sys.modules, {"displaysys.pgdisplay": None}
        ), mock.patch("displaysys.sdldisplay.SDLDisplay", return_value=display) as sdl_cls:
            result = AutoDisplay(
                width=160,
                height=120,
                title="sdl",
                quiet=True,
            )
        self.assertIs(result, display)
        self.assertFalse(result.requires_async_timer)
        sdl_cls.assert_called_once()
        kwargs = sdl_cls.call_args.kwargs
        self.assertEqual(kwargs["width"], 160)
        self.assertEqual(kwargs["height"], 120)
        self.assertEqual(kwargs["title"], "sdl")

    def test_win32_sets_directsound_before_non_pyscript_backends(self):
        display = mock.Mock(name="PGDisplay")
        display.get_events = mock.Mock()
        display.requires_async_timer = False
        pg_mod = types.ModuleType("displaysys.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.object(
            ad.sys, "platform", "win32"
        ), mock.patch("displaysys.env_get", return_value=None) as env_get, mock.patch(
            "displaysys.env_set"
        ) as env_set, mock.patch.dict(sys.modules, {"displaysys.pgdisplay": pg_mod}):
            AutoDisplay(width=10, height=10, quiet=True)
        env_get.assert_called_with("SDL_AUDIODRIVER")
        env_set.assert_called_once_with("SDL_AUDIODRIVER", "directsound")

    def test_win32_skips_directsound_for_pyscript(self):
        display = mock.Mock(name="PSDisplay")
        display.get_events = mock.Mock()
        display.requires_async_timer = True
        ps_mod = types.ModuleType("displaysys.psdisplay")
        ps_mod.PSDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="pyscript"), mock.patch.object(
            ad.sys, "platform", "win32"
        ), mock.patch("displaysys.env_set") as env_set, mock.patch.dict(
            sys.modules, {"displaysys.psdisplay": ps_mod}
        ):
            AutoDisplay(width=10, height=10, canvas_id="c", quiet=True)
        env_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
