# SPDX-License-Identifier: MIT
"""PI4IOE5V6408 I2C GPIO expander (M5Stack Tab5 LCD reset path)."""

from machine import I2C

_REG_CHIP_RESET = 0x01
_REG_IO_DIR = 0x03
_REG_OUT_SET = 0x05
_REG_OUT_H_IM = 0x07
_REG_PULL_SEL = 0x0D
_REG_PULL_EN = 0x0B

# Tab5 PI4IOE1 @ 0x43 — LCD reset on expander bit 7 (per M5Stack / CircuitPython board.c).
TAB5_PI4IOE1_ADDR = 0x43
TAB5_LCD_RESET_BIT = 7


def tab5_init_lcd_reset(i2c: I2C, address: int = TAB5_PI4IOE1_ADDR) -> None:
    """Program Tab5 PI4IOE expander and pulse LCD reset (ILI9881C / early Tab5 panels)."""
    i2c.writeto_mem(address, _REG_CHIP_RESET, b"\xff")
    i2c.writeto_mem(address, _REG_IO_DIR, bytes([0b01111111]))
    i2c.writeto_mem(address, _REG_OUT_H_IM, b"\x00")
    i2c.writeto_mem(address, _REG_PULL_SEL, bytes([0b01111111]))
    i2c.writeto_mem(address, _REG_PULL_EN, bytes([0b01111111]))
    i2c.writeto_mem(address, _REG_OUT_SET, bytes([0b01110110]))
