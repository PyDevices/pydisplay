# multimer timer probe report

Generated: 2026-07-06  
Command: `export PATH="$HOME/bin:$PATH" && python tools/run_test_timers.py`

Probes public multimer APIs only (`Timer`, `AsyncTimer`, plus hardware `machine.Timer` when present).

## Summary matrix

| Timer backend | micropython | micropython.exe | circuitpython | cpython-venv | python.exe |
|---------------|:-----------:|:-----------:|:-----------:|:-----------:|:-----------:|
| `machine.Timer` | SKIP | SKIP | SKIP | SKIP | SKIP |
| `AsyncTimer` | **PASS** | **FAIL** | **PASS** | **PASS** | **PASS** |
| `AsyncTimer (yield loop)` | **PASS** | **FAIL** | **PASS** | **PASS** | **PASS** |
| `multimer.Timer (default)` | **FAIL** | **FAIL** | **FAIL** | **PASS** | **FAIL** |

**Legend:** **PASS** = ≥2 callbacks in 300 ms · **FAIL** = ran but failed · **SKIP** = not on this port

Raw JSON: `.cursor/test_timers_results.json`

## Reproduce

```bash
export PATH="$HOME/bin:$PATH"
python tools/run_test_timers.py
```
