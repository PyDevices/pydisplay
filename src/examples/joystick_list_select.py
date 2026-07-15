# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
# pyscript skip: binaries
import board_config
import eventsys
import pdwidgets as pd

display = pd.Display(board_config.display_drv, board_config.runtime,40)
screen = pd.Screen(display, visible=False)

top, bottom, main = screen.top, screen.bottom, screen.main

pd.Label(top,value="Select an Item")

list_view = pd.ListView(main, w=int(main.width * .9), h=int(main.height * .9), align=pd.ALIGN.CENTER)

items = [pd.Label(list_view,value=i) for i in ["Item 1", "Item 2", "Item 3"]]
selected = 0
items[selected].bg = list_view.color_theme.secondary

screen.visible = True



def select_item(up: bool):
    global selected
    if up and selected > 0:
        selected -= 1
    elif not up and selected < len(items) - 1:
        selected += 1
    for i in items:
        i.bg = list_view.color_theme.secondary if i == items[selected] else list_view.color_theme.transparent
    list_view.invalidate()

def joystick_callback(event):
    if event.type == pd.events.JOYHATMOTION:
        if event.hat == 0:
            if event.value[1] != 0:
                select_item(event.value[1] > 0)

board_config.runtime.on_device(eventsys.JOYSTICK, joystick_callback)

board_config.runtime.run_forever()
