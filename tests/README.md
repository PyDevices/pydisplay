# Tests

This suite covers the pydisplay-owned examples, utilities, PyScript gallery,
and developer tooling.

Product-library tests moved with their sources to
[`micropython-hardware/tests`](https://github.com/PyDevices/micropython-hardware/tree/main/tests),
including `eventsys`, `displaydev`, `audiodev`, `multimer`, `events`, `keys`,
and `boarddev`.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The test environment adds the sibling `micropython-hardware` product paths so
the example and tooling tests exercise canonical sources rather than copied
libraries.

## What remains here

- `src/utils/audio.py` mixer and note helpers
- PyScript URL, loader, gallery, and PWA generation
- screenshot and recording tools
- Peter Hinch gallery integration
- example manifest and harness behavior
