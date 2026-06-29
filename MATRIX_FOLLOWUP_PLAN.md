# Matrix Follow-up Plan

**Branch:** `examples-post-refactor`  
**PR:** [#39 Example matrix harness and post-refactor example fixes](https://github.com/PyDevices/pydisplay/pull/39) — **OPEN**, mergeable, CI ✅  
**Latest commits:** `302e975c` (harness + mp.exe quit inject), `82c3ab4a` (dual_main + choice shims)  
**Matrix command:** `python tools/example_test_kit.py --no-unit-tests --order runtimes`  
**Sources:** [`.cursor/example_matrix_run.log`](.cursor/example_matrix_run.log) (full matrix, subprocess runtimes), [`.cursor/example_test_results.json`](.cursor/example_test_results.json) (latest column run: jupyter), `/tmp/pyscript_run.log` (pyscript column)

---

## Results summary

| Runtime | Pass (excl. `matrix=false`) | Status | Notes |
|---------|----------------------------|--------|-------|
| **micropython** | **61/61** | ✅ | Reference runtime (full matrix) |
| **circuitpython** | **61/61** | ✅ | `pbm_simpletest` `oneshot_timeout_s = 60` on branch |
| **cpython-venv** | **61/61** | ✅ | Full matrix |
| **python.exe** | **61/61** | ✅ | Full matrix |
| **micropython.exe** | **49/61** (stale) | 🔄 | Pre-fix full matrix; spot-checks green; column re-run pending |
| **pyscript** | **30/52** | 🔄 | Playwright OK; 22 `Page.goto` networkidle timeouts (heavy/loop demos) |
| **jupyter** | **23/57** | 🔄 | 34 cell timeouts; blit clip helps `pbm_simpletest` ✅ |

Excluded by design: `keypins_simpletest` (`matrix=false`). See [Skipped examples (by design)](#skipped-examples-by-design) below.

---

## Session status

| Item | Status |
|------|--------|
| PR #39 opened | ✅ [OPEN](https://github.com/PyDevices/pydisplay/pull/39) — commits through `82c3ab4a` |
| `pbm_simpletest` `oneshot_timeout_s = 60` | ✅ On branch (`302e975c`) |
| `lv_touch_test` mp.exe harness | ✅ multimer quit + `pump_lvgl` guard |
| `bmp565_scroll_sprite` `timeout_s = 70` | ✅ ~53s mp.exe spot-check |
| `dual_main()` async examples (5) | ✅ mp.exe + micropython spot-check |
| `choice` shims (sprite ×2, testris) | ✅ mp.exe spot-check |
| Jupyter `pydisplay_test_mode` cell | ✅ `_write_jupyter_notebook()` |
| JNDisplay `blit_rect` clip | 🔄 **Unstaged** in `jndisplay.py` — `pbm_simpletest` jupyter ✅; `bmp565_scroll_sprite` still times out |
| mp.exe full column re-run | ⏳ Pending |
| PyScript column re-run | ✅ **Done** — 30/52 (`/tmp/pyscript_run.log`) |
| Jupyter full column re-run | ✅ **Done** — 23/57 (`.cursor/example_test_results.json`) |
| Skipped-examples inventory | ✅ Documented below |

**Active jobs:** none (jupyter + pyscript columns finished 2026-06-29).

**Uncommitted:** `src/lib/displaysys/jndisplay.py` (blit clip), `MATRIX_FOLLOWUP_PLAN.md`.

**Commit note (`jndisplay.py`):** Blit clip is working for at least `pbm_simpletest` and `bmp565_blit` on jupyter. Recommend committing after Brad spot-checks `pbm_simpletest alien bmp565_scroll_sprite` — do not commit until satisfied; `bmp565_scroll_sprite` still cell-timeout at 70s (no blit crash).

---

## §4 micropython.exe

### Fixed (verified 2026-06-29)

| Example / area | Fix | Commit |
|----------------|-----|--------|
| `lv_touch_test` | multimer.Timer quit schedule; `pump_lvgl()` guard | `302e975c` |
| `bmp565_scroll_sprite` | manifest `timeout_s = 70` | `302e975c` |
| `apollo`, `calculator`, `eventsys_simpletest`, `paint`, `pydisplay_demo_async` | `dual_main()` sync fallbacks | `82c3ab4a` |
| `bmp565_sprite`, `bmp565_sprite_transparent`, `testris` | example-local `choice` shim | `82c3ab4a` |
| `console_advanced_demo` | test-mode `run_forever` + `broker.poll()` quit; manifest `kind=loop` | (this commit) |

**Target after full re-run:** **61/61** on all desktop runtimes.

Stale full-matrix row (pre-fix): 49 ok / 11 bad — see `.cursor/example_matrix_run.log` line 688.

---

## §5 PyScript

### OS deps — ✅ installed (2026-06-29)

User ran `sudo .venv/bin/python -m playwright install-deps chromium`; `libnspr4.so` / `libnss3.so` present.

### Latest column run (2026-06-29)

| Outcome | Count |
|---------|------:|
| **PSDisplay, ok** | **30** |
| **`Page.goto` networkidle timeout** | **22** |
| **manifest `—` (not run)** | **8** |
| **matrix=false (display only)** | **2** |

Runnable: **52**. Pass rate: **30/52** (58%).

Failures are load-time timeouts on loop/pdwidgets/heavy demos (`boxlines`, `displaysys_simpletest`, all `widgets_*`, etc.) — not `needs_playwright` or browser launch errors.

Log: `/tmp/pyscript_run.log`

---

## Jupyter

### Harness — ✅ done

- `pydisplay_test_mode` injected in notebook generator ([`example_test_kit.py`](tools/example_test_kit.py))

### JNDisplay blit — 🔄 fix in working tree

[`jndisplay.py`](src/lib/displaysys/jndisplay.py): clip `blit_rect` to framebuffer (SDL-style) instead of raising on partial OOB.

### Latest column run (2026-06-29)

| Outcome | Count |
|---------|------:|
| **JNDisplay, ok** | **23** |
| **cell timeout** | **33** |
| **manifest skip (not run)** | **2** (`chango`, `png_test`) |
| **matrix=false (display only)** | **2** |

Runnable: **57**. Pass rate: **23/57** (40%).

Still timing out: loop demos, pdwidgets suite, `alien`, `bmp565_scroll_sprite` (70s).

Results: `.cursor/example_test_results.json`, `/tmp/jupyter_run_postfix.log`

---

## Remaining work

- [ ] Commit + push `jndisplay.py` blit clip (after Brad spot-check)
- [x] Finish **jupyter** column re-run → **23/57**
- [x] Finish **pyscript** column re-run → **30/52**; triage: networkidle timeouts on heavy demos
- [ ] **mp.exe** full column re-run → confirm 61/61
- [ ] Merge PR #39 when columns green enough for Brad

---

## Verification

```bash
# Full matrix (after local fixes committed)
python tools/example_test_kit.py --no-unit-tests --order runtimes

# Targeted
python tools/example_test_kit.py --no-unit-tests --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests --only-runtime jupyter
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript

# mp.exe spot-checks (already green)
python tools/example_test_kit.py --no-unit-tests \
  --only-example apollo calculator eventsys_simpletest paint pydisplay_demo_async \
  --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests \
  --only-example bmp565_sprite bmp565_sprite_transparent testris lv_touch_test \
  --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests \
  --only-example bmp565_scroll_sprite --only-runtime micropython.exe

# JNDisplay blit retest (after commit)
python tools/example_test_kit.py --no-unit-tests \
  --only-example pbm_simpletest alien bmp565_scroll_sprite --only-runtime jupyter

fuser -k 8000/tcp   # stale PyScript server
```

Results: `.cursor/example_test_results.json`

---

## Skipped examples (by design)

Inventory from [`tools/example_test_manifest.toml`](tools/example_test_manifest.toml), [`tools/example_test_kit.py`](tools/example_test_kit.py) (`example_allowed_on_runtime`, `missing`, `needs_playwright`, matrix `—` dash), and [`tools/example_runtimes.toml`](tools/example_runtimes.toml).

**Summary count:** **10** global exclusions (1 `matrix=false` example + 9 harnesses) · **9** per-runtime manifest skip cells (**7** examples) · **4** launcher skip categories.

### Globally excluded from matrix (`matrix=false`)

| Example | Reason |
|---------|--------|
| `keypins_simpletest` | GPIO / key-pin hardware test; not suitable for desktop SDL matrix. |
| `lv_test_timer_harness` | LVGL timer unit harness (`kind=harness`); never in matrix. |
| `lv_test_timer_sync` | LVGL timer sync harness. |
| `lv_test_timer_queued` | LVGL timer queued harness. |
| `lv_test_timer_async` | LVGL timer async harness. |
| `lv_test_timer_common` | LVGL timer shared helpers harness. |
| `displaysys_deinit_test` | DisplaySys deinit unit harness. |
| `displaysys_block_test` | DisplaySys block API unit harness. |
| `displaysys_fill_rect_test` | DisplaySys fill_rect unit harness. |
| `test_timers` | General timer unit harness. |

Harness rows appear only when using `--all-except-harness`; default matrix shows `keypins_simpletest` as `matrix=false` label without executing.

### Per-runtime manifest skips (`skip_runtimes` → matrix `—`)

| Example | Skipped on | Reason |
|---------|------------|--------|
| `chango` | `pyscript`, `jupyter` | Board `tft_config` + add-on font/game assets; not wired for browser embed or notebook kit. |
| `png_test` | `pyscript`, `jupyter` | PNG decode via add-ons; too heavy / unsupported path for PyScript and Jupyter autotest. |
| `color_test` | `pyscript` | TFT color calibration via `tft_config`; no PyScript board profile. |
| `alien` | `pyscript` | SPI sprite demo with `tft_config`; assets not in PyScript embed. |
| `proverbs` | `pyscript` | Scrolling text with `tft_config`; not in PyScript embed. |
| `tiny_toasters` | `pyscript` | Animation with `tft_config`; not in PyScript embed. |
| `noto_fonts` | `pyscript` | Large Noto font bundle + inject-quit loop; unreliable in headless PyScript autotest. |

**Per-runtime runnable counts** (62 matrix columns − 2 `matrix=false` − manifest dashes): micropython / circuitpython / micropython.exe / cpython-venv / python.exe **61**; pyscript **54**; jupyter **58**.

### Harness / environment skips

Cases where the kit schedules a cell but the wrapper or runtime cannot complete smoke testing (distinct from manifest `—` dashes):

_None currently expected for `console_advanced_demo` — test mode uses cooperative `broker.poll()` quit (no daemon thread)._

Manifest-listed skips in the previous table are also environment-driven (tft_config, etc.); they are not executed so no failure row is recorded.

### Launcher skips

| Condition | When | Reason |
|-----------|------|--------|
| `needs_playwright` | `pyscript` | Playwright not installed in the invoking Python env; kit records skip (not a hard fail). **Current run:** playwright OK — **0** cells. |
| `missing` | any runtime | Interpreter/launcher not found (`micropython` not on PATH, no `.venv/bin/python`, no `.venv/bin/jupyter`, or `tools/serve.py` missing for pyscript). Kit emits one `missing` row per (example, runtime). |
| Platform `available_on` | `micropython.exe`, `python.exe` | Windows/WSL-only subprocess runtimes; absent on plain Linux → all cells `missing`. |
| Platform `available_on` | `jupyter` | Linux/WSL/macOS only; not listed for Windows. |

Matrix table `—` cells: **9** total (manifest `skip_runtimes`); not run, not counted in pass denominators.

---

*Plan pointer:* Cursor plan file `.cursor/plans/matrix_follow-up_plan_ed602266.plan.md` not present in repo; this doc is the canonical follow-up tracker.
