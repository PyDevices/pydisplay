# Android (CPython)

Platform notes for building pydisplay APKs with **python-for-android** and **buildozer**.

## Overview

On Android there is no MicroPython port. pydisplay runs under **CPython** in a **python-for-android** APK with the **SDL2 bootstrap**. The `import usdl2` API comes from the ctypes FFI package in [usdl2](https://github.com/PyDevices/usdl2) (`python/usdl2/`). pydisplay's existing `SDLDisplay` backend works unchanged once `usdl2` is installed.

APK integration — demo project, build scripts, and p4a recipes for `pydisplay` and `lvgl-cpython` — lives in [**pydisplay_android**](https://github.com/PyDevices/pydisplay_android). usdl2 keeps only the ctypes package and `p4a_recipes/usdl2/`.

## Workspace

Clone as siblings (e.g. under a [cmods](https://github.com/PyDevices/cmods) workspace):

```bash
git clone https://github.com/PyDevices/usdl2.git
git clone https://github.com/PyDevices/pydisplay.git
git clone https://github.com/PyDevices/pydisplay_android.git
git clone https://github.com/PyDevices/lv_cpython_mod.git   # optional, for LVGL demo
```

## Quick start

Prerequisites: [Android SDK + NDK](https://python-for-android.readthedocs.io/en/latest/quickstart.html), `pip install buildozer`.

```bash
cd pydisplay_android/android_demo
./build_apk.sh
adb install -r bin/*.apk
```

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydisplay_android/android_demo
./test_desktop.sh
```

## LVGL on Android

Prebuilt **`lvgl-cpython`** wheels for Android (`android_21_arm64_v8a`, etc.) are on [TestPyPI](https://test.pypi.org/project/lvgl-cpython/). The `lvglcpython` p4a recipe in pydisplay_android installs a matching wheel when `p4a.extra_index_url` points at TestPyPI, or cross-compiles from [lv_cpython_mod](https://github.com/PyDevices/lv_cpython_mod) when `P4A_lvgl_cpython_DIR` is set.

See [pydisplay_android README](https://github.com/PyDevices/pydisplay_android/blob/main/README.md) for demo entry points (`main_lvgl.py`, `board_config.py`) and recipe details.

## Timers

On Android, **multimer** selects the **`_sdl2`** backend (SDL timers on the UI thread) when `usdl2` is available — not `_threading`. See [multimer](../concepts/multimer.md#sdl2-bindings-usdl2).

## Your own app

Copy `pydisplay_android/android_demo/board_config.py`, add `pydisplay` and `usdl2` to your `buildozer.spec`, point `p4a.local_recipes` at pydisplay_android's `p4a_recipes/` (run `build_apk.sh` once to link the `usdl2` recipe from a sibling clone), and write your main loop with `display_drv` / `broker` as usual.
