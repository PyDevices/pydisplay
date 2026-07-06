# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_touchscreen`
================================================================================

CircuitPython library for 4-wire resistive touchscreens


* Author(s): ladyada

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""




from analogio import AnalogIn
from digitalio import DigitalInOut

try:
    from typing import Optional, Tuple

    from microcontroller import Pin
except ImportError:
    pass


def map_range(x: float, in_min: int, in_max: int, out_min: int, out_max: int) -> float:
    """
    Maps a number from one range to another.

    .. note:: This implementation handles values < in_min differently
              than arduino's map function does.


    :return: Returns value mapped to new range
    :rtype: float


    """
    mapped = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    if out_min <= out_max:
        return max(min(mapped, out_max), out_min)
    return min(max(mapped, out_max), out_min)


class Touchscreen:
    """A driver for common and inexpensive resistive touchscreens. Analog input
    capable pins are required to read the intrinsic potentiometers

    Create the Touchscreen object. At a minimum you need the 4 pins
    that will connect to the 4 contacts on a screen. X and Y are just our
    names, you can rotate and flip the data if you like. All pins must be
    capable of becoming DigitalInOut pins. :attr:`y2_pin`, :attr:`x1_pin`
    and :attr:`x2_pin` must also be capable of becoming AnalogIn pins.
    If you know the resistance across the x1 and x2 pins when not touched,
    pass that in as 'x_resistance'.
    :attr:`calibration` is a tuple of two tuples, the default is
    ((0, 65535), (0, 65535)). The numbers are the min/max readings for the
    X and Y coordinate planes, respectively. To figure these out, pass in
    no calibration value or size value and read the raw minimum and maximum
    values out while touching the panel.
    :attr:`size` is a tuple that gives the X and Y pixel size of the underlying
    screen. If passed in, we will automatically scale/rotate so touches
    correspond to the graphical coordinate system.

    :param ~microcontroller.Pin x1_pin: Data pin for Left side of the screen.
     Must also be capable of becoming AnalogIn pins.
    :param ~microcontroller.Pin x2_pin: Data pin for Right side of the screen.
     Must also be capable of becoming AnalogIn pins.
    :param ~microcontroller.Pin y1_pin: Data pin for Bottom side of the screen.
    :param ~microcontroller.Pin y2_pin: Data pin for Top side of the screen.
     Must also be capable of becoming AnalogIn pins.
    :param int x_resistance: If you know the resistance across the x1 and x2
     pins when not touched, pass that in as :attr:`x_resistance`
    :param int  samples: change by adjusting :attr:`samples` arg. Defaults to :const:`4`
    :param int z_threshold: We can also detect the 'z' threshold, how much
     its pressed. We don't register a touch unless its higher than :attr:`z_threshold`
    :param (int,int),(int,int) calibration: A tuple of two tuples The numbers are the min/max
     readings for the X and Y coordinate planes, respectively.
     Defaults to :const:`((0, 65535), (0, 65535))`
    :param int,int size: The dimensions of the screen as (x, y).
    :param bool invert_pressure: Whether to invert the pressure values. Some touchscreens and
     drivers may need this to be changed to `False` in order to properly register touches.

    """

    def __init__(
        self,
        x1_pin: Pin,
        x2_pin: Pin,
        y1_pin: Pin,
        y2_pin: Pin,
        *,
        x_resistance: Optional[int] = None,
        samples: int = 4,
        z_threshold: int = 10000,
        calibration: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
        size: Optional[Tuple[int, int]] = None,
        invert_pressure: bool = True,
    ) -> None:
        self._xm_pin = x1_pin
        self._xp_pin = x2_pin
        self._ym_pin = y1_pin
        self._yp_pin = y2_pin
        self._rx_plate = x_resistance
        self._xsamples = [0] * samples
        self._ysamples = [0] * samples
        if not calibration:
            calibration = ((0, 65535), (0, 65535))
        self._calib = calibration
        self._size = size
        self._zthresh = z_threshold
        self.invert_pressure = invert_pressure

    @property
    def touch_point(
        self,
    ) -> Optional[Tuple[int, int, int]]:
        """A tuple that represents the x, y and z (touch pressure) coordinates
        of a touch. Or, None if no touch is detected"""
        z_1 = z_2 = z = None
        with DigitalInOut(self._xp_pin) as x_p:
            x_p.switch_to_output(False)
            with DigitalInOut(self._ym_pin) as y_m:
                y_m.switch_to_output(True)
                with AnalogIn(self._xm_pin) as x_m:
                    z_1 = x_m.value
                with AnalogIn(self._yp_pin) as y_p:
                    z_2 = y_p.value
        # print(z_1, z_2)
        if self.invert_pressure:
            z = 65535 - (z_2 - z_1)
        else:
            z = z_2 + z_1
        if z > self._zthresh:
            with DigitalInOut(self._yp_pin) as y_p:
                with DigitalInOut(self._ym_pin) as y_m:
                    with AnalogIn(self._xp_pin) as x_p:
                        y_p.switch_to_output(True)
                        y_m.switch_to_output(False)
                        for i in range(len(self._xsamples)):
                            self._xsamples[i] = x_p.value
            x = sum(self._xsamples) / len(self._xsamples)
            x_size = 65535
            if self._size:
                x_size = self._size[0]
            x = int(map_range(x, self._calib[0][0], self._calib[0][1], 0, x_size - 1))

            with DigitalInOut(self._xp_pin) as x_p:
                with DigitalInOut(self._xm_pin) as x_m:
                    with AnalogIn(self._yp_pin) as y_p:
                        x_p.switch_to_output(True)
                        x_m.switch_to_output(False)
                        for i in range(len(self._ysamples)):
                            self._ysamples[i] = y_p.value
            y = sum(self._ysamples) / len(self._ysamples)
            y_size = 65535
            if self._size:
                y_size = self._size[1]
            y = int(map_range(y, self._calib[1][0], self._calib[1][1], 0, y_size - 1))

            return (x, y, z)
        return None
