# PyScript async demo pages — plan & known issues

This file tracks the new browser demo pages for the async examples and the
issues to pick up during desktop development. It is intentionally not part of
the deployed site (the deploy workflow only copies `index.html`, `html/**` and
`demo-pages/index.html`).

## What was added

- `html/demo.css` — shared stylesheet for the demo index and every example page.
- `demo-pages/site.css` — stylesheet for the root GitHub Pages landing page.
- One page per example marked `# multimer types: async`:
  | Page | Example | Install strategy | Status |
  | --- | --- | --- | --- |
  | `html/calculator.html` | `calculator.py` | single file → root | expected to work |
  | `html/paint.html` | `paint.py` | single file → root | expected to work |
  | `html/eventsys_simpletest.html` | `eventsys_simpletest.py` | single file → root | works, console-only output |
  | `html/pydisplay_demo_async.html` | `pydisplay_demo_async.py` | single file → root | expected to work (watch perf) |
  | `html/apollo.html` | `apollo.py` | `examples.json` → `target="examples"` | experimental |
  | `html/lv_test_timer_async.html` | `lv_test_timer_async.py` | `examples.json` → `target="examples"` | likely broken (needs LVGL) |
- `index.html` (demo index) and `demo-pages/index.html` (landing) restyled.
- `.github/workflows/deploy-demo.yml` now also copies `demo-pages/site.css`.

The async examples were identified by the `# multimer types: async` header
comment. Only these six carry that marker exactly:
`apollo.py`, `calculator.py`, `eventsys_simpletest.py`,
`lv_test_timer_async.py`, `paint.py`, `pydisplay_demo_async.py`.
(Examples marked `all` also run under async, but were left out per scope — see
"Open question" below.)

## How loading works

Each page mirrors the existing `html/example.html` pattern:

```python
import mip
mip.install("github:PyDevices/pydisplay/src/examples/<name>.py")  # or examples.json
import lib.path          # adds lib/, add_ons/, examples/ to sys.path
import <name>            # running the module schedules main() via multimer.aio.run
```

Dependencies that are *not* example-local (graphics, eventsys, palettes,
touch_keypad, board_config, displaysys, multimer …) are pre-mounted into the
PyScript VFS by `html/pyscript.toml` `[files]`, so single-file installs resolve.
Example-local packages (e.g. `apollo_dsky`) are only fetched when the whole
`packages/examples.json` manifest is installed with `target="examples"`.

All demos run on the **main thread** (no `worker`) because
`displaysys.psdisplay` uses `from js import document` and `pyscript.ffi`, which
are not available in a worker.

## Known issues to pick up on desktop

### 1. LVGL is not available in the browser runtime (blocker for `lv_test_timer_async`)
`lv_test_timer_async.py` → `display_driver` / `lv_utils` → `import lvgl`. The
bundled PyScript MicroPython (`html/pyscript/micropython/`) has no `lvgl`
binding, so the import will fail. Options:
- Ship an LVGL-enabled MicroPython wasm build and point `pyscript.toml` at it, or
- Drop this page / mark it clearly as "desktop/MCU only" (currently tagged
  `experimental`, with the failure surfaced in the on-page console).

### 2. `PSDisplay.blit_rect` is O(pixels) in pure Python (perf)
`src/lib/displaysys/psdisplay.py` builds the canvas `ImageData` one pixel at a
time in a Python loop (`for i in range(0, len(buf), BPP)`), converting each
RGB565 value with `color_rgb`. For full-width text/sprite blits this is slow:
- `pydisplay_demo_async` re-blits every notes row on each redraw.
- `apollo` blits large BMP regions and a 320×372 panel.
Consider a vectorised path (e.g. build a `Uint8ClampedArray` / use
`numpy`-style conversion, or precompute an RGBA buffer) before optimising the
examples themselves.

### 3. `apollo` asset + filesystem assumptions (experimental)
- Requires `apollo_dsky/__init__.py` **and** the binary
  `apollo_dsky/Apollo_DSKY_interface.bmp`. Both come from `examples.json`;
  verify `mip` actually writes the binary into the VFS and that
  `BMP565(..., streamed=True)` can `seek`/`read` it in the browser.
- `apollo_dsky` derives its asset path from `__file__`; confirm `__file__` is
  populated for modules installed under `/examples/apollo_dsky/`.
- Layout assumes a 320×480 viewport (matches `board_config`), so it should fit,
  but check keypad hit-testing via `display_drv.translate_point`.
- Downloading the full `examples.json` set is heavy. If desired, create a small
  per-demo manifest (apollo + apollo_dsky only) to cut download size.

### 4. `eventsys_simpletest` has no visual output by design
It only `print`s polled events. The page routes stdout to the on-page console
(`output="log"`). The `QUIT` event never fires in the browser, so the loop runs
forever — fine for a demo. Confirm the `output` attribute is honoured by the
bundled PyScript build; if not, fall back to a `terminal worker` variant (note
that worker mode loses canvas/DOM access, so board_config would need a headless
path).

### 5. Noisy `console.log` from pointer events
`PSDevices._on_move` / `_on_down` / `_on_up` call `console.log` on every mouse
event, flooding the browser console (and our `#log` panel) during paint/calc.
Gate these behind a debug flag in `psdisplay.py`.

### 6. Runtime fetches from GitHub
Every page `mip.install`s from `github:PyDevices/...` at load time, so demos
need network access and the first load is slow. If this becomes a problem,
pre-mount the async example files via `pyscript.toml` `[files]` like the
add-ons already are.

### 7. Cross-origin isolation
`html/mini-coi-fd.js` registers a service worker to provide COOP/COEP when the
host doesn't. GitHub Pages works with this today; keep it in mind if pages are
ever served from a context where the service worker can't register.

## Local preview

```bash
# from repo root
python -m http.server 8000
# demo index:    http://localhost:8000/index.html
# example pages: http://localhost:8000/html/calculator.html
```

The service worker in `mini-coi-fd.js` supplies the cross-origin-isolation
headers, so a plain static server is enough. The landing page references
`site.css` which only exists next to it after the deploy step copies it; for a
local landing preview open `demo-pages/index.html` (the CSS sits beside it).

## Open question for desktop session

Scope here was "examples marked `async`" (the 6 above). Examples marked
`all` (e.g. `hello`, `feathers`, `color_test`, `boxlines`, `rotations`,
`logo`, font/graphics simpletests …) are also async-compatible and would make
good additional demo pages. If wanted, the same single-file pattern applies and
they can reuse `demo.css` directly.
