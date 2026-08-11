# Tests

Stdlib `unittest` for pydisplay-owned packages: [`eventsys`](../src/lib/eventsys)
and `src/utils`, plus gallery/tooling helpers.

`displaydev`, `multimer`, `events`, `keys`, `boarddev`, `audiodev`, and
portable `utils` (`mip`, `byteswap`, …) are tested in
[micropython-hardware](https://github.com/PyDevices/micropython-hardware)
(`tests/`). This suite still needs a sibling (or nested) hardware checkout so
`eventsys` can import `events`, `keys`, and `multimer`.

[`_env.py`](_env.py) puts `src/lib`, `src/utils`, and hardware `lib/` +
`utils/` on `sys.path`.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

## What is covered

| Module | Area |
|--------|------|
| `test_devices.py` | `Runtime` and Queue/Touch/Encoder/Keypad devices |
| `test_joystick.py` | `JoystickDevice` with a mock driver |
| `test_eventsys_quit.py` | quit chords via `HostEventsDevice` |
| `test_eventsys_capabilities.py` | eventsys capability flags |
| `test_eventsys_interactive.py` | interactive / REPL runtime helpers |
| `test_auto_refresh.py` | runtime-owned display auto-refresh (uses `multimer`) |
| `test_standalone.py` | `eventsys` imports with none of the rest of pydisplay on the path |
| `test_audio_utils.py` | `src/utils/audio.py` mixer/notes (not `audiodev`) |
| `test_url_maker.py` | PyScript URL helpers |
| `test_gallery_frame.py` / `test_gallery_screenshots.py` | gallery generator |
| `test_screenshot_tool.py` / `test_record_tool.py` | desktop screenshot/record tools |
| `test_peterhinch_page.py` | Peter Hinch gallery page |

Device tests drive `poll()` with scripted `read` callbacks from
[`_support.py`](_support.py), so they run without hardware.
