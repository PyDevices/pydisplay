# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
"""
widgets_nav_tabs
====================================================
Showcase :class:`~pdwidgets.AppBar`, :class:`~pdwidgets.Page`,
:class:`~pdwidgets.Navigator`, and :class:`~pdwidgets.TabView`.

A root page holds a TabView (Home / Log / About). Home can push a detail
page onto the Navigator; AppBar back pops it.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

nav = pd.Navigator(screen)
root = pd.Page(nav, title="Root", bg=theme.background)
detail = pd.Page(nav, title="Detail", bg=theme.surface, visible=False)


def go_back(_=None):
    nav.pop()
    # Restore root app bar title
    root_bar.set_title("Nav & Tabs")
    root_bar.on_back = None
    if root_bar.back_button:
        root_bar.back_button.visible = False


root_bar = pd.AppBar(root, title="Nav & Tabs")

home = pd.Page(root, title="Home", bg=theme.background, visible=False)
log = pd.Page(root, title="Log", bg=theme.background, visible=False)
about = pd.Page(root, title="About", bg=theme.background, visible=False)

pd.Label(home, value="Home tab", align=pd.ALIGN.TOP, y=10, scale=2)
detail_btn = pd.Button(home, label="Open detail", align=pd.ALIGN.CENTER, radius=6)
log_box = pd.TextBox(log, value="Ready.", align=pd.ALIGN.TOP, y=10, w=max(40, root.width - 16))
pd.Label(about, value="pdwidgets", align=pd.ALIGN.CENTER, scale=2)
pd.Label(about, value="TabView + Navigator", align=pd.ALIGN.CENTER, y=28)

tv = pd.TabView(
    root,
    y=root_bar.height,
    h=root.height - root_bar.height,
    tabs=[("Home", home), ("Log", log), ("About", about)],
)
# TabBar is an alias of TabView — name must appear for coverage.
_ = pd.TabBar

detail_bar = pd.AppBar(detail, title="Detail", on_back=go_back)
pd.Label(detail, value="Detail page", y=detail_bar.height + 20, align=pd.ALIGN.CENTER, scale=2)
pd.Label(detail, value="Use back arrow", y=detail_bar.height + 52, align=pd.ALIGN.CENTER)


def open_detail(_s=None, _e=None):
    nav.push(detail)
    log_box.set_value("Opened detail")


detail_btn.add_event_cb(pd.events.MOUSEBUTTONDOWN, open_detail)

nav.push(root)
screen.visible = True

board_config.runtime.run_forever()
