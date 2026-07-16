# SPDX-FileCopyrightText: 2026 PyDevices / Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PyScript gallery loader install plans (MicroPython WASM + Pyodide).

Consolidates loader install logic for ``micropython.html``, ``pyodide.html``,
``run.html``, and ``run-pyodide.html``. MicroPython WASM uses firmware ``mip``.
Pyodide uses ``add_ons/mip.py`` for MIP manifests/modules and ``micropip`` for
wheels.
"""

import sys

MIP_LIB_INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
MANIFEST_MIP_TARGET = "examples"
WHEEL_INDEX_URLS = (
    "https://test.pypi.org/simple/",
    "https://pypi.org/simple/",
)
_MPY_LIB_CHANNEL_DEFAULT = "6"


def parse_names(raw):
    """Split a comma-separated loader query value into bare module/manifest names."""
    names = []
    for part in str(raw).split(","):
        name = part.strip()
        if name.lower().endswith(".py"):
            name = name[:-3]
        if name:
            names.append(name)
    return names


def _page_base():
    from js import document

    path = document.location.pathname
    root = path[: path.rfind("/") + 1] if "/" in path else "/"
    return document.location.origin + root


def _use_same_origin():
    from js import document

    host = document.location.hostname
    return host in ("127.0.0.1", "localhost") or host.endswith(".github.io")


def manifest_url(name):
    if _use_same_origin():
        return _page_base() + "packages/" + name + ".json"
    return "github:PyDevices/pydisplay/packages/" + name + ".json"


def module_url(name):
    if _use_same_origin():
        return _page_base() + "src/examples/" + name + ".py"
    return "github:PyDevices/pydisplay/src/examples/" + name + ".py"


def mip_lib_channel():
    mpy_byte = getattr(sys.implementation, "_mpy", 0) & 0xFF
    if mpy_byte:
        return str(mpy_byte)
    return _MPY_LIB_CHANNEL_DEFAULT


def _index_package_url(name, channel):
    return (
        MIP_LIB_INDEX.rstrip("/")
        + "/package/"
        + channel
        + "/"
        + name
        + "/latest.json"
    )


def _install_manifests_and_modules(mip_mod, modules, manifests, status=None, url_base=None):
    manifest_kw = {"target": MANIFEST_MIP_TARGET}
    if url_base is not None:
        manifest_kw["url_base"] = url_base
    for name in manifests:
        if status:
            status("Installing manifest " + name + "…")
        mip_mod.install(manifest_url(name), **manifest_kw)
    for name in modules:
        if status:
            status("Fetching " + name + "…")
        mip_mod.install(module_url(name))


def _install_index_deps_micropython(mip_mod, names, status):
    if not names:
        return
    channel = mip_lib_channel()
    for which in names:
        if status:
            status("Installing " + which + "…")
        pkg_url = _index_package_url(which, channel)
        print("MIP install:", which, "channel=", channel)
        mip_mod.install(pkg_url, index=MIP_LIB_INDEX)


def install_micropython(modules, manifests, index_deps, status=None):
    """Sync install plan for MicroPython WASM (firmware ``mip``)."""
    import mip

    _install_manifests_and_modules(mip, modules, manifests, status)
    import lib.path  # noqa: F401
    _install_index_deps_micropython(mip, index_deps, status)


def prepare_vfs():
    import os

    os.chdir("/")
    if "/" not in sys.path:
        sys.path.insert(0, "/")
    if "/add_ons" not in sys.path:
        sys.path.insert(0, "/add_ons")


async def _ensure_micropip(status):
    try:
        import micropip

        return micropip
    except ImportError:
        pass
    from pyodide_js import loadPackage

    if status:
        status("Loading micropip…")
    await loadPackage("micropip")
    import micropip

    return micropip


async def _install_wheels_pyodide(names, status):
    if not names:
        return
    micropip = await _ensure_micropip(status)
    for which in names:
        spec = str(which).strip()
        if not spec:
            continue
        if status:
            status("Installing " + spec + "…")
        if spec.startswith("http://") or spec.startswith("https://"):
            print("micropip.install", spec)
            await micropip.install(spec)
        else:
            print("micropip.install", spec, "indexes=", WHEEL_INDEX_URLS)
            await micropip.install(spec, index_urls=WHEEL_INDEX_URLS)


async def install_pyodide(modules, manifests, wheel_deps, status=None):
    """Async install plan for Pyodide (``mip`` manifests/modules + micropip wheels)."""
    prepare_vfs()
    import mip

    _install_manifests_and_modules(
        mip,
        modules,
        manifests,
        status,
        url_base=_page_base(),
    )
    import lib.path  # noqa: F401
    await _install_wheels_pyodide(wheel_deps, status)
