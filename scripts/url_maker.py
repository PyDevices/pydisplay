"""Build PyScript loader query strings from logical install intents.

Callers pass logical names matching example headers (``# deps:``, ``# modules:``,
``# manifests:``). This module rewrites deps per runtime, drops builtins for the
active profile, and emits query-only strings
(``?modules=…&manifests=…&deps=…``). Prepend ``micropython.html`` /
``pyodide.html`` yourself.

    from url_maker import urls_from_deps

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime="micropython")
    # -> '?modules=hello&deps=palettes'

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime="pyodide")
    # -> '?modules=hello&deps=palettes'

    urls_from_deps(modules=("hello",), deps=("palettes",), runtime=None)
    # -> {'micropython': '?modules=hello&deps=palettes',
    #     'pyodide': '?modules=hello&deps=palettes'}
"""

from __future__ import annotations

from typing import Iterable

RUNTIMES = ("micropython", "pyodide")

# Profiles → logical names already present (frozen, cmod, or toml-mounted).
# Skip those names when emitting deps for that profile.
PROFILES: dict[str, frozenset[str]] = {
    # Browser MP: src/lib + add_ons mounted; do not auto-install core libs.
    "pyscript-mp": frozenset(
        {
            "graphics",
            "displaysys",
            "multimer",
            "eventsys",
            "board_config",
        }
    ),
    "pyscript-pyodide": frozenset(
        {
            "graphics",
            "displaysys",
            "multimer",
            "eventsys",
            "board_config",
        }
    ),
    # Firmware with cmods compiled in — omit those from install lists.
    "firmware-cmods": frozenset({"graphics", "lvgl"}),
}

# Runtime-aware rewrites: logical name → install name (or None to omit).
_MIP_REWRITE: dict[str, str | None] = {
    "lvgl": None,  # C-only; no MIP package
    "lvgl-cpython": None,
    "graphics-cmod": "graphics",  # mip ships pure graphics
}

_WHEEL_REWRITE: dict[str, str | None] = {
    "lvgl": "lvgl-cpython",
    "lvglcpython": "lvgl-cpython",
    "graphics": "graphics-cmod",  # prefer native cmod wheel
}


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
    out: list[str] = []
    seen: set[str] = set()
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
        if logical in skip or logical.lower().replace("_", "-") in {
            s.lower().replace("_", "-") for s in skip
        }:
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
    **kwargs: object,
) -> str | dict[str, str]:
    """Emit a loader query string, or both runtimes when ``runtime`` is None.

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
        parts: list[tuple[str, list[str]]] = [
            ("modules", modules_t),
            ("manifests", manifests_t),
            ("deps", _apply_channel(deps_t, channel=channel, profile=prof)),
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
) -> str | dict[str, str]:
    """Emit loader queries from logical ``deps`` (rewritten per runtime)."""
    return url(
        modules=modules,
        manifests=manifests,
        deps=deps,
        runtime=runtime,
        profile=profile,
    )
