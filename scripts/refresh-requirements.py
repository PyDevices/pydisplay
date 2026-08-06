#!/usr/bin/env python3
"""Refresh repo-root requirements.txt TestPyPI floors to latest versions.

Used by:
  - Cursor sessionStart hook (when workspace is pydisplay)
  - Agent after tagging a TestPyPI-publishing repo (CLI: --force)

Preserves package install order and ``--index-url``. Only rewrites ``name>=ver``
lines for known packages. Fail-open: exits 0 with ``{}`` on any error.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Install order SoT (leaves before dependents). Keep in sync with the Cursor rule.
PACKAGE_ORDER = (
    "usdl2",
    "pygraphics",
    "lvgl-cpython",
    "multimer",
    "eventsys",
    "displaysys",
    "palettes",
    "pdwidgets",
    "pydisplay-desktop",
)

INDEX_URL = "https://test.pypi.org/simple/"
JSON_URL = "https://test.pypi.org/pypi/{}/json"

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REQ = os.path.join(_REPO_ROOT, "requirements.txt")


def _load_stdin():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _paths_from_payload(payload: dict) -> list[str]:
    paths = []
    for key in ("workspace_roots", "workspaceRoots", "roots"):
        val = payload.get(key)
        if isinstance(val, list):
            paths.extend(str(p) for p in val)
        elif isinstance(val, str):
            paths.append(val)
    for key in ("cwd", "workspace_root", "workspaceRoot", "project_dir", "projectDir"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            paths.append(val)
    # Only fall back to process env when the hook payload omitted roots
    # (avoids treating the hook's own PWD as the workspace).
    if not paths:
        env_cwd = os.environ.get("CURSOR_PROJECT_DIR") or os.environ.get("PWD")
        if env_cwd:
            paths.append(env_cwd)
    return paths


def _is_pydisplay_workspace(paths: list[str]) -> bool:
    for path in paths:
        norm = os.path.normpath(os.path.expanduser(path))
        base = os.path.basename(norm.rstrip(os.sep))
        if base == "pydisplay":
            return True
        if (
            os.path.isfile(os.path.join(norm, "requirements.txt"))
            and os.path.isdir(os.path.join(norm, "src", "lib"))
            and os.path.isfile(os.path.join(norm, "tools", "example_runtimes.toml"))
        ):
            return True
    return False


def _requirements_path(paths: list[str]) -> str:
    for path in paths:
        norm = os.path.normpath(os.path.expanduser(path))
        candidate = os.path.join(norm, "requirements.txt")
        if os.path.basename(norm.rstrip(os.sep)) == "pydisplay" and os.path.isdir(norm):
            return candidate
        if os.path.isfile(os.path.join(norm, "tools", "example_runtimes.toml")):
            return candidate
    return DEFAULT_REQ


def _latest_version(name: str) -> str:
    url = JSON_URL.format(name)
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.load(resp)
    return str(data["info"]["version"])


def refresh(path: str) -> dict[str, str]:
    versions = {}
    for name in PACKAGE_ORDER:
        versions[name] = _latest_version(name)

    lines = [f"--index-url {INDEX_URL}", ""]
    for name in PACKAGE_ORDER:
        lines.append(f"{name}>={versions[name]}")
    text = "\n".join(lines) + "\n"

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    old = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            old = handle.read()
    if old != text:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    return versions


def main() -> int:
    force = "--force" in sys.argv
    payload = _load_stdin() if not force else {}
    paths = _paths_from_payload(payload)

    if not force and not _is_pydisplay_workspace(paths):
        print("{}")
        return 0

    path = (
        _requirements_path(paths)
        if not force
        else (sys.argv[sys.argv.index("--path") + 1] if "--path" in sys.argv else DEFAULT_REQ)
    )

    try:
        versions = refresh(path)
    except (urllib.error.URLError, TimeoutError, KeyError, OSError) as exc:
        print("{}")
        if force:
            print(f"refresh failed: {exc}", file=sys.stderr)
            return 1
        return 0

    if force:
        print(f"Updated {path}", file=sys.stderr)
        for name in PACKAGE_ORDER:
            print(f"  {name}>={versions[name]}", file=sys.stderr)
        print("{}")
        return 0

    print(
        json.dumps(
            {
                "additional_context": (
                    "Refreshed pydisplay/requirements.txt TestPyPI floors to latest: "
                    + ", ".join(f"{n}>={versions[n]}" for n in PACKAGE_ORDER)
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
