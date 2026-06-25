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
(`CURATED`) and icons. The index has
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
`[files]`, so single-file installs resolve. Multi-file examples install sibling
`.py` modules via per-file `mip.install` (e.g. `chango/`, `noto_fonts/`).
Examples that need **binary** assets (`.bmp`, `.bin`, `.pbm`, …) are excluded
from the browser gallery — see `BINARY_SUFFIXES` in `tools/gen_demo_pages.py`.

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
- browser-gallery example `.py` files → `_site/demo/src/examples/` (via
  `python tools/gen_demo_pages.py --copy-examples`)
- `demo-pages/index.html` + `site.css` → `_site/`

Only `lib/` and `add_ons/` are copied from `src/` wholesale — not all of
`src/examples/` — because that tree contains tracked symlinks to paths outside
the repo that break CI. Gallery examples (Python-only, 36 files) are copied
file-by-file instead. Binary-dependent examples stay device-only.

Generated demo pages install from `_repo_base + "/src/examples/..."` on
localhost **and** `*.github.io` (same-origin); other hosts still use
`github:PyDevices/...` as a fallback.

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

Ten gallery pages carry the **`loops`** tag (`gen_demo_pages.py` sets `blocks`
when the source has `while True` and the example is not async). After **Run**
they never yield to the browser event loop — the tab becomes unresponsive until
reload. The Run gate already prevents an on-load hang.

**Not blocking:** `chango`, `noto_fonts` (draw once, then `broker.poll()` /
`run_queued()` — no `while True`).

| Demo | Loop style | Browser decision |
|------|------------|------------------|
| `displaysys_simpletest` | Tight `broker.poll()` spin | **Leave for now** — useful interactive demo but hogs CPU; future async variant mirroring `eventsys_simpletest` |
| `eventsys_encoder_test` | Tight `broker.poll()` spin | **Leave for now** — same; scroll-wheel test works briefly before the tab locks up |
| `boxlines` | Continuous random draw, no sleep | **Leave** — hardware-style stress demo; `loops` warning is enough |
| `hello` | 128× tight text draws per rotation | **Leave** — same |
| `tiny_hello` | 3× `sleep_ms(1000)` intro, then tight loop | **Leave** — intro is visible; loop freezes afterward |
| `color_test` | `sleep_ms(1000)` between border redraws | **Leave** — slow enough to see output once |
| `fonts` | `sleep_ms(3000)` between font pages | **Leave** |
| `rotations` | `sleep_ms(2000)` between rotations | **Leave** |
| `scroll` | `sleep_ms(10)` hardware scroll | **Leave** — exercises `vscsad`; acceptable as a reference |
| `feathers` | Tight scroll animation, no sleep | **Leave** — worst offender after `boxlines`/`hello`; keep `loops` tag |

**Policy:** No async rewrites in this pass. Async gallery examples (`paint`,
`calculator`, `eventsys_simpletest`, …) already show the browser-friendly
pattern. Converting the `tft_config` animation set would duplicate a lot of
device-oriented code for marginal gain. If we revisit, start with the two
poll-loop examples (`displaysys_simpletest`, `eventsys_encoder_test`).

**Status (2026-06):** assessed — keep all ten in the gallery with existing
`loops` tag and page notes; no generator or example changes required.

### C. Binary-asset examples — excluded from browser gallery
Examples whose `# pyscript files:` list includes a non-`.py` path are skipped by
`tools/gen_demo_pages.py` (`depends_on_binary_files`). Device installs still use
the full path list; the browser gallery only ships Python-only installs.

**Excluded:** `apollo`, all `bmp565_*`, `font_list`, `font_simpletest`,
`font_simpletest2`, `font_simpletest3`, `pbm_simpletest`, `alien` (`.png`).

**Included (Python-only assets):** `chango`, `noto_fonts` (converted font data
as `.py` modules), `pbm_create_new` (builds a PBM in code, no external file).

### D. Missing dependency — `nano_gui_simpletest`
Imports the `gui` (nano-gui) package, which is **not** in `pyscript.toml`
`[files]`. It will raise `ImportError` on Run until nano-gui is bundled or
installed via `mip`. Tagged `experimental`.

### E. LVGL not in the browser runtime — `lv_test_timer_async`
`lv_test_timer_async` → `display_driver` / `lv_utils` → `import lvgl`. The
bundled PyScript MicroPython has no `lvgl` binding, so Run will fail. Ship an
LVGL-enabled wasm build (point `pyscript.toml` at it) or keep it as a clearly
marked reference. Tagged `experimental`.

**Status (2026-06):** deferred — browser LVGL integration abandoned after repeated
tab hangs; page stays in the gallery as a reference only.

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
`to_js` path.

**Measured (2026-06, local Chromium, 320×480, `tools/serve.py`):**

| Demo | Wall time (Run→Running) | Notes |
|------|-------------------------|-------|
| `paint` (40 stroke events) | interactive | `drawImage` dirty rects ~0.04 ms avg (JS compositing negligible) |
| `graphics_simpletest` | ~5.9 s | ~1369 partial `render()` calls via `fill_rect`/`graphics.*`; canvas copy cheap, Python draw dominates |
| `framebuf_simpletest` | ~13.5 s | two full-frame `blit_rect` (RGB565→RGBA LUT + `putImageData`); ~6–7 s per 153k-pixel blit |

**Conclusion:** dirty-region updates (`fill_rect` → partial `drawImage`) are fine
for interactive browser demos (`paint`, `calculator`, async loops). Avoid
repeated full-frame `blit_rect` in the browser — one shot per frame is OK for
static gallery pages (`framebuf_simpletest`, `logo`) but too slow for animation.
No code change needed now; revisit if PyScript adds a bulk buffer copy API.

### H. Noisy init prints on PyScript
`DisplayDriver.__init__` and `rotation` log to stdout (hooked to `#log` on demo
pages). **`PSDisplay` sets `_quiet = True`** so browser demos stay clean. Pointer
move logging is not present in current `PSDevices`.

### I. Runtime fetches from GitHub
Library code (`lib/`, `add_ons/`) is pre-mounted by `html/pyscript.toml`
`[files]` and copied on deploy. Gallery example scripts are now copied to
`demo/src/examples/` on deploy and installed from the same origin on GitHub Pages
(no GitHub API fetch on Run). Locally `tools/serve.py` serves the repo root the
same way.

Non-gallery pages (`editor.html`, `example.html`, `test.html`, `repl.html`) still
use `github:` installs. To go fully offline-friendly, extend the copy list or
pre-mount those paths in `pyscript.toml` too.

**Status (2026-06):** gallery pages use origin install on `*.github.io`; deploy
copies 36 Python-only example files via `--copy-examples`.

## Next up

1. ~~**Section A (online)**~~ — done (2026-06).
2. ~~**Section C (binary assets)**~~ — excluded from gallery by generator policy.
3. ~~**Section B (blocking loops)**~~ — assessed; keep `loops` tag, no rewrites this pass.
4. ~~**Section E (LVGL)**~~ — deferred; `lv_test_timer_async` stays `experimental`.
5. ~~**Section G (perf)**~~ — measured locally (2026-06); dirty-region path OK, full `blit_rect` costly.
6. ~~**Section I (origin install)**~~ — gallery examples copied on deploy; Pages uses same-origin `mip`.
