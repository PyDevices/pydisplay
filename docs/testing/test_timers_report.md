# multimer timer probe report

Generated: 2026-06-30  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_test_timers.py`

`_posix.Timer` is the unified Linux librt backend (replaces former `_ffi` and `_ctypes`).

## Summary matrix

| Timer backend | micropython | micropython.exe | circuitpython | cpython-venv | python.exe |
|---------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| `machine.Timer` | SKIP | SKIP | SKIP | SKIP | SKIP |
| `_posix.Timer` | **PASS** | SKIP | SKIP | **PASS** | SKIP |
| `_threading.Timer` | **PASS** | SKIP | **PASS** | **PASS** | **PASS** |
| `_sdl2.Timer` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `_polling.Timer` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `AsyncTimer` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `AsyncTimer (yield loop)` | **FAIL** | **PASS** | **PASS** | **PASS** | **PASS** |
| `multimer.Timer (default)` | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |

**Legend:** **PASS** = ≥2 callbacks in 300 ms · **FAIL** = ran but failed · **SKIP** = not on this port

Raw JSON: `.cursor/test_timers_results.json`

## Reproduce

```bash
export PATH="$HOME/bin:$PATH"
python tools/run_test_timers.py
```
