```python
import mip
INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install("displaysys", index=INDEX)
mip.install("eventsys", index=INDEX)
mip.install("github:PyDevices/micropython-hardware/board_configs/<your_board>")
```

Replace `<your_board>` with a path from [board configs](https://pydevices.github.io/micropython-hardware/board-configs.html).
