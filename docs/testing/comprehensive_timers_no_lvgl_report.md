# Comprehensive multimer timer report (no LVGL)

Generated: 2026-07-01 11:25 UTC  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_comprehensive_timer_reports.py --phase no-lvgl`

Probes every importable ``multimer`` backend on each desktop runtime via ``tools/test_timers.py``.
Import failures are reported as **SKIP** with reason (expected on wrong OS/port).

## Summary matrix

| Timer backend | micropython | micropython.exe | circuitpython | cpython-venv | python.exe |
|---------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| `machine.Timer` | SKIP | ? | SKIP | SKIP | SKIP |
| `_librt.Timer` | **PASS** | ? | ? | **PASS** | SKIP |
| `_win32.Timer` | SKIP | ? | ? | SKIP | **PASS** |
| `_threading.Timer` | **PASS** | ? | ? | **PASS** | **PASS** |
| `_sdl2.Timer` | **PASS** | ? | ? | **PASS** | **PASS** |
| `_polling.Timer` | **FAIL** | ? | ? | **FAIL** | **FAIL** |
| `AsyncTimer` | **PASS** | ? | ? | **PASS** | **PASS** |
| `AsyncTimer (yield loop)` | **PASS** | ? | ? | **PASS** | **PASS** |
| `multimer.Timer (default)` | **PASS** | ? | ? | **PASS** | **PASS** |

## Per-runtime details

### `micropython`

- **Runner:** exit 0
- implementation: micropython (1, 29, 0, 'preview')
- platform: linux
- python: 3.4.0;

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ImportError: can't import name Timer |
| `_librt.Timer` | False | **PASS** | 16 callbacks in 300 ms |
| `_win32.Timer` | — | SKIP | ImportError: win32 timer backend requires win32 |
| `_threading.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `_sdl2.Timer` | True | **PASS** | 7 callbacks in 300 ms |
| `_polling.Timer` | True | **FAIL** | expected >=2 callbacks, got 0 |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 5 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 17 callbacks in 300 ms |

### `micropython.exe`

- **Runner:** exit 5

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | ? |  |
| `_librt.Timer` | — | ? |  |
| `_win32.Timer` | — | ? |  |
| `_threading.Timer` | — | ? |  |
| `_sdl2.Timer` | — | ? |  |
| `_polling.Timer` | — | ? |  |
| `AsyncTimer` | — | ? |  |
| `AsyncTimer (yield loop)` | — | ? |  |
| `multimer.Timer (default)` | — | ? |  |

### `circuitpython`

- **Runner:** exit -11
- implementation: circuitpython (10, 2, 1, '')
- platform: linux
- python: 3.4.0;

| Probe | NEEDS_PUMP | Result | Detail |
|-------|:----------:|--------|--------|
| `machine.Timer` | — | SKIP | ImportError: no module named 'machine' |
| `_librt.Timer` | — | ? |  |
| `_win32.Timer` | — | ? |  |
| `_threading.Timer` | True | ? |  |
| `_sdl2.Timer` | — | ? |  |
| `_polling.Timer` | — | ? |  |
| `AsyncTimer` | — | ? |  |
| `AsyncTimer (yield loop)` | — | ? |  |
| `multimer.Timer (default)` | — | ? |  |

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
| `_polling.Timer` | True | **FAIL** | expected >=2 callbacks, got 0 |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 4 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 16 callbacks in 300 ms |

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
| `_polling.Timer` | True | **FAIL** | expected >=2 callbacks, got 0 |
| `AsyncTimer` | False | **PASS** | 5 callbacks in 300 ms |
| `AsyncTimer (yield loop)` | False | **PASS** | 4 callbacks in 300 ms |
| `multimer.Timer (default)` | False | **PASS** | 6 callbacks in 300 ms |

## Legend

- **PASS** — ≥2 callbacks in 300 ms
- **FAIL** — ran but did not meet callback threshold or raised at runtime
- **SKIP** — backend not importable on this port (with reason in detail)
- **missing** — runtime executable not on PATH

Raw JSON: `.cursor/comprehensive_timers_no_lvgl_results.json`
