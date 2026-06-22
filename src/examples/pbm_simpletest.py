# multimer types: all
from board_config import display_drv
from framebuf import FrameBuffer, RGB565
from pbm import PBM


display_drv.fill(0xF800)
logo = PBM("examples/assets/micropython.pbm")

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
