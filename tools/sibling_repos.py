"""
Discover palettes / pdwidgets / pygraphics / usdl2 sibling repo ``lib`` directories
for the example harness.

Search order per package:
  1. ``PYDISPLAY_<PKG>_LIB`` (optional override; ``PYDISPLAY_PALETTES_SRC`` etc.
     still accepted as aliases)
  2. ``/agent/repos/<pkg>/lib``
  3. ``~/gh/pydevices/<pkg>/lib``
  4. ``<repo_root>/../<pkg>/lib``

MicroPython-safe (no ``os.path`` / pathlib) so ``example_test_wrapper.py`` can import it.
"""

import os

_SIBLING_PACKAGES = ("palettes", "pdwidgets", "pygraphics", "usdl2")
_ENV_KEYS = {
    "palettes": "PYDISPLAY_PALETTES_LIB",
    "pdwidgets": "PYDISPLAY_PDWIDGETS_LIB",
    "pygraphics": "PYDISPLAY_PYGRAPHICS_LIB",
    "usdl2": "PYDISPLAY_USDL2_LIB",
}
# Backward-compatible aliases (older harness / docs used *_SRC).
_ENV_ALIASES = {
    "palettes": ("PYDISPLAY_PALETTES_SRC",),
    "pdwidgets": ("PYDISPLAY_PDWIDGETS_SRC",),
    "pygraphics": (
        "PYDISPLAY_GRAPHICS_LIB",
        "PYDISPLAY_GRAPHICS_SRC",
        "PYDISPLAY_PYGRAPHICS_SRC",
    ),
    "usdl2": ("PYDISPLAY_USDL2_SRC",),
}
_PATHSEP = getattr(os, "pathsep", ":")


def _join(*parts):
    if not parts:
        return ""
    out = str(parts[0]).replace("\\", "/")
    for part in parts[1:]:
        if not part:
            continue
        part = str(part).replace("\\", "/").strip("/")
        if not out.endswith("/"):
            out += "/"
        out += part
    return out


def unix_path(path):
    """Map WSL/Windows spellings of a Linux path to a Unix ``/…`` path.

    ``micropython.exe`` under WSL often reports cwd as
    ``\\\\wsl.localhost\\\\<distro>\\\\home\\\\…`` or ``U:\\\\home\\\\…``.
    Sibling discovery and ``sys.path`` always use the Unix form so the same
    tree is visible to PE and native interpreters.
    """
    if not path:
        return path
    path = str(path).replace("\\", "/")
    lower = path.lower()
    for marker in ("//wsl.localhost/", "//wsl$/"):
        if lower.startswith(marker):
            rest = path[len(marker) :]
            slash = rest.find("/")
            if slash >= 0:
                return rest[slash:]
            return "/"
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        rest = path[2:]
        if not rest.startswith("/"):
            rest = "/" + rest
        return rest
    return path


def _dir_of(path):
    path = unix_path(path)
    if "/" in path:
        return path.rsplit("/", 1)[0]
    return "."


def _normpath(path):
    path = unix_path(path)
    absolute = path.startswith("/")
    parts = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            elif not absolute:
                parts.append("..")
        else:
            parts.append(part)
    if absolute:
        return "/" + "/".join(parts) if parts else "/"
    return "/".join(parts) if parts else "."


def _home_from_cwd():
    """Best-effort ``/home/<user>`` when ``HOME`` is unset (micropython.exe)."""
    try:
        cwd = unix_path(os.getcwd())
    except OSError:
        return None
    if cwd.startswith("/home/"):
        parts = [p for p in cwd.split("/") if p]
        if len(parts) >= 2:
            return "/" + parts[0] + "/" + parts[1]
    return None


def _expanduser(path):
    if path.startswith("~/"):
        home = _env_get("HOME") or _home_from_cwd()
        if home:
            return _join(unix_path(home).rstrip("/"), path[2:])
    return path


def _abspath(path):
    path = unix_path(path)
    if path.startswith("/"):
        return _normpath(path)
    try:
        cwd = unix_path(os.getcwd())
    except OSError:
        return _normpath(path)
    if not cwd.endswith("/"):
        cwd += "/"
    return _normpath(_join(cwd, path))


def _is_dir(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False


def _env_get(key):
    environ = getattr(os, "environ", None)
    if environ is not None:
        try:
            value = environ.get(key)
            if value:
                return value
        except Exception:
            pass
    getenv = getattr(os, "getenv", None)
    if getenv is not None:
        try:
            return getenv(key)
        except Exception:
            pass
    return None


def _repo_root(tools_dir=None):
    if tools_dir is None:
        tools_dir = _dir_of(_abspath(__file__))
    return _dir_of(tools_dir)


def _candidates(package, repo_root):
    paths = [
        _join("/agent/repos", package, "lib"),
        _expanduser(_join("~", "gh", "pydevices", package, "lib")),
        _normpath(_join(repo_root, "..", package, "lib")),
    ]
    # Day-to-day native-module checkouts live under cmods/.
    if package in ("pygraphics", "usdl2"):
        paths.extend(
            [
                _expanduser(_join("~", "gh", "pydevices", "cmods", package, "lib")),
                _normpath(_join(repo_root, "..", "cmods", package, "lib")),
            ]
        )
    return paths


def discover_sibling_src(package, repo_root=None, tools_dir=None):
    """Return an existing sibling ``lib`` path for *package*, or ``None``.

    Name kept for call-site compatibility; the directory is now ``lib/``.
    """
    env_key = _ENV_KEYS.get(package)
    if env_key:
        override = _env_get(env_key)
        if override:
            path = _normpath(_expanduser(override))
            return path if _is_dir(path) else None
    for alias in _ENV_ALIASES.get(package, ()):
        override = _env_get(alias)
        if override:
            path = _normpath(_expanduser(override))
            return path if _is_dir(path) else None

    root = unix_path(repo_root) if repo_root is not None else _repo_root(tools_dir)
    for candidate in _candidates(package, root):
        path = _normpath(candidate)
        if _is_dir(path):
            return path
    return None


def discover_sibling_srcs(repo_root=None, tools_dir=None):
    """Return existing sibling ``lib`` paths in package order."""
    found = []
    for package in _SIBLING_PACKAGES:
        path = discover_sibling_src(package, repo_root=repo_root, tools_dir=tools_dir)
        if path:
            found.append(path)
    return found


def apply_sibling_env(env, repo_root=None, tools_dir=None, prepend_paths=None):
    """Record discovered siblings in *env* and prepend them to ``PYTHONPATH``."""
    paths = []
    root = unix_path(repo_root) if repo_root is not None else _repo_root(tools_dir)
    for package in _SIBLING_PACKAGES:
        path = discover_sibling_src(package, repo_root=root, tools_dir=tools_dir)
        if path:
            paths.append(path)
            env[_ENV_KEYS[package]] = path

    ordered = list(paths)
    if prepend_paths:
        ordered = [unix_path(p) for p in prepend_paths] + ordered
    if ordered:
        prefix = _PATHSEP.join(ordered)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = prefix + (_PATHSEP + existing if existing else "")
    return paths


def prepend_sibling_sys_path(repo_root=None, tools_dir=None):
    """Insert discovered sibling ``lib`` dirs at the front of ``sys.path``."""
    import sys

    added = []
    for path in reversed(discover_sibling_srcs(repo_root=repo_root, tools_dir=tools_dir)):
        if path not in sys.path:
            sys.path.insert(0, path)
            added.append(path)
    return added
