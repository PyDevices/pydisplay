"""Build PyScript loader query strings from logical install intents.

Callers pass logical names matching example headers (``# deps:``, ``# modules:``,
``# manifests:``). This module rewrites deps per runtime, drops builtins for the
active profile, and emits query-only strings
(``?modules=…&manifests=…&deps=…``). Prepend ``micropython.html`` /
``pyodide.html`` (or ``run.html`` / ``run-pyodide.html``) yourself.

With ``shell="run"``, deps are emitted as ``mip=`` (MicroPython) /
``wheels=`` (Pyodide) for the minimal run pages.

    from url_maker import urls_from_deps

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime="micropython")
    # -> '?modules=hello'  (palettes frozen in MP WASM)

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime="pyodide")
    # -> '?modules=hello&deps=palettes,pygraphics-cmod'

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime=None)
    # -> {'micropython': '?modules=hello',
    #     'pyodide': '?modules=hello&deps=palettes,pygraphics-cmod'}
"""

from __future__ import annotations

from typing import Iterable

RUNTIMES = ("micropython", "pyodide")
SHELLS = ("chrome", "run")

# Profiles → logical names already present (frozen, cmod, or toml-mounted).
# Skip those names when emitting deps for that profile.
PROFILES: dict[str, frozenset[str]] = {
    # Browser MP WASM: pydisplay core (displaysys/eventsys/multimer) toml-mounted;
    # sister/ecosystem libs frozen in the pyscript vendor firmware (lvgl,
    # display_driver, pygraphics, palettes, pdwidgets, usdl2 when built in).
    # Do not mip-install those — Pyodide / CPython still get TestPyPI wheels.
    "pyscript-mp": frozenset(
        {
            "pygraphics",
            "displaysys",
            "multimer",
            "eventsys",
            "board_config",
            "lvgl",
            "lvgl-cpython",
            "display_driver",
            "palettes",
            "pdwidgets",
            "usdl2",
            "usdl2-py",
        }
    ),
    # Pyodide: pydisplay core toml-mounted. Sister packages (pygraphics-cmod
    # pyemscripten wasm, usdl2, …) come from TestPyPI via ?deps=.
    "pyscript-pyodide": frozenset(
        {
            "displaysys",
            "multimer",
            "eventsys",
            "board_config",
        }
    ),
    # Firmware with sister cmods compiled in — omit those from install lists.
    "firmware-cmods": frozenset(
        {
            "pygraphics",
            "lvgl",
            "lvgl-cpython",
            "display_driver",
            "palettes",
            "pdwidgets",
            "usdl2",
            "usdl2-py",
        }
    ),
}

# Runtime-aware rewrites: logical name → install name (or None to omit).
_MIP_REWRITE: dict[str, str | None] = {
    "lvgl": None,  # C-only; no MIP package
    "lvgl-cpython": None,
    "display_driver": None,  # ships with LVGL firmware / lvgl-cpython wheel
    "pygraphics-cmod": "pygraphics",  # mip ships pure-Python pygraphics
    "usdl2-py": "usdl2",  # same import name on MIP (PyDevices/usdl2)
}

_WHEEL_REWRITE: dict[str, str | None] = {
    "lvgl": "lvgl-cpython",
    "lvglcpython": "lvgl-cpython",
    "display_driver": "lvgl-cpython",  # bundled in the wheel
    "pygraphics": "pygraphics-cmod",  # native + pyemscripten wasm on TestPyPI
    "usdl2-py": "usdl2",  # prefer native TestPyPI wheel when available
}

# Logical deps that need pygraphics at runtime but often omit it from headers.
_WHEEL_PULLS_PYGRAPHICS = frozenset({"palettes", "pdwidgets"})


