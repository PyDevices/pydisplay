# CPython desktop

CPython uses the same `displaydev` interfaces and examples as embedded targets.
The desktop board config is published by micropython-hardware in the
`pydevices-desktop` TestPyPI distribution.

## Install

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay
python3 -m venv .venv
.venv/bin/pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ -r requirements.txt
cd src
../.venv/bin/python examples/pydisplay_demo.py
```

`AutoDisplay` selects WinDisplay on supported Windows hosts, PGDisplay when
`pygame-ce` is available, and otherwise SDLDisplay through `usdl2`.

## Linux and WSL

Install SDL2 and venv support before the Python packages:

```bash
sudo apt update
sudo apt install libsdl2-dev python3-venv
```

Fedora uses `SDL2-devel`; macOS users can install `sdl2` with Homebrew. Headless
CI can set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`.

## Windows

Install Python from python.org and use the same two-index pip command with
`.venv\Scripts\python.exe`. `pygame-ce` is generally the easiest window backend.
WSL is also supported for the Linux workflow.

## Editable source checkout

Clone `micropython-hardware` beside `pydisplay` and put these canonical trees on
`PYTHONPATH`:

```bash
cd pydisplay/src
export PYTHONPATH=.:utils:../../micropython-hardware/lib:../../micropython-hardware/utils:../../micropython-hardware/drivers/display:../../micropython-hardware/drivers/audio
python3 examples/pydisplay_demo.py
```

To select a specific host config, add the desired
`micropython-hardware/board_configs/...` directory before the other entries.

| Config | Display |
|---|---|
| `board_configs/desktop` | AutoDisplay |
| `board_configs/sdldisplay` | SDLDisplay |
| `board_configs/pgdisplay` | PGDisplay |
| `board_configs/windisplay` | WinDisplay |

## Runtime and timers

The board config exports host input and `timer_async` preferences but no
runtime. Non-LVGL examples instantiate optional eventsys through `app_runtime`;
LVGL examples use `display_driver`.

`multimer` selects an appropriate host backend. It avoids mixing the SDL timer
backend into pygame processes and falls back to threading or polling where
needed. See [multimer](../concepts/multimer.md) for the detailed matrix.

## MicroPython and CircuitPython on Unix

Use the same source layout with `MICROPYPATH` and the desired interpreter. The
desktop MIP board package supplies `board_config.py` and `usdl2.py` when a native
`usdl2` module is not frozen into the firmware.

## Linux KMS

For Linux without X11/Wayland, install the
`board_configs/sdldisplay/linux_kms` board config. It sets
`SDL_VIDEODRIVER=kmsdrm` before SDL initializes. The host needs an SDL build with
KMSDRM support, access to `/dev/dri`, and no competing DRM master.

| Path | Selection | Use case |
|---|---|---|
| Normal desktop | X11/Wayland default | Desktop session |
| KMS | `SDL_VIDEODRIVER=kmsdrm` | Direct scanout without a window manager |
| Headless CI | `SDL_VIDEODRIVER=dummy` | Automated tests |

## Input

Mouse input maps to touch-style events. Keyboard, encoder, and joystick adapters
use the same application-facing event model as embedded boards.
