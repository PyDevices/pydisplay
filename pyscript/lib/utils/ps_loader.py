# SPDX-FileCopyrightText: 2026 PyDevices / Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PyScript gallery loader install plans (MicroPython WASM + Pyodide).

Consolidates loader install logic for ``micropython.html``, ``pyodide.html``,
``mp.html``, and ``py.html``. Gallery pages call ``_ps_loader()`` on
Run only (``import utils.path`` then ``import ps_loader``). MicroPython WASM uses
firmware ``mip`` after ``utils.path``; Pyodide uses portable ``mip.py``
(from pydevices ``utils/``, mounted at ``/utils/``).
"""

MIP_LIB_INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
# Install modules and manifests into cwd so ``import name`` / ``import pkg`` work
# with ``/`` (or ``.``) on ``sys.path`` — same as desktop ``cd lib``.
MANIFEST_MIP_TARGET = "."
WHEEL_INDEX_URLS = (
    "https://test.pypi.org/simple/",
    "https://pypi.org/simple/",
)
# Browser default board package (display + board_peripherals + audio drivers).
DESKTOP_BOARD_CONFIG_PACKAGE = "github:PyDevices/pydevices/board_configs/desktop/package.json"
# JSON API (not simple) — used to pin pyemscripten wasm wheels by direct URL.
WHEEL_JSON_URL = "https://test.pypi.org/pypi/{package_name}/json"
BOARD_WIDTH = 320
BOARD_HEIGHT = 480


def _quiet_install(mip_mod, package, **kwargs):
    """Run MIP without its per-file download/copy chatter."""
    had_printer = hasattr(mip_mod, "print")
    printer = getattr(mip_mod, "print", None)
    try:
        mip_mod.print = lambda *args, **print_kwargs: None
        return mip_mod.install(package, **kwargs)
    finally:
        if had_printer:
            mip_mod.print = printer
        else:
            delattr(mip_mod, "print")


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


def set_board_defaults():
    """Set the gallery's browser defaults without importing board_config."""
    from displaydev import env_set

    env_set("PYDEVICES_WIDTH", BOARD_WIDTH)
    env_set("PYDEVICES_HEIGHT", BOARD_HEIGHT)


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
    return "github:PyDevices/pydevices-examples/packages/" + name + ".json"


def module_url(name):
    if _use_same_origin():
        # Pages/local tree keeps the browser path web/pyscript/lib/examples/.
        return _page_base() + "lib/examples/" + name + ".py"
    return "github:PyDevices/pydevices-examples/lib/examples/" + name + ".py"


def _install_manifests_and_modules(mip_mod, modules, manifests, status=None, url_base=None):
    import os

    manifest_kw = {"target": MANIFEST_MIP_TARGET}
    if url_base is not None:
        manifest_kw["url_base"] = url_base
    for name in manifests:
        if status:
            status("Installing manifest " + name + "…")
        _quiet_install(mip_mod, manifest_url(name), **manifest_kw)
        # Package lands at ./<name>/; cwd/``/`` on sys.path → ``import name``.
        # Flat sibling imports are handled by package ``__init__`` / entry modules.
    for name in modules:
        # Skip top-level fetch when the stem already lives inside a package.
        in_pkg = False
        for m in manifests:
            try:
                os.stat(m + "/" + name + ".py")
                in_pkg = True
                break
            except OSError:
                pass
        if in_pkg:
            continue
        if status:
            status("Fetching " + name + "…")
        _quiet_install(mip_mod, module_url(name), target=MANIFEST_MIP_TARGET)


def _install_index_deps_micropython(mip_mod, names, status):
    if not names:
        return
    for which in names:
        if status:
            status("Installing " + which + "…")
        _quiet_install(mip_mod, which, index=MIP_LIB_INDEX)


def _ensure_cwd():
    import os

    try:
        os.chdir("/")
    except OSError:
        pass


def _import_firmware_mip():
    """Firmware ``mip`` on MicroPython WASM (not portable ``mip.py``).

    ``utils.path`` must run first so ``utils`` is appended, not prepended.
    """
    import mip
    import utils.path  # noqa: F401

    return mip


def _import_portable_mip():
    """Portable ``mip.py`` for Pyodide (no firmware ``mip``)."""
    _ensure_cwd()
    import mip
    import utils.path  # noqa: F401

    return mip


def _refresh_path_after_install():
    """Re-run ``utils.path.update`` after mip may have created ``lib`` / ``utils``.

    ``utils.path`` often runs before installs exist; only existing dirs are added.
    """
    import utils.path

    utils.path.update()


def _has_board_config():
    try:
        import board_config  # noqa: F401

        return True
    except ImportError:
        return False


def _ensure_board_config(mip_mod, status=None, url_base=None):
    """Install desktop board_config (+ audio) when it is not already present."""
    if _has_board_config():
        return
    if status:
        status("Installing board_config (desktop)…")
    kwargs = {"target": MANIFEST_MIP_TARGET, "index": MIP_LIB_INDEX}
    if url_base is not None:
        kwargs["url_base"] = url_base
    _quiet_install(mip_mod, DESKTOP_BOARD_CONFIG_PACKAGE, **kwargs)
    _refresh_path_after_install()


def ensure_board_config(status=None):
    """Ensure browser ``board_config`` (desktop package) is importable.

    Call after ``utils.path`` and before ``from displaydev import env_set`` /
    importing demos or setup modules that ``import board_config``. The desktop
    package pulls in ``displaydev`` (not frozen in the gallery wasm). Set size
    overrides with ``env_set`` after this returns and before the first
    ``import board_config``.
    Same package as ``harness.html`` / gallery ``install_micropython``.
    """
    _ensure_cwd()
    mip = _import_firmware_mip()
    _ensure_board_config(mip, status)


def install_micropython(modules, manifests, index_deps, status=None):
    """Sync install plan for MicroPython WASM (firmware ``mip``)."""
    _ensure_cwd()
    mip = _import_firmware_mip()
    _ensure_board_config(mip, status)
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
    # Prefer the ABI pydevices-examples vendors (pyemscripten_2026_0).
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
            await micropip.install(spec)
            continue
        wheel_url = await _pyemscripten_wheel_url(spec)
        if wheel_url:
            await micropip.install(wheel_url)
        else:
            await micropip.install(spec, index_urls=WHEEL_INDEX_URLS)


async def install_pyodide(modules, manifests, wheel_deps, status=None):
    """Async install plan for Pyodide (``mip`` manifests/modules + micropip wheels)."""
    import asyncio

    # Let the gallery paint "Running…" before sync mip fetches block the thread.
    await asyncio.sleep(0)
    mip = _import_portable_mip()
    _ensure_board_config(mip, status, url_base=_page_base())

    _install_manifests_and_modules(
        mip,
        modules,
        manifests,
        status,
        url_base=_page_base(),
    )
    _refresh_path_after_install()
    await _install_wheels_pyodide(wheel_deps, status)
