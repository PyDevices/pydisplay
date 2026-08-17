# Android (CPython)

Platform notes for building pydevices-examples APKs with **python-for-android** and **buildozer**.

For an **installable browser app** on Android phones (Chrome home screen, no APK), see [Progressive Web Apps](pwa.md) — that path uses PyScript/`PSDisplay`, not this APK stack.

## Overview

On Android there is no MicroPython port. pydevices-examples runs under **CPython** in a **python-for-android** APK with the **SDL2 bootstrap** (no Kivy). Native `libSDL2.so` comes from p4a’s `sdl2` recipe. The `import usdl2` API is the pure-Python binding shipped in [pydevices-desktop](https://test.pypi.org/project/pydevices-desktop/) (ctypes against that library). `displaydev.auto.AutoDisplay` selects **`AndroidSDLDisplay`** (`SDL_WINDOW_SHOWN` / HIGHDPI; not `FULLSCREEN_DESKTOP` — that resizes the Activity surface after GL buffers exist and yields a black screen after splash).

APK integration — template app, build scripts, and p4a recipes — lives in [**pydevices-android-template**](https://github.com/PyDevices/pydevices-android-template).

The default APK is **PyDevices Launcher** (`org.pydevices.launcher`): a baked LVGL home that fetches examples on button press (`mip` / `pip`). It does **not** auto-fetch on launch.

## Workspace

Clone the Android packaging repo (TestPyPI supplies the wheels; a sibling `lvgl-python` clone is optional for local development):

```bash
git clone https://github.com/PyDevices/pydevices-android-template.git
```

## Quick start

Prerequisites: [Android SDK + NDK](https://python-for-android.readthedocs.io/en/latest/quickstart.html), Ubuntu/WSL build tools.

```bash
cd pydevices-android-template
./build_android.sh
./scripts/emulator.sh   # with an AVD already running
# or: adb install -r p4a_app/bin/*.apk
```

Package id: `org.pydevices.launcher` (home-screen label: **PyDevices Launcher**).

Desktop smoke test (Xvfb, before building an APK):

```bash
cd pydevices-android-template
./scripts/test_desktop.sh
```

## Stage an example over adb (`android.py`)

Host tool: [`pydevices/bin/android.py`](https://github.com/PyDevices/pydevices/blob/main/bin/android.py) (on PATH). Stages a **cwd path** onto the installed Runner APK (`org.pydevices.runner`) and relaunches — same shape as CLI `python` / `micropython`, **not** [`pyscript.sh`](https://github.com/PyDevices/pydevices-examples/blob/main/bin/pyscript.sh) gallery lookup.

```bash
cd pydevices-examples/lib
android.py examples/lv_test_timer.py
android.py examples/paint.py
android.py --clear
```

When stdin is a TTY, `android.py` **stays attached** after launch and wires this terminal to the app’s `stdin` / `stdout` / `stderr` (prints, tracebacks, and `input()`). Use `--no-attach` for fire-and-forget (CI / the example matrix).

```bash
android.py -h                         # micropython-shaped help (-c / -m / file / -i / -X …)
android.py --version
android.py -c 'print(1+1)' -i
android.py -i                         # omit main.py → clean >>> (like firmware with no main)
android.py examples/paint.py -i       # oneshot: stdio, then >>> when it exits
android.py examples/lv_test_timer.py -i   # looping: Ctrl+C → KeyboardInterrupt → >>>
android.py --clear                    # restore default runner entry
```

Startup matches MicroPython: the Runner APK's packaged **`boot.py`** does env / path / stdio setup, then runs **`main.py`** if present, otherwise parks for the attach REPL. `android.py` stages examples as `main.py` (`import <stem>`) plus `run/<stem>.py`.

### Attach / `-i` (like `python -i` / `micropython -i`)

| Situation | What you see |
|-----------|----------------|
| Script running (oneshot or `run_forever` loop) | Stdio only — prints and `input()` in this terminal; **no** `>>>` yet |
| Oneshot / falls off the bottom | Banner + `>>>` automatically |
| Looping entry + **Ctrl+C** | `KeyboardInterrupt`, then banner + `>>>` (same as desktop `-i` with the threading timer) |
| Bare `android.sh -i` | Clean `>>>` (`main.py` removed for this session) |

With `multimer` **threading** (`timer_async=False`, Android’s usual path) there is no MicroPython soft-IRQ into the REPL mid-loop — matching `micropython.exe -i` on Windows desktop. MicroPython’s **signals** / `machine.Timer` path can return from `run_forever` immediately so `>>>` coexists with ticks; Android does not try to fake that.

**Host vs in-app keys:** Ctrl+D on a blank line is a **soft reset** (fresh namespace), like MicroPython. To disconnect the host attach while leaving the app running, use **Ctrl+\\** (not Ctrl+D).

TTY / editing aim for MicroPython REPL parity:

| Key | Action |
|-----|--------|
| Ctrl+A | blank line → raw REPL; else start-of-line |
| Ctrl+B | blank line → normal REPL; else cursor left |
| Ctrl+C | interrupt running code / cancel line |
| Ctrl+D | blank line → soft reset; else delete; paste/raw → finish |
| Ctrl+E | blank line → paste mode; else end-of-line |
| Arrows | history (up/down) and cursor (left/right) |
| Tab | completion (`im`→`import `, `sys.`→members) / 4-space indent |
| Ctrl+P / Ctrl+N | history prev/next |
| Ctrl+K / Ctrl+U | kill to end / kill to start |
| Ctrl+\ | disconnect host attach (app keeps running) |

`help()`, `help("modules")` (top-level names, 4×18 columns), and `help(obj)` follow MicroPython’s help style. Auto-indent after `:` on compound statements.

Each launch hot-syncs `boot.py`, `stdio_sidecar.py`, and `mp_*.py` from a sibling `pydevices-android-template` checkout (when present) and drops stale bytecode that would otherwise shadow updates. Optional: `--kit`, `--deps` / `--modules` / `--manifests`. Matrix: `tools/example_test_kit.py --only-runtime android …`.

The boot-entrypoint Java patch requires an APK rebuild (`./build_android.sh`); hot-sync alone cannot retarget an older package that still launches `main.py` first.
## LVGL on Android

Prebuilt **`pydevices-lvgl`** wheels for Android are on [TestPyPI](https://test.pypi.org/project/pydevices-lvgl/) and are included in the launcher APK (`pydeviceslvgl` in `buildozer.spec`). The home UI is LVGL; buttons can `mip.install` examples such as `lv_test_timer` from GitHub with `index=` the [PyDevices MIP index](https://PyDevices.github.io/mip).

See [pydevices-android-template README](https://github.com/PyDevices/pydevices-android-template/blob/main/README.md) for entry points (`main.py` / `launcher.py`) and recipe details. Display wiring uses the MCU-shaped `board_config` from **pydevices-desktop** (`AutoDisplay` and neutral input readers). LVGL owns its runtime in `display_driver`; non-LVGL apps may instantiate optional `eventsys`. Set `PYDEVICES_WIDTH` / `HEIGHT` / `SCALE` in `main.py` (phone defaults are already set for Android).

## Orientation (MCU-like)

`AndroidSDLDisplay` locks the Activity to **fixed** landscape or portrait from the logical panel aspect (`width` vs `height`), including at `rotation = 0`:

- `1280×720` → landscape Activity  
- `720×1280` → portrait Activity  
- `rotation = 90` on a portrait panel swaps logical size → landscape Activity  

Tilting the phone does **not** change orientation (same contract as an SPI LCD on a board). The user turns the device to match the app. After an aspect change (e.g. `tft_config.WIDE`), `AndroidSDLDisplay` rebinds the logical texture and letterboxes with `RenderSetLogicalSize` (CreateWindow scale is forced to 1 so a stale tall window cannot clip landscape content). Desktop chrome fitting / `PYDEVICES_SCALE` do not drive the Android window size. Desktop `SDLDisplay` still uses software `RenderCopyEx` rotation.

## Timers

On Android, **multimer** skips auto **`sdl2`** (CPython `SDL_AddTimer` is not on the GLES thread → `EGL_BAD_ACCESS`). Auto-select falls through to **`threading`**; the launcher also sets `MULTIMER_BACKEND=threading`. See [multimer](https://pydevices.github.io/pydevices/multimer.html).

## Audio (lazy `audio_out`)

`board_config.audio_out` stays lazy. On first `open()` / `write()`, `audiodev.sdl2_audio` attaches an Android-only `PCMOutput(session=…)` that requests audio focus and starts the APK’s `mediaplayback` foreground service (`foregroundServiceType=mediaPlayback`). Last `close()` abandons focus and stops the service. Non-Android consumers still get `session=None` — no API change.

## Android TV / Fire OS

Same CPython + SDL2 APK stack as phones, with **leanback** packaging and landscape framebuffer env for 10-foot UI.

**Packaging** ([pydevices-android-template](https://github.com/PyDevices/pydevices-android-template)):

- `p4a_app/intent_filters_tv.xml` — `LEANBACK_LAUNCHER` so the app appears on the TV launcher (phone `LAUNCHER` remains).
- `p4a_app/tv_features.xml` — `android.software.leanback` and `android.hardware.touchscreen` with `required="false"` so non-touch sticks can install.
- `scripts/emulator_tv.sh` — install/launch helper for android-tv AVDs.

**Framebuffer:** import `board_config_tv` from `main.py` before the entry (sets `PYDEVICES_WIDTH=1280`, `HEIGHT=720`), or set those env vars yourself. Phone defaults stay portrait 720×1280 from `main.py`.

**Remote → eventsys** (SDL Android keyboard map; no extra remap required today):

| TV remote | `keys` |
|-----------|----------|
| D-pad | `K_UP` / `K_DOWN` / `K_LEFT` / `K_RIGHT` |
| Center / Enter | `K_RETURN` |
| Back | `K_AC_BACK` → `QUIT` via `HostEventsDevice` |

Why Back → quit: `AndroidSDLDisplay.quit_chord` is `(keys.K_AC_BACK, 0)`.

**Fire Stick / sideload:** build the APK, `adb connect <stick-ip>`, then `./scripts/emulator_tv.sh` or `adb install -r …` and launch from the Apps row.

TV **web** browsers (webOS / Tizen) are a different path — PyScript / [PWA](pwa.md), not this APK.

## Your own app

Use `pydevices-android-template/p4a_app/` as the template: customize `launcher.py` (or stage examples with `android.sh`), set `PYDEVICES_*` for your panel size, add TestPyPI packages to `buildozer.spec`, and keep `p4a.local_recipes` pointed at this repo's `p4a_recipes/`. Do not ship a local `board_config.py` that shadows pydevices-desktop’s module.
