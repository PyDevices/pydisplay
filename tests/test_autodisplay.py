# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Unit tests for ``displaydev.auto`` host selection."""

import builtins
import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401

from displaydev import auto as ad
from displaydev.auto import AutoDisplay, host_kind


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
        ), mock.patch.object(ad.sys, "platform", "linux"):
            self.assertEqual(host_kind(), "desktop")

    def test_android(self):
        with mock.patch.object(ad.sys, "platform", "android"):
            self.assertEqual(host_kind(), "android")


class TestAutoDisplay(unittest.TestCase):
    def test_pyscript_returns_display(self):
        display = mock.Mock(name="PSDisplay")
        display.get_events = mock.Mock(name="ps_get_events")
        display.requires_async_timer = True
        ps_mod = types.ModuleType("displaydev.psdisplay")
        ps_mod.PSDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="pyscript"), mock.patch.dict(
            sys.modules, {"displaydev.psdisplay": ps_mod}
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
        jn_mod = types.ModuleType("displaydev.jndisplay")
        jn_mod.JNDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="jupyter"), mock.patch.dict(
            sys.modules, {"displaydev.jndisplay": jn_mod}
        ):
            result = AutoDisplay(width=80, height=60, quiet=True)
        self.assertIs(result, display)
        self.assertTrue(result.requires_async_timer)
        jn_mod.JNDisplay.assert_called_once_with(80, 60, quiet=True)

    def test_desktop_pg_first(self):
        display = mock.Mock(name="PGDisplay")
        display.get_events = mock.Mock(name="pg_get_events")
        display.requires_async_timer = False
        pg_mod = types.ModuleType("displaydev.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.object(
            ad.sys, "platform", "linux"
        ), mock.patch.dict(sys.modules, {"displaydev.pgdisplay": pg_mod}):
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
        sdl_mod = types.ModuleType("displaydev.sdldisplay")
        sdl_mod.SDLDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.object(
            ad.sys, "platform", "linux"
        ), mock.patch.dict(
            sys.modules,
            {"displaydev.pgdisplay": None, "displaydev.sdldisplay": sdl_mod},
        ):
            result = AutoDisplay(
                width=160,
                height=120,
                title="sdl",
                quiet=True,
            )
        self.assertIs(result, display)
        self.assertFalse(result.requires_async_timer)
        self.assertIs(result.get_events, display.get_events)
        sdl_mod.SDLDisplay.assert_called_once()
        kwargs = sdl_mod.SDLDisplay.call_args.kwargs
        self.assertEqual(kwargs["width"], 160)
        self.assertEqual(kwargs["height"], 120)
        self.assertEqual(kwargs["title"], "sdl")

    def test_win32_prefers_windisplay(self):
        display = mock.Mock(name="WinDisplay")
        display.get_events = mock.Mock()
        display.requires_async_timer = False
        win_mod = types.ModuleType("displaydev.windisplay")
        win_mod.WinDisplay = mock.Mock(return_value=display)
        pg_mod = types.ModuleType("displaydev.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(name="PGDisplay_should_not_be_used")
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.object(
            ad.sys, "platform", "win32"
        ), mock.patch("displaydev.env_set") as env_set, mock.patch.dict(
            sys.modules, {"displaydev.windisplay": win_mod, "displaydev.pgdisplay": pg_mod}
        ):
            result = AutoDisplay(width=10, height=10, quiet=True)
        self.assertIs(result, display)
        win_mod.WinDisplay.assert_called_once()
        pg_mod.PGDisplay.assert_not_called()
        env_set.assert_not_called()

    def test_win32_sets_directsound_when_windisplay_unavailable(self):
        display = mock.Mock(name="PGDisplay")
        display.get_events = mock.Mock()
        display.requires_async_timer = False
        pg_mod = types.ModuleType("displaydev.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="desktop"), mock.patch.object(
            ad.sys, "platform", "win32"
        ), mock.patch("displaydev.env_get", return_value=None) as env_get, mock.patch(
            "displaydev.env_set"
        ) as env_set, mock.patch.dict(
            sys.modules, {"displaydev.windisplay": None, "displaydev.pgdisplay": pg_mod}
        ):
            AutoDisplay(width=10, height=10, quiet=True)
        env_get.assert_called_with("SDL_AUDIODRIVER")
        env_set.assert_called_once_with("SDL_AUDIODRIVER", "directsound")
        pg_mod.PGDisplay.assert_called_once()

    def test_win32_skips_directsound_for_pyscript(self):
        display = mock.Mock(name="PSDisplay")
        display.get_events = mock.Mock()
        display.requires_async_timer = True
        ps_mod = types.ModuleType("displaydev.psdisplay")
        ps_mod.PSDisplay = mock.Mock(return_value=display)
        with mock.patch.object(ad, "host_kind", return_value="pyscript"), mock.patch.object(
            ad.sys, "platform", "win32"
        ), mock.patch("displaydev.env_set") as env_set, mock.patch.dict(
            sys.modules, {"displaydev.psdisplay": ps_mod}
        ):
            AutoDisplay(width=10, height=10, canvas_id="c", quiet=True)
        env_set.assert_not_called()

    def test_android_uses_shown_highdpi_flags(self):
        display = mock.Mock(name="AndroidSDLDisplay")
        display.get_events = mock.Mock(name="sdl_get_events")
        display.requires_async_timer = False
        android_mod = types.ModuleType("displaydev.androidsdl")
        android_mod.AndroidSDLDisplay = mock.Mock(return_value=display)
        usdl2_mod = types.ModuleType("usdl2")
        usdl2_mod.SDL_WINDOW_SHOWN = 0x4
        usdl2_mod.SDL_WINDOW_ALLOW_HIGHDPI = 0x2000
        pg_mod = types.ModuleType("displaydev.pgdisplay")
        pg_mod.PGDisplay = mock.Mock(name="PGDisplay_should_not_be_used")
        with mock.patch.object(ad, "host_kind", return_value="android"), mock.patch.dict(
            sys.modules,
            {
                "usdl2": usdl2_mod,
                "displaydev.androidsdl": android_mod,
                "displaydev.pgdisplay": pg_mod,
            },
        ):
            result = AutoDisplay(
                width=720,
                height=1280,
                scale=1.0,
                title="android",
                quiet=True,
            )
        self.assertIs(result, display)
        pg_mod.PGDisplay.assert_not_called()
        kwargs = android_mod.AndroidSDLDisplay.call_args.kwargs
        self.assertEqual(kwargs["width"], 720)
        self.assertEqual(kwargs["height"], 1280)
        self.assertEqual(
            kwargs["window_flags"],
            usdl2_mod.SDL_WINDOW_SHOWN | usdl2_mod.SDL_WINDOW_ALLOW_HIGHDPI,
        )


if __name__ == "__main__":
    unittest.main()
