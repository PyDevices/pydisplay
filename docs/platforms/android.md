# Android (CPython)

Platform notes for building pydisplay APKs with **python-for-android** and **buildozer**.

For an **installable browser app** on Android phones (Chrome home screen, no APK), see [Progressive Web Apps](pwa.md) — that path uses PyScript/`PSDisplay`, not this APK stack.

## Overview

On Android there is no MicroPython port. pydisplay runs under **CPython** in a **python-for-android** APK with the **SDL2 bootstrap** (no Kivy). Native `libSDL2.so` comes from p4a’s `sdl2` recipe. The `import usdl2` API is the pure-Python binding shipped in [pydisplay-desktop](https://test.pypi.org/project/pydisplay-desktop/) (ctypes against that library). `displaysys.AutoDisplay` selects **`AndroidSDLDisplay`** (`SDL_WINDOW_SHOWN` / HIGHDPI; not `FULLSCREEN_DESKTOP` — that resizes the Activity surface after GL buffers exist and yields a black screen after splash).

APK integration — template app, build scripts, and p4a recipes — lives in [**pydisplay_android**](https://github.com/PyDevices/pydisplay_android).

The default APK is **PyDevices Launcher** (`org.pydevices.launcher`): a baked LVGL home that fetches examples on button press (`mip` / `pip`). It does **not** auto-fetch on launch.

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

Package id: `org.pydevices.launcher` (home-screen label: **PyDevices Launcher**).

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydisplay_android
./scripts/test_desktop.sh
```

## Stage an example over adb (`android.sh`)

From a pydisplay checkout, `bin/android.sh` stages a **cwd path** onto the installed launcher and relaunches — same shape as CLI `python` / `micropython`, **not** [pyscript.sh](../../bin/pyscript.sh) gallery lookup.

```bash
cd pydisplay/src
../bin/android.sh examples/lv_test_timer.py
../bin/android.sh examples/paint.py
../bin/android.sh --clear
```

Optional: `--kit` (writes `run_argv` for kit mode), `--deps` / `--modules` / `--manifests`. Matrix: `tools/example_test_kit.py --only-runtime android …`.

## LVGL on Android

Prebuilt **`lvgl-cpython`** wheels for Android are on [TestPyPI](https://test.pypi.org/project/lvgl-cpython/) and are included in the launcher APK (`lvglcpython` in `buildozer.spec`). The home UI is LVGL; buttons can `mip.install` examples such as `lv_test_timer` from GitHub with `index=` the [PyDevices MIP index](https://PyDevices.github.io/micropython-lib/mip/PyDevices).

See [pydisplay_android README](https://github.com/PyDevices/pydisplay_android/blob/main/README.md) for entry points (`main.py` / `launcher.py`) and recipe details. Display wiring uses the MCU-shaped `board_config` from **pydisplay-desktop** (`AutoDisplay` + `Runtime`); set `PYDISPLAY_WIDTH` / `HEIGHT` / `SCALE` in `main.py` (phone defaults are already set for Android).

## Orientation (MCU-like)

`AndroidSDLDisplay` locks the Activity to **fixed** landscape or portrait from the logical panel aspect (`width` vs `height`), including at `rotation = 0`:

- `1280×720` → landscape Activity  
- `720×1280` → portrait Activity  
- `rotation = 90` on a portrait panel swaps logical size → landscape Activity  

Tilting the phone does **not** change orientation (same contract as an SPI LCD on a board). The user turns the device to match the app. After an aspect change (e.g. `tft_config.WIDE`), `AndroidSDLDisplay` rebinds the logical texture and letterboxes with `RenderSetLogicalSize` (CreateWindow scale is forced to 1 so a stale tall window cannot clip landscape content). Desktop chrome fitting / `PYDISPLAY_SCALE` do not drive the Android window size. Desktop `SDLDisplay` still uses software `RenderCopyEx` rotation.

## Timers

On Android, **multimer** skips auto **`sdl2`** (CPython `SDL_AddTimer` is not on the GLES thread → `EGL_BAD_ACCESS`). Auto-select falls through to **`threading`**; the launcher also sets `MULTIMER_BACKEND=threading`. See [multimer](../concepts/multimer.md).

## Audio (lazy `audio_out`)

`board_config.audio_out` stays lazy. On first `open()` / `write()`, `sdl2audio` attaches an Android-only `PCMOutput(session=…)` that requests audio focus and starts the APK’s `mediaplayback` foreground service (`foregroundServiceType=mediaPlayback`). Last `close()` abandons focus and stops the service. Non-Android consumers still get `session=None` — no API change.

## Android TV / Fire OS

Same CPython + SDL2 APK stack as phones, with **leanback** packaging and landscape framebuffer env for 10-foot UI.

**Packaging** ([pydisplay_android](https://github.com/PyDevices/pydisplay_android)):

- `p4a_app/intent_filters_tv.xml` — `LEANBACK_LAUNCHER` so the app appears on the TV launcher (phone `LAUNCHER` remains).
- `p4a_app/tv_features.xml` — `android.software.leanback` and `android.hardware.touchscreen` with `required="false"` so non-touch sticks can install.
- `scripts/emulator_tv.sh` — install/launch helper for android-tv AVDs.

**Framebuffer:** import `board_config_tv` from `main.py` before the entry (sets `PYDISPLAY_WIDTH=1280`, `HEIGHT=720`), or set those env vars yourself. Phone defaults stay portrait 720×1280 from `main.py`.

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

Use `pydisplay_android/p4a_app/` as the template: customize `launcher.py` (or stage examples with `android.sh`), set `PYDISPLAY_*` for your panel size, add TestPyPI packages to `buildozer.spec`, and keep `p4a.local_recipes` pointed at this repo's `p4a_recipes/`. Do not ship a local `board_config.py` that shadows pydisplay-desktop’s module.
