# PyDisplay Platform Feasibility Report

**Date:** 2026-07-14  
**Scope:** Feasibility of extending PyDevices / PyDisplay to additional display targets beyond the current portability matrix.  
**Author:** PyDevices Cloud Agent (based on review of all owned repositories under `/home/ubuntu/gh/pydevices` and `/agent/repos`).

---

## Executive summary

PyDevices’ stated goal is to run **pydisplay everywhere Python runs with a usable display**. Today that is largely true for **MicroPython**, **CircuitPython**, and **CPython** across microcontrollers, Unix/Linux, Windows, the browser (PyScript/Wokwi), Jupyter, and **Android** (CPython via python-for-android). The stack is deliberately layered:

| Layer | Repos | Role |
|-------|-------|------|
| Application API | `pydisplay` (`displaysys`, `eventsys`, `graphics`, `multimer`) | Portable RGB565 display contract, unified input events, timers |
| Hardware acceleration | `displayif`, `graphics`, `usdl2` | Native C modules for bus/framebuffer interfaces, drawing, SDL2 subset |
| GUI toolkit (optional) | `lv_bindings` + `lv_*_mod` | LVGL bindings for all three Python runtimes |
| Packaging | `pydisplay_android`, TestPyPI wheels, MIP/`installer.py` | APK path and prebuilt packages |
| Build workspace | `cmods` | Optional multi-usermod MicroPython build orchestration |

**Display backends today** (`pydisplay/src/lib/displaysys/`):

| Backend | Typical target |
|---------|----------------|
| `BusDisplay` | MCU SPI/I80/I2C panels |
| `FBDisplay` | MCU/CircuitPython **panel RAM buffers** (`framebufferio`, `displayif.rgbframebuffer`, etc.) — *not* Linux `/dev/fb*` |
| `SDLDisplay` | CPython, MicroPython Unix, CircuitPython Unix, **Android** |
| `PGDisplay` | CPython desktop (PyGame CE) |
| `PSDisplay` | PyScript browser canvas |
| `JNDisplay` | Jupyter Notebook |
| `PixelDisplay` / `EPaperDisplay` | NeoPixel grids, e-paper |

The table below rates each requested target against this architecture.

| Target | Overall feasibility | Aligns with “Python + usable display”? | Recommended path |
|--------|:-------------------:|:----------------------------------------:|------------------|
| Apple iOS / iPadOS | **Low–Medium** | Partial (no first-class CPython/MP) | PyScript in Safari; long-term native bridge |
| Apple watchOS | **Very Low** | No | Out of scope for pydisplay as designed |
| Linux fbdev / DRM / KMS (no WM) | **Medium–High** | Yes (CPython / MP Unix) | New `LinuxDisplay` backend or SDL KMS driver |
| Zephyr RTOS | **Low–Medium** | Only if Python port exists | Piggyback MicroPython-on-Zephyr when mature |
| FreeRTOS | **Medium** (via MP) | Yes on supported SoCs | Continue MCU `BusDisplay`/`FBDisplay`; no new backend |
| Nintendo Switch | **Very Low** | No (homebrew only) | Not recommended for org roadmap |
| PlayStation Vita / PS | **Very Low** | No | Not recommended for org roadmap |
| Android TV / Fire OS | **Medium–High** | Yes (CPython) | Extend `pydisplay_android` for TV input/UX |
| LG webOS | **Low–Medium** | Via web only | PyScript / hosted web app |
| Samsung Tizen | **Low** | Via web only | HTML5 hosted app; no native Python |

---

## Methodology

This report is based on:

1. README, platform docs, and source review across **all owned repos**: `pydisplay`, `pydisplay_android`, `displayif`, `graphics`, `usdl2`, `cmods`, `lv_bindings`, `lv_micropython_cmod`, `lv_circuitpython_mod`, `lv_cpython_mod`, `PyDevices.github.io`, `.github`.
2. Mapping each target to existing **display backend contracts**, **runtime availability** (MicroPython / CircuitPython / CPython), and **packaging** paths already in the ecosystem.
3. External platform constraints (store policies, official language runtimes, input modalities) where the codebase has no prior work.

