# multimer types: queued, sync
# pyscript binaries: assets/warrior.bmp
from collections import namedtuple
from random import choice

from board_config import display_drv
from graphics import BMP565
from multimer import pump, sleep_ms

image = BMP565("examples/assets/warrior.bmp", streamed=True)
print(f"\n{image.width=}, {image.height=}, {image.bpp=}")
sprite_height = image.height // 4
sprite_width = image.width // 3
bg = image[0]
print(f"{sprite_width=}, {sprite_height=} {bg=:#0x}\n")

back, right, fwd, left = [x * sprite_height for x in range(4)]
directions = [fwd, left, right, back]
a, b, c = [x * sprite_width for x in range(3)]
positions = [a, b, c, b]
print("Sprite coordinates:")
for col in [fwd, left, right, back]:
    print(f"{(a, col)} {(b, col)} {(c, col)} {(b, col)}")


def draw_sprite(
    dest_x,
    dest_y,
    source_x,
    source_y,
    source_image=image,
    width=sprite_width,
    height=sprite_height,
):
    display_drv.blit_rect(
        source_image[source_x : source_x + width, source_y : source_y + height],
        dest_x,
        dest_y,
        width,
        height,
    )


display_drv.fill(bg)
display_drv.show()

point = namedtuple("point", "x y")
location = point(0, 0)
sprite = (a, fwd)
draw_sprite(*location, *sprite)

step = 3
dir = choice(directions)
while True:
    if choice((True, False, False, False, False)):
        dir = choice(directions)
    if dir == fwd and location.y + sprite_height > display_drv.height - step * 4:
        continue
    elif dir == back and location.y < step * 4:
        continue
    elif dir == left and location.x < step * 4:
        continue
    elif dir == right and location.x + sprite_width > display_drv.width - step * 4:
        continue

    for pos in positions:
        if dir == fwd:
            display_drv.fill_rect(location.x, location.y, sprite_width, step, bg)
            location = point(location.x, location.y + step)
        elif dir == back:
            display_drv.fill_rect(
                location.x, location.y + sprite_height - step, sprite_width, step, bg
            )
            location = point(location.x, location.y - step)
        elif dir == left:
            display_drv.fill_rect(
                location.x + sprite_width - step, location.y, step, sprite_height, bg
            )
            location = point(location.x - step, location.y)
        elif dir == right:
            display_drv.fill_rect(location.x, location.y, step, sprite_height, bg)
            location = point(location.x + step, location.y)
        draw_sprite(*location, pos, dir)
        display_drv.show()
        pump()
        sleep_ms(100)
