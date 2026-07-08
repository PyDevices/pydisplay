# Cross-runtime example tests

Automated **smoke tests** that run `[src/examples/](../../src/examples/)` scripts on every available **runtime** (desktop interpreter or launcher). These are not unit tests — run unit tests first.

- Runtimes
  The canonical runtime list lives in `[tools/example_runtimes.toml](../../tools/example_runtimes.toml)`. Agents should read that file before running the matrix.
  The desktop interpreter runtimes are `micropython`, `micropython.exe`, `circuitpython`, `python.exe`, and repo-root `.venv/bin/python` (`cpython-venv` in the harness). The launcher runtimes are `tools/jupyter.sh` and `tools/pyscript.sh`.

  | Runtime id        | Platform            | How it runs                                                                                        |
  | ----------------- | ------------------- | -------------------------------------------------------------------------------------------------- |
  | `micropython`     | MicroPython unix    | `micropython` from `src/`                                                                          |
  | `micropython.exe` | MicroPython Windows | `micropython.exe` from `src/`                                                                      |
  | `circuitpython`   | CircuitPython unix  | `circuitpython` from `src/`                                                                        |
  | `cpython-venv`    | CPython desktop     | repo-root `.venv/bin/python` from `src/`                                                           |
  | `python.exe`      | CPython Windows     | `python.exe` from `src/`                                                                           |
  | `pyscript`        | PyScript browser    | `tools/pyscript.sh` launcher; autotest uses `embed.html?modules=…&autotest=1` via `tools/serve.py` |
  | `jupyter`         | Jupyter notebook    | `tools/jupyter.sh` launcher; executes generated `src/run-{example}.ipynb`                          |

  **Platform** (MicroPython, PyScript, …) is the product category in [Portability & platforms](../platforms/index.md). **Runtime** is the concrete executable or launcher used in automation.
  ## Prerequisites
  1. **Unit tests pass** (default gate):
    ```bash
     python -m unittest discover -s tests -v
    ```
  2. **Subprocess runtimes** on `PATH` or `~/bin/` as documented in `example_runtimes.toml`.
  3. **CPython venv** at repo-root `.venv` for `cpython-venv` and Jupyter.
  4. **PyScript** (optional): `pip install playwright && playwright install chromium` for headless kit runs.
  ## Running the matrix
  From the repository root:
  ```bash
  # Default: unit tests, then runnable examples on all runtimes; matrix=false and
  # legacy/pending entries appear in the table but are not executed
  python tools/example_test_kit.py

  # Run every manifest example except harnesses (executes matrix=false / legacy/pending too)
  python tools/example_test_kit.py --all-except-harness

  # Runtime-major order: finish one runtime before moving to the next
  python tools/example_test_kit.py --order runtimes

  # v1 curated subset only (~11 examples)
  python tools/example_test_kit.py --curated-only

  # Subset
  python tools/example_test_kit.py --only-example calculator,pydisplay_demo
  python tools/example_test_kit.py --only-runtime micropython,circuitpython

  # Skip unit-test gate (local iteration only)
  python tools/example_test_kit.py --no-unit-tests --curated-only
  ```
  Results: summary table on stderr, full JSON at `.cursor/example_test_results.json`.
  ## Example manifest
  Per-example metadata (kind, quit handling, timeouts, skip lists) is in `[tools/example_test_manifest.toml](../../tools/example_test_manifest.toml)`. Inventory of all example *files* is in `[packages/examples.json](../../packages/examples.json)` (regenerate with `./scripts/install_refresh_manifests.sh`).
  ### Example contract
  Every matrix example should be one of:
  1. **Oneshot** — draws and exits with code 0 (`timer_simpletest`, `graphics_simpletest`).
  2. **Loop + quit** — main loop handles `events.QUIT` or checks `runtime.quit_requested` after `runtime.poll()`.
  3. **Library-driven** — `run_forever()`, `display_driver.run()`, or `pd.run_forever()` exits cleanly when Quit is injected.
  Harness scripts (`lv_test_timer_*`, `displaysys_*_test`) are tagged `kind = harness` and are never included in the matrix.
  By default, examples with `matrix = false` or `kind = legacy` + `quit = pending` appear in the results table with those labels but are **not executed**. Use `--all-except-harness` to run them (still excludes harnesses only).
  ## API (for scripts)
  `[tools/example_test_kit.py](../../tools/example_test_kit.py)` exposes:
  - `test_all_examples()` — outer loop: example → all runtimes
  - `test_all_runtimes()` — outer loop: runtime → all examples
  - `run_case(example, runtime, …)` — single cell

Subprocess runs use `[tools/example_test_wrapper.py](../../tools/example_test_wrapper.py)`, which prints `EXAMPLE_RESULT=` JSON on stdout (same pattern as `KIT_RESULT=` in the LVGL harness).

## Debugging

- `PYDISPLAY_TEST_TRACE=1` — wrapper logs progress on stderr
- `--verbose` — kit logs skipped runtimes
- PyScript autotest posts to `tools/serve.py` `/__debug/example_autotest` when quit injection runs
- JS timer smoke: `embed.html?autotest=1&duration=5` logs `EXAMPLE_RESULT=` after N seconds (for async demos that block on import)



## Related

- [Unit tests](../../tests/README.md)
- [LVGL desktop test suite](../guis/lvgl.md#desktop-test-suite)
- `[tools/README.md](../../tools/README.md)`

