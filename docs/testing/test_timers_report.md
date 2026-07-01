# multimer timer probe report

Generated: 2026-07-01  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_test_timers.py`

`_librt.Timer` is the unified Linux librt backend (replaces former `_ffi` and `_ctypes`).

## Summary matrix

| Timer backend | micropython | micropython.exe | circuitpython | cpython-venv | python.exe |
|---------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| `machine.Timer` | ? | ? | ? | ? | SKIP |
| `_librt.Timer` | ? | ? | ? | ? | SKIP |
| `_win32.Timer` | ? | ? | ? | ? | **PASS** |
| `_threading.Timer` | ? | ? | ? | ? | **PASS** |
| `_sdl2.Timer` | ? | ? | ? | ? | **PASS** |
| `_polling.Timer` | ? | ? | ? | ? | **PASS** |
| `AsyncTimer` | ? | ? | ? | ? | **PASS** |
| `AsyncTimer (yield loop)` | ? | ? | ? | ? | **PASS** |
| `multimer.Timer (default)` | ? | ? | ? | ? | **PASS** |

**Legend:** **PASS** = ≥2 callbacks in 300 ms · **FAIL** = ran but failed · **SKIP** = not on this port

Raw JSON: `.cursor/test_timers_results.json`

## Reproduce

```bash
export PATH="$HOME/bin:$PATH"
python tools/run_test_timers.py
```
