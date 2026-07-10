# multimer types: all
# pyscript skip: gallery
import board_config
import pdwidgets as pd


pd.DEBUG = False
pd.MARK_UPDATES = False
# pd.init_timer(10)  # Remove this line to use polled mode in a while loop


display = pd.Display(board_config.display_drv, board_config.runtime, 40, 40)
pal = display.pal
screen = pd.Screen(display, None, visible=False)

if screen.partitioned:
    top, bottom, main = screen.top, screen.bottom, screen.main
else:
    top = bottom = main = screen

color_wheel = pd.get_palette(
    name="wheel", swapped=display.needs_swap, length=display.vsa, saturation=1.0
)
if screen.partitioned:

    def main_area_draw(area=None):
        area = area or pd.Area(display.vsa_area)
        # print(f"draw_bg: {area}")
        for i in range(area.y, area.y + area.h):
            display.framebuf.fill_rect(area.x, i, area.w, 1, color_wheel[i - display.tfa])

    main.draw = main_area_draw
    main_area_draw()

aligns = [
    pd.ALIGN.TOP_LEFT,
    pd.ALIGN.TOP,
    pd.ALIGN.TOP_RIGHT,
    pd.ALIGN.LEFT,
    pd.ALIGN.CENTER,
    pd.ALIGN.RIGHT,
    pd.ALIGN.BOTTOM_LEFT,
    pd.ALIGN.BOTTOM,
    pd.ALIGN.BOTTOM_RIGHT,
    pd.ALIGN.OUTER_TOP_LEFT,
    pd.ALIGN.OUTER_TOP,
    pd.ALIGN.OUTER_TOP_RIGHT,
    pd.ALIGN.OUTER_LEFT,
    pd.ALIGN.OUTER_RIGHT,
    pd.ALIGN.OUTER_BOTTOM_LEFT,
    pd.ALIGN.OUTER_BOTTOM,
    pd.ALIGN.OUTER_BOTTOM_RIGHT,
]

align_names = [
    "TL",
    "TOP",
    "TR",
    "LEFT",
    "CTR",
    "RIGHT",
    "BL",
    "BOT",
    "BR",
    "OTL",
    "OT",
    "OTR",
    "OL",
    "OR",
    "OBL",
    "OB",
    "OBR",
]


def demo_alignments(parent, align_to=None):
    for name, align in zip(align_names, aligns):
        pd.Label(parent, align=align, align_to=align_to, value=name)


def scroll_by(value):
    display.vscroll += value


def scroll_to(value):
    display.vscroll = value


auto_scroll_task = None


def toggle_auto_scroll(sender, event=None):
    global auto_scroll_task
    if not auto_scroll_task:
        auto_scroll_task = display.add_task(lambda: scroll_by(1), 1)
    else:
        display.remove_task(auto_scroll_task)
        auto_scroll_task = None


home = pd.IconButton(
    top, align=pd.ALIGN.TOP_LEFT, icon_file=pd.icon_theme.home(pd.ICON_SIZE.LARGE)
)
toggle = pd.ToggleButton(top, align_to=home, align=pd.ALIGN.OUTER_RIGHT, value=False)
down = pd.IconButton(
    top, align=pd.ALIGN.TOP_RIGHT, icon_file=pd.icon_theme.down_arrow(pd.ICON_SIZE.LARGE)
)
up = pd.IconButton(
    top,
    align_to=down,
    align=pd.ALIGN.OUTER_LEFT,
    icon_file=pd.icon_theme.up_arrow(pd.ICON_SIZE.LARGE),
)
slider1 = pd.Slider(
    top, y=9, w=up.x - toggle.x - toggle.width - 16, h=18, align=pd.ALIGN.TOP, value=0, step=0.05
)

clock = pd.DigitalClock(bottom, y=-12, align=pd.ALIGN.BOTTOM_RIGHT, visible=False)
clock_toggle = pd.ToggleButton(bottom, align_to=clock, align=pd.ALIGN.OUTER_LEFT, value=False)
status = pd.TextBox(
    bottom, y=-8, w=clock_toggle.x, align=pd.ALIGN.BOTTOM_LEFT, scale=1, value="Status: loaded."
)

button = pd.Button(
    main, w=main.width // 2, h=64, align=pd.ALIGN.CENTER, label="test", radius=10, pressed_offset=5
)
# demo_alignments(button)

scroll_jump = 5
home.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: scroll_to(0))
toggle.add_event_cb(pd.events.MOUSEBUTTONDOWN, toggle_auto_scroll)
down.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: scroll_by(-scroll_jump))
up.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: scroll_by(scroll_jump))
slider1.set_change_cb(lambda sender: scroll_to(int(sender.value * display.vsa)))
button.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: status.set_value("Button pressed")
)
button.add_event_cb(pd.events.MOUSEBUTTONUP, lambda sender, e: status.set_value("Button released"))
clock_toggle.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: clock.hide(not sender.value)
)
screen.add_event_cb(pd.events.MOUSEWHEEL, lambda sender, e: scroll_by(-e.y))

screen.visible = True


pd.run_forever()
