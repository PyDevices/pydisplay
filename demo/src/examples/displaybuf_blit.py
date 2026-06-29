# multimer types: all
from color_setup import ssd
from graphics import FrameBuffer, RGB565

ssd.fill(0xF800)
ssd.show()

ba = bytearray(100 * 100 * 2)
fb = FrameBuffer(ba, 100, 100, RGB565)
fb.fill(0x000F)

ssd.blit_rect(ba, 100, 100, 100, 100)
ssd.show()
