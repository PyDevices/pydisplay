WOKWI = False
TARGET = "/tmp/lib"

if WOKWI:
    import wifi

    wifi.connect_from_secrets()
    TARGET = "lib"


import mip

MICROPYTHON_LIB = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
HARDWARE = "github:PyDevices/micropython-hardware"
PYDISPLAY = "github:PyDevices/pydisplay"

# index= is required so bare deps like "displaydev" resolve from PyDevices MIP
# (not micropython.org). displaydev → eventsys → multimer via package deps.
mip.install(
    HARDWARE + "/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/",
    index=MICROPYTHON_LIB,
    target=TARGET,
)
# mip.install("pygraphics", index=MICROPYTHON_LIB, target=TARGET)
mip.install(PYDISPLAY + "/src/examples/testris.py", target=TARGET)

# isort: off
if WOKWI:
    import testris
