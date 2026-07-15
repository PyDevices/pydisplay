# Make your PyScript app a Progressive Web App (PWA)

**Who:** You host a pydisplay (or other PyScript) demo on GitHub Pages — or any HTTPS origin — and want users to install it like a native app and run it offline after the first visit.

**Prerequisites:** A working PyScript HTML shell (see [PyScript guide](pyscript.md)). Basic familiarity with browser DevTools.

**Live reference:** The [pydisplay PyScript gallery](https://pydevices.github.io/pydisplay/pyscript/) is a PWA. Open DevTools → **Application** to inspect its manifest and service worker, or click **Install app** in the header.

---

## What a PWA is (and what Python does)

A **Progressive Web App** is still a website. Browsers treat it as installable when three pieces are in place:

| Requirement | Purpose |
|-------------|---------|
| **HTTPS** (or `localhost` for dev) | Secure origin; required for service workers |
| **Web app manifest** (`manifest.json`) | Name, icons, theme colors, launch URL, display mode |
| **Service worker** (`sw.js`) | Background script that can cache assets and enable offline use |

Python runs **inside** the page via PyScript/Pyodide. It does not replace the manifest or service worker — those are standard web files served alongside your HTML.

```mermaid
flowchart LR
  subgraph browser [Browser]
    HTML[HTML shell]
    Manifest[manifest.json]
    SW[sw.js service worker]
    PyScript[PyScript / Pyodide runtime]
    App[Your Python example]
  end
  HTML --> PyScript --> App
  HTML --> Manifest
  HTML --> SW
  SW -->|cache| HTML
  SW -->|cache| PyScript
```

---

## PyScript-specific constraints

PyScript demos are heavier than typical static sites. Plan for these up front.

### SharedArrayBuffer needs Cross-Origin Isolation (COI)

MicroPython and Pyodide in the browser often need `SharedArrayBuffer`. That requires **cross-origin isolated** pages (`Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` headers).

GitHub Pages does **not** send those headers by default. The pydisplay gallery solves this in **one** service worker (`web/pyscript/sw.js`) that:

1. Intercepts fetches and adds COI headers to responses.
2. Caches gallery assets for offline use.

!!! important "One service worker per scope"
    A given URL path can only have **one** active service worker. If you already register a worker (for example `mini-coi-fd.js` for COI), merge COI and PWA caching into a single `sw.js` instead of registering two scripts.

### Register the worker before PyScript boots

COI must be active before the runtime tries to allocate `SharedArrayBuffer`. Load `pwa.js` **synchronously in `<head>`**, before `vendor/core.js`:

```html
<script src="./pwa.js"></script>
<script type="module" src="./vendor/core.js"></script>
```

Do **not** use `defer` on `pwa.js` for loader pages (`micropython.html`, `pyodide.html`).

### Offline caching is large

A first online visit downloads PyScript/Pyodide `.wasm` bundles and any packages your demo imports from CDNs. The service worker caches those on the fly. Storage can reach tens to hundreds of MB per demo.

Use **stale-while-revalidate** (serve cache immediately, refresh in background) rather than precaching every runtime file at install time — precaching everything often hits browser storage limits on first load.

---

## Files you need

For a pydisplay-style deployment under `web/pyscript/`, these are the PWA files in this repository:

| File | Role |
|------|------|
| [`manifest.json`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/manifest.json) | Install metadata |
| [`sw.js`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/sw.js) | COI headers + offline cache |
| [`pwa.js`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/pwa.js) | Register `sw.js`, install button, offline toast |
| [`pwa.css`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/pwa.css) | Styles for install button and toast |
| `icon-192.png`, `icon-512.png` | Launcher icons (PNG; manifest requires raster icons) |

Gallery pages that include the full PWA UI: `index.html`, `micropython.html`, `pyodide.html`. Minimal shells (`simple.html`, `repl.html`, `embed.html`) link the manifest and load `pwa.js` without the install button.

---

## Step 1 — Create `manifest.json`

Place `manifest.json` next to your HTML entry point (same directory or adjust paths).

### Gallery app (many demos, one install icon)

Use when users install the **whole demo hub** and pick a demo from the grid:

```json
{
  "name": "PyDevices pydisplay",
  "short_name": "pydisplay",
  "description": "Cross-platform display and event drivers — PyScript demos in your browser.",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "background_color": "#100e0b",
  "theme_color": "#f54e00",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

### Single-demo app (one install icon opens one module)

Use when the installed app should **always** launch the same demo, including query parameters:

```json
{
  "name": "pydisplay demo",
  "short_name": "Demo",
  "description": "Flagship pydisplay board_config demo in the browser.",
  "start_url": "./micropython.html?modules=pydisplay_demo",
  "scope": "./",
  "display": "standalone",
  "background_color": "#100e0b",
  "theme_color": "#f54e00",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

!!! tip "`start_url` and `scope`"
    - **`scope`** — URL prefix the PWA owns. Usually `"./"` for everything under `web/pyscript/`.
    - **`start_url`** — page opened when the user taps the home-screen icon. Include `?modules=` or `?manifests=` when you want a fixed entry demo.
    - Paths are relative to the manifest file location.

### Icons

Provide at least **192×192** and **512×512** PNG files. Maskable icons (safe zone in the center) improve Android adaptive icons.

You can adapt the [PyDevices logo SVG](https://github.com/PyDevices/pydisplay/blob/main/web/vendor/pydevices-chrome/logo.svg) or export PNGs from any design tool. The gallery icons live at `web/pyscript/icon-192.png` and `web/pyscript/icon-512.png`.

---

## Step 2 — Create `sw.js` (service worker)

The service worker runs in the background. It can cache responses and, for PyScript, inject COI headers.

### Minimal structure

1. **`install`** — precache a small **shell** of HTML/CSS/JS you control (not the entire Pyodide tree).
2. **`activate`** — delete caches from older versions when you bump `CACHE_NAME`.
3. **`fetch`** — cache-first with background revalidation for your origin and known CDN hosts; add COI headers where needed.

Key constants from the pydisplay worker:

```javascript
const CACHE_NAME = 'pydisplay-pwa-v1';  // bump when cache layout changes

const STATIC_ASSETS = [
  './index.html',
  './micropython.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './site.css',
  './pwa.js',
  // add your shell files; avoid listing every vendor/*.js
];

const RUNTIME_ORIGINS = [
  'pyscript.net',
  'cdn.jsdelivr.net',
  'pyodide.org',
  'pydevices.github.io',
];
```

### COI header helper

```javascript
function withCoiHeaders(response) {
  const { body, status, statusText } = response;
  if (!status || status > 399) return response;
  const headers = new Headers(response.headers);
  headers.set('Cross-Origin-Opener-Policy', 'same-origin');
  headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
  headers.set('Cross-Origin-Resource-Policy', 'cross-origin');
  return new Response(status === 204 ? null : body, { status, statusText, headers });
}
```

Apply `withCoiHeaders` to **same-origin** responses (and shell assets) so `SharedArrayBuffer` works after the worker controls the page.

### Caching strategy

| Asset type | Strategy |
|------------|----------|
| Your HTML, CSS, `manifest.json`, icons | Precache in `install` + stale-while-revalidate |
| `vendor/` PyScript bundles | Cache on first network fetch; do not `cache.addAll` the whole tree |
| CDN packages (jsDelivr, pyscript.net, …) | Stale-while-revalidate per request URL |
| POST / non-GET | Do not cache |

After deploying a new `sw.js`, bump `CACHE_NAME` so `activate` drops obsolete entries.

See the full implementation: [`web/pyscript/sw.js`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/sw.js).

---

## Step 3 — Link the manifest and register the worker

In every HTML page that should participate in the PWA, add to `<head>`:

```html
<link rel="manifest" href="./manifest.json">
<meta name="theme-color" content="#f54e00">
<link rel="apple-touch-icon" href="./icon-192.png">
<link rel="stylesheet" href="./pwa.css">
<script src="./pwa.js"></script>
```

`pwa.js` registers `./sw.js` immediately (required for COI) and wires optional UI when elements exist.

### Install button (optional)

Add a button anywhere in your layout (the gallery puts it in the header):

```html
<button type="button" class="pwa-install-btn" id="pwa-install-btn">Install app</button>
```

`pwa.js` listens for `beforeinstallprompt`, shows the button, and calls `prompt()` when clicked. Browsers only fire that event when installability criteria are met.

### Offline toast (optional)

No extra HTML is required. `pwa.js` creates a `#pwa-toast` element on first use and shows messages when:

- the service worker finishes its first activation;
- the browser goes online or offline.

Styles are in [`pwa.css`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/pwa.css).

---

## Step 4 — Deploy

### GitHub Pages (this repo)

Pushes to `main` that touch `web/**` or `src/**` run [Deploy PyScript site to GitHub Pages](https://github.com/PyDevices/pydisplay/blob/main/.github/workflows/deploy-pyscript.yml). The workflow:

1. Verifies generated manifests are fresh (`install_refresh_manifests.sh --audit`, `pyscript_gen_packages.py --check`).
2. Copies `web/pyscript/*` into `_site/pyscript/`.
3. Copies `src/lib`, `src/add_ons`, and examples into `_site/pyscript/src/`.
4. Publishes to the `gh-pages` branch.

Before pushing PWA changes, refresh gallery metadata locally:

```bash
./scripts/install_refresh_manifests.sh
python scripts/pyscript_gen_packages.py
```

Commit any updated `packages/*.json` files the scripts produce.

### Other hosts

Any static host works if:

- HTTPS is enabled (Let's Encrypt, Cloudflare, GitHub Pages, etc.).
- `manifest.json`, `sw.js`, and icons are served from the same scope as your HTML.
- `sw.js` is served with `Content-Type: application/javascript` (default on most hosts).

---

## Step 5 — Test installability and offline use

Use Chrome or Edge on desktop, or Chrome on Android. Safari on iOS supports **Add to Home Screen** but not `beforeinstallprompt` (no custom install button).

### Checklist

1. **Manifest**
   - DevTools → **Application** → **Manifest**
   - No errors; icons and `start_url` resolve.

2. **Service worker**
   - DevTools → **Application** → **Service Workers**
   - `sw.js` is activated and controls the page (may require one reload on first visit for COI).

3. **Install**
   - Look for the install icon in the address bar, or your **Install app** button.
   - If you tested an install earlier, **uninstall** the PWA first — browsers suppress `beforeinstallprompt` for already-installed origins.

4. **Offline**
   - Open your demo **once online** and click **Run** so Pyodide/MicroPython and packages download.
   - DevTools → **Network** → enable **Offline**.
   - Reload. The shell and cached runtime should still load; uncached assets fail until you go back online.

5. **COI / SharedArrayBuffer**
   - DevTools → **Console**: no `SharedArrayBuffer` errors after the COI reload cycle.
   - **Application** → check that cross-origin isolation is active (or verify `crossOriginIsolated === true` in the console).

### Example URLs (live gallery)

| Page | URL |
|------|-----|
| Gallery (PWA home) | [pyscript/](https://pydevices.github.io/pydisplay/pyscript/) |
| Flagship demo | [micropython.html?modules=pydisplay_demo](https://pydevices.github.io/pydisplay/pyscript/micropython.html?modules=pydisplay_demo) |
| Calculator | [micropython.html?modules=calc_graphics,calc_engine](https://pydevices.github.io/pydisplay/pyscript/micropython.html?modules=calc_graphics,calc_engine) |

---

## Adapting for your own project

### Fork or copy the PWA bundle

1. Copy `manifest.json`, `sw.js`, `pwa.js`, `pwa.css`, and icon PNGs into your `web/pyscript/` tree (or equivalent).
2. Edit `manifest.json` — name, colors, `start_url`.
3. Edit `STATIC_ASSETS` in `sw.js` — list only pages and styles **you** ship.
4. Add the `<head>` links and `pwa.js` script to your HTML shells.
5. Optionally add `#pwa-install-btn` to your layout.

### Minimal PyScript page (no gallery chrome)

For a single-file demo like [`simple.html`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/simple.html):

```html
<head>
  <link rel="manifest" href="./manifest.json">
  <meta name="theme-color" content="#f54e00">
  <script src="./pwa.js"></script>
  <script type="module" src="./vendor/core.js"></script>
</head>
```

Point `start_url` at that page (or at a parametric loader URL with your module query).

### Parametric loader (`micropython.html` / `pyodide.html`)

The gallery loader accepts:

- `?modules=stem1,stem2` — install `.py` files from `src/examples/`
- `?manifests=name` — install a MIP JSON manifest from `packages/` (via `web/pyscript/packages`)

For a dedicated PWA around one module, set:

```json
"start_url": "./micropython.html?modules=your_module"
```

Users who install get that module every time. To ship multiple installable apps from one repo, use separate manifest files in subfolders (each with its own `scope`) or separate GitHub Pages projects.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| No install prompt / button never appears | Already installed, or manifest/SW invalid | Uninstall PWA; fix manifest errors in DevTools |
| `SharedArrayBuffer` error | COI not active | Ensure one `sw.js` adds COI headers; reload after first SW install |
| Offline reload fails immediately | Demo never run online | Visit once online; click **Run** to pull runtime + packages |
| Storage quota errors | Precache list too aggressive | Shrink `STATIC_ASSETS`; rely on fetch-time caching for WASM |
| Stale content after deploy | Old cache | Bump `CACHE_NAME` in `sw.js` |
| iOS: no custom install button | Safari limitation | Document **Share → Add to Home Screen** for users |
| `micropython.html` 404 on old links | Renamed from `load.html` | Update bookmarks to `micropython.html?modules=…` |

---

## Related docs

- [PyScript local development](pyscript.md) — run the gallery locally, gallery markers, deploy overview
- [PyScript asyncio porting](pyscript-asyncio.md) — make examples work under PyScript's event loop
- [PyScript platform notes](../platforms/pyscript.md) — board config and contribution pointers
- [Try pydisplay](../try/index.md) — live demo links

## Reference (source files)

| Topic | Location |
|-------|----------|
| Manifest | `web/pyscript/manifest.json` |
| Service worker | `web/pyscript/sw.js` |
| Client bootstrap + UI | `web/pyscript/pwa.js`, `web/pyscript/pwa.css` |
| Deploy workflow | `.github/workflows/deploy-pyscript.yml` |
| Gallery generator | `scripts/pyscript_gen_packages.py` |
