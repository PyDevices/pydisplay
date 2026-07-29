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
    def test_micropython_skips_frozen_palettes(self):
        q = url(
            modules=("hello",),
            deps=("palettes",),
            runtime="micropython",
        )
        self.assertEqual(q, "?modules=hello")

    def test_pyodide_deps(self):
        q = url(
            modules=("hello",),
            deps=("palettes",),
            runtime="pyodide",
        )
        self.assertEqual(q, "?modules=hello&deps=palettes,pygraphics-cmod")

    def test_runtime_none_returns_both(self):
        out = url(modules=("hello",), deps=("palettes",), runtime=None)
        self.assertEqual(
            out,
            {
                "micropython": "?modules=hello",
                "pyodide": "?modules=hello&deps=palettes,pygraphics-cmod",
            },
        )

    def test_deps_expand_both_channels(self):
        out = urls_from_deps(modules=("hello",), deps=("palettes",), runtime=None)
        self.assertEqual(out["micropython"], "?modules=hello")
        self.assertEqual(out["pyodide"], "?modules=hello&deps=palettes,pygraphics-cmod")

    def test_lvgl_rewrite_wheels_omit_mip(self):
        out = urls_from_deps(
            modules=("calc_lvgl", "calc_engine"),
            deps=("lvgl",),
            runtime=None,
        )
        self.assertEqual(out["micropython"], "?modules=calc_lvgl,calc_engine")
        self.assertEqual(
            out["pyodide"],
            "?modules=calc_lvgl,calc_engine&deps=lvgl-cpython",
        )

    def test_run_shell_also_uses_deps_key(self):
        out = urls_from_deps(
            manifests=("car_cluster",),
            deps=("lvgl",),
            runtime=None,
        )
        self.assertEqual(out["micropython"], "?manifests=car_cluster")
        self.assertEqual(
            out["pyodide"],
            "?manifests=car_cluster&deps=lvgl-cpython",
        )

    def test_pygraphics_prefers_cmod_wheel(self):
        self.assertEqual(rewrite_wheel("pygraphics"), "pygraphics-cmod")
        self.assertEqual(rewrite_mip("pygraphics"), "pygraphics")
        # MP skips frozen pygraphics; Pyodide installs pygraphics-cmod from TestPyPI
        out = urls_from_deps(modules=("x",), deps=("pygraphics",), runtime=None)
        self.assertEqual(out["micropython"], "?modules=x")
        self.assertEqual(out["pyodide"], "?modules=x&deps=pygraphics-cmod")
        q = url(
            modules=("x",),
            deps=("pygraphics",),
            runtime="micropython",
            profile="firmware-cmods",
        )
        self.assertEqual(q, "?modules=x")

    def test_pdwidgets_mp_frozen_pyodide_wheels(self):
        out = urls_from_deps(
            modules=("calc_widgets", "calc_engine"),
            deps=("pdwidgets",),
            runtime=None,
        )
        self.assertEqual(out["micropython"], "?modules=calc_widgets,calc_engine")
        self.assertEqual(
            out["pyodide"],
            "?modules=calc_widgets,calc_engine&deps=pdwidgets,pygraphics-cmod",
        )

    def test_manifests_and_modules(self):
        q = url(
            modules=("demo",),
            manifests=("alien",),
            deps=("palettes",),
            runtime="micropython",
        )
        self.assertEqual(q, "?modules=demo&manifests=alien")

    def test_unknown_kwarg_errors(self):
        with self.assertRaises(TypeError):
            url(modules=("a",), packages=("x",))  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            url(modules=("a",), mip=("x",))  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            url(modules=("a",), wheels=("x",))  # type: ignore[call-arg]

    def test_github_passthrough_on_deps(self):
        q = url(
            modules=("x",),
            deps=("github:PyDevices/pydisplay/packages/foo.json",),
            runtime="micropython",
        )
        self.assertEqual(
            q,
            "?modules=x&deps=github:PyDevices/pydisplay/packages/foo.json",
        )

    def test_rewrite_helpers(self):
        self.assertEqual(rewrite_wheel("lvgl"), "lvgl-cpython")
        self.assertIsNone(rewrite_mip("lvgl"))
        self.assertEqual(rewrite_wheel("display_driver"), "lvgl-cpython")
        self.assertIsNone(rewrite_mip("display_driver"))
        self.assertEqual(rewrite_wheel("usdl2-py"), "usdl2")
        self.assertEqual(rewrite_mip("usdl2-py"), "usdl2")

    def test_usdl2_mp_frozen_pyodide_wheels(self):
        out = urls_from_deps(modules=("x",), deps=("usdl2",), runtime=None)
        self.assertEqual(out["micropython"], "?modules=x")
        self.assertEqual(out["pyodide"], "?modules=x&deps=usdl2")


if __name__ == "__main__":
    unittest.main()
