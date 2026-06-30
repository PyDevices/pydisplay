# Matrix Follow-up Plan

**Branch:** `examples-post-refactor`  
**PR:** [#39 Example matrix harness and post-refactor example fixes](https://github.com/PyDevices/pydisplay/pull/39) — **MERGED** 2026-06-29  
**Latest commits:** `70677fa5` (tft_config PyScript autotest — **ahead 1, not pushed**), `5a77c8b6` (harness + manifest skips), `97aab56e` (console_advanced_demo)  
**Matrix command:** `python tools/example_test_kit.py --no-unit-tests --order runtimes`  
**Sources:** [`.cursor/example_matrix_run.log`](.cursor/example_matrix_run.log) (full matrix, subprocess runtimes), [`.cursor/example_test_results.json`](.cursor/example_test_results.json) (latest column run: harness spot-check), `/tmp/pyscript_run.log` (pyscript column, pre–tft_config enablement), `/tmp/tft_config_pyscript.log` (tft_config pyscript spot run)

---

## Results summary

| Runtime | Pass (excl. `matrix=false`) | Runnable | Status | Notes |
|---------|----------------------------|----------|--------|-------|
| **micropython** | **61/61** (last full) | **68** | ✅ | Reference runtime; tft_config examples ✅ spot (`/tmp/mp_matrix3.log`) |
| **circuitpython** | **59+** (spot) | **68** | ✅ | tft_config examples ✅ spot (`/tmp/cp-matrix.txt`; run ended on harness crash) |
| **cpython-venv** | **61/61** (last full) | **68** | ✅ | Full matrix pre-expand; re-run pending for +7 columns |
| **python.exe** | **61/61** (last full) | **68** | ✅ | Full matrix pre-expand |
| **micropython.exe** | **58/68** | **68** | 🔄 | Full column 2026-06-30 — **10** failures (hangs + 2 import errors); see §4 |
| **pyscript** | **30/52** (stale full column) | **67** | 🔄 | tft_config examples **6/6** ✅ (`70677fa5`); stale baseline — `noto_fonts` now enabled |
| **jupyter** | **23/57** (stale) | **67** | 🔄 | `chango` now runs (timeout, not skip); tft_config cell-timeouts at 30s (quit-injection gap) |

Runnable denominators: desktop runtimes **68** (69 matrix columns − 1 `matrix=false`); pyscript / jupyter **67** (only `png_test` manifest skip on both).

Excluded by design: `keypins_simpletest` (`matrix=false`), `lv_test_timer_harness`, `lv_test_timer_common` (`kind=harness`). See [Skipped examples (by design)](#skipped-examples-by-design) below.

---

## Session status

| Item | Status |
|------|--------|
| PR #39 merged | ✅ **MERGED** 2026-06-29 — includes harness, mp.exe quit inject, dual_main + choice shims, JNDisplay blit clip |
| `nano_gui_simpletest` all runtimes | ✅ `64a36124` |
| `hello` in matrix | ✅ `a2daa012` |
| `console_advanced_demo` no threading | ✅ `97aab56e` — test mode uses cooperative `broker.poll()` quit |
| JNDisplay `blit_rect` clip | ✅ Merged via PR #39 (`20e063fe`); `pbm_simpletest` jupyter ✅ |
| `pbm_simpletest` `oneshot_timeout_s = 60` | ✅ On branch |
| `lv_touch_test` mp.exe harness | ✅ multimer quit + `pump_lvgl` guard |
| `bmp565_scroll_sprite` `timeout_s = 70` | ✅ ~53s mp.exe spot-check |
| `dual_main()` async examples (5) | ✅ mp.exe + micropython spot-check |
| `choice` shims (sprite ×2, testris) | ✅ mp.exe spot-check |
| Jupyter `pydisplay_test_mode` cell | ✅ `_write_jupyter_notebook()` |
| **Manifest skip removal** | ✅ `5a77c8b6` — pyscript skips removed for `color_test`, `chango`, `alien`, `proverbs`, `tiny_toasters`; jupyter skip removed for `chango` |
| **Harness matrix enablement** | ✅ `5a77c8b6` — `lv_test_timer_sync/queued/async`, `displaysys_*_test`, `test_timers`; LVGL timer script fixes |
| **tft_config PyScript autotest** | ✅ `70677fa5` — MIP manifests, `pyscript_embed_query()`, embed autotest fixes, `hello` yield; **6/6** PSDisplay ok |
| tft_config desktop spot-check | ✅ micropython + circuitpython (`/tmp/mp_matrix3.log`, `/tmp/cp-matrix.txt`) |
| Harness spot-check (micropython + cpython-venv) | ✅ **14/14** (`5a77c8b6`) — all 7 former harness examples green on both runtimes |
| **Manifest skip removal (`noto_fonts`)** | ✅ — `skip_runtimes` pyscript removed; `html/noto_fonts.json` already present |
| mp.exe full column re-run | ✅ **58/68** (2026-06-30) — log `/tmp/mpexe_matrix_run.log` |
| Skipped-examples inventory | ✅ Documented below |

**Active jobs:** none. Branch has local edits (manifest + plan).

---

## §4 micropython.exe

### Full column re-run (2026-06-30)

**Result: 58/68** — log `/tmp/mpexe_matrix_run.log`, JSON `.cursor/example_test_results.json`

| Outcome | Count | Examples |
|---------|------:|----------|
| **SDLDisplay, ok** | **58** | — |
| **hang** (quit-injection timeout) | **8** | `boxlines`, `displaysys_simpletest`, `eventsys_encoder_test`, `feathers`, `font_simpletest`, `font_simpletest2`, `font_simpletest3`, `scroll_touch_test_displaybuf` |
| **import error** | **1** | `lv_test_timer_async` (`uasyncio`) |

Target **68/68** not met — hangs are poll-loop examples without mp.exe quit path; import errors need shims like other mp.exe fixes.

### Fixed (verified 2026-06-29)

| Example / area | Fix | Commit |
|----------------|-----|--------|
| `lv_touch_test` | multimer.Timer quit schedule; `pump_lvgl()` guard | `302e975c` |
| `bmp565_scroll_sprite` | manifest `timeout_s = 70` | `302e975c` |
| `apollo`, `calculator`, `eventsys_simpletest`, `paint`, `pydisplay_demo_async` | `dual_main()` sync fallbacks | `82c3ab4a` |
| `bmp565_sprite`, `bmp565_sprite_transparent`, `testris`, `displaysys_block_test` | example-local `choice` shim | `82c3ab4a` / follow-up |
| `console_advanced_demo` | test-mode `run_forever` + `broker.poll()` quit; manifest `kind=loop` | `97aab56e` |

**Target after mp.exe fixes:** **68/68** on all desktop runtimes.

Stale full-matrix row (pre-fix): 49 ok / 11 bad — see `.cursor/example_matrix_run.log` line 688.

---

## §5 PyScript

### OS deps — ✅ installed (2026-06-29)

User ran `sudo .venv/bin/python -m playwright install-deps chromium`; `libnspr4.so` / `libnss3.so` present.

### tft_config examples — ✅ PyScript autotest (`70677fa5`)

| Item | Status |
|------|--------|
| MIP manifests | ✅ `html/alien.json`, `html/proverbs.json`, `html/tiny_toasters.json` (+ `chango.json`) |
| `pyscript_embed_query()` + kit tweaks | ✅ `manifests=<id>` embed URLs; `wait_until="load"` |
| `html/embed.html` autotest | ✅ multimer quit before import; `EXAMPLE_RESULT` → `console.log` |
| Spot run | ✅ **6/6** — `hello`, `color_test`, `chango`, `alien`, `proverbs`, `tiny_toasters` |
| `noto_fonts` MIP manifest | ✅ `html/noto_fonts.json` — `manifests=noto_fonts` embed path |

### Latest column run (2026-06-29, **stale** — pre–tft_config enablement)

| Outcome | Count |
|---------|------:|
| **PSDisplay, ok** | **30** |
| **`Page.goto` networkidle timeout** | **22** |
| **manifest `—` (not run)** | **8** (tft_config + `noto_fonts` at time of run; both now enabled) |
| **matrix=false (display only)** | **2** |

Runnable at time of run: **52**. Pass rate: **30/52** (58%). Current runnable denominator: **67** (`png_test` only skip).

Failures are load-time timeouts on loop/pdwidgets/heavy demos (`boxlines`, `displaysys_simpletest`, all `widgets_*`, etc.) — not `needs_playwright` or browser launch errors.

Log: `/tmp/pyscript_run.log`

---

## Jupyter

### Harness — ✅ done

- `pydisplay_test_mode` injected in notebook generator ([`example_test_kit.py`](tools/example_test_kit.py))

### JNDisplay blit — ✅ merged (PR #39)

[`jndisplay.py`](src/lib/displaysys/jndisplay.py): clip `blit_rect` to framebuffer (SDL-style) instead of raising on partial OOB. Merged via #39 (`20e063fe`).

### tft_config examples — 🔄 runnable, quit-injection gap

| Example | Status |
|---------|--------|
| `chango` | ✅ Passes (inject-quit) |
| `color_test`, `hello` | 🔄 Cell-timeout — infinite loops block notebook execution (needs notebook quit scheduling like embed autotest) |
| `alien`, `proverbs`, `tiny_toasters` | 🔄 Cell-timeout at 30s (quit-injection gap) |

### Latest column run (2026-06-29, **stale** — pre–tft_config/chango enablement)

| Outcome | Count |
|---------|------:|
| **JNDisplay, ok** | **23** |
| **cell timeout** | **33** |
| **manifest skip (not run)** | **2** (`chango`, `png_test` — **`chango` now enabled**) |
| **matrix=false (display only)** | **2** |

Runnable at time of run: **57**. Pass rate: **23/57** (40%). Current runnable denominator: **67** (`png_test` only skip).

Still timing out: loop demos, pdwidgets suite, tft_config examples (quit gap), `bmp565_scroll_sprite` (70s).

Results: `.cursor/example_test_results.json`, `/tmp/jupyter_run_postfix.log`

---

## Remaining work

- [ ] **Push** `70677fa5` + follow-up commits to `origin/examples-post-refactor`
- [ ] **mp.exe hang fixes** — poll-loop quit injection for 8 examples (see §4)
- [ ] **mp.exe import shims** — `lv_test_timer_async` (`uasyncio`)
- [ ] **Follow-up PR to main** for post-#39 stack through `70677fa5`

---

## Verification

```bash
# Full matrix (after tft_config + harness changes committed)
python tools/example_test_kit.py --no-unit-tests --order runtimes

# mp.exe full column (2026-06-30)
python tools/example_test_kit.py --no-unit-tests --only-runtime micropython.exe --order runtimes
# log: /tmp/mpexe_matrix_run.log
python tools/example_test_kit.py --no-unit-tests --only-runtime jupyter
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript

# tft_config pyscript spot (manifests wired)
.venv/bin/python tools/example_test_kit.py --no-unit-tests \
  --only-example color_test chango hello alien proverbs tiny_toasters --only-runtime pyscript

# tft_config desktop spot
python tools/example_test_kit.py --no-unit-tests \
  --only-example color_test chango alien proverbs tiny_toasters hello --only-runtime micropython

# Harness spot-check
python tools/example_test_kit.py --no-unit-tests \
  --only-example lv_test_timer_sync lv_test_timer_queued lv_test_timer_async --only-runtime micropython

# mp.exe spot-checks (already green)
python tools/example_test_kit.py --no-unit-tests \
  --only-example apollo calculator eventsys_simpletest paint pydisplay_demo_async \
  --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests \
  --only-example bmp565_sprite bmp565_sprite_transparent testris lv_touch_test \
  --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests \
  --only-example bmp565_scroll_sprite --only-runtime micropython.exe

# JNDisplay blit retest
python tools/example_test_kit.py --no-unit-tests \
  --only-example pbm_simpletest alien bmp565_scroll_sprite --only-runtime jupyter

fuser -k 8000/tcp   # stale PyScript server
```

Results: `.cursor/example_test_results.json`

---

## Skipped examples (by design)

Inventory from [`tools/example_test_manifest.toml`](tools/example_test_manifest.toml), [`tools/example_test_kit.py`](tools/example_test_kit.py) (`example_allowed_on_runtime`, `missing`, `needs_playwright`, matrix `—` dash), and [`tools/example_runtimes.toml`](tools/example_runtimes.toml).

**Summary count:** **3** global exclusions (1 `matrix=false` example + 2 harnesses) · **2** per-runtime manifest skip cells (**1** example) · **4** launcher skip categories.

### Globally excluded from matrix (`matrix=false`)

| Example | Reason |
|---------|--------|
| `keypins_simpletest` | GPIO / key-pin hardware test; not suitable for desktop SDL matrix. |
| `lv_test_timer_harness` | LVGL timer unit harness (`kind=harness`); automated KIT_RESULT runner, not a matrix demo. |
| `lv_test_timer_common` | LVGL timer shared helpers (`kind=harness`); import-only, not runnable. |

Harness rows (`kind=harness`) appear only when using `--all-except-harness`; default matrix shows `keypins_simpletest` as `matrix=false` label without executing.

**Matrix-enabled former harnesses** (`5a77c8b6`): `lv_test_timer_sync`, `lv_test_timer_queued`, `lv_test_timer_async`, `displaysys_deinit_test`, `displaysys_block_test`, `displaysys_fill_rect_test`, `test_timers`.

### Per-runtime manifest skips (`skip_runtimes` → matrix `—`)

| Example | Skipped on | Reason |
|---------|------------|--------|
| `png_test` | `pyscript`, `jupyter` | PNG decode via add-ons; too heavy / unsupported path for PyScript and Jupyter autotest. |

**Enabled on all runtimes (`5a77c8b6` manifest, `70677fa5` PyScript autotest):** `color_test`, `chango`, `alien`, `proverbs`, `tiny_toasters`, `hello`, `noto_fonts` — `tft_config` + `board_config` (PSDisplay / JNDisplay); `noto_fonts` via `html/noto_fonts.json` MIP manifest.

**Per-runtime runnable counts** (69 matrix columns − 1 `matrix=false` − manifest dashes): micropython / circuitpython / micropython.exe / cpython-venv / python.exe **68**; pyscript **67**; jupyter **67**.

### Harness / environment skips

Cases where the kit schedules a cell but the wrapper or runtime cannot complete smoke testing (distinct from manifest `—` dashes):

_None currently expected for `console_advanced_demo` — test mode uses cooperative `broker.poll()` quit (no daemon thread)._

### Launcher skips

| Condition | When | Reason |
|-----------|------|--------|
| `needs_playwright` | `pyscript` | Playwright not installed in the invoking Python env; kit records skip (not a hard fail). **Current run:** playwright OK — **0** cells. |
| `missing` | any runtime | Interpreter/launcher not found (`micropython` not on PATH, no `.venv/bin/python`, no `.venv/bin/jupyter`, or `tools/serve.py` missing for pyscript). Kit emits one `missing` row per (example, runtime). |
| Platform `available_on` | `micropython.exe`, `python.exe` | Windows/WSL-only subprocess runtimes; absent on plain Linux → all cells `missing`. |
| Platform `available_on` | `jupyter` | Linux/WSL/macOS only; not listed for Windows. |

Matrix table `—` cells: **2** total (manifest `skip_runtimes`: `png_test` ×2); not run, not counted in pass denominators.

---

*Plan pointer:* Cursor plan file `.cursor/plans/matrix_follow-up_plan_ed602266.plan.md` not present in repo; this doc is the canonical follow-up tracker.
