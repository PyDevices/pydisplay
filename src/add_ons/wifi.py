"""
wifi.py - connect to wifi

Usage:
    import wifi
    wifi.radio.connect('ssid', 'password')
"""

from time import sleep_ms

import network

_retries = 50


class Radio:
    def __init__(self):
        self._wlan = network.WLAN(network.STA_IF)

    def connect(self, ssid, password):
        if not self._wlan.active() or not self._wlan.isconnected():
            self._wlan.active(True)
            print("Connecting to:", ssid, end=" ")
            self._wlan.connect(ssid, password)
            tries = 0
            while tries < _retries:
                print(".", end="")
                if self._wlan.isconnected():
                    print(
                        "\nConnection established.\nNetwork config:", self._wlan.ifconfig(), "\n"
                    )
                    break
                sleep_ms(100)
                tries += 1
            else:
                print("\nFailed to connect.\n")
        else:
            print("\nAlready connected.\nNetwork config:", self._wlan.ifconfig(), "\n")
        return self._wlan

    @property
    def ipv4_address(self):
        return self._wlan.ifconfig()[0]


radio = Radio()
