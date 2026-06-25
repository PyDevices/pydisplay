# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.byteswap``.

``displaysys`` imports a native ``byteswap`` if one is available and otherwise
falls back to a pure-Python implementation defined in the package. Either way
the contract is the same: swap each pair of bytes in place. These tests cover
whichever implementation the host wired up.
"""

import unittest

import _env  # noqa: F401

from displaysys import byteswap


class TestByteswap(unittest.TestCase):
    def test_swaps_pairs_in_place(self):
        buf = bytearray(b"\x01\x02\x03\x04")
        byteswap(buf)
        self.assertEqual(bytes(buf), b"\x02\x01\x04\x03")

    def test_returns_none(self):
        # in-place: the helper mutates the buffer rather than returning a copy
        self.assertIsNone(byteswap(bytearray(b"\x01\x02")))

    def test_leaves_trailing_odd_byte_untouched(self):
        buf = bytearray(b"\x01\x02\x03")
        byteswap(buf)
        self.assertEqual(bytes(buf), b"\x02\x01\x03")

    def test_empty_buffer_is_noop(self):
        buf = bytearray()
        byteswap(buf)
        self.assertEqual(bytes(buf), b"")

    def test_double_swap_is_identity(self):
        original = bytes(range(16))
        buf = bytearray(original)
        byteswap(buf)
        byteswap(buf)
        self.assertEqual(bytes(buf), original)


if __name__ == "__main__":
    unittest.main()
