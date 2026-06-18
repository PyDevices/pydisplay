"""
A wrapper for ezFBfont that allows rendering to non-framebuffer objects.

See ezFBfont at https://github.com/easytarget/microPyEZfonts
"""

from ezFBfont import ezFBfont, framebuf


class EZFont(ezFBfont):
    def _put_char(self, char, x, y, fg, bg, tkey):
        # fetch the glyph
        glyph, char_height, char_width = self._font.get_ch(char)
        if glyph is None:
            return 0, 0  # Nothing to print. skip.
        charbuf = framebuf.FrameBuffer(glyph, char_width, char_height, self._font_format)

        if (
            (-x >= char_width)
            or (-y >= char_height)
            or (x >= self._device.width)
            or (y >= self._device.height)
        ):
            # Out of bounds, no-op.
            return

        # Clip.
        # x0 = max(0, x)
        # y0 = max(0, y)
        # x1 = max(0, -x)
        # y1 = max(0, -y)
        # x0end = min(self._device.width, x + char_width)
        # y0end = min(self._device.height, y + char_height)

        print("\n")
        for cy in range(char_height):
            for cx in range(char_width):
                color = charbuf.pixel(cx, cy)
                print(color, end=" ")
                color = self.fg if color > 0 else self.bg
                if color != tkey:
                    self._device.pixel(x + cx, y + cy, color)
            print("")
        return char_width, char_height
