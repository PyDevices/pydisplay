# drivers — moved

Hardware drivers live in the sibling repo
**[PyDevices/micropython-hardware](https://github.com/PyDevices/micropython-hardware)**
(`drivers/`).

```text
~/gh/pydevices/micropython-hardware/drivers/
```

MIP package manifests under pydisplay `packages/` (e.g. `spibus.json`,
`tt21100.json`) still install from here for convenience; their `urls` point at
`micropython-hardware`.
