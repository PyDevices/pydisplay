"""Wokwi pydisplay — bundle + testris (optional add_ons + examples)."""

import network
import time

print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect("Wokwi-GUEST", "")
while not sta_if.isconnected():
    print(".", end="")
    time.sleep(0.1)
print(" Connected!")

import mip  # noqa: E402

mip.install("github:PyDevices/pydisplay/sim/wokwi/pydisplay-bundle.json", target=".")
# mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
# mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
mip.install(
    "github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3",
    target=".",
)  # last — root board_config.py
mip.install(
    "github:PyDevices/pydisplay/src/examples/testris.py",
    target=".",
)

# isort: off
import lib.path  # noqa: E402
import testris  # noqa: E402
# isort: on
# Full catalog: import hello, bmp565_simpletest, pydisplay_demo_async, etc. after uncommenting above
