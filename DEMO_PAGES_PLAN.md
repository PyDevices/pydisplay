# PyScript demo pages — plan & known issues

Tracks the browser demo pages for the pydisplay examples and the issues to pick
up during desktop development (Cursor Debug mode). This file is **not** part of
the deployed site (the deploy workflow copies `index.html`, `html/**`,
`demo-pages/index.html`, and `demo/src/{lib,add_ons,jupyter_notebook.ipynb}`).

## What was added

- `html/demo.css` — shared stylesheet for the demo index and every example page.
- `demo-pages/site.css` — stylesheet for the root GitHub Pages landing page.
- `tools/gen_demo_pages.py` — generator that writes one page per example marked
  `# multimer types: async` **or** `all`, and refreshes the index card grids.
- `tools/serve.py` — CPython dev server (see below).
- 27 generated example pages in `html/` (5 `async`, 22 `all`), plus hand-written
  pages (`repl.html`, `editor.html`, `example.html`, `test.html`).
- `index.html` (demo index) and `demo-pages/index.html` (landing) restyled.
- `.github/workflows/deploy-demo.yml` — assembles `_site/` and pushes to
  `gh-pages` (see **GitHub Pages deploy** below).

## Generating pages

Pages and the index card grids are generated, not hand-written:

```bash
python tools/gen_demo_pages.py          # regenerate html/*.html + index cards
python tools/gen_demo_pages.py --check  # CI: fail if anything is stale
```

`tools/gen_demo_pages.py` scans `src/examples/` for the `# multimer types:`
header, derives a blurb from the module docstring, and applies curated overrides
(`CURATED`), manifest-install hints (`NEEDS_MANIFEST`) and icons. The index has
`<!-- GEN:async:start -->` / `<!-- GEN:all:start -->` markers the generator fills.
To tweak copy for a specific example, edit its entry in `CURATED` and rerun.

### How loading works (Run button)

Every example page loads the PyScript runtime first and only installs + imports
the example **when the user clicks Run**. This is deliberate: many `all`
examples run a blocking `while True` loop at import, which would freeze the tab
on load. The page wires a click handler that runs:

```python
import mip
mip.install(...)        # single file, or examples.json -> target="examples"
import lib.path         # adds lib/, add_ons/, examples/ to sys.path
import <module>         # module-level code runs (schedules async main, or blocks)
```

Library deps (graphics, eventsys, displaysys, multimer, palettes, touch_keypad,
tft_config, console, framebuf, fonts …) are pre-mounted by `html/pyscript.toml`
`[files]`, so single-file installs resolve. Example-local packages and assets
(`apollo_dsky/`, `chango/`, `noto_fonts/`, `examples/assets/*`) only exist when
the full `packages/examples.json` manifest is installed with `target="examples"`
— the generator picks that strategy for those (`NEEDS_MANIFEST` + sub-packages).

All demos run on the **main thread** (no `worker`) because
`displaysys.psdisplay` uses `from js import document` / `pyscript.ffi`.

## GitHub Pages deploy

`tools/serve.py` serves the **repo root** locally, so `pyscript.toml` paths like
`../src/lib/...` resolve to `/src/lib/...`. On GitHub Pages the demo lives under
`/pydisplay/demo/html/`, so the same TOML paths resolve to
`/pydisplay/demo/src/lib/...`.

The deploy workflow (`.github/workflows/deploy-demo.yml`) therefore copies:

- `index.html` → `_site/demo/`
- `html/` → `_site/demo/html/`
- `src/lib/`, `src/add_ons/`, `src/jupyter_notebook.ipynb` → `_site/demo/src/`
- `demo-pages/index.html` + `site.css` → `_site/`

Only `lib/` and `add_ons/` are copied — not all of `src/` — because
`src/examples/` contains tracked symlinks to paths outside the repo that break
CI. Examples are still fetched at Run time via `mip.install("github:PyDevices/...")`.

Triggers on changes to `html/**`, `src/**`, `index.html`, `demo-pages/**`, or
the workflow file itself.

