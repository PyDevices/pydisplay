# Tests

Self-contained tests for the standalone [`eventsys`](../src/lib/eventsys) package.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest tests.test_keys -v
# or
python tests/test_keys.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_events.py` | the `events` types/classes and `eventsys.custom_type` |
| `test_devices.py` | `Broker` and the `Queue`/`Touch`/`Encoder`/`Keypad` devices plus `devices.custom_type` |
| `test_keys.py` | the `Keys` key/modifier tables and `keyname`/`key`/`modname`/`mod` helpers |
| `test_standalone.py` | proves `eventsys` imports and runs with **none** of the rest of pydisplay (and no `micropython` shim) on the path |

The device tests drive each device through its `poll()` method using small
scripted `read` callbacks from [`_support.py`](_support.py), so they run
identically on every host without any hardware.
