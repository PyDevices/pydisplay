# Product package publishing

`pydisplay` is the examples, documentation, and PyScript showcase repository.
It does not publish the core hardware/runtime packages.

The canonical release pipeline lives in
[`micropython-hardware`](https://github.com/PyDevices/micropython-hardware):

- Source: `drivers/display/displaydev`, `drivers/audio/audiodev`, and `lib/`
- MIP sync: `scripts/publish_sync_packages.sh`
- MIP index publication: `scripts/publish_mip_ghpages.sh`
- TestPyPI + MIP workflow: `.github/workflows/publish-pydevices.yml`

## Package names

TestPyPI distributions carry the organization prefix. Imports and MIP package
names do not:

| TestPyPI distribution | Python import / MIP name |
|---|---|
| `pydevices-displaydev` | `displaydev` |
| `pydevices-audiodev` | `audiodev` |
| `pydevices-eventsys` | `eventsys` |
| `pydevices-multimer` | `multimer` |
| `pydevices-events` | `events` |
| `pydevices-keys` | `keys` |
| `pydevices-desktop` | `board_config`, `board_devices`, host adapters |

Sibling projects follow the same rule: `pydevices-pygraphics`,
`pydevices-palettes`, and `pydevices-pdwidgets` are imported or installed by
MIP as `pygraphics`, `palettes`, and `pdwidgets`.

## Install from TestPyPI

TestPyPI is the primary index because PyDevices distributions currently live
there; production PyPI remains the fallback for third-party dependencies:

```bash
python -m pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-desktop pydevices-eventsys pydevices-pygraphics
```

`eventsys` is optional. Non-LVGL example applications use it as their traffic
controller; LVGL uses the runtime implemented by `display_driver`.

## Install with MIP

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install("displaydev", index=INDEX)
mip.install("eventsys", index=INDEX)  # only when the app chooses it
```

For maintainer release commands and validation steps, use
[`micropython-hardware/docs/install-workflows.md`](https://github.com/PyDevices/micropython-hardware/blob/main/docs/install-workflows.md)
and `micropython-hardware/docs/pydevices-desktop.md`.
