# pyscript gallery: all
from board_config import display_drv
from graphics import Draw, FrameBuffer, RGB565
from pbm import PBM


def draw_logo(logo):
    w = logo.width
    h = logo.height
    black = background = 0
    blue = amber = 1
    center_x = w // 2
    center_y = h // 2
    unit = min(w, h) // 2
    draw = Draw(logo)

    logo.fill(background)

    draw.circle(center_x, center_y, unit, blue, True)
    draw.circle(center_x, center_y, int(unit * 0.9), black, True)
    draw.circle(center_x, center_y, int(unit * 0.8), amber, True)

    left = int(center_x - (unit * 1.2) // 2)
    top = int(center_y - (unit * 1.0) // 2)
    draw.round_rect(left, top, int(unit * 1.2), int(unit * 1.0), unit // 7, black, True)

    left = int(center_x - (unit * 1.1) // 2)
    top = int(center_y - (unit * 0.9) // 2)
    draw.round_rect(left, top, int(unit * 1.1), int(unit * 0.9), unit // 9, amber, True)

    left = center_x - (unit * 3 // 8)
    top = center_y - (unit * 3 // 8)
    size = unit // 4

    draw.fill_rect(left, top, size, size, black)
    draw.fill_rect(w - (left + size), h - (top + size), size, size, black)

    size = size // 2
    draw.circle(w - (left + size), top + size, size, black, True)
    draw.circle(left + size, h - (top + size), size, black, True)


display_drv.fill(0xF800)
logo = PBM(width=64, height=64)
draw_logo(logo)

logo.render(display_drv, 0, 0, 0xFFFF, 0x0000)
logo.render(display_drv, 0, display_drv.height // 2, 0xFFFF)

buf = bytearray(logo.width * logo.height * 2)
fb = FrameBuffer(buf, logo.width, logo.height, RGB565)
logo.render(fb, 0, 0, 0xFFFF)

display_drv.blit_rect(buf, display_drv.width // 3, 0, logo.width, logo.height)
display_drv.blit_transparent(
    buf, display_drv.width // 3, display_drv.height // 2, logo.width, logo.height, 0x0
)

palette = FrameBuffer(memoryview(bytearray(2 * 2)), 2, 1, RGB565)
palette.pixel(0, 0, 0x0FF0)
palette.pixel(1, 0, 0xFFFF)
fb.fill(0x000F)
logo.render(fb, 0, 0, palette.pixel(1, 0), palette.pixel(0, 0))

display_drv.blit_rect(buf, display_drv.width * 2 // 3, 0, logo.width, logo.height)
display_drv.blit_transparent(
    buf, display_drv.width * 2 // 3, display_drv.height // 2, logo.width, logo.height, 0x000F
)

display_drv.show()
