# Architecture

pydisplay is a **foundation layer** — display drivers, input events, drawing primitives, and board wiring. It is not a GUI toolkit. Your app (or a third-party GUI library) sits on top.

## Component diagram

```mermaid
flowchart TB
  subgraph config [Configuration]
    BC[board_config.py]
    DD[display driver module]
    TD[touch driver module]
  end
  subgraph core [Core libraries]
    DS[displaysys]
    ES[eventsys]
    GR[graphics optional]
    MT[multimer]
  end
  subgraph app [Your code]
    EX[examples / your app]
    GUI[LVGL Nano-GUI PyWidgets etc]
  end
  BC --> DS
  BC --> ES
  DD --> DS
  TD --> ES
  DS --> EX
  ES --> EX
  MT --> EX
  DS --> GUI
  ES --> GUI
  MT --> GUI
  GR --> EX
  GR --> GUI
```

## What each piece does

| Piece | Role |
|-------|------|
| **`board_config.py`** | Selects display class, wires pins, creates `display_drv` and optional `runtime`. One file per hardware target. |
| **`displaysys`** | Display backends (`BusDisplay`, `SDLDisplay`, `PGDisplay`, `PSDisplay`, `JNDisplay`, `FBDisplay`) with a unified drawing API. |
| **`eventsys`** | `Runtime` polls hardware and enqueues PyGame/SDL2-style events; your loop calls `runtime.poll()`. |
| **`graphics`** | Optional helpers on top of `framebuf` (rounded rects, gradients, `Area` bounding boxes). |
| **`multimer`** | Cross-platform `Timer` / `AsyncTimer`, ticks/sleep, and sync/async main-loop helpers (`run_forever`, `dual_main`). |
| **`add_ons`** | Optional shims and integrations (`framebuf` on CPython, `displaybuf`, `pdwidgets`, config templates). |

## Typical boot sequence

1. Install packages (MIP, clone, or Wokwi `mip.install`).
2. Import or install `board_config.py` for your hardware.
3. `board_config` constructs `display_drv` and `runtime` (or `runtime = None` on display-only MCU boards).
4. Your main loop: draw on `display_drv`, poll input via `runtime` (hosted backends refresh via `Runtime` when `needs_refresh` is true).

```python
from board_config import display_drv, runtime
import eventsys

while not runtime.quit_requested:
    for event in runtime.poll():
        if event.type == eventsys.QUIT:
            break
        ...  # handle touch, keys, etc.
    display_drv.fill_rect(0, 0, 10, 10, 0xF800)
```

Or use `multimer.run_forever(poll=runtime.poll)` — see [Runtime](runtime.md), [multimer](multimer.md), and [Events](events.md).

On desktop, `board_config` selects `PGDisplay` (CPython, PyGame) or `SDLDisplay` (SDL2). On ESP32, `BusDisplay` talks to the panel over SPI or I80. See [Portability & platforms](../platforms/index.md) for the full backend matrix.

For a complete minimal app using this pattern (plus scrolling and timers), see [**pydisplay_demo**](../examples/pydisplay_demo.md).

## Where to go next

- [Displays](displays.md) — pick a display driver class
- [Runtime](runtime.md) — board_config contract, auto-refresh, quit lifecycle
- [Events](events.md) — devices, subscribe, poll loop
- [Board configs](../hardware/board-configs.md) — find or add hardware wiring
- [API reference (core)](../reference/) — method signatures
