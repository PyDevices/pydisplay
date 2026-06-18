# MicroPython firmware for Wokwi VS Code

Wokwi VS Code simulations need a MicroPython firmware binary. **Do not commit `.bin` files** to this repo.

## Download

Copy the ESP32-S3 generic firmware from the official Wokwi MicroPython example:

```bash
mkdir -p wokwi/firmware
curl -L -o wokwi/firmware/ESP32_GENERIC_S3.bin \
  https://github.com/wokwi/wokwi-vscode-micropython/raw/main/esp32-s3/ESP32_GENERIC_S3-20251209-v1.27.0.bin
```

Update the filename in each project's `wokwi.toml` if you use a different version.

## Wokwi.com

Browser simulations on [wokwi.com](https://wokwi.com) use built-in MicroPython firmware — you only need `main.py` and `diagram.json` from the project folder.
