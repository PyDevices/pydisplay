# PyScript

Experimental browser support via [PyScript](https://pyscript.net/) and `displaysys.psdisplay.PSDisplay`.

**Quick start:** [PyScript guide](../guides/pyscript.md) and [Try pydisplay](../try/index.md).

**Installable / offline (major feature):** The live gallery is a [Progressive Web App](pwa.md). Read [where PWAs run](pwa.md#where-pwas-run) for the host matrix (desktop Chromium, Android Chrome, iOS home screen, TV web). Build your own with the [PyScript PWA guide](../guides/pyscript-pwa.md).

**Asyncio porting:** [PyScript asyncio guide](../guides/pyscript-asyncio.md).

!!! warning "Work in progress"
    PyScript support is experimental. The [browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) ships curated `async` and `all` examples (Run-gated). Other scripts may still use blocking `while True` loops and need asyncio porting — see [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Board config

`board_configs/psdisplay/board_config.py` — 320×480 canvas with `eventsys.Runtime` and PSDevices input.

## Apple mobile (iOS / iPadOS)

There is no native iOS app on the foreseeable roadmap. Use **Mobile Safari** (or another WebKit browser) with the [PyScript gallery](https://PyDevices.github.io/pydisplay/pyscript/), optionally **Add to Home Screen** as a [PWA](pwa.md#apple-mobile-ios--ipados).

## Smart TVs (webOS / Tizen)

Browser / PyScript only — see [PWA — Smart TVs](pwa.md#smart-tvs-webos--tizen) and the [`tv_remote_menu`](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=tv_remote_menu) example. Do not expect `SDLDisplay` on those OS shells.

## Contributing

Pull requests welcome for `displaysys/psdisplay.py`, asyncio example ports, and files under `web/pyscript/`.
