#!/usr/bin/env python3
"""Smoke-test add_ons/secrets.py. Run with cwd=src and the target interpreter.

Usage::

    cd src && python ../tools/_secrets_smoke.py
    cd src && micropython ../tools/_secrets_smoke.py
"""

import sys


def _dir_of(path):
    path = path.replace("\\", "/")
    return path.rsplit("/", 1)[0] if "/" in path else "."


def main():
    try:
        import lib.path  # noqa: F401
    except ImportError:
        src = _dir_of(_dir_of(__file__.replace("\\", "/"))) + "/src"
        if src not in sys.path:
            sys.path.insert(0, src)
        import lib.path  # noqa: F401

    sys.modules.pop("secrets", None)

    from displaysys import env_set

    env_set("GEMINI_API_KEY", "x")
    env_set("WIFI_SSID", "ssid-test")
    env_set("WIFI_PASSWORD", "pass-test")

    sys.modules.pop("secrets", None)
    import secrets

    assert getattr(secrets, "GEMINI_API_KEY", None) == "x", secrets
    assert secrets.WIFI_SSID == "ssid-test", secrets.WIFI_SSID
    assert secrets.WIFI_PASSWORD == "pass-test", secrets.WIFI_PASSWORD
    assert secrets.get("WIFI_SSID") == "ssid-test"
    assert secrets.get("NO_SUCH_SECRET_XYZ") is None

    # MCU guard (sys.platform is not assignable on MP/CP — use helper args).
    assert secrets._is_mcu_host("micropython", "esp32") is True
    assert secrets._is_mcu_host("circuitpython", "rp2") is True
    assert secrets._is_mcu_host("micropython", "linux") is False
    assert secrets._is_mcu_host("micropython", "unix") is False
    assert secrets._is_mcu_host("cpython", "esp32") is False
    assert secrets._is_mcu_host() is False  # this desktop host

    print(
        "OK secrets smoke impl=%s platform=%s file=%s"
        % (sys.implementation.name, sys.platform, getattr(secrets, "__file__", "?"))
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
