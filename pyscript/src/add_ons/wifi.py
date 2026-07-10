"""
Minimal ``wifi`` shim for MicroPython (``network.WLAN``).

Provides a CircuitPython-shaped subset so examples can use::

    import wifi
    wifi.radio.connect("ssid", "password")
    print(wifi.radio.ipv4_address)

This is **not** a full ``wifi.Radio`` implementation and is **not** a drop-in
for CircuitPython ``socketpool.SocketPool(wifi.radio)`` (that requires the
native CP radio object). On MicroPython, use ``network``/``socket`` or a
third-party HTTP client instead.

``connect()`` returns ``None`` (like CP). ``ipv4_address`` is ``None`` until
DHCP assigns a non-zero address.
"""

from time import sleep_ms

import network

_retries = 50


def _valid_ipv4(ip):
    return bool(ip) and ip != "0.0.0.0"


class Radio:
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)

    def _ipv4(self):
        if not self._wlan.isconnected():
            return None
        ip = self._wlan.ifconfig()[0]
        if not _valid_ipv4(ip):
            return None
        return ip

    def connect(self, ssid, password):
        if self._ipv4() is not None:
            print("\nAlready connected.\nNetwork config:", self._wlan.ifconfig(), "\n")
            return None

        self._wlan.active(True)
        print("Connecting to:", ssid, end=" ")
        self._wlan.connect(ssid, password)
        for _ in range(_retries):
            print(".", end="")
            if self._ipv4() is not None:
                print("\nConnection established.\nNetwork config:", self._wlan.ifconfig(), "\n")
                return None
            sleep_ms(100)
        print("\nFailed to connect.\n")
        return None

    @property
    def ipv4_address(self):
        return self._ipv4()


radio = Radio()
