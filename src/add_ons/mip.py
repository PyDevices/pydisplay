# SPDX-FileCopyrightText: 2022 Jim Mussared
# SPDX-FileCopyrightText: 2026 PyDevices / Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Portable ``mip`` for hosts that lack MicroPython's built-in package installer.

Ported from ``tools/mpremote/mpremote/mip.py`` (itself from on-device mip), with
mpremote transport/CLI removed and local filesystem writes. For:

  - CPython (desktop)
  - Pyodide / PyScript
  - CircuitPython (when urllib, urequests, or requests is available)

MicroPython ships ``mip`` in firmware. ``lib.path`` appends ``add_ons`` on
MicroPython (does not prepend), so firmware ``mip`` stays preferred when both
exist.

API (compatible subset of on-device mip)::

    import mip
    mip.install("palettes", index="https://…/mip/PyDevices")
    mip.install("github:org/repo/path/package.json", target="add_ons")
    mip.install("http://example.com/pkg.py")

``mpy`` defaults to **False** on non-MicroPython hosts (they cannot execute
MicroPython ``.mpy`` bytecode).
"""

from __future__ import annotations

import json
import os
import sys

_PACKAGE_INDEX = "https://micropython.org/pi/v2"

# Final URL is "https://" + format(org, repo, branch, p=path).
_HOSTS = {
    "codeberg:": "codeberg.org/api/v1/repos/{}/{}/raw/{p}?ref={}",
    "github:": "raw.githubusercontent.com/{}/{}/{}/{p}",
    "gitlab:": "gitlab.com/{}/{}/-/raw/{}/{p}",
}

_ALLOWED_PREFIXES = ("http://", "https://", "codeberg:", "github:", "gitlab:")


def _is_micropython():
    try:
        return sys.implementation.name == "micropython"
    except AttributeError:
        return False


def _default_mpy():
    return _is_micropython()


def _ensure_dir(path):
    """Create directory tree for *path* (MIP-friendly; no exist_ok required)."""
    if not path or path in (".", "/"):
        return
    parts = path.replace("\\", "/").split("/")
    cur = ""
    for part in parts:
        if not part:
            if not cur:
                cur = "/"
            continue
        cur = part if not cur else (cur.rstrip("/") + "/" + part)
        try:
            os.mkdir(cur)
        except OSError:
            pass


def _rewrite_url(url, branch=None):
    for provider, url_format in _HOSTS.items():
        if not url.startswith(provider):
            continue
        components = url[len(provider) :].split("/")
        if len(components) < 2:
            raise ValueError("bad package URL: " + repr(url))
        return "https://" + url_format.format(
            components[0],
            components[1],
            branch or "HEAD",
            p="/".join(components[2:]),
        )
    return url


def _http_get(url):
    """Sync GET → bytes (urllib, Pyodide open_url, urequests, or requests)."""
    try:
        from pyodide.http import open_url  # type: ignore[import-not-found]

        data = open_url(url).read()
        if isinstance(data, str):
            return data.encode("utf-8")
        return data
    except ImportError:
        pass

    try:
        from urllib.error import HTTPError, URLError
        from urllib.request import urlopen

        try:
            with urlopen(url) as resp:
                return resp.read()
        except HTTPError as e:
            raise RuntimeError("HTTP " + str(getattr(e, "code", e)) + " fetching " + url) from e
        except URLError as e:
            raise RuntimeError(str(getattr(e, "reason", e)) + " fetching " + url) from e
    except ImportError:
        pass

    for mod_name in ("urequests", "requests"):
        try:
            mod = __import__(mod_name)
        except ImportError:
            continue
        resp = mod.get(url)
        try:
            if hasattr(resp, "content"):
                data = resp.content
            elif hasattr(resp, "text"):
                text = resp.text
                data = text.encode("utf-8") if isinstance(text, str) else text
            elif callable(getattr(resp, "read", None)):
                data = resp.read()
            else:
                data = bytes(resp)
            if isinstance(data, str):
                data = data.encode("utf-8")
            status = getattr(resp, "status_code", getattr(resp, "status", 200))
            if status and int(status) >= 400:
                raise RuntimeError("HTTP " + str(status) + " fetching " + url)
            return data
        finally:
            close = getattr(resp, "close", None)
            if callable(close):
                close()

    raise RuntimeError(
        "no HTTP client for mip (need urllib, pyodide.http, urequests, or requests)"
    )


def _http_get_json(url):
    raw = _http_get(url)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def _fetch_url(url, version=None):
    """Resolve github:/gitlab:/codeberg: then return bytes (or read local path)."""
    if url.startswith(("codeberg:", "github:", "gitlab:")):
        return _http_get(_rewrite_url(url, version))
    if url.startswith(("http://", "https://")):
        return _http_get(url)
    if "\\" in url:
        raise ValueError('Use "/" instead of "\\" in file URLs: ' + repr(url))
    with open(url, "rb") as f:
        return f.read()


def _download_file(url, dest, version=None):
    data = _fetch_url(url, version)
    print("Installing:", dest)
    parent = dest.replace("\\", "/").rsplit("/", 1)
    if len(parent) == 2 and parent[0]:
        _ensure_dir(parent[0])
    with open(dest, "wb") as f:
        f.write(data)


def _check_exists(path, short_hash):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return False
    try:
        import hashlib

        digest = hashlib.sha256(data).hexdigest()
    except ImportError:
        return False
    return digest[: len(short_hash)] == short_hash


def _default_target():
    for p in sys.path:
        if not p or p == ".":
            continue
        norm = p.replace("\\", "/").rstrip("/")
        if norm.endswith("/lib") or norm == "lib" or norm.endswith("\\lib"):
            return p
    for candidate in ("lib", "/lib", "add_ons"):
        try:
            os.stat(candidate)
            return candidate
        except OSError:
            pass
    return "lib"


def _install_json(package_json_url, index, target, version, mpy):
    base_url = ""
    if package_json_url.startswith(_ALLOWED_PREFIXES):
        if package_json_url.startswith(("codeberg:", "github:", "gitlab:")):
            fetch = _rewrite_url(package_json_url, version)
        else:
            fetch = package_json_url
        package_json = _http_get_json(fetch)
        base_url = package_json_url.rpartition("/")[0]
    elif package_json_url.endswith(".json"):
        with open(package_json_url, "r") as f:
            package_json = json.load(f)
        base_url = package_json_url.replace("\\", "/").rpartition("/")[0]
    else:
        raise ValueError("Invalid url for package: " + package_json_url)

    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target.rstrip("/") + "/" + target_path
        if _check_exists(fs_target_path, short_hash):
            print("Exists:", fs_target_path)
        else:
            file_url = index.rstrip("/") + "/file/" + short_hash[:2] + "/" + short_hash
            _download_file(file_url, fs_target_path)

    for target_path, src in package_json.get("urls", ()):
        fs_target_path = target.rstrip("/") + "/" + target_path
        url = str(src)
        abs_fs = url.startswith("/") or (len(url) > 1 and url[1] == ":")
        if (
            base_url
            and not url.startswith(_ALLOWED_PREFIXES)
            and not abs_fs
        ):
            rel = url[2:] if url.startswith("./") else url
            url = base_url.rstrip("/") + "/" + rel
        _download_file(url, fs_target_path, version)

    for dep, dep_version in package_json.get("deps", ()):
        install(dep, index=index, target=target, version=dep_version, mpy=mpy)


def _install_package(package, index, target, version, mpy):
    if package.startswith(_ALLOWED_PREFIXES):
        if package.endswith(".py") or package.endswith(".mpy"):
            print("Downloading " + package + " to " + target)
            name = package.replace("\\", "/").rsplit("/", 1)[-1]
            dest = target.rstrip("/") + "/" + name
            _download_file(package, dest, version)
            return
        if not package.endswith(".json"):
            if not package.endswith("/"):
                package += "/"
            package += "package.json"
        print("Installing " + package + " to " + target)
        _install_json(package, index, target, version, mpy)
        return

    if package.endswith(".json"):
        print("Installing " + package + " to " + target)
        _install_json(package, index, target, version, mpy)
        return

    if not version:
        version = "latest"
    print("Installing " + package + " (" + version + ") from " + index + " to " + target)

    # Index layout uses "py" or an mpy version byte. Hosts always use "py".
    mpy_version = "py"
    if mpy and _is_micropython():
        mpy_version = str(getattr(sys.implementation, "_mpy", 0) & 0xFF) or "py"

    package_url = (
        index.rstrip("/") + "/package/" + mpy_version + "/" + package + "/" + version + ".json"
    )
    _install_json(package_url, index, target, version, mpy)


def install(package, index=None, target=None, version=None, mpy=None):
    """Install a package the way MicroPython ``mip.install`` does.

    *package*
        Index short name, ``github:`` / ``gitlab:`` / ``codeberg:`` URL,
        ``http(s):`` URL, or a local ``package.json`` / ``.py`` path.
    *index*
        Package index base (default ``https://micropython.org/pi/v2``).
    *target*
        Destination directory (default: first ``…/lib`` on ``sys.path``, else
        ``lib``).
    *version*
        Index version or VCS branch/tag for ``github:`` etc.
    *mpy*
        Prefer ``.mpy`` from the index when True. Defaults to False on
        CPython / CircuitPython / Pyodide.
    """
    if index is None:
        index = _PACKAGE_INDEX
    if target is None:
        target = _default_target()
    if mpy is None:
        mpy = _default_mpy()

    if (
        version is None
        and isinstance(package, str)
        and "@" in package
        and not package.startswith(_ALLOWED_PREFIXES)
        and not package.endswith(".json")
    ):
        package, version = package.split("@", 1)

    _ensure_dir(target)
    _install_package(str(package), str(index).rstrip("/"), str(target), version, bool(mpy))
