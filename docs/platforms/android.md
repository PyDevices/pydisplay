# Android (CPython)

Platform notes for building pydisplay APKs with **python-for-android** and **buildozer**.

For an **installable browser app** on Android phones (Chrome home screen, no APK), see [Progressive Web Apps](pwa.md) — that path uses PyScript/`PSDisplay`, not this APK stack.

## Overview

On Android there is no MicroPython port. pydisplay runs under **CPython** in a **python-for-android** APK with the **SDL2 bootstrap** (no Kivy). Native `libSDL2.so` comes from p4a’s `sdl2` recipe. The `import usdl2` API is the pure-Python binding shipped in [pydisplay-desktop](https://test.pypi.org/project/pydisplay-desktop/) (ctypes against that library). `displaysys.AutoDisplay` selects `SDLDisplay` with fullscreen/HIGHDPI window flags when `sys.platform == "android"`.

APK integration — template app, build scripts, and p4a recipes — lives in [**pydisplay_android**](https://github.com/PyDevices/pydisplay_android).

## Workspace

Clone the Android packaging repo (TestPyPI supplies the wheels; a sibling `lv_cpython_mod` clone is optional for local development):

```bash
git clone https://github.com/PyDevices/pydisplay_android.git
```

## Quick start

Prerequisites: [Android SDK + NDK](https://python-for-android.readthedocs.io/en/latest/quickstart.html), Ubuntu/WSL build tools.

```bash
cd pydisplay_android
./build_android.sh
./scripts/emulator.sh   # with an AVD already running
# or: adb install -r p4a_app/bin/*.apk
```

Package id: `org.pydevices.p4a_app`.

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydisplay_android
./scripts/test_desktop.sh
```

## LVGL on Android

Prebuilt **`lvgl-cpython`** wheels for Android (`android_21_arm64_v8a`, etc.) are on [TestPyPI](https://test.pypi.org/project/lvgl-cpython/). The default paint APK does not include LVGL; add `lvglcpython` to `p4a_app/buildozer.spec` `requirements` and wire `main.py` to your LVGL module when you need it.

See [pydisplay_android README](https://github.com/PyDevices/pydisplay_android/blob/main/README.md) for entry points (`main.py` / `paint.py`) and recipe details. Display wiring uses the MCU-shaped `board_config` from **pydisplay-desktop** (`AutoDisplay` + `Runtime`); set `PYDISPLAY_WIDTH` / `HEIGHT` / `SCALE` in `main.py` (phone defaults are already set for Android).

## Timers

On Android, **multimer** selects the **`sdl2`** backend (SDL timers on the UI thread) when `usdl2` is available — ahead of `threading` in the auto chain. See [multimer](../concepts/multimer.md#sdl2-bindings-usdl2).

## Android TV / Fire OS

Same CPython + SDL2 APK stack as phones, with **leanback** packaging and landscape framebuffer env for 10-foot UI.

**Packaging** ([pydisplay_android](https://github.com/PyDevices/pydisplay_android)):

- `p4a_app/intent_filters_tv.xml` — `LEANBACK_LAUNCHER` so the app appears on the TV launcher (phone `LAUNCHER` remains).
- `p4a_app/tv_features.xml` — `android.software.leanback` and `android.hardware.touchscreen` with `required="false"` so non-touch sticks can install.
- `scripts/emulator_tv.sh` — install/launch helper for android-tv AVDs.

**Framebuffer:** import `board_config_tv` from `main.py` before `paint` (sets `PYDISPLAY_WIDTH=1280`, `HEIGHT=720`), or set those env vars yourself. Phone paint keeps portrait 720×1280 defaults from `main.py`.

**Remote → eventsys** (SDL Android keyboard map; no extra remap required today):

| TV remote | eventsys |
|-----------|----------|
| D-pad | `K_UP` / `K_DOWN` / `K_LEFT` / `K_RIGHT` |
| Center / Enter | `K_RETURN` |
| Back | `K_AC_BACK` → `QUIT` via `HostEventsDevice` |

Why Back → quit: matches phone Android Back and the shared `eventsys.key_triggers_quit` path.

**Fire Stick / sideload:** build the APK, `adb connect <stick-ip>`, then `./scripts/emulator_tv.sh` or `adb install -r …` and launch from the Apps row.

TV **web** browsers (webOS / Tizen) are a different path — PyScript / [PWA](pwa.md), not this APK.

## Your own app

Use `pydisplay_android/p4a_app/` as the template: replace `paint.py` (and the `import …` in `main.py`), set `PYDISPLAY_*` for your panel size, add TestPyPI packages to `buildozer.spec`, and keep `p4a.local_recipes` pointed at this repo's `p4a_recipes/`. Do not ship a local `board_config.py` that shadows pydisplay-desktop’s module.
