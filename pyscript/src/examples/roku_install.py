# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_install
====================================================
On-device installer for the Roku remote example.

Fetches precompiled ``.mpy`` libraries from the PyDevices micropython-lib MIP
index, then fetches ``roku_*.py`` sources from the pydisplay GitHub Pages tree
(``web/pyscript/src`` symlink → published ``pyscript/src/...``).

**Prerequisite:** WiFi already working (e.g. ``wifi.radio.connect(...)``), plus
your own ``board_config`` and any hardware drivers on the board.

``graphics`` is expected to be compiled into the firmware (cmod / freeze), so
it is not installed here.

Typical first-time flow on a networked board::

    import mip
    mip.install(
        "https://PyDevices.github.io/pydisplay/pyscript/src/examples/roku_install.py",
        target="/lib",
    )
    import roku_install
    roku_install.main()

Then::

    import roku_remote
"""

import mip

LIB_INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
EXAMPLES_BASE = "https://PyDevices.github.io/pydisplay/pyscript/src/examples"

# .mpy via micropython-lib index (mpy version selected by firmware)
LIB_PACKAGES = (
    "displaysys",
    "eventsys",
    "multimer",
    "palettes",
)

# Plain .py from gh-pages (pyscript/src → src)
ROKU_FILES = (
    "roku_engine.py",
    "roku_remote.py",
    "roku_install.py",
)


def install_libs(target="/lib", index=LIB_INDEX, mpy=True):
    for name in LIB_PACKAGES:
        print("mip:", name, "→", target, "(mpy=%s)" % mpy)
        mip.install(name, index=index, target=target, mpy=mpy)


def install_roku_examples(target="/lib", base=EXAMPLES_BASE):
    for name in ROKU_FILES:
        url = base + "/" + name
        print("mip:", url, "→", target)
        mip.install(url, target=target)


def main(lib_target="/lib", examples_target="/lib", index=LIB_INDEX, mpy=True):
    """Install libraries and Roku example scripts. Returns None."""
    print("Installing from", index)
    print("Examples from", EXAMPLES_BASE)
    install_libs(target=lib_target, index=index, mpy=mpy)
    install_roku_examples(target=examples_target)
    print("Done. Provide board_config + drivers, then: import roku_remote")


# Allow ``import roku_install`` then call main(), or run as a script.
if __name__ == "__main__":
    main()
