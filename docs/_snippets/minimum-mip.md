```python
import mip
INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install("displaydev", index=INDEX)
mip.install("eventsys", index=INDEX)
mip.install("github:PyDevices/pydevices/board_configs/<your_board>")
```

Replace `<your_board>` with a path from [board configs](https://pydevices.github.io/pydevices/board-configs.html).
