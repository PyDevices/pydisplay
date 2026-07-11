# pyscript gallery: all
from board_config import runtime
from keypins import KeyPins, Keys
from multimer.loop import run_forever


buttons = KeyPins(
    left=Keys.K_LEFT,
    right=Keys.K_RIGHT,
    go=Keys.K_UP,
    stop=Keys.K_DOWN,
    fire=Keys.K_SPACE,
)

print("\nDetails of the buttons (KeyPins) object:")
print(f"\n{buttons=}")
print(f"\n{buttons=!s}")
print(f"\n{dir(buttons)=}\n")

print("\nFour ways to read the value: ")
print(f"{buttons.fire.value()=}")
print(f"{buttons.fire()=}")
print(f"{buttons['fire'].value()=}")
print(f"{buttons['fire']()=}\n")

print("\nOther attributes:")
print(f"{buttons.fire.name=}")
print(f"{buttons.fire.key=}")
print(f"{buttons.fire.keyname=}\n")

# Subscribe the to the display driver so _KeyPin states are updated
# on KEYDOWN and KEYUP events when runtime.poll() is called.
runtime.on([runtime.events.KEYDOWN, runtime.events.KEYUP], buttons)

print(f"Press any of these keys:  {[button.keyname for button in buttons]}")


def poll():
    elist = runtime.poll() if runtime else []
    if runtime.quit_requested if runtime else False:
        return True
    if any(e.type == runtime.events.QUIT for e in elist):
        return True
    for button in buttons:
        if button.value():
            print(f"{button.name} ({button.keyname}) pressed")
    return False


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(poll, delay_ms=20)
