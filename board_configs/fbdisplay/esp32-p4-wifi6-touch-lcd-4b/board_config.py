"""Waveshare ESP32-P4-WIFI6-Touch-LCD-4B — 720×720 MIPI DSI + GT911 touch

Product: https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-4b.htm
Wiki:    https://www.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-4B
BSP:     waveshareteam/Waveshare-ESP32-components ``esp32_p4_wifi6_touch_lcd_4b``

4-inch 720×720 IPS panel on MIPI DSI (ST7703 driver IC, 2-lane).  Capacitive
touch uses GT911 over I2C (5-point).  Wi-Fi 6 / BLE 5 is provided by an onboard
ESP32-C6 co-processor via SDIO (not configured here).

Pixel scanout requires a future ``displayif`` MIPI-DSI cmod for ESP32-P4; until
then importing this module raises ``NotImplementedError`` after defining pins
and timings (same pattern as ``fbdisplay/t-rgb_480``).
"""

from machine import I2C, Pin

from gt911 import GT911
import eventsys

# ---------------------------------------------------------------------------
# Board identity
# ---------------------------------------------------------------------------

BOARD_NAME = "ESP32-P4-WIFI6-Touch-LCD-4B"
BOARD_MCU = "ESP32-P4NRW32"
BOARD_VARIANTS = (
    "ESP32-P4-WIFI6-Touch-LCD-4B",  # camera header
    "ESP32-P4-86-Panel-ETH-2RO",  # Ethernet / RS485 / relays (different back box)
)
PRODUCT_URL = "https://www.waveshare.com/esp32-p4-wifi6-touch-lcd-4b.htm"
WIKI_URL = "https://www.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-4B"

# ---------------------------------------------------------------------------
# Display panel (product page + Waveshare BSP)
# ---------------------------------------------------------------------------

DISPLAY_WIDTH = 720
DISPLAY_HEIGHT = 720
DISPLAY_DIAGONAL_IN = 4.0
DISPLAY_TYPE = "IPS"
DISPLAY_COLORS = 16_700_000  # 16.7M
DISPLAY_BRIGHTNESS_CD_M2 = 400
DISPLAY_CONTRAST = 1200
DISPLAY_VIEWING_ANGLE_DEG = 170
DISPLAY_AREA_MM = (71.93, 71.93)
DISPLAY_OUTLINE_MM = (86.5, 86.5)
DISPLAY_PIXEL_PITCH_MM = (0.0999, 0.0999)
DISPLAY_COLOR_FORMATS = ("RGB565", "RGB666", "RGB888")

DISPLAY_CONTROLLER = "ST7703"  # waveshare/esp_lcd_st7703
DISPLAY_BUS = "MIPI-DSI"
DISPLAY_DSI_LANES = 2
DISPLAY_DSI_LANE_BITRATE_MBPS = 1000  # BSP_LCD_MIPI_DSI_LANE_BITRATE_MBPS
DISPLAY_DSI_PHY_LDO_CHAN = 3  # LDO_VO3 → VDD_MIPI_DPHY
DISPLAY_DSI_PHY_LDO_MV = 2500
DISPLAY_COLOR_DEPTH = 16  # default RGB565
DISPLAY_RGB_ORDER = "RGB"
DISPLAY_BIG_ENDIAN = False

LCD_RST = 27
LCD_BACKLIGHT = 26
LCD_BACKLIGHT_PWM_FREQ_HZ = 5000
LCD_BACKLIGHT_INVERTED = True
# Waveshare maps user 0–100 % → hardware 47–100 % duty (LEDC 10-bit).
LCD_BACKLIGHT_MIN_PERCENT = 47

# ST7703_720_720_PANEL_60HZ_DPI_CONFIG (waveshare esp_lcd_st7703.h)
dsi_timings = {
    "dpi_clock_freq_mhz": 38,
    "width": DISPLAY_WIDTH,
    "height": DISPLAY_HEIGHT,
    "hsync_pulse_width": 20,
    "hsync_back_porch": 50,
    "hsync_front_porch": 50,
    "vsync_pulse_width": 4,
    "vsync_back_porch": 20,
    "vsync_front_porch": 20,
}

dsi_bus = {
    "bus_id": 0,
    "num_data_lanes": DISPLAY_DSI_LANES,
    "lane_bit_rate_mbps": DISPLAY_DSI_LANE_BITRATE_MBPS,
}

dsi_dbi = {
    "virtual_channel": 0,
    "lcd_cmd_bits": 8,
    "lcd_param_bits": 8,
}

