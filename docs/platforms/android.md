# Android (CPython)

Platform notes for building pydisplay APKs with **python-for-android** and **buildozer**.

For an **installable browser app** on Android phones (Chrome home screen, no APK), see [Progressive Web Apps](pwa.md) — that path uses PyScript/`PSDisplay`, not this APK stack.

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

Package id: `org.pydevices.p4a_app`.

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydisplay_android
./scripts/test_desktop.sh
```

## Customize buildozer.spec (LVGL editor)

From a pydisplay checkout (CPython + `lvgl-cpython`), run the landscape desktop
editor which emits a comment-free `src/examples/buildozer.spec` (gitignored)
for you to copy into `pydisplay_android/p4a_app/buildozer.spec`:

```bash
cd pydisplay
# optional size; defaults to 1280x720 landscape window
PYDISPLAY_WIDTH=1280 PYDISPLAY_HEIGHT=720 \
  .venv/bin/python -c "import runpy; runpy.run_path('src/examples/p4a_spec_lvgl.py')"
# or from src/:
# cd src && PYDISPLAY_WIDTH=1280 PYDISPLAY_HEIGHT=720 ../.venv/bin/python examples/p4a_spec_lvgl.py
```

Defaults load from a sibling `pydisplay_android/p4a_app/buildozer.spec` when
present. Desktop size can also be set with `PYDISPLAY_SCALE`. Generated
`orientation` follows the template (portrait for the paint defaults) and is
independent of the landscape desktop window.

## LVGL on Android

Prebuilt **`lvgl-cpython`** wheels for Android (`android_21_arm64_v8a`, etc.) are on [TestPyPI](https://test.pypi.org/project/lvgl-cpython/). The default paint APK does not include LVGL; add `lvglcpython` to `p4a_app/buildozer.spec` `requirements` and wire `main.py` to your LVGL module when you need it.

See [pydisplay_android README](https://github.com/PyDevices/pydisplay_android/blob/main/README.md) for entry points (`main.py` / `paint.py`, `board_config.py`) and recipe details.

## Timers

On Android, **multimer** selects the **`_sdl2`** backend (SDL timers on the UI thread) when `usdl2` is available — not `_threading`. See [multimer](../concepts/multimer.md#sdl2-bindings-usdl2).

## Android TV / Fire OS

Same CPython + SDL2 APK stack as phones, with **leanback** packaging and a landscape board config for 10-foot UI.

**Packaging** ([pydisplay_android](https://github.com/PyDevices/pydisplay_android)):

- `p4a_app/intent_filters_tv.xml` — `LEANBACK_LAUNCHER` so the app appears on the TV launcher (phone `LAUNCHER` remains).
- `p4a_app/tv_features.xml` — `android.software.leanback` and `android.hardware.touchscreen` with `required="false"` so non-touch sticks can install.
- `scripts/emulator_tv.sh` — install/launch helper for android-tv AVDs.

**Board config:** `p4a_app/board_config_tv.py` — 1280×720 landscape, fullscreen on device. Copy over `board_config.py` (or import it from `main.py`) before a TV-oriented build. Phone paint stays on the portrait config by default.

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

Use `pydisplay_android/p4a_app/` as the template: adapt `board_config.py`, replace `paint.py` (and the `import …` in `main.py`), add TestPyPI packages to `buildozer.spec`, and keep `p4a.local_recipes` pointed at this repo's `p4a_recipes/`.
