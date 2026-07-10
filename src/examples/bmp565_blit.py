# pyscript gallery: all
# pyscript binaries: assets/warrior.bmp
from color_setup import ssd
from graphics import BMP565
from multimer import sleep_ms

ssd.fill(0x0)
ssd.show()
bmp = BMP565("examples/assets/warrior.bmp")

ssd.blit_rect(bmp[0 : bmp.width, 0 : bmp.height], 0, 0, bmp.width, bmp.height)
print(ssd.width, ssd.height, bmp.width, bmp.height)
ssd.show()
sleep_ms(1000)

ssd.fill(0x0)
ssd.show()
sleep_ms(250)

ssd.blit_rect(bmp[:], 0, 0, bmp.width, bmp.height)
ssd.show()
sleep_ms(1000)