# SDIO 3.0 TF-card LDO (also used before DSI init in BSP)
SD_LDO_CHAN = 4
SD_LDO_MV = 3300

# ---------------------------------------------------------------------------
# Touch — GT911 capacitive, 5-point (product page)
# ---------------------------------------------------------------------------

TOUCH_CONTROLLER = "GT911"
TOUCH_POINTS = 5
TOUCH_I2C_ADDR = 0x5D  # alternate 0x14; board straps 0x5D
TOUCH_RST = 23
# INT is not routed to the MCU on this board (BSP: GPIO_NC).  Polling only.
# GPIO22 is an unused dummy for the GT911 driver reset sequence.
TOUCH_INT_DUMMY = 22

# ---------------------------------------------------------------------------
# I2C shared bus (Codec ES8311 @0x18, ES7210, GT911)
# ---------------------------------------------------------------------------

I2C_ID = 1  # CONFIG_BSP_I2C_NUM
I2C_SDA = 7
I2C_SCL = 8
I2C_FREQ = 400_000

# ---------------------------------------------------------------------------
# I2S audio — ES8311 playback + ES7210 microphone (echo cancellation)
# ---------------------------------------------------------------------------

I2S_ID = 1
I2S_SCLK = 12
I2S_MCLK = 13
I2S_LRCK = 10
I2S_DOUT = 9  # ASDOUT → DAC
I2S_DIN = 11  # DSDIN ← ADC / ES7210
AUDIO_PA_ENABLE = 53  # active high
AUDIO_CODEC_PLAYBACK = "ES8311"
AUDIO_CODEC_CAPTURE = "ES7210"

# ---------------------------------------------------------------------------
# microSD — SDIO 3.0, 4-bit
# ---------------------------------------------------------------------------

SD_CLK = 43
SD_CMD = 44
SD_D0 = 39
SD_D1 = 40
SD_D2 = 41
SD_D3 = 42
SD_WIDTH = 4
SD_FREQ_DEFAULT_KHZ = 20_000
SD_FREQ_HIGHSPEED_KHZ = 40_000
SD_INTERNAL_PULLUP = True

# ---------------------------------------------------------------------------
# ESP32-C6 Wi-Fi 6 / Bluetooth 5 co-processor (SDIO slave)
# ---------------------------------------------------------------------------

C6_SDIO_CLK = 18
C6_SDIO_CMD = 19
C6_SDIO_D0 = 14
C6_SDIO_D1 = 15
C6_SDIO_D2 = 16
C6_SDIO_D3 = 17
C6_RESET = 54

# ---------------------------------------------------------------------------
# Other onboard signals
# ---------------------------------------------------------------------------

# MIPI CSI camera header (ESP32-P4-WIFI6-Touch-LCD-4B only; 2-lane, 15-pin 1.0 mm)
MIPI_CSI_LANES = 2

# ---------------------------------------------------------------------------
# Runtime wiring
# ---------------------------------------------------------------------------

i2c = I2C(I2C_ID, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)

backlight = Pin(LCD_BACKLIGHT, Pin.OUT, value=1)


def backlight_set(percent):
    """Set backlight 0–100 % (maps to Waveshare 47–100 % hardware range)."""
    percent = max(0, min(100, percent))
    if percent == 0:
        backlight.value(0)
        return
    actual = LCD_BACKLIGHT_MIN_PERCENT + (
        percent * (100 - LCD_BACKLIGHT_MIN_PERCENT)
    ) // 100
    backlight.value(1 if actual > 0 else 0)


touch_drv = GT911(
    i2c,
    reset_pin=TOUCH_RST,
    irq_pin=TOUCH_INT_DUMMY,
    address=TOUCH_I2C_ADDR,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    touch_points=TOUCH_POINTS,
)


def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


touch_rotation_table = (0, 0, 0, 0)

try:
    from mipidsiframebuffer import MIPIFrameBuffer
except ImportError as exc:
    raise NotImplementedError(
        "MIPI DSI scanout requires displayif mipidsiframebuffer cmod (esp32p4 port)"
    ) from exc

fb = MIPIFrameBuffer(
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    reset_pin=LCD_RST,
    backlight_pin=LCD_BACKLIGHT,
    dsi_bus=dsi_bus,
    dsi_dbi=dsi_dbi,
    timings=dsi_timings,
    dsi_phy_ldo_chan=DISPLAY_DSI_PHY_LDO_CHAN,
    dsi_phy_ldo_mv=DISPLAY_DSI_PHY_LDO_MV,
    color_depth=DISPLAY_COLOR_DEPTH,
)

from displaysys.fbdisplay import FBDisplay

display_drv = FBDisplay(fb)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
