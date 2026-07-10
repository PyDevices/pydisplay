# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Themes used by the pdwidgets library.  The IconTheme class is used to manage icons and the ColorTheme class is used to manage colors.
"""

from palettes import get_palette  # noqa: F401

from ._constants import ICON_SIZE

try:
    from os import sep  # PyScript doesn't have os.sep
except ImportError:
    sep = "/"


class IconTheme:
    _suffix = "dp.pbm"
    _home = "home_filled_"
    _up_arrow = "keyboard_arrow_up_"
    _down_arrow = "keyboard_arrow_down_"
    _left_arrow = "keyboard_arrow_left_"
    _right_arrow = "keyboard_arrow_right_"
    _check_box_checked = "check_box_"
    _check_box_unchecked = "check_box_outline_blank_"
    _radio_button_checked = "radio_button_checked_"
    _radio_button_unchecked = "radio_button_unchecked_"
    _toggle_on = "toggle_on_"
    _toggle_off = "toggle_off_"
    _close = "close_"
    _add = "add_"
    _remove = "remove_"
    _info = "info_"
    _warning = "warning_"
    _error = "error_"
    _dropdown = "expand_more_"
    _menu = "menu_"

    def __init__(self, path):
        """
        A class to manage icon themes.  The path is the directory where the icons are stored.
        Icon file names are in the format "icon_name_18dp.pbm" where 18dp is the size of the icon.
        Valid sizes are in the ICON_SIZE enumeration, which are 18, 24, 36, and 48 pixels.

        Args:
            path (str): The path to the directory containing the icon files.

        Usage:
            from pdwidgets import IconTheme, ICON_SIZE
            icon_theme = IconTheme("/path/to/icons/")
            ...
            icon_button = IconButton(screen, icon_file=icon_theme.home(ICON_SIZE.LARGE), ...)
        """
        try:
            from os import sep  # PyScipt doesn't have os.sep
        except ImportError:
            sep = "/"
        if path[-1] != sep:
            path += sep
        self._path = path

    def _icon(self, name, size):
        if size not in ICON_SIZE:
            raise ValueError("Invalid icon size.")
        return f"{self._path}{getattr(self, '_' + name)}{size}{self._suffix}"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return lambda size: self._icon(name, size)


icon_theme = IconTheme(sep.join(__file__.split(sep)[0:-1]) + sep + "icons" + sep)


class ColorTheme:
    """
    Semantic color theme for pdwidgets.

    The default palette is a friendly, slightly colorful "early color Mac" look:
    a soft warm-cream background, near-black ink, and a small set of muted
    pastel accents (slate blue, warm gold, soft coral) with warm greys for
    inactive states — chunky-but-clean rather than a saturated Material blue.

    Colors are computed through ``pal.color565`` so the display's byteswap is
    respected. Widgets reference these slots by name, so re-skinning the whole
    toolkit is a matter of assigning different values here (or after
    construction via ``display.color_theme``).

    Args:
        pal (Palette): A palette object from the ``palettes`` package; used only
            for its ``color565`` conversion (and byteswap handling).
    """

    def __init__(self, pal):
        c = pal.color565
        # Neutrals
        self.background = c(0xF2EEE3)  # warm cream page
        self.on_background = c(0x2A2A30)  # near-black ink
        self.surface = c(0xFBF8F0)  # card / raised surface
        self.on_surface = c(0x2A2A30)
        self.surface_variant = c(0xE7E1D3)  # subtle sunken panel
        self.outline = c(0xB6AE9C)  # hairline borders
        self.shadow = c(0xCAC3B4)  # cheap fake drop shadow (warm grey)
        # Accents
        self.primary = c(0x4E6E8E)  # muted slate blue
        self.on_primary = c(0xFFFFFF)
        self.primary_variant = c(0x3A536B)  # darker slate (pressed / shadow)
        self.secondary = c(0xE6B24C)  # warm muted gold
        self.on_secondary = c(0x2A2A30)
        self.secondary_variant = c(0xCC7A5C)  # soft coral (third accent)
        self.tertiary = c(0x9E978A)  # warm grey (inactive)
        self.on_tertiary = c(0x2A2A30)
        self.tertiary_variant = c(0xC4BDAD)  # light warm grey
        # Status
        self.error = c(0xC1544A)  # muted brick red
        self.on_error = c(0xFFFFFF)
        self.success = c(0x5E9E6E)  # muted green (status dots, badges)
        self.on_success = c(0xFFFFFF)
        self.transparent = False
