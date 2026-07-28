# SPDX-FileCopyrightText: 2026 PyDevices / Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PyScript gallery loader install plans (MicroPython WASM + Pyodide).

Consolidates loader install logic for ``micropython.html``, ``pyodide.html``,
``run.html``, and ``run-pyodide.html``. Gallery pages call ``_ps_loader()`` on
Run only (``import lib.path`` then ``import ps_loader``). MicroPython WASM uses
firmware ``mip`` after ``lib.path``; Pyodide uses ``add_ons/mip.py``.
"""

MIP_LIB_INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
MANIFEST_MIP_TARGET = "examples"
WHEEL_INDEX_URLS = (
    "https://test.pypi.org/simple/",
    "https://pypi.org/simple/",
)
# JSON API (not simple) — used to pin pyemscripten wasm wheels by direct URL.
WHEEL_JSON_URL = "https://test.pypi.org/pypi/{package_name}/json"


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


def _install_manifests_and_modules(mip_mod, modules, manifests, status=None, url_base=None):
    import os
    import sys

    manifest_kw = {"target": MANIFEST_MIP_TARGET}
    if url_base is not None:
        manifest_kw["url_base"] = url_base
    for name in manifests:
        if status:
            status("Installing manifest " + name + "…")
        mip_mod.install(manifest_url(name), **manifest_kw)
        # Flat sibling imports (``import roku_engine``) match desktop wrapper,
        # which puts ``examples/<pkg>/`` on ``sys.path``.
        pkg_path = MANIFEST_MIP_TARGET + "/" + name
        if pkg_path not in sys.path:
            sys.path.insert(0, pkg_path)
    for name in modules:
        # Skip top-level fetch when the stem already lives inside a package.
        in_pkg = False
        for m in manifests:
            try:
                os.stat(MANIFEST_MIP_TARGET + "/" + m + "/" + name + ".py")
                in_pkg = True
                break
            except OSError:
                pass
        if in_pkg:
            continue
        if status:
            status("Fetching " + name + "…")
        mip_mod.install(module_url(name))


def _install_index_deps_micropython(mip_mod, names, status):
    if not names:
        return
    for which in names:
        if status:
            status("Installing " + which + "…")
        print("MIP install:", which, "index=", MIP_LIB_INDEX)
        mip_mod.install(which, index=MIP_LIB_INDEX)


def _ensure_cwd():
    import os

    try:
        os.chdir("/")
    except OSError:
        pass


def _import_firmware_mip():
    """Firmware ``mip`` on MicroPython WASM (not ``add_ons/mip.py``).

    ``lib.path`` must run first so ``add_ons`` is appended, not prepended.
    """
    import mip

    import lib.path  # noqa: F401

    return mip


def _import_portable_mip():
    """Portable ``add_ons/mip.py`` for Pyodide (no firmware ``mip``)."""
    _ensure_cwd()
    import mip

    import lib.path  # noqa: F401

    return mip


def _refresh_path_after_install():
    """Re-scan cwd dirs so mip-created ``examples/`` is on ``sys.path``.

    ``lib.path`` often runs before manifests exist; only existing dirs are added.
    """
    import lib.path

    lib.path.update()


def install_micropython(modules, manifests, index_deps, status=None):
    """Sync install plan for MicroPython WASM (firmware ``mip``)."""
    _ensure_cwd()
    mip = _import_firmware_mip()
    _install_manifests_and_modules(mip, modules, manifests, status)
    _refresh_path_after_install()
    _install_index_deps_micropython(mip, index_deps, status)


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


async def _pyemscripten_wheel_url(spec):
    """Return TestPyPI URL for a ``pyemscripten_*_wasm32`` wheel, or None.

    Micropip can only load pure-Python or pyemscripten wheels. Resolving the
    wasm file to a direct ``.whl`` URL avoids stale IndexedDB / simple-index
    metadata that still lists only manylinux/win builds (common after a
    package first gained a wasm wheel).
    """
    name = str(spec).strip()
    if not name or name.endswith(".whl") or "://" in name:
        return None
    if name.startswith(("github:", "gitlab:", "codeberg:")):
        return None
    try:
        from pyodide.http import pyfetch
    except ImportError:
        return None
    url = WHEEL_JSON_URL.format(package_name=name)
    try:
        resp = await pyfetch(url)
        if resp.status != 200:
            return None
        data = await resp.json()
    except Exception as exc:
        print("wheel metadata fetch failed:", name, exc)
        return None
    candidates = []
    for entry in data.get("urls") or ():
        filename = str(entry.get("filename") or "")
        file_url = entry.get("url")
        if file_url and "pyemscripten_" in filename and filename.endswith("_wasm32.whl"):
            candidates.append(str(file_url))
    if not candidates:
        # Latest release may lag; scan all versions for a wasm wheel.
        releases = data.get("releases") or {}
        for files in releases.values():
            for entry in files or ():
                filename = str(entry.get("filename") or "")
                file_url = entry.get("url")
                if file_url and "pyemscripten_" in filename and filename.endswith("_wasm32.whl"):
                    candidates.append(str(file_url))
    if not candidates:
        return None
    # Prefer the ABI pydisplay vendors (pyemscripten_2026_0).
    for preferred in candidates:
        if "pyemscripten_2026_0_wasm32" in preferred:
            return preferred
    return candidates[0]


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
            continue
        wheel_url = await _pyemscripten_wheel_url(spec)
        if wheel_url:
            print("micropip.install", spec, "→", wheel_url)
            await micropip.install(wheel_url)
        else:
            print("micropip.install", spec, "indexes=", WHEEL_INDEX_URLS)
            await micropip.install(spec, index_urls=WHEEL_INDEX_URLS)


async def install_pyodide(modules, manifests, wheel_deps, status=None):
    """Async install plan for Pyodide (``mip`` manifests/modules + micropip wheels)."""
    mip = _import_portable_mip()

    _install_manifests_and_modules(
        mip,
        modules,
        manifests,
        status,
        url_base=_page_base(),
    )
    _refresh_path_after_install()
    await _install_wheels_pyodide(wheel_deps, status)
