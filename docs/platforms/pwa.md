# Progressive Web Apps (PWA)

Installable, offline-capable PyScript apps are a **major pydisplay feature** — the same `PSDisplay` demos you open in a browser tab can be installed like a native app on phones, tablets, and desktops.

**Live gallery (already a PWA):** [pydevices.github.io/pydisplay/pyscript/](https://pydevices.github.io/pydisplay/pyscript/)

**How to build one:** [Make your PyScript app a PWA](../guides/pyscript-pwa.md) — this page is about **where** those apps run and how install UX differs by host.

---

## What you get

| Capability | Notes |
|------------|--------|
| **In-browser** | Tab or window — no install required |
| **Installable** | Home screen / app launcher icon when the host supports it |
| **Standalone window** | Chromium `display: "standalone"` hides browser chrome after install |
| **Offline (after first visit)** | Service worker caches shell + runtime; run each demo once online so WASM/packages land in cache |
| **Same Python** | MicroPython or Pyodide via PyScript; drawing still goes through `PSDisplay` |

A PWA is still a website on HTTPS. Python runs inside the page; the browser owns install, caching, and the launcher icon.

---

## Where PWAs run

| Host | Install UX | Typical result | Notes |
|------|------------|----------------|-------|
| **Chrome / Edge (Windows, macOS, Linux)** | Address-bar install icon or **Install app**; `beforeinstallprompt` | Standalone app window | Best-supported desktop path |
| **Chrome on Android** | **Install app** / Add to Home screen | Launcher icon; standalone | Phone/tablet web install — not the same as the [Android APK](android.md) |
| **Chromebook (Chrome OS)** | Same as desktop Chrome | Launcher / shelf icon | Treat as Chromium desktop |
| **Safari on iOS / iPadOS** | **Share → Add to Home Screen** (no programmatic prompt) | Home-screen icon; opens fullscreen-ish WebKit | See [Apple mobile](#apple-mobile-ios--ipados) |
| **Firefox / Safari (desktop)** | Limited or no Chromium-style install prompt | Often stays a bookmark / tab | Gallery still runs in-tab; install polish is Chromium-first |
| **LG webOS / Samsung Tizen (TV browsers)** | Host web app / browser only | In-browser or platform web-app packaging | **Web path only** — no native `SDLDisplay` on TV OS shells |

!!! tip "Try the live gallery"
    Open the [PyScript gallery](https://pydevices.github.io/pydisplay/pyscript/) on the device you care about, then use that host’s install path from the table.

---

## Install UX differences

### Chromium (`beforeinstallprompt`)

Chrome and Edge (desktop and Android) can fire `beforeinstallprompt`. The gallery **Install app** button calls that API when available. Uninstall an earlier install of the same origin if the prompt never appears — browsers suppress it for already-installed scopes.

### iOS / iPadOS (no install API)

Safari never fires `beforeinstallprompt`. The gallery button shows a short **Share → Add to Home Screen** tip instead. That is expected, not a bug.

### Standalone vs browser tab

| Mode | What the user sees |
|------|--------------------|
| **Tab** | Normal browser chrome; URL bar visible |
| **Installed standalone** | App-like window; gallery keeps same-origin demo links in one window (Chromium would otherwise open a new app window for `target="_blank"`) |

Details and manifest/`pwa.js` behavior: [PWA guide — wire pages](../guides/pyscript-pwa.md#step-3--wire-your-html-pages).

---

## Offline and storage

1. Visit **once online** and click **Run** on a demo so PyScript/Pyodide (and packages) download.
2. The service worker caches the shell and subsequent CDN/runtime responses.
3. Later offline reloads work for cached assets; first-run or uncached demos still need the network.

Storage can reach tens to hundreds of MB. Prefer stale-while-revalidate over precaching every WASM blob — see the [PWA guide](../guides/pyscript-pwa.md).

Deploy-time `CACHE_NAME` hashing and the July 2026 legacy-cache migration are documented in [Orphaned service workers and cache migration](../guides/pyscript-pwa.md#orphaned-service-workers-and-cache-migration).

---

## PWA vs native Android APK

| | **PWA (this page)** | **Android APK** |
|--|---------------------|-----------------|
| Runtime | PyScript in the browser / WebView | CPython in [pydisplay_android](https://github.com/PyDevices/pydisplay_android) |
| Display | `PSDisplay` | `SDLDisplay` + `usdl2` |
| Distribution | HTTPS URL + install/home screen | Play / sideload APK |
| Best for | Zero-install demos, cross-OS shareable links, offline gallery | Store packaging, deeper device integration |

Phone Android APK notes: [Android platform guide](android.md). Android TV / Fire OS packaging is a separate pursue track on the org roadmap — still SDL/APK, not this PWA story.

---

## Apple mobile (iOS / iPadOS)

There is **no** native iOS pydisplay app on the foreseeable roadmap. Apple phones and tablets use:

- **Mobile Safari** (or another WebKit browser) → [PyScript gallery](https://pydevices.github.io/pydisplay/pyscript/) in a tab, and/or
- **Add to Home Screen** → installed PWA-style icon launching the same `PSDisplay` site.

That is the supported Apple mobile path: browser + optional home-screen install, not App Store packaging.

---

## Smart TVs (webOS / Tizen)

LG webOS and Samsung Tizen ship Chromium-based browsers and encourage **web apps**. pydisplay’s TV story is the same PyScript/`PSDisplay` stack (large UI, remote keys) — **not** a native SDL build on those OS shells. A hosted gallery or TV web-app package can reuse the PWA assets; treat installability as host-specific.

**Example:** [`tv_remote_menu`](https://pydevices.github.io/pydisplay/pyscript/micropython.html?modules=tv_remote_menu) — large-row D-pad menu. Remote key notes: [`web/pyscript/tv/README.md`](https://github.com/PyDevices/pydisplay/blob/main/web/pyscript/tv/README.md).

TV Back (`BrowserBack` / `GoBack` / `Back`) maps to `K_AC_BACK` in `eventsys.keys` so quit matches Android remotes.

Native Android TV / Fire OS APKs are separate — see [Android TV / Fire OS](android.md#android-tv--fire-os).

---

## Related

| Doc | Role |
|-----|------|
| [PyScript platform notes](pyscript.md) | Board config, experimental status, contribution pointers |
| [Make your PyScript app a PWA](../guides/pyscript-pwa.md) | Manifest, service worker, COI, deploy, troubleshooting |
| [Portability & platforms](index.md) | Full runtime × target matrix |
| [Android](android.md) | Native APK path (contrast with PWA) |
| [Try pydisplay](../try/index.md) | Live demo links |
