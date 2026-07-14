# Android (CPython)

Platform notes for building pydisplay APKs with **python-for-android** and **buildozer**.

## Overview

On Android there is no MicroPython port. pydisplay runs under **CPython** in a **python-for-android** APK with the **SDL2 bootstrap**. The `import usdl2` API comes from the [usdl2](https://github.com/PyDevices/usdl2) package on TestPyPI (native `android_21_*` wheels). pydisplay's existing `SDLDisplay` backend works unchanged once `usdl2` is installed.

APK integration — template app, build scripts, and p4a recipes — lives in [**pydisplay_android**](https://github.com/PyDevices/pydisplay_android).

## Workspace

Clone the Android packaging repo (TestPyPI supplies the wheels; sibling `usdl2` / `lv_cpython_mod` clones are optional for local development):

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

(`p4a_app/build_apk.sh` is a thin wrapper around the same script.) Package id: `org.pydevices.p4a_app`.

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydisplay_android/p4a_app
./test_desktop.sh
```

## LVGL on Android

Prebuilt **`lvgl-cpython`** wheels for Android (`android_21_arm64_v8a`, etc.) are on [TestPyPI](https://test.pypi.org/project/lvgl-cpython/). The default paint APK does not include LVGL; add `lvglcpython` to `p4a_app/buildozer.spec` `requirements` and wire `main.py` to your LVGL module when you need it.

See [pydisplay_android README](https://github.com/PyDevices/pydisplay_android/blob/main/README.md) for entry points (`main.py` / `paint.py`, `board_config.py`) and recipe details.

## Timers

On Android, **multimer** selects the **`_sdl2`** backend (SDL timers on the UI thread) when `usdl2` is available — not `_threading`. See [multimer](../concepts/multimer.md#sdl2-bindings-usdl2).

## Your own app

Use `pydisplay_android/p4a_app/` as the template: adapt `board_config.py`, replace `paint.py` (and the `import …` in `main.py`), add TestPyPI packages to `buildozer.spec`, and keep `p4a.local_recipes` pointed at this repo's `p4a_recipes/`.
