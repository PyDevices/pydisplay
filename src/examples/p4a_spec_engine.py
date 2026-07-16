# gallery: skip
# SPDX-License-Identifier: MIT
"""
`p4a_spec_engine`
====================================================

Parse / edit / emit comment-free ``buildozer.spec`` text for
``pydisplay_android`` packaging. No display or LVGL imports.

Defaults are loaded from a sibling ``pydisplay_android/p4a_app/buildozer.spec``
when present (override with ``PYDISPLAY_ANDROID_SPEC``). The LVGL front end
lives in ``p4a_spec_lvgl.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

OUTPUT_NAME = "buildozer.spec"

# Android-for-Python "Some buildozer.spec options" TOC keys.
AFP_OPTION_KEYS = (
    "package.name",
    "package.domain",
    "version",
    "requirements",
    "orientation",
    "fullscreen",
    "source.include_exts",
    "android.permissions",
    "android.api",
    "android.minapi",
    "android.ndk",
    "android.sdk",
    "android.archs",
)

OMIT_WHEN_EMPTY = frozenset(("android.ndk", "android.sdk"))

ORIENTATIONS = (
    "portrait",
    "landscape",
    "portrait-reverse",
    "landscape-reverse",
    "all",
)

ARCHS = ("arm64-v8a", "armeabi-v7a", "x86_64", "x86")

BOOL_KEYS_TRUEFALSE = frozenset(("android.skip_update",))
BOOL_KEYS_01 = frozenset(("fullscreen", "warn_on_root"))

# Curated Manifest permission short names for multi-select UI.
PERMISSIONS = (
    "INTERNET",
    "ACCESS_NETWORK_STATE",
    "ACCESS_WIFI_STATE",
    "CHANGE_WIFI_STATE",
    "CHANGE_NETWORK_STATE",
    "CAMERA",
    "RECORD_AUDIO",
    "MODIFY_AUDIO_SETTINGS",
    "VIBRATE",
    "WAKE_LOCK",
    "FLASHLIGHT",
    "READ_EXTERNAL_STORAGE",
    "WRITE_EXTERNAL_STORAGE",
    "MANAGE_EXTERNAL_STORAGE",
    "READ_MEDIA_IMAGES",
    "READ_MEDIA_VIDEO",
    "READ_MEDIA_AUDIO",
    "ACCESS_COARSE_LOCATION",
    "ACCESS_FINE_LOCATION",
    "ACCESS_BACKGROUND_LOCATION",
    "BLUETOOTH",
    "BLUETOOTH_ADMIN",
    "BLUETOOTH_CONNECT",
    "BLUETOOTH_SCAN",
    "BLUETOOTH_ADVERTISE",
    "NEARBY_WIFI_DEVICES",
    "READ_CONTACTS",
    "WRITE_CONTACTS",
    "GET_ACCOUNTS",
    "READ_PHONE_STATE",
    "CALL_PHONE",
    "READ_CALL_LOG",
    "WRITE_CALL_LOG",
    "SEND_SMS",
    "RECEIVE_SMS",
    "READ_SMS",
    "RECEIVE_MMS",
    "BODY_SENSORS",
    "ACTIVITY_RECOGNITION",
    "POST_NOTIFICATIONS",
    "FOREGROUND_SERVICE",
    "FOREGROUND_SERVICE_CAMERA",
    "FOREGROUND_SERVICE_MICROPHONE",
    "FOREGROUND_SERVICE_LOCATION",
    "REQUEST_INSTALL_PACKAGES",
    "SYSTEM_ALERT_WINDOW",
    "WRITE_SETTINGS",
    "NFC",
    "USB_PERMISSION",
    "QUERY_ALL_PACKAGES",
)

# Fallback when sibling pydisplay_android is missing.
_FALLBACK_PAINT = {
    "app": {
        "title": "Paint",
        "package.name": "p4a_app",
        "package.domain": "org.pydevices",
        "source.dir": ".",
        "source.include_exts": "py",
        "source.main": "main.py",
        "icon.filename": "%(source.dir)s/icon.png",
        "presplash.filename": "%(source.dir)s/icon.png",
        "version": "0.5.0",
        "requirements": "python3,sdl2,usdl2,displaysys,eventsys,graphics,multimer",
        "orientation": "portrait",
        "fullscreen": "0",
        "android.api": "31",
        "android.minapi": "24",
        "android.archs": "arm64-v8a, armeabi-v7a",
        "p4a.bootstrap": "sdl2",
        "android.bootstrap": "sdl2",
        "android.permissions": "INTERNET",
        "android.skip_update": "True",
        "p4a.extra_args": (
            "--extra-index-url https://test.pypi.org/simple/ "
            "--extra-index-url https://pypi.org/simple/"
        ),
        "p4a.local_recipes": "../p4a_recipes",
        "android.ndk": "",
        "android.sdk": "",
    },
    "buildozer": {
        "log_level": "2",
        "warn_on_root": "0",
    },
}


def _repo_root_from_here():
    # src/examples/this_file → pydisplay root
    return Path(__file__).resolve().parents[2]


def discover_defaults_path():
    """Return path to defaults buildozer.spec, or None."""
    override = os.environ.get("PYDISPLAY_ANDROID_SPEC")
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return p
    root = _repo_root_from_here()
    candidates = (
        root.parent / "pydisplay_android" / "p4a_app" / "buildozer.spec",
        root / ".." / "pydisplay_android" / "p4a_app" / "buildozer.spec",
    )
    for c in candidates:
        try:
            p = c.resolve()
        except OSError:
            continue
        if p.is_file():
            return p
    return None


def parse_spec_text(text):
    """Parse buildozer.spec text → {section: {key: value}} (comments stripped)."""
    sections = {}
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            sections.setdefault(section, {})
            continue
        if section is None or "=" not in line:
            continue
        key, val = line.split("=", 1)
        sections[section][key.strip()] = val.strip()
    return sections


def parse_spec_file(path):
    return parse_spec_text(Path(path).read_text(encoding="utf-8"))


def _normalize_sections(sections):
    """Ensure [app]/[buildozer] and AfP keys exist; values are strings."""
    out = {
        "app": dict(sections.get("app") or {}),
        "buildozer": dict(sections.get("buildozer") or {}),
    }
    for other, data in sections.items():
        if other in ("app", "buildozer"):
            continue
        out.setdefault(other, dict(data))
    for key in AFP_OPTION_KEYS:
        out["app"].setdefault(key, "")
    return out


class SpecModel:
    """Editable buildozer.spec model."""

    def __init__(self, sections, source_path=None):
        self.sections = _normalize_sections(sections)
        self.source_path = source_path

    def get(self, key, section="app", default=""):
        return self.sections.get(section, {}).get(key, default)

    def set(self, key, value, section="app"):
        self.sections.setdefault(section, {})[key] = "" if value is None else str(value)

    def list_get(self, key, section="app"):
        raw = self.get(key, section=section, default="")
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    def list_set(self, key, items, section="app"):
        self.set(key, ", ".join(items), section=section)

    def bool_get(self, key, section="app"):
        raw = str(self.get(key, section=section, default="")).strip().lower()
        return raw in ("1", "true", "yes", "on")

    def bool_set(self, key, on, section="app"):
        if key in BOOL_KEYS_01:
            self.set(key, "1" if on else "0", section=section)
        else:
            self.set(key, "True" if on else "False", section=section)

    def editable_keys(self):
        """Ordered (section, key) pairs for the UI."""
        seen = set()
        keys = []
        for key in AFP_OPTION_KEYS:
            keys.append(("app", key))
            seen.add(("app", key))
        for section in ("app", "buildozer"):
            for key in sorted(self.sections.get(section, {})):
                item = (section, key)
                if item not in seen:
                    keys.append(item)
                    seen.add(item)
        for section, data in self.sections.items():
            if section in ("app", "buildozer"):
                continue
            for key in sorted(data):
                item = (section, key)
                if item not in seen:
                    keys.append(item)
                    seen.add(item)
        return keys


def load_defaults():
    path = discover_defaults_path()
    if path is not None:
        return SpecModel(parse_spec_file(path), source_path=str(path))
    return SpecModel({k: dict(v) for k, v in _FALLBACK_PAINT.items()}, source_path=None)


def _format_value(key, value):
    text = "" if value is None else str(value).strip()
    if key in OMIT_WHEN_EMPTY and not text:
        return None
    if key in BOOL_KEYS_TRUEFALSE:
        on = text.lower() in ("1", "true", "yes", "on")
        return "True" if on else "False"
    if key in BOOL_KEYS_01:
        on = text.lower() in ("1", "true", "yes", "on")
        return "1" if on else "0"
    return text


def model_to_text(model):
    """Emit comment-free buildozer.spec text."""
    lines = []
    order = ["app", "buildozer"] + [
        s for s in model.sections if s not in ("app", "buildozer")
    ]
    for section in order:
        data = model.sections.get(section) or {}
        if not data and section != "app":
            continue
        lines.append("[{}]".format(section))
        # Prefer AfP order inside [app], then remaining keys sorted.
        keys = []
        if section == "app":
            for key in AFP_OPTION_KEYS:
                if key in data:
                    keys.append(key)
            for key in sorted(data):
                if key not in keys:
                    keys.append(key)
        else:
            keys = sorted(data)
        for key in keys:
            formatted = _format_value(key, data.get(key, ""))
            if formatted is None:
                continue
            lines.append("{} = {}".format(key, formatted))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_output(model, path=None):
    if path is None:
        path = Path(__file__).with_name(OUTPUT_NAME)
    path = Path(path)
    path.write_text(model_to_text(model), encoding="utf-8")
    return path
