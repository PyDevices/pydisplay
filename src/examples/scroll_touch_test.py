# multimer types: all
from board_config import display_drv, runtime
from graphics import Draw
from multimer import sleep_ms
from multimer.loop import run_forever
from palettes import get_palette
from random import getrandbits



canvas = display_drv


def main():
    line_height = 16
    canvas.set_vscroll(16, 16)  # Does not have to == line_height

    pal = get_palette()
    draw = Draw(canvas)

    if canvas.tfa > 0:
        # draw top fixed area
        draw.fill_rect(0, 0, canvas.width, canvas.tfa, pal.RED)
        if canvas.tfa > 15:
            draw.text14("0 TFA", 1, 1, pal.WHITE)
            draw.round_rect(canvas.width - 44, 1, 40, 12, 4, pal.GREEN, True)
            draw.text("Up", canvas.width - 32, 4, pal.WHITE)
    if canvas.bfa > 0:
        # draw bottom fixed area
        draw.fill_rect(0, canvas.height - canvas.bfa, canvas.width, canvas.bfa, pal.BLUE)
        if canvas.bfa > 15:
            draw.text14(
                f"{canvas.height - canvas.bfa} BFA", 1, canvas.height - canvas.bfa + 1, pal.WHITE
            )
            draw.round_rect(
                canvas.width - 44, canvas.height - canvas.bfa + 1, 40, 12, 4, pal.GREEN, True
            )
            draw.text("Down", canvas.width - 40, canvas.height - canvas.bfa + 5, pal.WHITE)

    for i, y in enumerate(range(canvas.tfa, canvas.vsa + canvas.tfa, line_height)):
        # Draw alternating bars on the scrollable area
        fg, bg = pal.WHITE, pal.BLACK
        if i % 2:
            fg, bg = bg, fg
        draw.fill_rect(0, y, canvas.width, line_height, bg)
        txt = f"vssa: {y}, vscroll: {y - canvas.tfa}"
        draw.text14(txt, 1, y + 1, fg)
        draw.rect(canvas.width - 20, y + 2, 12, 12, fg)

    canvas.show()

    def poll_events():
        elist = runtime.poll() if runtime else []
        if runtime.quit_requested if runtime else False:
            return True
        quit_requested = False
        for e in elist:
            if e.type == runtime.events.QUIT:
                quit_requested = True
                break
            if e.type == runtime.events.MOUSEBUTTONDOWN:
                x, y = canvas.translate_point(e.pos)
                if y < canvas.tfa:
                    canvas.vscroll -= line_height
                elif y > canvas.height - canvas.bfa:
                    canvas.vscroll += line_height
                else:
                    y_pos = (y // line_height) * line_height
                    canvas.fill_rect(
                        canvas.width - 20, y_pos + 2, 12, 12, getrandbits(canvas.color_depth)
                    )
                canvas.show()
            if quit_requested:
                return True
        return False

    run_forever(poll_events, delay_ms=0)


main()
