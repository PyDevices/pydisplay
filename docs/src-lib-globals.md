# `src/lib` module globals audit

Private reference (not for RTD). Generated 2026-07-08 by AST scan of `src/lib/**/*.py`.

## Summary

| Category | Count | Notes |
|----------|------:|-------|
| Module-level bindings (all files) | 132+ | Includes constants, aliases, and mutable state |
| Runtime-mutated (explicit `global`) | 14 | See table below |
| Import-time mutables (no `global`, but `.append` / reassigned in-module) | 8 | `_displays`, `_joysticks`, `_mapping`, etc. |
| User-editable config | 2 files | `board_config.py`, `path.py` |

Most bindings are **constants** (display command bytes, framebuf format IDs, event type aliases, font bitmaps). The items worth tracking for refactors are **mutable module state** and **board bootstrap exports**.

## Public bootstrap exports (`board_config.py`)

Created at import time; examples import these by convention:

| Name | Set when | Notes |
|------|----------|-------|
| `width`, `height`, `rotation`, `scale` | always | User-tunable panel geometry |
| `display_drv` | always | Backend instance (`PSDisplay`, `JNDisplay`, `PGDisplay`, or `SDLDisplay`) |
| `runtime` | always | `eventsys.Runtime` wired to display + input |
| `devices_drv` | PyScript / Jupyter only | `PSDevices` or `JNDevices` |

Also sets private flags `_ps`, `_jn` and (desktop MCU branch) `_DESKTOP_PLATFORMS`, `_impl`.

## User-editable path config (`path.py`)

| Name | Default | Mutated by |
|------|---------|------------|
| `directories` | `["lib", "add_ons", "examples"]` | user edit |
| `prepend_directories` | `[]` | `prepend()` appends at runtime |
| `RELPATH` | `True` | user edit |

## Runtime-mutated module globals

These use `global` and change after import:

| Module | Name | Initial | Purpose |
|--------|------|---------|---------|
| `multimer/_select.py` | `Timer`, `_sleep_ms`, `_drain` | `None` | Backend selection (`_set_backend`) |
| `multimer/_mpasyncio.py` | `cur_task` | `None` | Current asyncio task |
| `multimer/_mpasyncio.py` | `_stop_task` | `None` | Stop sentinel for `run_forever` |
| `multimer/_mpasyncio.py` | `_task_queue`, `_io_queue` | (created in `run`) | Async scheduler queues |
| `multimer/_asyncio_loader.py` | `_asyncio_mod` | `None` | Lazy asyncio import |
| `multimer/_backends/sdl2.py` | `_sdl2_timer_inited` | `False` | One-time SDL timer init |
| `multimer/_backends/win32.py` | `_main_thread_handle`, `_active`, `_registry_lock` | `None` / `False` | Win32 APC timer backend |
| `multimer/_backends/win32.py` | `_next_token` | `1` | Timer token allocator |
| `displaysys/sdldisplay.py` | `_saved_tty`, `_event` | `None` / `SDL_Event()` | TTY restore + event scratch |
| `displaysys/pgdisplay.py` | `_joysticks` | `[]` | Joystick list reset on deinit |

## Import-time / in-module mutables (no `global`)

Mutated via method calls (`.append`, `.clear`, dict insert) without a `global` declaration:

| Module | Name | Initial | Mutated by |
|--------|------|---------|------------|
| `displaysys/sdldisplay.py` | `_displays` | `[]` | display ctor/dtor |
| `displaysys/sdldisplay.py` | `_joysticks` | `{}` | `_init_joysticks`, `_close_joysticks` |
| `eventsys/_device.py` | `_mapping` | `{}` | device type registration |
| `multimer/_backends/polling.py` | `_active` | `[]` | timer register/deregister |
| `multimer/_backends/librt.py` | `_ALLOCATED_DEFAULT_IDS` | `set()` | timer ID allocation |
| `path.py` | `prepend_directories` | `[]` | `prepend()` |
| `graphics/_framebuf_plus.py` | `_NATIVE_FRAMEBUF` | `False` | set `True` if native `framebuf` imports |

## Import-time configuration flags

Set once at import, not mutated later:

| Module | Name | Value |
|--------|------|-------|
| `displaysys/sdldisplay.py` | `_NATIVE_USDL2` | `not hasattr(usdl2, "_USE_FFI")` |
| `displaysys/sdldisplay.py` | `_HAS_JOYSTICK_API` | SDL joystick API probe |
| `multimer/_backends/librt.py` | `_USE_CTYPES` | `sys.implementation.name == "cpython"` |
| `eventsys/_capabilities.py` | `_DIALECT` | `sys.implementation.name` |
| `graphics/_capabilities.py` | `_DIALECT` | `sys.implementation.name` |

## Public re-exports (`eventsys/__init__.py`)

Event type constants and `Keys` re-exported from submodules (aliases, not mutable):

`Keys`, `HOST`, `TOUCH`, `ENCODER`, `KEYPAD`, `JOYSTICK`, `QUIT`, `KEYDOWN`, `KEYUP`, `MOUSEMOTION`, `MOUSEBUTTONDOWN`, `MOUSEBUTTONUP`, `MOUSEWHEEL`, `JOYAXISMOTION`, `JOYBALLMOTION`, `JOYHATMOTION`, `JOYBUTTONDOWN`, `JOYBUTTONUP`

## Per-package inventory

### `board_config.py`

`width`, `height`, `rotation`, `scale`, `_ps`, `_jn`, `display_drv`, `devices_drv` (PyScript/JN), `runtime`, `_DESKTOP_PLATFORMS`, `_impl`

### `displaysys/`

- **`__init__.py`:** `_DEFAULT_AUTO_REFRESH_PERIOD`
- **`busdisplay.py`:** ST77xx command/constants, rotation tables
- **`epaperdisplay.py`:** `_ACEP_PALETTE_RGB`
- **`jndisplay.py`:** `_JN_DEPS`, `_CSS_DISPLAY_ID`
- **`pgdisplay.py`:** `_joysticks`
- **`pixeldisplay.py`:** `HORIZONTAL`, `VERTICAL`
- **`sdldisplay.py`:** SDL/TTY constants, `_saved_tty`, `_event`, `_displays`, `_joysticks`, native FFI flags

### `eventsys/`

- **`__init__.py`:** public event/type aliases (see above)
- **`_capabilities.py`:** `_DIALECT`, `_CAPS`
- **`_device.py`:** `_mapping`
- **`_runtime.py`:** `DEFAULT_REFRESH_MS`
- **`_touch.py`:** rotation bit flags, default table
- **`keys.py`:** DOM key maps, modifier groups, browser scroll keycodes

### `graphics/`

- **`_framebuf.py`:** format constants (`MONO_*`, `RGB565`, `GS*`)
- **`_framebuf_plus.py`:** `_NATIVE_FRAMEBUF`, `RGB888`
- **`_bmp565.py`:** `BMP565_BPP`, `BMP565_BYTES_PER_PIXEL`
- **`_font*.py`:** embedded `_FONT` blobs, public `FONT` memoryviews
- **`_font.py`:** `sep`, `_DEFAULT_FONT`
- **`_capabilities.py`**, **`_clip.py`**, **`_blit_hooks.py`**, **`_files.py`:** internal constants/maps

### `multimer/`

- **`_select.py`:** backend slots (`Timer`, `_sleep_ms`, `_drain`)
- **`_mpasyncio.py`:** asyncio runtime state (`cur_task`, queues, `_sleep_ms_sgen`)
- **`_ticks.py`:** tick period constants, `_needs_software_ticks_math`, `_sleep_ms` alias
- **`_asyncio_loader.py`:** `_asyncio_mod`
- **`_backends/*`:** platform timer backend singletons (SDL, Win32, librt, polling)

### `path.py`

`directories`, `prepend_directories`, `RELPATH`

## Takeaways

1. **No stray `global` in `eventsys/` or `graphics/`** — mutable state is concentrated in `multimer/` backends and `displaysys/` SDL/pygame drivers.
2. **`board_config.py` is the main public global surface** for examples (`display_drv`, `runtime`, geometry).
3. **`path.py` is the only intentional user-edited module global** besides board geometry.
4. Most other module bindings are **constants or import-time probes** safe to treat as immutable after load.