def _norm_dep(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _as_tuple(value: Iterable[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise TypeError("pass a sequence of names, not a bare string")
    return tuple(value)


def _dedupe(names: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in names:
        name = str(raw).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def rewrite_mip(name: str) -> str | None:
    """Return MIP install name, or None if this logical name has no MIP."""
    key = name.strip()
    if key in _MIP_REWRITE:
        return _MIP_REWRITE[key]
    return key


def rewrite_wheel(name: str) -> str | None:
    """Return wheel project name, or None if this logical name has no wheel."""
    key = name.strip()
    lowered = key.lower().replace("_", "-")
    if lowered in _WHEEL_REWRITE:
        return _WHEEL_REWRITE[lowered]
    if key in _WHEEL_REWRITE:
        return _WHEEL_REWRITE[key]
    return key


def _apply_channel(
    names: Iterable[str],
    *,
    channel: str,
    profile: str,
) -> list[str]:
    skip = PROFILES.get(profile, frozenset())
    skip_norm = {_norm_dep(s) for s in skip}
    out: list[str] = []
    seen: set[str] = set()
    pull_pygraphics = False
    for raw in names:
        logical = str(raw).strip()
        if not logical:
            continue
        # Already a URL / github: path — pass through.
        if "://" in logical or logical.startswith(("github:", "gitlab:", "codeberg:")):
            if logical not in seen:
                seen.add(logical)
                out.append(logical)
            continue
        if _norm_dep(logical) in _WHEEL_PULLS_PYGRAPHICS:
            pull_pygraphics = True
        if logical in skip or _norm_dep(logical) in skip_norm:
            continue
        if channel == "mip":
            resolved = rewrite_mip(logical)
        elif channel == "wheels":
            resolved = rewrite_wheel(logical)
        else:
            raise ValueError(f"unknown channel {channel!r}")
        if resolved is None:
            if channel == "mip" and logical.lower().startswith("lvgl"):
                continue  # omit silently for mip (C-only)
            continue
        if resolved not in seen:
            seen.add(resolved)
            out.append(resolved)
    # palettes / pdwidgets need pygraphics; prefer the native TestPyPI cmod wheel.
    if channel == "wheels" and pull_pygraphics and "pygraphics-cmod" not in seen:
        out.append("pygraphics-cmod")
    return out


def _join_query(parts: list[tuple[str, list[str]]]) -> str:
    chunks: list[str] = []
    for key, values in parts:
        if values:
            chunks.append(f"{key}={','.join(values)}")
    if not chunks:
        return "?"
    return "?" + "&".join(chunks)


def url(
    *,
    modules: Iterable[str] = (),
    manifests: Iterable[str] = (),
    deps: Iterable[str] = (),
    runtime: str | None = None,
    profile: str | None = None,
    shell: str = "chrome",
    **kwargs: object,
) -> str | dict[str, str]:
    """Emit a loader query string, or both runtimes when ``runtime`` is None.

    ``shell`` selects the deps query key:
      - ``chrome`` (default): ``deps=`` for micropython.html / pyodide.html
      - ``run``: ``mip=`` / ``wheels=`` for run.html / run-pyodide.html

    Unknown keyword arguments raise ``TypeError``.
    """
    if kwargs:
        bad = ", ".join(sorted(kwargs))
        raise TypeError(f"url() got unexpected keyword argument(s): {bad}")

    modules_t = _dedupe(_as_tuple(modules))
    manifests_t = _dedupe(_as_tuple(manifests))
    deps_t = _as_tuple(deps)

    if runtime is not None and runtime not in RUNTIMES:
        raise ValueError(f"runtime must be one of {RUNTIMES!r} or None, got {runtime!r}")
    if shell not in SHELLS:
        raise ValueError(f"shell must be one of {SHELLS!r}, got {shell!r}")

    def _one(rt: str) -> str:
        if profile is None:
            prof = "pyscript-mp" if rt == "micropython" else "pyscript-pyodide"
        else:
            if profile not in PROFILES and profile not in (
                "pyscript-mp",
                "pyscript-pyodide",
                "firmware-cmods",
            ):
                # Allow unknown profiles with empty skip set.
                pass
            prof = profile

        channel = "mip" if rt == "micropython" else "wheels"
        deps_key = ("mip" if rt == "micropython" else "wheels") if shell == "run" else "deps"
        parts: list[tuple[str, list[str]]] = [
            ("modules", modules_t),
            ("manifests", manifests_t),
            (deps_key, _apply_channel(deps_t, channel=channel, profile=prof)),
        ]
        return _join_query(parts)

    if runtime is None:
        return {rt: _one(rt) for rt in RUNTIMES}
    return _one(runtime)


def urls_from_deps(
    *,
    modules: Iterable[str] = (),
    manifests: Iterable[str] = (),
    deps: Iterable[str] = (),
    runtime: str | None = None,
    profile: str | None = None,
    shell: str = "chrome",
) -> str | dict[str, str]:
    """Emit loader queries from logical ``deps`` (rewritten per runtime)."""
    return url(
        modules=modules,
        manifests=manifests,
        deps=deps,
        runtime=runtime,
        profile=profile,
        shell=shell,
    )
