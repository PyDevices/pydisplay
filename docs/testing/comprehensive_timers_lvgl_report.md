# Comprehensive LVGL timer report

Generated: 2026-07-01 09:51 UTC  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_comprehensive_timer_reports.py --phase lvgl`

Runs ``examples/lv_test_timer_harness.py`` (no_pump / pump / async) on every desktop runtime.
``no_pump`` on pump-required backends (``multimer.Timer`` NEEDS_PUMP=True) may hang or report no timers — both are expected.

## Summary matrix

| Runtime | no_pump | pump | async |
|---------|:---------:|:---------:|:---------:|
| micropython | _librt, ok | _librt, ok | _async, ok |
| circuitpython | _polling, no timers (expected) | _polling, ok | _async, ok |
| cpython-venv | _librt, ok | _librt, ok | _async, ok |
| micropython.exe | _polling, ok | _polling, ok | _async, ok |
| python.exe | _win32, ok | _win32, ok | _async, ok |

## Per-cell details

### `micropython` / `no_pump`

- **Summary:** _librt, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","backend":"_librt","mode":"no_pump","seconds":6,"broker_polls":0,"status":"ok","sdl_lv_taps":1,"taps":1,"sdl_stolen_taps":0,"fifo_taps":0,"taps_total":1,"lv_event_ok":true}`

### `micropython` / `pump`

- **Summary:** _librt, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","backend":"_librt","mode":"pump","seconds":4,"broker_polls":0,"status":"ok","sdl_lv_taps":0,"taps":2,"sdl_stolen_taps":0,"fifo_taps":0,"taps_total":1,"lv_event_ok":true}`

### `micropython` / `async`

- **Summary:** _async, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","broker_polls":0,"mode":"async","fifo_taps":0,"backend":"_async","sdl_lv_taps":1,"status":"ok","sdl_stolen_taps":0,"seconds":3,"taps":1,"taps_total":1,"lv_event_ok":true}`

### `circuitpython` / `no_pump`

- **Summary:** _polling, no timers (expected)
- **Exit code:** -11
- **KIT_RESULT:** `{"click_status":"no timers","backend":"_polling","mode":"no_pump","seconds":0,"broker_polls":0,"status":"fail","sdl_lv_taps":0,"taps":0,"sdl_stolen_taps":0,"fifo_taps":0,"taps_total":0,"lv_event_ok":false}`

### `circuitpython` / `pump`

- **Summary:** _polling, ok
- **Exit code:** -11
- **KIT_RESULT:** `{"click_status":"ok","backend":"_polling","mode":"pump","seconds":4,"broker_polls":0,"status":"ok","sdl_lv_taps":0,"taps":1,"sdl_stolen_taps":0,"fifo_taps":0,"taps_total":1,"lv_event_ok":true}`

### `circuitpython` / `async`

- **Summary:** _async, ok
- **Exit code:** -11
- **KIT_RESULT:** `{"click_status":"ok","broker_polls":0,"mode":"async","fifo_taps":0,"backend":"_async","sdl_lv_taps":1,"status":"ok","sdl_stolen_taps":0,"seconds":3,"taps":1,"taps_total":1,"lv_event_ok":true}`

### `cpython-venv` / `no_pump`

- **Summary:** _librt, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"no_pump","status":"ok","click_status":"ok","backend":"_librt","seconds":4,"taps":1,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":1,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

### `cpython-venv` / `pump`

- **Summary:** _librt, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"pump","status":"ok","click_status":"ok","backend":"_librt","seconds":6,"taps":1,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":0,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

### `cpython-venv` / `async`

- **Summary:** _async, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"async","status":"ok","click_status":"ok","backend":"_async","seconds":3,"taps":1,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":1,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

<details><summary>stderr</summary>

```
/home/brad/github/pydisplay/src/../tools/quit_inject.py:71: RuntimeWarning: coroutine 'sleep_ms' was never awaited
  sleep_ms(ms)
RuntimeWarning: Enable tracemalloc to get the object allocation traceback

```
</details>

### `micropython.exe` / `no_pump`

- **Summary:** _polling, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","taps_total":1,"mode":"no_pump","taps":2,"sdl_stolen_taps":0,"status":"ok","seconds":2,"sdl_lv_taps":0,"fifo_taps":0,"backend":"_polling","broker_polls":0,"lv_event_ok":true}`

### `micropython.exe` / `pump`

- **Summary:** _polling, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","taps_total":2,"mode":"pump","taps":2,"sdl_stolen_taps":1,"status":"ok","seconds":6,"sdl_lv_taps":1,"fifo_taps":1,"backend":"_polling","broker_polls":0,"lv_event_ok":true}`

### `micropython.exe` / `async`

- **Summary:** _async, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"click_status":"ok","lv_event_ok":true,"fifo_taps":0,"sdl_stolen_taps":0,"sdl_lv_taps":1,"status":"ok","taps":1,"seconds":3,"mode":"async","backend":"_async","taps_total":1,"broker_polls":0}`

### `python.exe` / `no_pump`

- **Summary:** _win32, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"no_pump","status":"ok","click_status":"ok","backend":"_win32","seconds":4,"taps":1,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":0,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

### `python.exe` / `pump`

- **Summary:** _win32, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"pump","status":"ok","click_status":"ok","backend":"_win32","seconds":4,"taps":2,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":0,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

### `python.exe` / `async`

- **Summary:** _async, ok
- **Exit code:** 0
- **KIT_RESULT:** `{"mode":"async","status":"ok","click_status":"ok","backend":"_async","seconds":3,"taps":1,"broker_polls":0,"sdl_stolen_taps":0,"sdl_lv_taps":1,"fifo_taps":0,"lv_event_ok":true,"taps_total":1}`

## Legend

- **ok** — timers ≥2 s and click checks passed
- **no timers (expected)** / **hang (expected)** — ``no_pump`` on a runtime whose default ``multimer.Timer`` has NEEDS_PUMP=True
- **hang** — subprocess timed out unexpectedly (often post-``KIT_RESULT`` quit teardown)
- **missing** — runtime executable not on PATH

Raw JSON: `.cursor/comprehensive_timers_lvgl_results.json`
