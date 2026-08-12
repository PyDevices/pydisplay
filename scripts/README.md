# pydisplay scripts

These scripts maintain the examples, utility manifests, documentation, and
PyScript/PWA gallery. Product publishing scripts live in sibling
`micropython-hardware`.

## GitHub Actions

| Workflow | Trigger | Purpose |
|---|---|---|
| `manifests.yml` | relevant source/config paths + manual | Verify example, utility, and gallery manifests |
| `tests.yml` | examples, utils, tests, scripts, gallery + manual | Run pydisplay tests against canonical hardware packages |
| `docs.yml` | docs, MkDocs config/helpers + manual | Verify the integration docs build |
| `deploy-pyscript.yml` | gallery/example paths + manual | Assemble and publish the browser showcase |

pydisplay has no package-release workflow. Tags here do not publish reusable
libraries. Core TestPyPI and MIP releases are tagged and published from
`micropython-hardware`; companion repos publish their own prefixed distributions.

## Normal maintenance

After adding, removing, or renaming examples or utilities:

```bash
./scripts/install_refresh_manifests.sh --audit
./scripts/install_refresh_manifests.sh
python scripts/gallery_generator.py
python scripts/gallery_generator.py --check
```

`install_gen_manifests.py` enumerates pydisplay examples/utilities and the
canonical sibling `micropython-hardware/lib/eventsys` source. The gallery keeps
the historical virtual URL `./src/lib/eventsys/...`, but pydisplay does not own
a second eventsys copy. The local server and Pages workflow map that URL to the
hardware source.

Normal gallery generation captures missing 240×320 thumbnails. Existing
`web/pyscript/thumbnails/*.png` files are preserved; `--check` never launches
examples.

## Script groups

| Prefix | Scripts | Purpose |
|---|---|---|
| `install_` | `install_gen_manifests.py`, `install_refresh_manifests.sh` | Example/helper manifests and gallery mounts |
| `pyscript_` | cache/version helpers | Build the deployable PWA |
| `mkdocs_` | reference/notebook generators | Build pydisplay integration docs |
| `gen_` | `gen_package_pyi.sh` | Generate editor stubs from canonical sibling product sources |

## Package ownership

Generated `packages/examples.json` and `packages/utils.json` belong here. The
manual Peter Hinch integration manifests also remain here:

- `micropython-micro-gui.json`
- `micropython-nano-gui.json`
- `micropython-touch.json`

Core packages (`displaydev`, `audiodev`, `events`, `keys`, `multimer`, and
optional `eventsys`) come from the unprefixed PyDevices MIP index or prefixed
TestPyPI distributions. Board configs and drivers come from
micropython-hardware. Companion packages (`pygraphics`, `palettes`, `pdwidgets`,
and LVGL) come from their own repositories.

## Publishing names

TestPyPI distributions use `pydevices-*`; imports and MIP names stay unprefixed.
The gallery URL generator follows the same rule: Pyodide dependencies are
rewritten to prefixed wheel names, while MicroPython dependencies use unprefixed
MIP names.
