# gallery: skip
from board_config import runtime
from keypins import KeyPins

import keys

# utils: keypins


buttons = KeyPins(
    left=keys.K_LEFT,
    right=keys.K_RIGHT,
    go=keys.K_UP,
    stop=keys.K_DOWN,
    fire=keys.K_SPACE,
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

# KeyPins updates on KEYDOWN/KEYUP via the runtime auto-service (no app poll).
runtime.on([runtime.events.KEYDOWN, runtime.events.KEYUP], buttons)

print(f"Press any of these keys:  {[button.keyname for button in buttons]}")


def _on_key(e):
    if runtime.quit_requested:
        return
    for button in buttons:
        if button.value():
            print(f"{button.name} ({button.keyname}) pressed")


runtime.on([runtime.events.KEYDOWN, runtime.events.KEYUP], _on_key)
runtime.run_forever()
