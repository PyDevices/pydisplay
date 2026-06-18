"""Minimum pydisplay install on Wokwi — displaysys, eventsys, board config, hello."""

import mip

mip.install("github:PyDevices/pydisplay/packages/displaysys.json")
mip.install("github:PyDevices/pydisplay/packages/eventsys.json")
mip.install("github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3")
mip.install("github:PyDevices/pydisplay/src/lib/path.py")

import hello  # noqa: E402
import path  # noqa: E402
