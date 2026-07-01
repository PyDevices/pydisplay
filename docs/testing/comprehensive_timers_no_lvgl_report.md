# Comprehensive multimer timer report (no LVGL)

Generated: 2026-07-01 14:28 UTC  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_comprehensive_timer_reports.py --phase no-lvgl`

Probes every importable ``multimer`` backend on each desktop runtime via ``tools/test_timers.py``.
Import failures are reported as **SKIP** with reason (expected on wrong OS/port).

## Summary matrix

| Timer backend | micropython | micropython.exe | circuitpython | cpython-venv | python.exe |
|---------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| `machine.Timer` | SKIP | SKIP | SKIP | SKIP | SKIP |
| `_librt.Timer` | **PASS** | SKIP | SKIP | **PASS** | SKIP |
| `_win32.Timer` | SKIP | SKIP | SKIP | SKIP | **PASS** |
| `_threading.Timer` | **PASS** | SKIP | **PASS** | **PASS** | **PASS** |
| `_sdl2.Timer` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `_polling.Timer` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `AsyncTimer` | **PASS** | **FAIL** | **PASS** | **PASS** | **PASS** |
| `AsyncTimer (yield loop)` | **PASS** | **FAIL** | **PASS** | **PASS** | **PASS** |
| `multimer.Timer (default)` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |

## Per-runtime details

### `micropython`

- **Runner:** exit 0
- implementation: micropython (1, 29, 0, 'preview')
- platform: linux
- python: 3.4.0;

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ImportError: can't import name Timer |
| `_librt.Timer` | False | **PASS** | 15 callbacks in 300 ms |
| `_win32.Timer` | — | SKIP | ImportError: win32 timer backend requires win32 |
| `_threading.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `_sdl2.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `_polling.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 5 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 16 callbacks in 300 ms |

### `micropython.exe`

- **Runner:** exit 0
- implementation: micropython (1, 29, 0, 'preview')
- platform: win32
- python: 3.4.0;

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ImportError: can't import name Timer |
| `_librt.Timer` | — | SKIP | ImportError: librt timer backend requires Linux |
| `_win32.Timer` | — | SKIP | ImportError: no module named 'ctypes' |
| `_threading.Timer` | — | SKIP | ImportError: no thread support |
| `_sdl2.Timer` | True | **PASS** | 87 callbacks in 300 ms |
| `_polling.Timer` | True | **PASS** | 60 callbacks in 300 ms |
| `AsyncTimer` | False | **FAIL** | ImportError: multimer async support requires asyncio or uasyncio with create_task |
| `AsyncTimer (yield loop)` | False | **FAIL** | ImportError: multimer async support requires asyncio or uasyncio with create_task |
| `multimer.Timer (default)` | True | **PASS** | 60 callbacks in 300 ms |

### `circuitpython`

- **Runner:** exit 0
- implementation: circuitpython (10, 2, 1, '')
- platform: linux
- python: 3.4.0;

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ImportError: no module named 'machine' |
| `_librt.Timer` | — | SKIP | ImportError: no module named 'ffi' |
| `_win32.Timer` | — | SKIP | ImportError: win32 timer backend requires win32 |
| `_threading.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `_sdl2.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `_polling.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 5 callbacks in 300 ms |
| `multimer.Timer (default)` | True | **PASS** | 7 callbacks in 300 ms |

### `cpython-venv`

- **Runner:** exit 0
- implementation: cpython sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
- platform: linux
- python: 3.12.3

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ModuleNotFoundError: No module named 'machine' |
| `_librt.Timer` | False | **PASS** | 16 callbacks in 300 ms |
| `_win32.Timer` | — | SKIP | ImportError: win32 timer backend requires win32 |
| `_threading.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `_sdl2.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `_polling.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 4 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 15 callbacks in 300 ms |

### `python.exe`

- **Runner:** exit 0
- implementation: cpython sys.version_info(major=3, minor=14, micro=6, releaselevel='final', serial=0)
- platform: win32
- python: 3.14.6

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ModuleNotFoundError: No module named 'machine' |
| `_librt.Timer` | — | SKIP | ImportError: librt timer backend requires Linux |
| `_win32.Timer` | False | **PASS** | 6 callbacks in 300 ms |
| `_threading.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `_sdl2.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `_polling.Timer` | True | **PASS** | 6 callbacks in 300 ms |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 4 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 6 callbacks in 300 ms |

## Legend

- **PASS** — ≥2 callbacks in 300 ms
- **FAIL** — ran but did not meet callback threshold or raised at runtime
- **SKIP** — backend not importable on this port (with reason in detail)
- **missing** — runtime executable not on PATH

Raw JSON: `.cursor/comprehensive_timers_no_lvgl_results.json`
