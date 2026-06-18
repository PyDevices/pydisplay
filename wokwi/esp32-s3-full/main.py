"""Full pydisplay install on Wokwi — matches installer.py with Wokwi board config."""

import mip

mip.install("github:PyDevices/pydisplay/installer.py")

from installer import install  # noqa: E402

install("pydisplay-bundle")
install("/packages/add_ons.json", target="./add_ons")
install("/packages/examples.json", target="./examples")
install(
    "/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3",
    target="./",
)
install("/src/lib/path.py", target="./")

import hello  # noqa: E402
import path  # noqa: E402
