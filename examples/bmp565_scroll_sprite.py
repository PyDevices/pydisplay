from board_config import display_drv
from mpdisplay import Events
from bmp565 import BMP565
from time import sleep
from random import choice
from collections import namedtuple
point = namedtuple("point", "x y")

display_drv.rotation = 90

display_drv.fill(0)

image = BMP565("examples/assets/longstreet.bmp", streamed=True, mirrored=True)
print(f"\n{image.width=}, {image.height=}, {image.bpp=}")

def draw_bg(dest_x, source_y, count=1, source=image):
    display_drv.blit_rect(source[source_y:source_y + count], dest_x, 0, count, display_drv.height)

char_sprites = BMP565("examples/assets/animated-runner-character.bmp")
print(f"\n{char_sprites.width=}, {char_sprites.height=}, {char_sprites.bpp=}")
char_height = char_sprites.height // 3
char_width = char_sprites.width // 6
bg = char_sprites[0]  # top left pixel is the background color
print(f"{char_width=}, {char_height=} {bg=:#0x}\n")

run_sprites = [point(x * char_width, 0) for x in range(6)]
shoot_sprites = [point(x * char_width, char_height) for x in range(6)]
jump_sprites = [point(x * char_width, char_height * 2) for x in range(2)]
jump_shoot_sprites = [point((x + 2) * char_width, char_height * 2) for x in range(2)]
shot_sprite = point(4 * char_width, char_height * 2)

def draw_sprite(dest_x, dest_y, source_x, source_y, source=char_sprites, width=char_width, height=char_height):
    display_drv.blit_rect(source[source_x:source_x + width, source_y:source_y + height], dest_x, dest_y, width, height)

def main():
    i = 0
    scroll = 0
    char_y = display_drv.height - char_height
    char_x = 200
    while True:    
        if i > display_drv.width:
            scroll = i % display_drv.width
            display_drv.vscsad(scroll)
        draw_bg(i % display_drv.width, i % image.height, 1)
        i += 1
        if i < display_drv.width:
            continue
        event = display_drv.poll()
        if (event and event.type == Events.MOUSEMOTION and event.buttons[0] == 1):
            touched_point = event.pos
            if touched_point[1] < display_drv.height // 2:
                sprites = jump_shoot_sprites
            elif touched_point[0] < display_drv.width // 2:
                sprites = jump_sprites
            elif touched_point[0] > display_drv.width // 2:
                sprites = shoot_sprites
        else:
            sprites = run_sprites
        draw_x = scroll + char_x
        if not jumping and not shooting:
            sprite = sprites[i % len(sprites)]
            draw_sprite(draw_x, char_y, sprite.x, sprite.y)
        sleep(0.05)

main()