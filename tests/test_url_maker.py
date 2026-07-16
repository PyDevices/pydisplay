"""Unit tests for scripts/url_maker.py."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from url_maker import rewrite_mip, rewrite_wheel, url, urls_from_deps  # noqa: E402


class UrlMakerTests(unittest.TestCase):
    def test_micropython_filters_wheels(self):
        q = url(
            modules=("hello",),
            mip=("palettes",),
            wheels=("palettes",),
            runtime="micropython",
        )
        self.assertEqual(q, "?modules=hello&mip=palettes")

    def test_pyodide_filters_mip(self):
        q = url(
            modules=("hello",),
            mip=("palettes",),
            wheels=("palettes",),
            runtime="pyodide",
        )
        self.assertEqual(q, "?modules=hello&wheels=palettes")

    def test_runtime_none_returns_both(self):
        out = url(modules=("hello",), mip=("palettes",), wheels=("palettes",), runtime=None)
        self.assertEqual(
            out,
            {
                "micropython": "?modules=hello&mip=palettes",
                "pyodide": "?modules=hello&wheels=palettes",
            },
        )

    def test_deps_expand_both_channels(self):
        out = urls_from_deps(modules=("hello",), deps=("palettes",), runtime=None)
        self.assertEqual(out["micropython"], "?modules=hello&mip=palettes")
        self.assertEqual(out["pyodide"], "?modules=hello&wheels=palettes")

    def test_lvgl_rewrite_wheels_omit_mip(self):
        out = urls_from_deps(
            modules=("calc_lvgl", "calc_engine"),
            deps=("lvgl",),
            runtime=None,
        )
        self.assertEqual(out["micropython"], "?modules=calc_lvgl,calc_engine")
        self.assertEqual(
            out["pyodide"],
            "?modules=calc_lvgl,calc_engine&wheels=lvgl-cpython",
        )

    def test_graphics_prefers_cmod_wheel(self):
        self.assertEqual(rewrite_wheel("graphics"), "graphics-cmod")
        self.assertEqual(rewrite_mip("graphics"), "graphics")
        # pyscript profiles skip graphics (mounted)
        out = urls_from_deps(modules=("x",), deps=("graphics",), runtime=None)
        self.assertEqual(out["micropython"], "?modules=x")
        self.assertEqual(out["pyodide"], "?modules=x")
        # empty-skip profile emits graphics-cmod on wheels
        q = url(
            modules=("x",),
            wheels=("graphics",),
            runtime="pyodide",
            profile="bare",
        )
        self.assertEqual(q, "?modules=x&wheels=graphics-cmod")
        q = url(
            modules=("x",),
            mip=("graphics",),
            runtime="micropython",
            profile="firmware-cmods",
        )
        self.assertEqual(q, "?modules=x")

    def test_pdwidgets_passthrough(self):
        out = urls_from_deps(
            modules=("calc_widgets", "calc_engine"),
            deps=("pdwidgets",),
            runtime=None,
        )
        self.assertEqual(
            out["micropython"],
            "?modules=calc_widgets,calc_engine&mip=pdwidgets",
        )
        self.assertEqual(
            out["pyodide"],
            "?modules=calc_widgets,calc_engine&wheels=pdwidgets",
        )

    def test_manifests_and_modules(self):
        q = url(
            modules=("demo",),
            manifests=("alien",),
            mip=("palettes",),
            runtime="micropython",
        )
        self.assertEqual(q, "?modules=demo&manifests=alien&mip=palettes")

    def test_unknown_kwarg_errors(self):
        with self.assertRaises(TypeError):
            url(modules=("a",), packages=("x",))  # type: ignore[call-arg]

    def test_github_passthrough_on_mip(self):
        q = url(
            modules=("x",),
            mip=("github:PyDevices/pydisplay/packages/foo.json",),
            runtime="micropython",
        )
        self.assertEqual(
            q,
            "?modules=x&mip=github:PyDevices/pydisplay/packages/foo.json",
        )

    def test_rewrite_helpers(self):
        self.assertEqual(rewrite_wheel("lvgl"), "lvgl-cpython")
        self.assertIsNone(rewrite_mip("lvgl"))


if __name__ == "__main__":
    unittest.main()
