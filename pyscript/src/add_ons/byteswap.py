# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
`byteswap`
====================================================

Swap 16-bit pixel bytes in place. Implementations, in preference order:

- numpy / ulab (CPython, CircuitPython, MicroPython with ulab)
- inlined MicroPython ``@viper``
- ``viper_tools.byteswap_viper`` when present
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
    _viper_impl = None
    try:
        import micropython

        if getattr(micropython, "viper", None) is not None:

            @micropython.viper
            def _byteswap_viper(buf: ptr8, buf_size: int):  # noqa: F821
                i = 0
                while i < buf_size:
                    tmp = buf[i]
                    buf[i] = buf[i + 1]
                    buf[i + 1] = tmp
                    i += 2

            _viper_impl = _byteswap_viper
    except Exception:
        _viper_impl = None

    if _viper_impl is None:
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
