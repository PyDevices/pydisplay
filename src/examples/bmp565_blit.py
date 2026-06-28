# multimer types: all
# pyscript binaries: assets/warrior.bmp
from color_setup import ssd
from bmp565 import BMP565
from graphics import FrameBuffer, RGB565
from multimer import sleep_ms

ssd.fill(0x0)
ssd.show()
bmp = BMP565("examples/assets/warrior.bmp")
fb = FrameBuffer(bmp.buffer, bmp.width, bmp.height, RGB565)

a = ssd.blit(fb, 0, 0)
print(a)
ssd.show()
sleep_ms(1000)

ssd.fill(0x0)
ssd.show()
sleep_ms(250)

a = ssd.blit_rect(bmp[:], 0, 0, bmp.width, bmp.height)
print(a)
ssd.show()
sleep_ms(1000)
