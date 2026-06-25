# multimer types: all
# pyscript files: pbm_create_new.py
from board_config import display_drv
from framebuf import FrameBuffer, RGB565
from pbm import PBM
import graphics


def draw_logo(canvas):
    w = canvas.width
    h = canvas.height
    black = background = 0
    blue = amber = 1
    center_x = w // 2
    center_y = h // 2
    unit = min([w, h]) // 2

    canvas.fill(background)

    # Draw the 3 concentric circles
    graphics.circle(canvas, center_x, center_y, unit, blue, True)
    graphics.circle(canvas, center_x, center_y, int(unit * 0.9), black, True)
    graphics.circle(canvas, center_x, center_y, int(unit * 0.8), amber, True)

    # Draw the outer rounded rectangle
    left = int(center_x - (unit * 1.2) // 2)
    top = int(center_y - (unit * 1.0) // 2)
    graphics.round_rect(
        canvas, left, top, int(unit * 1.2), int(unit * 1.0), unit // 7, black, True
    )

    # Draw the inner rounded rectangle
    left = int(center_x - (unit * 1.1) // 2)
    top = int(center_y - (unit * 0.9) // 2)
    graphics.round_rect(
        canvas, left, top, int(unit * 1.1), int(unit * 0.9), unit // 9, amber, True
    )

    # Draw the 2 small squares
    left = center_x - (unit * 3 // 8)
    top = center_y - (unit * 3 // 8)
    size = unit // 4

    graphics.fill_rect(canvas, left, top, size, size, black)
    graphics.fill_rect(canvas, w - (left + size), h - (top + size), size, size, black)

    # Draw the 2 small circles
    size = size // 2
    graphics.circle(canvas, w - (left + size), top + size, size, black, True)
    graphics.circle(canvas, left + size, h - (top + size), size, black, True)


display_drv.fill(0xF800)
logo = PBM(width=64, height=64)
draw_logo(logo)

# render direct to the display with fg and bg colors
logo.render(display_drv, 0, 0, 0xFFFF, 0x0000)

# render direct to the display with fg and transparent bg
logo.render(display_drv, 0, display_drv.height // 2, 0xFFFF)


# render to a frame buffer
buf = bytearray(logo.width * logo.height * 2)
fb = FrameBuffer(buf, logo.width, logo.height, RGB565)
logo.render(fb, 0, 0, 0xFFFF)  # add a bg color if needed

# blit the frame buffer to the display
display_drv.blit_rect(buf, display_drv.width // 3, 0, logo.width, logo.height)

# blit the frame buffer to the display with transparent bg
display_drv.blit_transparent(
    buf, display_drv.width // 3, display_drv.height // 2, logo.width, logo.height, 0x0
)


# blit to a frame buffer; re-use the same buffer and frame buffer but fill with blue first
palette = FrameBuffer(memoryview(bytearray(2 * 2)), 2, 1, RGB565)
palette.pixel(0, 0, 0x0FF0)
palette.pixel(1, 0, 0xFFFF)
fb.fill(0x000F)
fb.blit(logo, 0, 0, palette.pixel(0, 0), palette)

# blit the frame buffer to the display
display_drv.blit_rect(buf, display_drv.width * 2 // 3, 0, logo.width, logo.height)

# blit the frame buffer to the display with transparent bg
display_drv.blit_transparent(
    buf, display_drv.width * 2 // 3, display_drv.height // 2, logo.width, logo.height, 0x000F
)

display_drv.show()
