# Align enum smoke for pdwidgets — labels at every ALIGN around a center button.
# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime, 40, 40)
screen = pd.Screen(display, None, visible=False)

if screen.partitioned:
    main = screen.main
else:
    main = screen

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

anchor = pd.Button(
    main, w=main.width // 3, h=48, align=pd.ALIGN.CENTER, label="anchor", radius=8
)
for name, align in zip(align_names, aligns):
    if align == pd.ALIGN.CENTER:
        continue
    pd.Label(main, align=align, align_to=anchor, value=name)

screen.visible = True
board_config.runtime.run_forever()
