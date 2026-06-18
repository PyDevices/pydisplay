# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

from sys import implementation, platform

from machine import Pin as _Pin

if platform == "pyboard":
    import stm

    gpio_data = {
        "pyboard": {
            "BSRR": stm.GPIO_BSRR,
        }
    }
else:
    gpio_data = {
        "esp32": {
            "SET": 0x8,
            "CLR": 0xC,
            "gpios": {
                "esp32s3": (0x60004000, 0x6000400C),
                "esp32c3": (0x60004000, 0x6000400C),
                "esp32c2": (0x60004000, 0x6000400C),
                "esp32p4": (0x60091000, 0x6009100C),
                "esp32c6": (0x60091000, 0x6009100C),
                "esp32c5": (0x60091000, 0x6009100C),
                "esp32h2": (0x60091000, 0x6009100C),
                "esp32s2": (0x3F404000, 0x3F40400C),
                "*": (0x3FF44000, 0x3FF4400C),
            },
        },
        "samd": {
            "SET": 0x18,
            "CLR": 0x14,
            "gpios": {
                "samd21": (0x41004400, 0x41004480),
                "samd51": (0x41008000, 0x41008080, 0x41008100, 0x41008180),
            },
        },
        "rp2": {
            # See 3.1.11 at https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
            "SET": 0x14,
            "CLR": 0x18,
            "gpios": {
                "rp2040": (
                    # The SIO registers start at a base address of 0xd0000000 (defined as SIO_BASE in SDK).
                    0xD0000000,
                ),
            },
        },
        "nrf": {
            "SET": 0x8,
            "CLR": 0xC,
            "gpios": {
                "nrf5": (0x50000000, 0x50000300),
                "nrf9": (0x40842000,),
            },
        },
        "mimxrt": {
            "SET": 0x84,
            "CLR": 0x88,
            "gpios": {
                "mimxrt10": (
                    0x401B8000,
                    0x401BC000,
                    0x401C0000,
                    0x401C4000,
                    0x400C0000,
                    0x42000000,
                    0x42004000,
                    0x42008000,
                    0x4200C000,
                ),
                "mimxrt11": (
                    0x4012C000,
                    0x40130000,
                    0x40134000,
                    0x40138000,
                    0x4013C000,
                    0x40140000,
                    0x40C5C000,
                    0x40C60000,
                    0x40C64000,
                    0x40C68000,
                    0x40C6C000,
                    0x40C70000,
                    0x40CA0000,
                ),
            },
        },
        "renasas-ra": {
            "BSRR": 0x8,
            "gpios": {
                "ra6m5": (
                    0x40080000,
                    0x40080020,
                    0x40080040,
                    0x40080060,
                    0x40080080,
                    0x400800A0,
                    0x400800C0,
                    0x400800E0,
                    0x40080100,
                    0x40080120,
                    0x40080140,
                    0x40080160,
                ),
                "*": (
                    0x40040000,
                    0x40040020,
                    0x40040040,
                    0x40040060,
                    0x40040080,
                    0x400400A0,
                    0x400400C0,
                    0x400400E0,
                    0x40040100,
                    0x40040120,
                ),
            },
        },
    }


def _init_module():
    data = gpio_data[platform.lower()]
    if "BSRR" in data:
        GPIO_Pin.BSRR = data["BSRR"]
    else:
        GPIO_Pin.SET = data["SET"]
        GPIO_Pin.CLR = data["CLR"]

    if hasattr(_Pin, "gpio"):  # If the gpio method is already implemented
        return

    # Convert to lowercase and remove - and _ from sys.implementation._machine
    # which is in the format "Generic ESP32S3 module with ESP32S3"
    machine = implementation._machine.lower().replace("-", "").replace("_", "")
    for mcu, gpios in data["gpios"].items():  # Find the GPIOs for the current machine
        if mcu in machine:  # If the mcu is in the machine name
            GPIO_Pin._gpios = gpios  # Set the GPIOs and break
            break
    if GPIO_Pin._gpios is None:  # If the GPIOs are not set
        if "*" in data["gpios"]:  # If there is a wildcard
            GPIO_Pin._gpios = data["gpios"]["*"]  # Set the GPIOs to the wildcard
        else:
            raise NotImplementedError(
                f"class GPIO_Pin not implemented for {platform} on {machine}"
            )


class GPIO_Pin(_Pin):
    """
    GPIO_Pin is a subclass of machine.Pin that provides additional methods for
    accessing the GPIO registers on a microcontroller. It is used by the
    I80Bus class to control the GPIO pins that are used to communicate with
    the display.
    """

    PPP = None
    SET = None
    CLR = None
    BSRR = None
    _gpios = None

    def __init__(self, id, *args, **kwargs):
        if hasattr(id, "names"):
            id = id.names()[1]
        super().__init__(id, *args, **kwargs)
        self._id = id if isinstance(id, int) else None
        if self.BSRR is None:
            self.PPP = 32
        else:
            self.PPP = 16

    def pin(self):
        """
        Returns the pin number in the port of the GPIO pin.

        Returns:
            int: The pin number in the port of the GPIO pin
        """
        if hasattr(super(), "pin"):
            return super().pin()
        if isinstance(self._id, int):
            return self._id & (self.PPP - 1)
        raise NotImplementedError("GPIO_Pin.pin not implemented for this platform")

    def port(self) -> int:
        """
        Returns the port number of the GPIO pin.

        Returns:
            int: The port number of the GPIO pin.
        """
        if hasattr(super(), "port"):
            return super().port()
        if isinstance(self._id, int):
            return self._id // self.PPP
        raise NotImplementedError("GPIO_Pin.port not implemented for this platform")

    def gpio(self) -> int:
        """
        Returns the address of the GPIO pin.

        Returns:
            int: The address of the GPIO pin.
        """
        if hasattr(super(), "gpio"):
            x = super().gpio()  # returns as signed int
            if x < 0:  # if it is negative
                x = x + (1 << 31)  # convert it to unsigned int
            return x
        return self._gpios[self.port()]


_init_module()
