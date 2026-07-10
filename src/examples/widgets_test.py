# multimer types: all
# pyscript skip: gallery
import board_config
import pdwidgets as pd

try:
    from gc import collect, mem_free
except ImportError:
    mem_free = None


pd.DEBUG = False
pd.MARK_UPDATES = False
pd.init_timer(10)  # Remove this line to use polled mode in a while loop


REVERSE = False  # for troubleshooting progressbar, sliders, scrollbars

display = pd.Display(board_config.display_drv, board_config.runtime)
screen = pd.Screen(display, visible=False)

status = pd.TextBox(screen, w=screen.width, align=pd.ALIGN.BOTTOM, scale=1)

toggle = pd.Toggle(screen, on_file=pd.icon_theme.home(pd.ICON_SIZE.LARGE))  # noqa: F841

label1 = pd.Label(
    screen, align=pd.ALIGN.TOP, value="Inverted", bg=screen.bg, scale=2, inverted=True
)  # noqa: F841
toggle_button = pd.ToggleButton(screen, align_to=toggle, align=pd.ALIGN.OUTER_RIGHT, value=False)


def flip_label(sender, event):
    label1._inverted = not label1._inverted
    label1.changed()


toggle_button.add_event_cb(pd.events.MOUSEBUTTONDOWN, flip_label)

checkbox = pd.CheckBox(screen, align=pd.ALIGN.OUTER_BOTTOM, align_to=toggle, value=False)
checkbox.add_event_cb(
    pd.events.MOUSEBUTTONDOWN,
    lambda sender, e: status.set_value(f"{'checked' if sender.value else 'unchecked'}"),
)
cb_label = pd.Label(checkbox, value="Check Me", align=pd.ALIGN.OUTER_RIGHT)

button1 = pd.Button(screen, w=96, align=pd.ALIGN.CENTER, value="button1", label="Mem_free")
if mem_free:
    mem_free_label = pd.Label(
        screen, y=6, align_to=button1, align=pd.ALIGN.OUTER_BOTTOM, value=f"Free mem: {mem_free()}"
    )

    def mem_free_action(sender, event):
        collect()
        mem_free_label.set_value(f"Free mem: {mem_free()}")

    button1.add_event_cb(pd.events.MOUSEBUTTONDOWN, mem_free_action)

hide_button = pd.Button(
    screen,
    align=pd.ALIGN.OUTER_LEFT,
    align_to=button1,
    value="Hide",
    label="Hide",
)
hide_button.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: hide_button.hide(True))

jmp_button = pd.Button(
    screen, align=pd.ALIGN.OUTER_RIGHT, align_to=button1, value="Jump", label="Jump"
)


def jump(sender, event):
    if jmp_button.align == pd.ALIGN.OUTER_RIGHT:
        jmp_button.set_position(align=pd.ALIGN.OUTER_LEFT)
    else:
        jmp_button.set_position(align=pd.ALIGN.OUTER_RIGHT)


jmp_button.add_event_cb(pd.events.MOUSEBUTTONUP, (jump))

radio_group = pd.RadioGroup(screen)
radio1 = pd.RadioButton(
    screen, group=radio_group, y=10, align_to=checkbox, align=pd.ALIGN.OUTER_BOTTOM, value=False
)
r1_label = pd.Label(radio1, value="Radio 1", align=pd.ALIGN.OUTER_RIGHT, scale=2)
radio2 = pd.RadioButton(
    screen, group=radio_group, align_to=radio1, align=pd.ALIGN.OUTER_BOTTOM, value=True
)
r2_label = pd.Label(radio2, value="Radio 2", align=pd.ALIGN.OUTER_RIGHT, scale=2)
radio1.add_event_cb(
    pd.events.MOUSEBUTTONDOWN,
    lambda sender, e: status.set_value(
        f"RadioButton 1 is now {'checked' if sender.value else 'unchecked'}"
    ),
)
radio2.add_event_cb(
    pd.events.MOUSEBUTTONDOWN,
    lambda sender, e: status.set_value(
        f"RadioButton 2 is now {'checked' if sender.value else 'unchecked'}"
    ),
)

scrollbar2 = pd.ScrollBar(
    screen, align_to=status, align=pd.ALIGN.OUTER_TOP, vertical=False, value=0.5, reverse=REVERSE
)
scrollbar2.slider.add_event_cb(
    pd.events.MOUSEBUTTONDOWN,
    lambda sender, e: status.set_value(f"ScrollBar value: {sender.value:.2f}"),
)

slider1 = pd.Slider(
    screen, align_to=scrollbar2, align=pd.ALIGN.OUTER_TOP, value=0.5, step=0.05, reverse=REVERSE
)
slider1.add_event_cb(
    pd.events.MOUSEBUTTONDOWN,
    lambda sender, e: status.set_value(f"Slider value: {sender.value:.2f}"),
)

# # Simulate a scroll bar. Shows how to add an Icon to a Button. Also shows how to use an IconButton.
pbar = pd.ProgressBar(
    screen,
    y=slider1.y - screen.height,
    w=display.width // 2,
    align=pd.ALIGN.BOTTOM,
    value=0.5,
    reverse=REVERSE,
)
pbar.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: status.set_value(f"Progress: {sender.value:.0%}")
)
pbtn1 = pd.Button(pbar, w=22, h=22, align=pd.ALIGN.OUTER_LEFT)
pbtn1_icon = pd.Icon(
    pbtn1, align=pd.ALIGN.CENTER, value=pd.icon_theme.left_arrow(pd.ICON_SIZE.SMALL)
)  # noqa: F841
pbtn2 = pd.IconButton(
    pbar, align=pd.ALIGN.OUTER_RIGHT, icon_file=pd.icon_theme.right_arrow(pd.ICON_SIZE.SMALL)
)
pbtn1.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: pbar.set_value(pbar.value - 0.1))
pbtn2.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: pbar.set_value(pbar.value + 0.1))


clock = pd.DigitalClock(screen, align=pd.ALIGN.TOP_RIGHT)

screen.visible = True

pd.run_forever()
