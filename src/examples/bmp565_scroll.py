# multimer types: all
# pyscript binaries: assets/longstreet.bmp
from board_config import display_drv, runtime
from graphics import BMP565
from multimer import sleep_ms

display_drv.rotation = 0

image = BMP565("examples/assets/longstreet.bmp", streamed=True)
print(f"\n{image.width=}, {image.height=}, {image.bpp=}")


def draw_bg(dest_x, dest_y, source_x, source_y, source_image=image, width=image.width, height=1):
    display_drv.blit_rect(
        source_image[source_x : source_x + width, source_y : source_y + height],
        dest_x,
        dest_y,
        width,
        height,
    )


for j in range(display_drv.height):
    draw_bg(0, j, 0, j, height=1)
display_drv.show()
sleep_ms(3000)

i = display_drv.height
while True:
    display_drv.vscsad(i % display_drv.height)
    draw_bg(0, i % display_drv.height, 0, i % image.height)
    display_drv.show()
    sleep_ms(0)
    if runtime.quit_requested if runtime else False:
        break
    sleep_ms(1)
    i += 1
