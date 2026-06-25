# PyScript demo pages — plan & known issues

Tracks the browser demo pages for the pydisplay examples and the issues to pick
up during desktop development (Cursor Debug mode). This file is **not** part of
the deployed site (the deploy workflow only copies `index.html`, `html/**` and
`demo-pages/index.html`).

## What was added

- `html/demo.css` — shared stylesheet for the demo index and every example page.
- `demo-pages/site.css` — stylesheet for the root GitHub Pages landing page.
- `tools/gen_demo_pages.py` — generator that writes one page per example marked
  `# multimer types: async` **or** `all`, and refreshes the index card grids.
- `tools/serve.py` — CPython dev server (see below).
- 35 generated example pages in `html/` (6 `async`, 29 `all`).
- `index.html` (demo index) and `demo-pages/index.html` (landing) restyled.
- `.github/workflows/deploy-demo.yml` also copies `demo-pages/site.css`.

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
time, calling `color_rgb` per pixel and writing each RGBA byte straight into the
JS `Uint8ClampedArray`. For a 320×480 frame that's ~153k `color_rgb` calls and
~614k **per-element FFI writes** — and the boundary crossings, not the math,
dominate. This is the main bottleneck for text/sprite-heavy examples (fonts,
bmp565, apollo, `pydisplay_demo_async`).

**Proposed fix** (two changes, biggest win first):

1. Build the whole RGBA buffer in a native Python `bytearray` (no FFI in the
   loop), then transfer it in **one** `img_data.data.set(rgba)` call.
2. Precompute an RGB565→RGBA lookup table once (only 65,536 possible values), so
   the inner loop is a table read instead of a function call + bit ops.

```python
def init(self) -> None:
    self._canvas.width = self.width
    self._canvas.height = self.height
    # One-time RGB565(LE) -> packed RGBA LUT: 65536 * 4 bytes = 256 KiB.
    if getattr(self, "_rgba_lut", None) is None:
        lut = bytearray(65536 * 4)
        for v in range(65536):
            lo, hi = v & 0xFF, v >> 8
            k = v << 2
            lut[k]     = (hi & 0xF8) | ((hi >> 5) & 0x07)         # R
            lut[k + 1] = ((hi << 5) & 0xE0) | ((lo >> 3) & 0x1F)  # G
            lut[k + 2] = ((lo << 3) & 0xF8) | ((lo >> 2) & 0x07)  # B
            lut[k + 3] = 255                                      # A
        self._rgba_lut = lut

def blit_rect(self, buf, x, y, w, h):
    BPP = self.color_depth // 8
    if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
        raise ValueError("The provided x, y, w, h values are out of range")
    if len(buf) != w * h * BPP:
        raise ValueError("The source buffer is not the correct size")
    lut = self._rgba_lut
    rgba = bytearray(w * h * 4)
    o = 0
    for i in range(0, len(buf), 2):
        k = (buf[i] | (buf[i + 1] << 8)) << 2   # 565 value * 4
        rgba[o] = lut[k]
        rgba[o + 1] = lut[k + 1]
        rgba[o + 2] = lut[k + 2]
        rgba[o + 3] = lut[k + 3]
        o += 4
    img_data = self._ctx.createImageData(w, h)
    img_data.data.set(rgba)          # single bulk FFI copy
    self._ctx.putImageData(img_data, x, y)
    return (x, y, w, h)
```

Verify on desktop:
- `img_data.data.set(rgba)` relies on MicroPython marshaling the `bytearray` to a
  JS typed array (usual emscripten behaviour). If not, wrap with
  `pyscript.ffi.to_js(rgba)` — still one crossing. This is the linchpin.
- Even-faster variant (more memory): keep the LUT as a `list` of 65,536 four-byte
  `bytes` and build the frame with the C-level join —
  `rgba = b"".join([lut[v] for v in array("H", buf)])` (`from array import array`;
  `array('H', buf)` reads 16-bit LE units).
- Endianness: both assume little-endian RGB565 (matches `requires_byteswap=False`
  and today's `color_rgb`); rebuild the LUT if byte order is ever swapped.
- `fill_rect`/`pixel` are already fine — only `blit_rect` needs this.
- If full-frame redraws are still heavy after the LUT, blit only dirty regions or
  keep a persistent backing `ImageData`/`OffscreenCanvas` — but measure first.

### H. Noisy `console.log` from pointer events
`PSDevices._on_move/_on_down/_on_up` log on every mouse event, flooding the
console and the on-page `#log` panel. Gate behind a debug flag in
`psdisplay.py`.

### I. Runtime fetches from GitHub
Every page `mip.install`s from `github:PyDevices/...` at Run time, so demos need
network access and the first run is slow. To go offline-friendly, pre-mount the
example files via `pyscript.toml` `[files]` like the add-ons.

## Open question for desktop session

Examples marked `queued, sync`, `sync` or `NA` were intentionally left out —
they require a synchronous multimer backend and won't run under PyScript's async
loop without an async rewrite. If any are worth porting, add an async variant
and they will be picked up automatically by the generator.
