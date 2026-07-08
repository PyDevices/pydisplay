# multimer types: all
from board_config import runtime
from keypins import KeyPins, Keys


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
while True:
    if elist := runtime.poll():
        if any(e.type == runtime.events.QUIT for e in elist):
            break
    for button in buttons:
        if button.value():
            print(f"{button.name} ({button.keyname}) pressed")
