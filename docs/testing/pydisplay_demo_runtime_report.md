# pydisplay demo runtime report

Generated: 2026-07-06

Command:

```bash
.venv/bin/python tools/example_test_kit.py \
  --only-example pydisplay_demo pydisplay_demo_async \
  --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe pyscript jupyter \
  --no-unit-tests --json
```

Raw JSON: `.cursor/example_test_results.json`

## Summary matrix

| Example | micropython | micropython.exe | circuitpython | cpython-venv | python.exe | pyscript | jupyter |
|---------|:-----------:|:---------------:|:-------------:|:------------:|:----------:|:--------:|:-------:|
| `pydisplay_demo` | PASS (`SDLDisplay`) | FAIL (`hang`) | PASS (`SDLDisplay`) | PASS (`SDLDisplay`) | PASS (`PGDisplay`) | PASS (`PSDisplay`) | N/A |
| `pydisplay_demo_async` | PASS (`SDLDisplay`) | FAIL (`exit_5`) | PASS (`SDLDisplay`) | PASS (`SDLDisplay`) | PASS (`PGDisplay`) | PASS (`PSDisplay`) | PASS (`JNDisplay`) |

## Notes

- `pydisplay_demo` is skipped on `jupyter` by manifest because it is sync-only and Jupyter is async-only for this harness.
- `micropython.exe` selected the SDL2-backed sync timer successfully in timer probes, but the full display demo still failed: sync demo timed out as `hang`; async demo exited with code `5` after SDLDisplay initialization.
- Linux `micropython` runs passed, but stderr included repeated SDL callback `MemoryError: heap is locked` messages from `sdldisplay.py` during scroll rendering.
- PyScript runs passed with `PSDisplay`; stderr still included the known autotest debug fetch header-conversion warning.

## Failed cells

### `pydisplay_demo` on `micropython.exe`

- Summary: `hang`
- Return code: `-1`
- Timed out: `true`
- Timeout: `60.0s`
- Captured stdout/stderr: empty

### `pydisplay_demo_async` on `micropython.exe`

- Summary: `exit_5`
- Return code: `5`
- Timed out: `false`
- Captured stdout:

```text
Initializing SDLDisplay...
SDLDisplay: initialized.
SDLDisplay: requires_byteswap = False
```

