# SPDX-FileCopyrightText: 2026 PyDevices / Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PyScript gallery install plans (MicroPython WASM + Pyodide).

Consolidates loader install logic for ``micropython.html``, ``pyodide.html``,
``run.html``, and ``run-pyodide.html``. Uses firmware ``mip`` on MicroPython
WASM and async ``pyfetch`` / ``micropip`` on Pyodide — not ``add_ons/mip.py``.
"""

import json
import os
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


def github_to_raw(url):
    rest = url[len("github:") :].lstrip("/")
    parts = rest.split("/")
    if len(parts) < 3:
        raise RuntimeError("Bad github: mip URL: " + url)
    owner, repo = parts[0], parts[1]
    path = "/".join(parts[2:])
    return (
        "https://raw.githubusercontent.com/"
        + owner
        + "/"
        + repo
        + "/HEAD/"
        + path
    )


def abs_url(rel_or_abs, base_url=None):
    from urllib.parse import urljoin

    s = str(rel_or_abs).strip()
    if s.startswith("github:"):
        return github_to_raw(s)
    if s.startswith("http://") or s.startswith("https://"):
        return s
    if base_url:
        return urljoin(base_url, s)
    if s.startswith("/"):
        from js import document

        return document.location.origin + s
    return urljoin(_page_base(), s)


def mip_fetch_url(src):
    s = str(src).strip()
    if s.startswith("github:"):
        return github_to_raw(s)
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return abs_url(s)


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


def _install_index_deps_micropython(mip, names, status):
    if not names:
        return
    channel = mip_lib_channel()
    for which in names:
        if status:
            status("Installing " + which + "…")
        pkg_url = _index_package_url(which, channel)
        print("MIP install:", which, "channel=", channel)
        mip.install(pkg_url, index=MIP_LIB_INDEX)


def install_micropython(modules, manifests, index_deps, status=None):
    """Sync install plan for MicroPython WASM (firmware ``mip``)."""
    import mip

    for name in manifests:
        if status:
            status("Installing manifest " + name + "…")
        mip.install(manifest_url(name), target=MANIFEST_MIP_TARGET)
    for name in modules:
        if status:
            status("Fetching " + name + "…")
        mip.install(module_url(name))
    import lib.path  # noqa: F401
    _install_index_deps_micropython(mip, index_deps, status)


def prepare_vfs():
    os.chdir("/")
    if "/" not in sys.path:
        sys.path.insert(0, "/")
    if "/add_ons" not in sys.path:
        sys.path.insert(0, "/add_ons")


def _ensure_parent_dirs(path):
    parent = os.path.dirname(path)
    if parent and parent not in (".", "/"):
        os.makedirs(parent, exist_ok=True)


async def _fetch_text(url):
    from pyodide.http import pyfetch

    print("Fetching", url)
    resp = await pyfetch(url)
    if not resp.ok:
        raise RuntimeError("HTTP " + str(resp.status) + " fetching " + url)
    return await resp.string()


async def _install_module_pyodide(name):
    code = await _fetch_text(abs_url("src/examples/" + name + ".py"))
    with open(name + ".py", "w", encoding="utf-8") as f:  # noqa: ASYNC230
        f.write(code)


async def _install_manifest_pyodide(name):
    raw = await _fetch_text(abs_url("packages/" + name + ".json"))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("Invalid MIP JSON packages/" + name + ".json: " + str(e)) from e
    urls = data.get("urls")
    if not isinstance(urls, list) or not urls:
        raise RuntimeError("MIP manifest packages/" + name + ".json has no urls")
    os.makedirs(MANIFEST_MIP_TARGET, exist_ok=True)
    for entry in urls:
        if not (isinstance(entry, (list, tuple)) and len(entry) >= 2):
            raise RuntimeError("Bad mip urls entry in packages/" + name + ".json: " + repr(entry))
        dest_rel, src = entry[0], entry[1]
        dest = os.path.join(MANIFEST_MIP_TARGET, dest_rel)
        _ensure_parent_dirs(dest)
        code = await _fetch_text(mip_fetch_url(src))
        with open(dest, "w", encoding="utf-8") as f:  # noqa: ASYNC230
            f.write(code)
        print("Installed", dest)


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
    """Async install plan for Pyodide (MIP-json fetch + micropip wheels)."""
    prepare_vfs()
    for name in manifests:
        if status:
            status("Installing manifest " + name + "…")
        await _install_manifest_pyodide(name)
    for name in modules:
        if status:
            status("Fetching " + name + "…")
        await _install_module_pyodide(name)
    import lib.path  # noqa: F401
    await _install_wheels_pyodide(wheel_deps, status)
