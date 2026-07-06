# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.boarddisplay.BoardDisplay``."""

import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401


class _FakeBitmap:
  def __init__(self, width, height, colors):
    self.width = width
    self.height = height
    self.colors = colors
    self.pixels = {}

  def __setitem__(self, key, value):
    self.pixels[key] = value


class _FakePalette:
  def __init__(self, size):
    self.size = size
    self.colors = {}

  def __setitem__(self, key, value):
    self.colors[key] = value


class _FakeTileGrid:
  def __init__(self, bitmap, pixel_shader):
    self.bitmap = bitmap
    self.pixel_shader = pixel_shader


class _FakeGroup:
  def __init__(self):
    self.children = []

  def append(self, child):
    self.children.append(child)


class _FakeDisplay:
  width = 4
  height = 4
  rotation = 0
  root_group = None
  refresh_count = 0

  def refresh(self):
    self.refresh_count += 1


def _install_fake_displayio():
  displayio = types.ModuleType("displayio")
  displayio.Bitmap = _FakeBitmap
  displayio.Palette = _FakePalette
  displayio.TileGrid = _FakeTileGrid
  displayio.Group = _FakeGroup
  return displayio


class TestBoardDisplay(unittest.TestCase):
  def setUp(self):
    self._board = types.ModuleType("board")
    self._board.DISPLAY = _FakeDisplay()
    self._displayio = _install_fake_displayio()
    self._modules = {
        "board": self._board,
        "displayio": self._displayio,
    }

  def _import_boarddisplay(self):
    with mock.patch.dict(sys.modules, self._modules):
      from displaysys.boarddisplay import BoardDisplay

      return BoardDisplay

  def test_fill_rect_writes_rgb565_buffer(self):
    BoardDisplay = self._import_boarddisplay()
    with mock.patch.dict(sys.modules, self._modules):
      d = BoardDisplay(width=4, height=4, color_depth=16)
    d.fill_rect(0, 0, 2, 1, 0xF800)
    self.assertEqual(d._buffer[0], 0x00)
    self.assertEqual(d._buffer[1], 0xF8)

  def test_show_assigns_root_group_and_refreshes(self):
    BoardDisplay = self._import_boarddisplay()
    with mock.patch.dict(sys.modules, self._modules):
      d = BoardDisplay(width=4, height=4, color_depth=16, bitmap_colors=256)
      d.fill_rect(0, 0, 4, 4, 0x001F)
      d.show()
      self.assertIsNotNone(self._board.DISPLAY.root_group)
      self.assertEqual(self._board.DISPLAY.refresh_count, 1)


if __name__ == "__main__":
  unittest.main()
