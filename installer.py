#!/usr/bin/env python3
"""
Universal MicroPython package installer for pydisplay.
=====================================================
This installer can be run on a network connected MicroPython device
or on a host computer connected to a MicroPython device via a serial
connection.  It will install pydisplay and its dependencies from the
PyDevices fork of the micropython-lib repository or the PyDevices/pydisplay
repository on GitHub.

To see this file in action on Wokwi, uncomment add_ons + examples in web/sim/wokwi/main.py:
    https://github.com/PyDevices/pydisplay/tree/main/web/sim/wokwi

To download this file:
1. Download it with your browser from its home on Github:
https://github.com/PyDevices/pydisplay/blob/main/installer.py

2. On a network-connected MicroPython microcontroller or Micropython on Unix:

```python
import mip
mip.install("github:PyDevices/pydisplay/installer.py")
```

3. On a host computer with mpremote:

```bash
wget https://raw.githubusercontent.com/PyDevices/pydisplay/main/installer.py
```

Usage:
```python
from installer import install  # Installs the packages at the end of the file
install("ANY OTHER PACKAGE(S) YOU WANT TO INSTALL")
```

Details
=======
Includes 2 functions that install from different sources:
- `lib_install`: Installs from the PyDevices fork of the micropython-lib library.
    - By default, installs all modules as precompiled bytecode (.mpy) files.
    - Includes:
        - Core packages:
            - displaysys (full package — all backends)
            - eventsys
            - graphics
            - multimer
        - Display drivers, for example:
            - gc9a01
            - ili9341
            - st7789
        - Touch drivers, for example:
            - ft6x36
            - cst226
            - xpt2046
        - Note the add_ons, examples, spibus and i80bus packages are not available from the PyDevices
          fork of the micropython-lib repository.  It isn't the correct place for add_ons and examples,
          while spibus and i80bus use micropython.viper, which is not supported by micropython-lib.
- `repo_install`: Installs from the PyDevices/pydisplay repository on GitHub.
    - Can retrieve any file from the repository, not just packages.
    - Retrieves files as is, without precompilation (no .mpy files).
    - Includes:
        - GitHub-only packages:
            - /packages/add_ons.json
            - /packages/examples.json
        - Board configs, hardware drivers, and bus/touch MIP packages live in
          PyDevices/micropython-hardware (install with full github: URLs via mip,
          not via this helper's pydisplay-prefixed paths).
        - Can be used to get non-packaged files from the repository, useful for getting:
            - /src/lib/board_config.py - The default board configuration file - for desktop environments.
- Since micropython-lib packages will never have a '/' in their name and the PyDevices/pydisplay
  repository packages always have a '/', there is a third function that will determine which of the
  2 installers to use.  It is simply called `install`.
"""

from sys import implementation

pkg_index = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
repo = "github:PyDevices/pydisplay"


if implementation.name == "micropython":
    import mip

    def lib_install(package, **kwargs):
        """
        Installs 'library packages' from the PyDevices fork of micropython-lib.
        Runs on the MicroPython device.
        """
        mip.install(package, index=pkg_index, **kwargs)

    def repo_install(package, **kwargs):
        """
        Installs 'repository packages' (and individual files) from the PyDevices/pydisplay repository.
        Runs on the MicroPython device.
        """
        mip.install(repo + package, **kwargs)
else:
    import os

    def lib_install(package, target="", index=None, mpy=True):
        """
        Installs 'library packages' from the PyDevices fork of micropython-lib.
        Runs on the host computer.
        """
        if index:
            raise ValueError("The 'index' option is not supported for 'lib_install'.")
        option = "" if mpy else "--no-mpy"
        os.system(f"mpremote mip install {option} --index {pkg_index} --target={target} {package}")

    def repo_install(package, target="", index=None, mpy=False):
        """
        Installs 'repository packages' (and files) from the PyDevices/pydisplay repository on GitHub.
        Runs on the host computer.
        """
        if mpy:
            raise ValueError("The 'mpy' option is not supported for 'repo_install'.")
        if index:
            raise ValueError("The 'index' option is not supported for 'repo_install'.")
        os.system(f"mpremote mip install --target={target} {repo + package}")


def install(package, **kwargs):
    if "/" in package:
        repo_install(package, **kwargs)
    else:
        lib_install(package, **kwargs)


####################################################################################################
# Library packages - install as precompiled bytecode (.mpy) files
####################################################################################################
"""
## Core packages:
install("displaysys")
install("eventsys")
install("graphics")
install("multimer")

## Display drivers, for example:
install("gc9a01")
install("ili9341")
install("st7789")

## Touch drivers, for example:
install("ft6x36")
install("cst226")
install("xpt2046")
"""

####################################################################################################
# Repository packages - contains no precompiled bytecode (.mpy) files
####################################################################################################
"""
## GitHub-only packages (source .py; not on the micropython-lib index):
install("/packages/add_ons.json", target="./add_ons")
install("/packages/examples.json", target="./examples")

## Hardware (boards / drivers / bus packages) — use mip against micropython-hardware:
# mip.install("github:PyDevices/micropython-hardware/packages/spibus.json")
# mip.install("github:PyDevices/micropython-hardware/board_configs/busdisplay/i80/wt32sc01-plus")

## Non-packaged files from the repository:
##### For example, the default board configuration file for desktop environments
install("/src/lib/board_config.py", target="./")
"""

####################################################################################################
# Customize as you see fit by copying the line(s) you want from above and pasting below.
##### The default is the recommended "full" installation
####################################################################################################

install("displaysys")
install("eventsys")
install("graphics")
install("multimer")
install("/packages/add_ons.json", target="./add_ons")
install("/packages/examples.json", target="./examples")

## If you are running on a microcontroller, uncomment and edit the following line to match your hardware.
# install("/board_configs/busdisplay/i80/wt32sc01-plus", target="./")

## Otherwise uncomment the following line to get the default board_config.py
install("/src/lib/board_config.py", target="./")
install("/src/lib/path.py", target="./")

##### Note, you can also use `mip.install` to install from micropython-lib or other repositories.