**Important naming note:** PyDisplay’s `FBDisplay` wraps **device-local scanout buffers** (CircuitPython `framebufferio`, MicroPython `displayif` RGB/MIPI modules). It is **not** a Linux kernel framebuffer (`/dev/fb0`) driver. Linux desktop targets today use **SDL2** (`SDLDisplay` + `usdl2`) or **PyGame** (`PGDisplay`), which require a display server or SDL’s platform layer—not bare fbdev/KMS directly.

---

## 1. Apple Mobile Ecosystem (iOS / iPadOS / watchOS)

### Current state in PyDevices

- **No iOS, iPadOS, or watchOS references** in pydisplay or sibling repos.
- **No MicroPython or CircuitPython port** for Apple mobile OSes.
- **CPython on iOS** is not supported by `pydisplay_android` (python-for-android targets Android only).
- Closest existing capability: **[PyScript](https://pydevices.github.io/pydisplay/pyscript/)** (`PSDisplay`) runs in **Mobile Safari** with no App Store packaging—usable display, but not a native app.

### Technical assessment

| Sub-target | Python runtime | Display path | Blockers |
|------------|----------------|--------------|----------|
| **iOS / iPadOS (native app)** | CPython possible via [BeeWare Briefcase](https://beeware.org/), [Kivy-ios](https://github.com/kivy/kivy-ios), or custom Xcode embedding; not in PyDevices today | `usdl2` / SDL2 *can* target iOS, but PyDevices has no iOS build recipes, signing, or App Store pipeline | Apple code-signing; App Store review; no JIT on iOS (affects some Python builds); SDL main-loop integration; touch-safe `multimer` backend |
| **iOS / iPadOS (web)** | PyScript / WASM asyncio | `PSDisplay` canvas | Offline/PWA limits; no full filesystem; performance vs native |
| **watchOS** | No practical CPython/MP | N/A | Screen ~200×200; no SDL; watchOS app model incompatible with pydisplay’s event loop assumptions |

### Feasibility: **Low–Medium** (iOS/iPadOS), **Very Low** (watchOS)

**Why not High:** PyDevices has invested in Android CPython (`pydisplay_android` + TestPyPI `usdl2` Android wheels). iOS would require a **parallel packaging track** (Xcode, CocoaPods/SDL, Apple Developer Program) with no shared p4a infrastructure.

**What would work with minimal new code:**

- **Short term:** Document and test **PyScript on iPad/iPhone** as the “Apple mobile” story—same Python drawing code, `PSDisplay`, async `multimer`.
- **Medium term:** Prototype **SDLDisplay on iOS** via Kivy-ios or a thin BeeWare template, reusing `usdl2` bindings if SDL2 iOS linkage is solved (major packaging effort, separate repo e.g. `pydisplay_ios` mirroring `pydisplay_android`).

**Effort estimate (native iOS):** Large — new repo, CI on macOS runners, SDL iOS glue, touch + safe-area input in `eventsys`, App Store compliance. **6+ subsystem touchpoints** (`usdl2`, `displaysys`, `multimer`, `eventsys`, packaging, LVGL wheels).

**Recommendation:** Treat **watchOS as out of scope**. Pursue **PyScript for iPad** immediately; defer native iOS until there is explicit demand and macOS CI budget.

---

## 2. Bare Linux Framebuffer / DRM / KMS (No Window Manager)

### Current state in PyDevices

- **Linux desktop** is supported via `SDLDisplay` / `PGDisplay` under X11 or Wayland (`docs/platforms/cpython-desktop.md`).
- **`FBDisplay` is MCU-oriented** — wraps RAM buffers flushed to panels via `displayif` or CircuitPython `framebufferio`, not `/dev/fb*`.
- **LVGL** (in `lv_bindings`) includes optional `LV_USE_LINUX_FBDEV` and `LV_USE_LINUX_DRM` drivers, but PyDevices’ `lv_cpython_mod/lv_conf.h` sets `LV_USE_OS` to `LV_OS_NONE` and does **not** enable Linux fbdev/DRM for pydisplay’s presentation path.
- **`usdl2`** exposes a pydisplay-sized SDL2 subset; SDL2 on Linux can use `SDL_VIDEODRIVER=kmsdrm` on many embedded boards **without a window manager**, but this is untested/documented in PyDevices.

### Technical assessment

Embedded Linux kiosks (Raspberry Pi without desktop, industrial HMI, digital signage SBCs) often need:

1. Direct scanout to `/dev/fb0` (legacy fbdev), or  
2. **DRM/KMS** via `/dev/dri/card0` (modern), or  
3. **SDL KMS/DRM backend** (reuse existing `SDLDisplay`).

| Approach | Reuses existing code | Pros | Cons |
|----------|---------------------|------|------|
| **A. SDL `kmsdrm` video driver** | `SDLDisplay`, `usdl2`, `eventsys`, `multimer._sdl2` | Smallest diff; same Python API | Needs SDL2 with KMS; input via `evdev`/SDL; dependency on SDL behavior |
| **B. New `LinuxFBDisplay` (fbdev mmap)** | `DisplayDriver` contract, `graphics` | No X11/Wayland; true bare metal feel | New C extension or ctypes; rotation/format quirks; deprecated on many distros |
| **C. New `DRMDisplay` (libdrm/GBM)** | Same | Modern, zero-copy potential with `displayif`-style thinking | Most engineering; buffer management; mode-setting |
| **D. LVGL linux fbdev/drm driver + flush shim** | `lv_cpython_mod` / `lv_micropython_cmod` | LVGL already has drivers | Bypasses pydisplay `show()` path unless integrated as backend |

### Feasibility: **Medium–High**

**Why High potential:** Target users already run **CPython or MicroPython Unix** on Linux SBCs. The **RGB565 `DisplayDriver` API** is backend-agnostic; only presentation and input differ.

**Recommended phased plan:**

1. **Phase 0 (validation):** Document `SDL_VIDEODRIVER=kmsdrm` + `SDLDisplay` on a Pi or similar without desktop; add `board_configs/sdldisplay/linux_kms/` example config.
2. **Phase 1:** If SDL KMS is insufficient, add **`linuxfb` native module** in `displayif` or new `linuxdisplay` repo exposing mmap’d fbdev or DRM dumb buffers to `FBDisplay`-like Python wrapper.
3. **Phase 2:** Touch via Linux `evdev` → existing `eventsys` broker patterns (similar to SDL touch normalization).

**Risks:** Variable pixel format (ARGB8888 vs RGB565); DPI/scaling; concurrent VT switch; headless CI difficulty.

**Recommendation:** **Pursue** — closest fit to “usable display everywhere Python runs” on industrial/embedded Linux. Start with SDL KMS before writing fbdev/DRM from scratch.

---

## 3. Zephyr RTOS & FreeRTOS

### Current state in PyDevices

- **FreeRTOS** already underpins many **MicroPython MCU ports** (ESP32, STM32, RP2040, etc.) where pydisplay runs today via `BusDisplay` / `FBDisplay` + `displayif`.
- **No Zephyr-specific** board configs, `displayif` ports, or documentation.
- **LVGL** vendored in `lv_bindings` includes OS abstraction for FreeRTOS/CMSIS-RTOS2, but pydisplay’s Python layer does not select an RTOS backend—it runs **on top of** the MP/CP runtime’s scheduler.
- **CircuitPython** does not target Zephyr in the PyDevices matrix.

### Technical assessment

| RTOS | Python availability | PyDisplay fit |
|------|---------------------|---------------|
| **FreeRTOS (via MP on ESP32, etc.)** | MicroPython ports exist | **Already supported** where display hardware has board configs + `displayif` modules |
| **FreeRTOS (no Python)** | None | **Not feasible** without porting MicroPython or another embedded Python |
| **Zephyr** | [MicroPython Zephyr port](https://docs.zephyrproject.org/) exists but is niche vs ESP32/RP2 | Would need Zephyr `displayif` port (SPI/RGB drivers), frozen `pydisplay` manifest, Zephyr-specific `board_config` |
| **Zephyr + LVGL** | LVGL has Zephyr integration in upstream LVGL; PyDevices LVGL bindings are separate | Possible long-term via MP+LVGL, not pydisplay pure-Python alone |

### Feasibility

- **FreeRTOS (with MicroPython):** **Medium–High** — largely **already done** on supported chips; work is **per-board hardware enablement**, not a new OS backend.
- **Zephyr:** **Low–Medium** — depends on MicroPython Zephyr port maturity and display driver availability in `displayif`.

**Recommendation:**

- **FreeRTOS:** Document that pydisplay **does not need an RTOS-specific backend** when MicroPython is the runtime; expand `displayif` + board configs for new SoCs.
- **Zephyr:** **Monitor** MP Zephyr port; pilot only when a specific board + sponsor appears. Expect **`displayif/ports/zephyr/`**-scale effort.

---

## 4. Nintendo Switch & PlayStation Vita / PS

### Current state in PyDevices

- **No references** to game consoles in any owned repo.
- PyDevices targets **legitimate developer paths**: open MCU boards, desktop OSes, browser, and Android APK sideloading/store.

### Technical assessment

| Platform | Python runtime | Display | Reality |
|----------|----------------|---------|---------|
| **Nintendo Switch** | Homebrew Python ports exist (e.g. community projects); no official support | Homebrew GPU APIs (nvn reverse-engineered) | Console is locked; distribution limited to homebrew; Nintendo legal/ToS constraints |
| **PlayStation Vita** | **VitaSDK** homebrew; limited Python experiments | GLES framebuffer | Tiny homebrew audience |
| **PlayStation (PS4/PS5)** | No consumer Python | Proprietary | Not viable for PyDevices open-source goals |

### Feasibility: **Very Low**

**Why:** These platforms violate the practical meaning of “everywhere Python runs” for a **mainstream open-source project**:

- No App Store / official SDK path for Python GUIs.
- Would require **bespoke C display glue** unrelated to `displayif`’s MCU bus model or SDL desktop model.
- Maintenance burden with **legal and hardware-access risk**.

**Recommendation:** **Do not pursue** on the org roadmap unless a dedicated homebrew maintainer forks independently. Mention only as out-of-scope in portability docs.

---

## 5. Android TV / Fire OS

### Current state in PyDevices

- **`pydisplay_android`** provides a **proven CPython + SDL2** path (`SDLDisplay`, `usdl2`, TestPyPI wheels).
- Android TV and **Fire OS** (Amazon’s Android fork) run standard Android APKs with adjustments for **leanback launcher**, **D-pad/remote input**, and often **no touchscreen**.

### Technical assessment

| Concern | Status | Work needed |
|---------|--------|-------------|
| Display (SDL fullscreen) | `board_config.py` already uses `SDL_WINDOW_FULLSCREEN_DESKTOP` on Android | Verify on TV emulator (1080p/4K, overscan) |
| Input | `eventsys` maps touch to mouse-like events; key events exist | Map `KEYCODE_DPAD_*`, `KEYCODE_ENTER`, back button; optional leanback focus model |
| Packaging | `buildozer.spec` + p4a recipes | TV launcher intent category; possibly separate `pydisplay_android_tv` template |
| Fire OS | Sideload APKs; no Google Play required | Test on Fire Stick; Amazon may restrict some native libs—SDL historically OK |
| MicroPython on TV | N/A | CPython only (same as phone Android) |

### Feasibility: **Medium–High**

**Why High:** This is an **extension of existing Android work**, not a new runtime or display backend. Same `SDLDisplay` + `usdl2` + `multimer._sdl2` stack.

**Recommended plan:**

1. Add **Android TV emulator** smoke test to `pydisplay_android/scripts/`.
2. Ship **`board_config_tv.py`** variant (focus on key/gamepad events, 10-foot UI scale).
3. Document in `docs/platforms/android.md` § Android TV / Fire OS.
4. Optional: PyWidgets / LVGL **focus navigation** for D-pad (larger widget effort).

**Risks:** Store policies (Play Store vs sideload); Fire OS version fragmentation; performance on low-end sticks.

**Recommendation:** **Pursue** after phone Android path stabilizes—high value for kiosk/TV dashboards using same Python code as desktop.

---

## 6. LG webOS & Samsung Tizen

### Current state in PyDevices

- **No webOS or Tizen** native integration.
- Closest match: **browser-based PyScript** (`PSDisplay`) — both TV platforms ship **Chromium-based browsers** and encourage **web apps** for UI.

### Technical assessment

| Platform | Native Python | Practical UI stack | PyDisplay path |
|----------|---------------|-------------------|----------------|
| **LG webOS** | Not supported for consumer apps | Enact/JS, HTML5 web apps | Package PyScript static bundle; host on device browser or webOS web app manifest |
| **Samsung Tizen** | Tizen .NET/C++; HTML5 for TV apps | Tizen Web CLI | Same—hosted PyScript or WASM Python; no `SDLDisplay` |

**webOS** developer mode allows installing web apps; **Tizen** uses Samsung’s IDE and certificate signing for store distribution.

### Feasibility: **Low–Medium** (web-only), **Very Low** (native Python)

**Why not native:** Neither platform offers a **CPython or MicroPython** story comparable to Android’s p4a. Building `usdl2` for webOS/Tizen native apps would mean **platform-specific C++ app shells**—outside PyDevices’ Python-first packaging model.

**Recommended plan:**

1. **Position PyScript gallery** as the TV web story—`PSDisplay` + async timers already work in Chromium.
2. If demand exists, add **`web/pyscript/tv/`** examples (large fonts, remote key handling via JS bridge)—may require small **PyScript JS callbacks** for Tizen/webOS key codes.
3. Do **not** plan native `SDLDisplay` on these OSes.

**Recommendation:** **Pursue only via web/PyScript** for smart-TV browsers; treat native TV OS Python as **out of scope**.

---

## Cross-cutting requirements

Any new platform likely needs coordinated updates across:

| Component | Repo | Notes |
|-----------|------|-------|
| Display backend | `pydisplay` `displaysys/` | New class or SDL driver env |
| Native glue | `usdl2`, `displayif`, or new repo | mmap fbdev, DRM, or platform SDL |
| Input normalization | `pydisplay` `eventsys/` | evdev, TV remote, gamepad |
| Timers | `pydisplay` `multimer/` | Must not block UI thread (see Android `_sdl2` precedent) |
| Board config | `pydisplay/board_configs/` | Per-target wiring |
| Packaging | `pydisplay_android`, new `pydisplay_*` | p4a, Xcode, static web |
| LVGL (optional) | `lv_cpython_mod`, etc. | Separate display flush integration |
| Docs / CI | `pydisplay/docs/platforms/` | Headless smoke tests are hard for bare KMS |

---

## Prioritized roadmap suggestion

| Priority | Target | Rationale |
|:--------:|--------|-----------|
| 1 | **Linux KMS / embedded (no WM)** | Fills largest gap in “Python on Linux with display” without desktop; reuses SDL or `displayif` patterns |
| 2 | **Android TV / Fire OS** | Incremental on proven `pydisplay_android` stack |
| 3 | **iOS/iPadOS via PyScript** | Low cost; immediate Mobile Safari audience |
| 4 | **FreeRTOS boards (new SoCs)** | Continue `displayif` + board_config expansion (not a new OS layer) |
| 5 | **webOS / Tizen (web)** | PyScript packaging only if TV web apps are a stated product goal |
| 6 | **iOS native** | Only with dedicated packaging repo + macOS CI |
| 7 | **Zephyr** | Wait for MP port + hardware sponsor |
| — | **Switch / Vita / PS** | Decline for official roadmap |

---

## Conclusion

PyDevices is **well architected for portability**: the `DisplayDriver` RGB565 contract, `board_config` wiring pattern, and split between pure Python (`pydisplay`) and native acceleration (`displayif`, `graphics`, `usdl2`) make **incremental platform additions** possible without rewriting application code.

The **highest-return targets** that align with “Python runs with a usable display” are:

1. **Bare Linux (KMS/fbdev)** — extend hosted Linux beyond X11/Wayland-dependent SDL defaults.  
2. **Android TV / Fire OS** — extend the existing Android APK template for leanback and remote input.  
3. **Apple mobile (web first)** — PyScript already runs; native iOS is a large packaging project.

**FreeRTOS** is already served wherever **MicroPython + display hardware** exist. **Zephyr**, **game consoles**, and **native smart-TV OSes** are poor fits unless scope narrows to web apps (TV) or community homebrew forks (consoles).

---

## References (in-repo)

| Document | Path |
|----------|------|
| PyDisplay README & portability table | `README.md` |
| Platform matrix | `docs/platforms/index.md` |
| Android platform notes | `docs/platforms/android.md` |
| Display backend internals | `docs/concepts/display-backends.md` |
| pydisplay_android README | `../pydisplay_android/README.md` |
| displayif module map | `../displayif/README.md` |
| usdl2 scope & Android wheels | `../usdl2/README.md` |
| Org overview | `../.github/profile/README.md` |