**Status (2026-06):** Deploy fixed and verified — online
[paint.html](https://pydevices.github.io/pydisplay/demo/html/paint.html) reaches
“Runtime ready”, Run installs from GitHub, and shows “Application loaded”.

## Local dev server (`tools/serve.py`)

CPython stdlib only. Serves the repo root the way GitHub Pages does, with two
extras aimed at troubleshooting:

```bash
python tools/serve.py                  # serve repo root on 127.0.0.1:8000
python tools/serve.py -p 9000 --no-coi # custom port, no isolation headers
python tools/serve.py /some/other/dir  # serve a different directory
```

Open:
- `http://127.0.0.1:8000/index.html` — demo index
- `http://127.0.0.1:8000/html/<example>.html` — an example page
- `http://127.0.0.1:8000/demo-pages/index.html` — landing page

1. **Cross-origin isolation headers.** It sends `Cross-Origin-Opener-Policy:
   same-origin`, `Cross-Origin-Embedder-Policy: require-corp` and
   `Cross-Origin-Resource-Policy: cross-origin` — the same headers
   `html/mini-coi-fd.js` injects in production — so the worker-backed pages
   (REPL, example picker) get `SharedArrayBuffer` and local behaviour matches
   production. Disable with `--no-coi` if a cross-origin asset is blocked.

2. **Debug log sink for Cursor Debug mode.** It accepts `POST` (and `OPTIONS`
   preflight) at `/__debug` with permissive CORS and prints whatever it receives
   to the terminal (which the desktop agent can read). `GET /__debug` is a
   health check. Wire a page-side beacon so browser console/errors stream back:

   ```js
   for (const k of ['log','warn','error']) {
     const orig = console[k];
     console[k] = (...a) => { try { navigator.sendBeacon('/__debug',
       JSON.stringify({level:k, args:a.map(String), url:location.href})); }
       catch(_){} orig.apply(console, a); };
   }
   ```

   This endpoint is the hook for any instrumentation Cursor Debug mode injects;
   extend `do_POST` / `_log_debug` in `tools/serve.py` as needed (e.g. to fan
   out to a websocket or persist to a file).

## Known issues to pick up on desktop

### A. Examples that should "just work"
No blocking loop, deps pre-mounted — draw once and idle, or run async:
`graphics_simpletest`, `graphics_area_test`, `logo`, `displaybuf_simpletest`,
`framebuf_simpletest`, `console_simpletest`, `pbm_create_new`,
`eventsys_touch_test` (async-capable), plus the async set
(`pydisplay_demo_async`, `calculator`, `paint`, `eventsys_simpletest`).
Verify rendering and confirm the spinner/Run flow.

**Status (2026-06):** Section A verified in Cursor browser via `tools/serve.py`
(local). Fixed along the way: localhost `mip.install`, console `#log` hook, 1:1
canvas layout (no CSS scaling), `PSDevices` + `map_pointer`, scroll compositing on
`PSDisplay`, async `sleep(0.02)` in tight loops, `multimer.aio.run()` on
PyScript. Clicks and auto-scroll confirmed on `calculator` and
`pydisplay_demo_async` locally.

**Online (2026-06):** After the GitHub Pages `src/` deploy fix, verified on
[pydevices.github.io](https://pydevices.github.io/pydisplay/demo/html/):

| Demo | Result |
|------|--------|
| `paint` | Run → “Application loaded”, palette on canvas |
| `calculator` | Run → Running, UI on canvas |
| `eventsys_simpletest` | Run → polling, pointer events in console |
| `pydisplay_demo_async` | Run → aio timer started, auto-scroll UI |
| `graphics_simpletest` | Run → shapes drawn (non-black pixels) |
| `logo` | Run → logo rendered |
| `framebuf_simpletest` | Run → no import errors |

Section A online spot-check **complete** for the core async + draw-once set.

### B. Blocking `while True` loops freeze the tab (tagged `loops`)
These render but never yield to the event loop, so the tab becomes unresponsive
after **Run** (reload to stop): `displaysys_simpletest`, `color_test`,
`boxlines`, `feathers`, `eventsys_encoder_test`, `fonts`, `font_simpletest`,
`font_simpletest2`, `font_simpletest3`, `font_list`, `hello`, `rotations`,
`scroll`, `tiny_hello`, `chango`, `noto_fonts`. Options to make them
browser-friendly: add an async variant (`await asyncio.sleep(0)` in the loop)
or a frame cap, or run them in a worker with a headless display path. The Run
gate already prevents an on-load hang.

### C. Asset-dependent examples (need the manifest install)
Load files from `examples/assets/` or sub-packages, so they use the
`examples.json` install: `bmp565_blit`, `bmp565_simpletest`, `font_list`,
`font_simpletest`, `font_simpletest2`, `font_simpletest3`, `pbm_simpletest`,
`chango`, `noto_fonts`. Verify `mip` writes the **binary** assets (`.bmp`,
`.pbm`) into the VFS and that relative paths like `examples/assets/warrior.bmp`
resolve from cwd `/`. Downloading the whole example set per page is heavy —
consider small per-demo manifests if load time matters.

**Status (2026-06):** `chango` verified online — per-file GitHub installs into
`examples/chango/`, import succeeds, status Running. Still to verify: binary
asset demos (`bmp565_*`, `pbm_simpletest`, font tests with assets).

### D. Missing dependency — `nano_gui_simpletest`
Imports the `gui` (nano-gui) package, which is **not** in `pyscript.toml`
`[files]`. It will raise `ImportError` on Run until nano-gui is bundled or
installed via `mip`. Tagged `experimental`.

### E. LVGL not in the browser runtime — `lv_test_timer_async`
`lv_test_timer_async` → `display_driver` / `lv_utils` → `import lvgl`. The
bundled PyScript MicroPython has no `lvgl` binding, so Run will fail. Ship an
LVGL-enabled wasm build (point `pyscript.toml` at it) or keep it as a clearly
marked reference. Tagged `experimental`.

### F. `apollo` asset + filesystem assumptions
Needs `apollo_dsky/__init__.py` and the binary `Apollo_DSKY_interface.bmp`
(both via `examples.json`). Verify `mip` writes the binary, that `__file__` is
populated for `/examples/apollo_dsky/`, and keypad hit-testing via
`display_drv.translate_point`. Designed for 320×480 (matches `board_config`).
Tagged `experimental`.

### G. `PSDisplay.blit_rect` is O(pixels) in pure Python (perf)
`src/lib/displaysys/psdisplay.py` builds the canvas `ImageData` one pixel at a
time via FFI. For a 320×480 frame that's ~153k pixels × several FFI writes each
— boundary crossings dominate.

**Done (2026-06):** RGB565→RGBA LUT in `init()`; offscreen buffer + ILI9341-style
`render()` for vertical scroll; single-pass LUT write into `ImageData` (bulk
`bytearray` + `data.set()` is a no-op in PyScript). Pointer mapping moved to
`PSDevices` at capture time (`PSDevices(canvas_id, display_drv)`).

**Still open:** faster bulk copy if PyScript gains a working `data.set(rgba)` or
`to_js` path; measure dirty-region blits if full-frame redraw is still heavy.

### H. Noisy init prints on PyScript
`DisplayDriver.__init__` and `rotation` log to stdout (hooked to `#log` on demo
pages). **`PSDisplay` sets `_quiet = True`** so browser demos stay clean. Pointer
move logging is not present in current `PSDevices`.

### I. Runtime fetches from GitHub
Every page `mip.install`s the **example script** from `github:PyDevices/...` at
Run time (when not on localhost), so demos need network access and the first run
is slow. Library code (`lib/`, `add_ons/`) is now **pre-mounted on GitHub Pages**
via the deploy workflow; locally it comes from the repo root via `pyscript.toml`.
To go fully offline-friendly, pre-mount example files in `pyscript.toml` too.

## Next up

1. ~~**Section A (online)**~~ — done (2026-06).
2. **Section C** — verify manifest-install examples (`chango`, font tests, `bmp565_*`).
3. **Section B** — decide per-demo whether to add async variants or leave as Run-and-freeze.
4. **Section E** — LVGL browser path deferred; `lv_test_timer_async` stays `experimental`.
5. **Section G** — measure dirty-region blits if full-frame redraw is still heavy online.
