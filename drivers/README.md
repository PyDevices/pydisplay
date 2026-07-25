# drivers — moved

Hardware drivers and their MIP package manifests live in the sibling repo
**[PyDevices/micropython-hardware](https://github.com/PyDevices/micropython-hardware)**
(`drivers/`, `packages/`).

```text
~/gh/pydevices/micropython-hardware/drivers/
~/gh/pydevices/micropython-hardware/packages/   # spibus, i80bus, tt21100, …
```

```python
mip.install("github:PyDevices/micropython-hardware/packages/spibus.json")
```
