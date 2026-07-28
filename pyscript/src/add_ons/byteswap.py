# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
`byteswap`
====================================================

Swap 16-bit pixel bytes in place. Implementations, in preference order:

- numpy / ulab (CPython, CircuitPython, MicroPython with ulab)
- ``viper_tools.byteswap_viper`` when present

Do not put ``@micropython.viper`` in this file: MicroPython validates that
decorator at parse time, so a runtime check cannot protect non-viper ports
(e.g. Windows). Keep viper bodies in :mod:`viper_tools` and import them
inside ``except Exception`` so ``SyntaxError`` is handled.
"""

try:
    try:
        import numpy as np
    except ImportError:
        from ulab import numpy as np

    def byteswap(buf):
        """Swap the bytes of a 16-bit buffer in place using numpy."""
        npbuf = np.frombuffer(buf, dtype=np.uint16)
        npbuf.byteswap(inplace=True)

except Exception:
    try:
        from viper_tools import byteswap_viper as _viper_impl
    except Exception:
        raise ImportError("No implementation of byteswap available") from None

    def byteswap(buf):
        """Swap the bytes of a 16-bit buffer in place using viper."""
        n = len(buf)
        if n & 1:
            raise ValueError("buffer size must be a multiple of 2")
        _viper_impl(buf, n)
