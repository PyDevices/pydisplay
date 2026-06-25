# multimer types: all
# pyscript files: displaybuf_blit.py
from color_setup import ssd
from graphics import FrameBuffer, RGB565


ssd.fill(0xF800)
ssd.show()

ba = bytearray(100 * 100 * 2)
mv = memoryview(ba)
fb = FrameBuffer(mv, 100, 100, RGB565)
fb.fill(0x000F)

ssd.blit(fb, 100, 100)
ssd.show()
