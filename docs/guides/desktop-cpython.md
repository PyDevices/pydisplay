# Desktop CPython

Use this path to develop examples on Linux, macOS, or Windows in a local window.

## Dependencies

Install Python 3 and git. The `pydevices-desktop` distribution supplies the
default host board config and portable SDL binding. The install can also use
`pygame-ce` when available. Linux users may need the system `libsdl2` package;
see [CPython desktop](../platforms/cpython-desktop.md).

## First run

--8<-- "_snippets/first-run-desktop.md"

The installed desktop config uses `displaydev.auto.AutoDisplay`: WinDisplay on
supported Windows hosts, then PGDisplay when pygame is available, otherwise
SDLDisplay.

## Source-checkout development

To edit product code and examples together, clone them as siblings:

```text
workspace/
├── pydevices/
└── pydevices-examples/
```

Run from `pydevices-examples/src` after adding the canonical product paths:

```bash
export PYTHONPATH=.:utils:../../pydevices/lib:../../pydevices/utils:../../pydevices/drivers/display:../../pydevices/drivers/audio
python3 examples/pydevices_demo.py
```

`import utils.path` performs the same sibling discovery on targets where setting
an environment variable is inconvenient.

## Input and runtime

Mouse events map to the same event model as touch. The default board config
exports `display_drv` and input readers; `app_runtime` instantiates the optional
`eventsys` coordinator for non-LVGL examples. LVGL examples use the independent
coordinator from `display_driver`.

## Next

- [App starter](../examples/app-starter.md)
- [Architecture](../concepts/architecture.md)
- [Examples](../examples/index.md)
- [ESP32 guide](esp32-board.md)
