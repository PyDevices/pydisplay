# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
`eventsys.keys`
====================================================
"""

try:
    from micropython import const as _const
except ImportError:

    def _const(x):
        return x


class Keys:
    """
    A container for key codes and names.  Similar to a C enum and struct.
    """

    def keyname(x):
        return Keys._keytable.get(x, "Unknown")

    def key(x):
        return list(Keys._keytable.keys())[list(Keys._keytable.values()).index(x)]

    def modname(x):
        return Keys._modtable.get(x, "Unknown")

    def mod(x):
        return list(Keys._modtable.keys())[list(Keys._modtable.values()).index(x)]

    K_UNKNOWN = _const(0)
    K_BACKSPACE = _const(8)
    K_TAB = _const(9)
    K_RETURN = _const(13)
    K_ESCAPE = _const(27)
    K_SPACE = _const(32)
    K_EXCLAIM = _const(33)
    K_QUOTEDBL = _const(34)
    K_HASH = _const(35)
    K_DOLLAR = _const(36)
    K_PERCENT = _const(37)
    K_AMPERSAND = _const(38)
    K_QUOTE = _const(39)
    K_LEFTPAREN = _const(40)
    K_RIGHTPAREN = _const(41)
    K_ASTERISK = _const(42)
    K_PLUS = _const(43)
    K_COMMA = _const(44)
    K_MINUS = _const(45)
    K_PERIOD = _const(46)
    K_SLASH = _const(47)
    K_0 = _const(48)
    K_1 = _const(49)
    K_2 = _const(50)
    K_3 = _const(51)
    K_4 = _const(52)
    K_5 = _const(53)
    K_6 = _const(54)
    K_7 = _const(55)
    K_8 = _const(56)
    K_9 = _const(57)
    K_COLON = _const(58)
    K_SEMICOLON = _const(59)
    K_LESS = _const(60)
    K_EQUALS = _const(61)
    K_GREATER = _const(62)
    K_QUESTION = _const(63)
    K_AT = _const(64)
    K_LEFTBRACKET = _const(91)
    K_BACKSLASH = _const(92)
    K_RIGHTBRACKET = _const(93)
    K_CARET = _const(94)
    K_UNDERSCORE = _const(95)
    K_BACKQUOTE = _const(96)
    K_a = _const(97)
    K_b = _const(98)
    K_c = _const(99)
    K_d = _const(100)
    K_e = _const(101)
    K_f = _const(102)
    K_g = _const(103)
    K_h = _const(104)
    K_i = _const(105)
    K_j = _const(106)
    K_k = _const(107)
    K_l = _const(108)
    K_m = _const(109)
    K_n = _const(110)
    K_o = _const(111)
    K_p = _const(112)
    K_q = _const(113)
    K_r = _const(114)
    K_s = _const(115)
    K_t = _const(116)
    K_u = _const(117)
    K_v = _const(118)
    K_w = _const(119)
    K_x = _const(120)
    K_y = _const(121)
    K_z = _const(122)
    K_DELETE = _const(127)
    K_CAPSLOCK = _const(1073741881)
    K_F1 = _const(1073741882)
    K_F2 = _const(1073741883)
    K_F3 = _const(1073741884)
    K_F4 = _const(1073741885)
    K_F5 = _const(1073741886)
    K_F6 = _const(1073741887)
    K_F7 = _const(1073741888)
    K_F8 = _const(1073741889)
    K_F9 = _const(1073741890)
    K_F10 = _const(1073741891)
    K_F11 = _const(1073741892)
    K_F12 = _const(1073741893)
    K_PRINTSCREEN = _const(1073741894)
    K_SCROLLLOCK = _const(1073741895)
    K_PAUSE = _const(1073741896)
    K_INSERT = _const(1073741897)
    K_HOME = _const(1073741898)
    K_PAGEUP = _const(1073741899)
    K_END = _const(1073741901)
    K_PAGEDOWN = _const(1073741902)
    K_RIGHT = _const(1073741903)
    K_LEFT = _const(1073741904)
    K_DOWN = _const(1073741905)
    K_UP = _const(1073741906)
    K_NUMLOCKCLEAR = _const(1073741907)
    K_KP_DIVIDE = _const(1073741908)
    K_KP_MULTIPLY = _const(1073741909)
    K_KP_MINUS = _const(1073741910)
    K_KP_PLUS = _const(1073741911)
    K_KP_ENTER = _const(1073741912)
    K_KP_1 = _const(1073741913)
    K_KP_2 = _const(1073741914)
    K_KP_3 = _const(1073741915)
    K_KP_4 = _const(1073741916)
    K_KP_5 = _const(1073741917)
    K_KP_6 = _const(1073741918)
    K_KP_7 = _const(1073741919)
    K_KP_8 = _const(1073741920)
    K_KP_9 = _const(1073741921)
    K_KP_0 = _const(1073741922)
    K_KP_PERIOD = _const(1073741923)
    K_APPLICATION = _const(1073741925)
    K_POWER = _const(1073741926)
    K_KP_EQUALS = _const(1073741927)
    K_F13 = _const(1073741928)
    K_F14 = _const(1073741929)
    K_F15 = _const(1073741930)
    K_F16 = _const(1073741931)
    K_F17 = _const(1073741932)
    K_F18 = _const(1073741933)
    K_F19 = _const(1073741934)
    K_F20 = _const(1073741935)
    K_F21 = _const(1073741936)
    K_F22 = _const(1073741937)
    K_F23 = _const(1073741938)
    K_F24 = _const(1073741939)
    K_EXECUTE = _const(1073741940)
    K_HELP = _const(1073741941)
    K_MENU = _const(1073741942)
    K_SELECT = _const(1073741943)
    K_STOP = _const(1073741944)
    K_AGAIN = _const(1073741945)
    K_UNDO = _const(1073741946)
    K_CUT = _const(1073741947)
    K_COPY = _const(1073741948)
    K_PASTE = _const(1073741949)
    K_FIND = _const(1073741950)
    K_MUTE = _const(1073741951)
    K_VOLUMEUP = _const(1073741952)
    K_VOLUMEDOWN = _const(1073741953)
    K_KP_COMMA = _const(1073741957)
    K_KP_EQUALSAS400 = _const(1073741958)
    K_ALTERASE = _const(1073741977)
    K_SYSREQ = _const(1073741978)
    K_CANCEL = _const(1073741979)
    K_CLEAR = _const(1073741980)
    K_PRIOR = _const(1073741981)
    K_RETURN2 = _const(1073741982)
    K_SEPARATOR = _const(1073741983)
    K_OUT = _const(1073741984)
    K_OPER = _const(1073741985)
    K_CLEARAGAIN = _const(1073741986)
    K_CRSEL = _const(1073741987)
    K_EXSEL = _const(1073741988)
    K_KP_00 = _const(1073742000)
    K_KP_000 = _const(1073742001)
    K_THOUSANDSSEPARATOR = _const(1073742002)
    K_DECIMALSEPARATOR = _const(1073742003)
    K_CURRENCYUNIT = _const(1073742004)
    K_CURRENCYSUBUNIT = _const(1073742005)
    K_KP_LEFTPAREN = _const(1073742006)
    K_KP_RIGHTPAREN = _const(1073742007)
    K_KP_LEFTBRACE = _const(1073742008)
    K_KP_RIGHTBRACE = _const(1073742009)
    K_KP_TAB = _const(1073742010)
    K_KP_BACKSPACE = _const(1073742011)
    K_KP_A = _const(1073742012)
    K_KP_B = _const(1073742013)
    K_KP_C = _const(1073742014)
    K_KP_D = _const(1073742015)
    K_KP_E = _const(1073742016)
    K_KP_F = _const(1073742017)
    K_KP_XOR = _const(1073742018)
    K_KP_POWER = _const(1073742019)
    K_KP_PERCENT = _const(1073742020)
    K_KP_LESS = _const(1073742021)
    K_KP_GREATER = _const(1073742022)
    K_KP_AMPERSAND = _const(1073742023)
    K_KP_DBLAMPERSAND = _const(1073742024)
    K_KP_VERTICALBAR = _const(1073742025)
    K_KP_DBLVERTICALBAR = _const(1073742026)
    K_KP_COLON = _const(1073742027)
    K_KP_HASH = _const(1073742028)
    K_KP_SPACE = _const(1073742029)
    K_KP_AT = _const(1073742030)
    K_KP_EXCLAM = _const(1073742031)
    K_KP_MEMSTORE = _const(1073742032)
    K_KP_MEMRECALL = _const(1073742033)
    K_KP_MEMCLEAR = _const(1073742034)
    K_KP_MEMADD = _const(1073742035)
    K_KP_MEMSUBTRACT = _const(1073742036)
    K_KP_MEMMULTIPLY = _const(1073742037)
    K_KP_MEMDIVIDE = _const(1073742038)
    K_KP_PLUSMINUS = _const(1073742039)
    K_KP_CLEAR = _const(1073742040)
    K_KP_CLEARENTRY = _const(1073742041)
    K_KP_BINARY = _const(1073742042)
    K_KP_OCTAL = _const(1073742043)
    K_KP_DECIMAL = _const(1073742044)
    K_KP_HEXADECIMAL = _const(1073742045)
    K_LCTRL = _const(1073742048)
    K_LSHIFT = _const(1073742049)
    K_LALT = _const(1073742050)
    K_LGUI = _const(1073742051)
    K_RCTRL = _const(1073742052)
    K_RSHIFT = _const(1073742053)
    K_RALT = _const(1073742054)
    K_RGUI = _const(1073742055)
    K_MODE = _const(1073742081)
    K_AUDIONEXT = _const(1073742082)
    K_AUDIOPREV = _const(1073742083)
    K_AUDIOSTOP = _const(1073742084)
    K_AUDIOPLAY = _const(1073742085)
    K_AUDIOMUTE = _const(1073742086)
    K_MEDIASELECT = _const(1073742087)
    K_WWW = _const(1073742088)
    K_MAIL = _const(1073742089)
    K_CALCULATOR = _const(1073742090)
    K_COMPUTER = _const(1073742091)
    K_AC_SEARCH = _const(1073742092)
    K_AC_HOME = _const(1073742093)
    K_AC_BACK = _const(1073742094)
    K_AC_FORWARD = _const(1073742095)
    K_AC_STOP = _const(1073742096)
    K_AC_REFRESH = _const(1073742097)
    K_AC_BOOKMARKS = _const(1073742098)
    K_BRIGHTNESSDOWN = _const(1073742099)
    K_BRIGHTNESSUP = _const(1073742100)
    K_DISPLAYSWITCH = _const(1073742101)
    K_KBDILLUMTOGGLE = _const(1073742102)
    K_KBDILLUMDOWN = _const(1073742103)
    K_KBDILLUMUP = _const(1073742104)
    K_EJECT = _const(1073742105)
    K_SLEEP = _const(1073742106)

    _keytable = {
        K_UNKNOWN: "Unknown",
        K_BACKSPACE: "Backspace",
        K_TAB: "Tab",
        K_RETURN: "Return",
        K_ESCAPE: "Escape",
        K_SPACE: "Space",
        K_EXCLAIM: "!",
        K_QUOTEDBL: '"',
        K_HASH: "#",
        K_DOLLAR: "$",
        K_PERCENT: "%",
        K_AMPERSAND: "&",
        K_QUOTE: "'",
        K_LEFTPAREN: "(",
        K_RIGHTPAREN: ")",
        K_ASTERISK: "*",
        K_PLUS: "+",
        K_COMMA: ",",
        K_MINUS: "-",
        K_PERIOD: ".",
        K_SLASH: "/",
        K_0: "0",
        K_1: "1",
        K_2: "2",
        K_3: "3",
        K_4: "4",
        K_5: "5",
        K_6: "6",
        K_7: "7",
        K_8: "8",
        K_9: "9",
        K_COLON: ":",
        K_SEMICOLON: ";",
        K_LESS: "<",
        K_EQUALS: "=",
        K_GREATER: ">",
        K_QUESTION: "?",
        K_AT: "@",
        # 65: " A",
        # 66: " B",
        # 67: " C",
        # 68: " D",
        # 69: " E",
        # 70: " F",
        # 71: " G",
        # 72: " H",
        # 73: " I",
        # 74: " J",
        # 75: " K",
        # 76: " L",
        # 77: " M",
        # 78: " N",
        # 79: " O",
        # 80: " P",
        # 81: " Q",
        # 82: " R",
        # 83: " S",
        # 84: " T",
        # 85: " U",
        # 86: " V",
        # 87: " W",
        # 88: " X",
        # 89: " Y",
        # 90: " Z",
        K_LEFTBRACKET: "[",
        K_BACKSLASH: "\\",
        K_RIGHTBRACKET: "]",
        K_CARET: "^",
        K_UNDERSCORE: "_",
        K_BACKQUOTE: "`",
        K_a: "A",
        K_b: "B",
        K_c: "C",
        K_d: "D",
        K_e: "E",
        K_f: "F",
        K_g: "G",
        K_h: "H",
        K_i: "I",
        K_j: "J",
        K_k: "K",
        K_l: "L",
        K_m: "M",
        K_n: "N",
        K_o: "O",
        K_p: "P",
        K_q: "Q",
        K_r: "R",
        K_s: "S",
        K_t: "T",
        K_u: "U",
        K_v: "V",
        K_w: "W",
        K_x: "X",
        K_y: "Y",
        K_z: "Z",
        # 123: "{",
        # 124: "|",
        # 125: "}",
        # 126: "~",
        K_DELETE: "Delete",
        K_CAPSLOCK: "CapsLock",
        K_F1: "F1",
        K_F2: "F2",
        K_F3: "F3",
        K_F4: "F4",
        K_F5: "F5",
        K_F6: "F6",
        K_F7: "F7",
        K_F8: "F8",
        K_F9: "F9",
        K_F10: "F10",
        K_F11: "F11",
        K_F12: "F12",
        K_PRINTSCREEN: "PrintScreen",
        K_SCROLLLOCK: "ScrollLock",
        K_PAUSE: "Pause",
        K_INSERT: "Insert",
        K_HOME: "Home",
        K_PAGEUP: "PageUp",
        K_END: "End",
        K_PAGEDOWN: "PageDown",
        K_RIGHT: "Right",
        K_LEFT: "Left",
        K_DOWN: "Down",
        K_UP: "Up",
        K_NUMLOCKCLEAR: "Numlock",
        K_KP_DIVIDE: "Keypad /",
        K_KP_MULTIPLY: "Keypad *",
        K_KP_MINUS: "Keypad -",
        K_KP_PLUS: "Keypad +",
        K_KP_ENTER: "Keypad Enter",
        K_KP_1: "Keypad 1",
        K_KP_2: "Keypad 2",
        K_KP_3: "Keypad 3",
        K_KP_4: "Keypad 4",
        K_KP_5: "Keypad 5",
        K_KP_6: "Keypad 6",
        K_KP_7: "Keypad 7",
        K_KP_8: "Keypad 8",
        K_KP_9: "Keypad 9",
        K_KP_0: "Keypad 0",
        K_KP_PERIOD: "Keypad .",
        K_APPLICATION: "Application",
        K_POWER: "Power",
        K_KP_EQUALS: "Keypad =",
        K_F13: "F13",
        K_F14: "F14",
        K_F15: "F15",
        K_F16: "F16",
        K_F17: "F17",
        K_F18: "F18",
        K_F19: "F19",
        K_F20: "F20",
        K_F21: "F21",
        K_F22: "F22",
        K_F23: "F23",
        K_F24: "F24",
        K_EXECUTE: "Execute",
        K_HELP: "Help",
        K_MENU: "Menu",
        K_SELECT: "Select",
        K_STOP: "Stop",
        K_AGAIN: "Again",
        K_UNDO: "Undo",
        K_CUT: "Cut",
        K_COPY: "Copy",
        K_PASTE: "Paste",
        K_FIND: "Find",
        K_MUTE: "Mute",
        K_VOLUMEUP: "VolumeUp",
        K_VOLUMEDOWN: "VolumeDown",
        K_KP_COMMA: "Keypad ",
        K_KP_EQUALSAS400: "Keypad = (AS400)",
        K_ALTERASE: "AltErase",
        K_SYSREQ: "SysReq",
        K_CANCEL: "Cancel",
        K_CLEAR: "Clear",
        K_PRIOR: "Prior",
        K_RETURN2: "Return",
        K_SEPARATOR: "Separator",
        K_OUT: "Out",
        K_OPER: "Oper",
        K_CLEARAGAIN: "Clear / Again",
        K_CRSEL: "CrSel",
        K_EXSEL: "ExSel",
        K_KP_00: "Keypad 00",
        K_KP_000: "Keypad 000",
        K_THOUSANDSSEPARATOR: "ThousandsSeparator",
        K_DECIMALSEPARATOR: "DecimalSeparator",
        K_CURRENCYUNIT: "CurrencyUnit",
        K_CURRENCYSUBUNIT: "CurrencySubUnit",
        K_KP_LEFTPAREN: "Keypad (",
        K_KP_RIGHTPAREN: "Keypad )",
        K_KP_LEFTBRACE: "Keypad {",
        K_KP_RIGHTBRACE: "Keypad }",
        K_KP_TAB: "Keypad Tab",
        K_KP_BACKSPACE: "Keypad Backspace",
        K_KP_A: "Keypad A",
        K_KP_B: "Keypad B",
        K_KP_C: "Keypad C",
        K_KP_D: "Keypad D",
        K_KP_E: "Keypad E",
        K_KP_F: "Keypad F",
        K_KP_XOR: "Keypad XOR",
        K_KP_POWER: "Keypad ^",
        K_KP_PERCENT: "Keypad %",
        K_KP_LESS: "Keypad <",
        K_KP_GREATER: "Keypad >",
        K_KP_AMPERSAND: "Keypad &",
        K_KP_DBLAMPERSAND: "Keypad &&",
        K_KP_VERTICALBAR: "Keypad |",
        K_KP_DBLVERTICALBAR: "Keypad ||",
        K_KP_COLON: "Keypad :",
        K_KP_HASH: "Keypad #",
        K_KP_SPACE: "Keypad Space",
        K_KP_AT: "Keypad @",
        K_KP_EXCLAM: "Keypad !",
        K_KP_MEMSTORE: "Keypad MemStore",
        K_KP_MEMRECALL: "Keypad MemRecall",
        K_KP_MEMCLEAR: "Keypad MemClear",
        K_KP_MEMADD: "Keypad MemAdd",
        K_KP_MEMSUBTRACT: "Keypad MemSubtract",
        K_KP_MEMMULTIPLY: "Keypad MemMultiply",
        K_KP_MEMDIVIDE: "Keypad MemDivide",
        K_KP_PLUSMINUS: "Keypad +/-",
        K_KP_CLEAR: "Keypad Clear",
        K_KP_CLEARENTRY: "Keypad ClearEntry",
        K_KP_BINARY: "Keypad Binary",
        K_KP_OCTAL: "Keypad Octal",
        K_KP_DECIMAL: "Keypad Decimal",
        K_KP_HEXADECIMAL: "Keypad Hexadecimal",
        K_LCTRL: "Left Ctrl",
        K_LSHIFT: "Left Shift",
        K_LALT: "Left Alt",
        K_LGUI: "Left GUI",
        K_RCTRL: "Right Ctrl",
        K_RSHIFT: "Right Shift",
        K_RALT: "Right Alt",
        K_RGUI: "Right GUI",
        K_MODE: "ModeSwitch",
        K_AUDIONEXT: "AudioNext",
        K_AUDIOPREV: "AudioPrev",
        K_AUDIOSTOP: "AudioStop",
        K_AUDIOPLAY: "AudioPlay",
        K_AUDIOMUTE: "AudioMute",
        K_MEDIASELECT: "MediaSelect",
        K_WWW: "WWW",
        K_MAIL: "Mail",
        K_CALCULATOR: "Calculator",
        K_COMPUTER: "Computer",
        K_AC_SEARCH: "AC Search",
        K_AC_HOME: "AC Home",
        K_AC_BACK: "AC Back",
        K_AC_FORWARD: "AC Forward",
        K_AC_STOP: "AC Stop",
        K_AC_REFRESH: "AC Refresh",
        K_AC_BOOKMARKS: "AC Bookmarks",
        K_BRIGHTNESSDOWN: "BrightnessDown",
        K_BRIGHTNESSUP: "BrightnessUp",
        K_DISPLAYSWITCH: "DisplaySwitch",
        K_KBDILLUMTOGGLE: "KBDIllumToggle",
        K_KBDILLUMDOWN: "KBDIllumDown",
        K_KBDILLUMUP: "KBDIllumUp",
        K_EJECT: "Eject",
        K_SLEEP: "Sleep",
    }

    # SDL_Keycode mod values (not complete)
    KMOD_NONE = _const(0x0000)
    KMOD_LSHIFT = _const(0x0001)
    KMOD_RSHIFT = _const(0x0002)
    KMOD_LCTRL = _const(0x0040)
    KMOD_RCTRL = _const(0x0080)
    KMOD_LALT = _const(0x0100)
    KMOD_RALT = _const(0x0200)
    KMOD_LGUI = _const(0x0400)
    KMOD_RGUI = _const(0x0800)
    KMOD_NUM = _const(0x1000)
    KMOD_CAPS = _const(0x2000)
    KMOD_MODE = _const(0x4000)
    KMOD_CTRL = KMOD_LCTRL | KMOD_RCTRL
    KMOD_SHIFT = KMOD_LSHIFT | KMOD_RSHIFT
    KMOD_ALT = KMOD_LALT | KMOD_RALT
    KMOD_GUI = KMOD_LGUI | KMOD_RGUI

    _modtable = {
        KMOD_NONE: "None",
        KMOD_LSHIFT: "Left Shift",
        KMOD_RSHIFT: "Right Shift",
        KMOD_LCTRL: "Left Ctrl",
        KMOD_RCTRL: "Right Ctrl",
        KMOD_LALT: "Left Alt",
        KMOD_RALT: "Right Alt",
        KMOD_LGUI: "Left GUI",
        KMOD_RGUI: "Right GUI",
        KMOD_NUM: "Num Lock",
        KMOD_CAPS: "Caps Lock",
        KMOD_MODE: "Mode",
        KMOD_CTRL: "Ctrl",
        KMOD_SHIFT: "Shift",
        KMOD_ALT: "Alt",
        KMOD_GUI: "GUI",
    }


# ---------------------------------------------------------------------------
# Browser / DOM keyboard helpers
#
# Translate values from a JavaScript ``KeyboardEvent`` (as delivered by
# PyScript or ipyevents) into the SDL-style key codes and modifier masks above,
# so web/notebook backends can emit the same ``Key`` events as the desktop
# SDL2 / PyGame backends.  ``KeyboardEvent.key`` holds either a single printable
# character (mapped by code point) or a named value such as ``"ArrowUp"``
# (mapped via the table below).
# ---------------------------------------------------------------------------

_DOM_NAMED_KEYS = {
    "Backspace": Keys.K_BACKSPACE,
    "Tab": Keys.K_TAB,
    "Enter": Keys.K_RETURN,
    "Escape": Keys.K_ESCAPE,
    "Delete": Keys.K_DELETE,
    "ArrowUp": Keys.K_UP,
    "ArrowDown": Keys.K_DOWN,
    "ArrowLeft": Keys.K_LEFT,
    "ArrowRight": Keys.K_RIGHT,
    "Home": Keys.K_HOME,
    "End": Keys.K_END,
    "PageUp": Keys.K_PAGEUP,
    "PageDown": Keys.K_PAGEDOWN,
    "Insert": Keys.K_INSERT,
    "CapsLock": Keys.K_CAPSLOCK,
    "NumLock": Keys.K_NUMLOCKCLEAR,
    "ScrollLock": Keys.K_SCROLLLOCK,
    "Pause": Keys.K_PAUSE,
    "PrintScreen": Keys.K_PRINTSCREEN,
    "ContextMenu": Keys.K_MENU,
    "Control": Keys.K_LCTRL,
    "Shift": Keys.K_LSHIFT,
    "Alt": Keys.K_LALT,
    "Meta": Keys.K_LGUI,
    "F1": Keys.K_F1,
    "F2": Keys.K_F2,
    "F3": Keys.K_F3,
    "F4": Keys.K_F4,
    "F5": Keys.K_F5,
    "F6": Keys.K_F6,
    "F7": Keys.K_F7,
    "F8": Keys.K_F8,
    "F9": Keys.K_F9,
    "F10": Keys.K_F10,
    "F11": Keys.K_F11,
    "F12": Keys.K_F12,
}

# Right-hand variants of modifier keys, selected when the DOM key event reports
# ``location == DOM_KEY_LOCATION_RIGHT`` (2).
_DOM_RIGHT_KEYS = {
    "Control": Keys.K_RCTRL,
    "Shift": Keys.K_RSHIFT,
    "Alt": Keys.K_RALT,
    "Meta": Keys.K_RGUI,
}

_MOD_GROUPS = (Keys.KMOD_CTRL, Keys.KMOD_SHIFT, Keys.KMOD_ALT, Keys.KMOD_GUI)


def key_to_keycode(key, location=0):
    """
    Map a DOM ``KeyboardEvent.key`` value to an eventsys key code.

    Args:
        key (str): The ``KeyboardEvent.key`` value (e.g. ``"a"`` or ``"ArrowUp"``).
        location (int): The ``KeyboardEvent.location`` value.  ``2`` selects the
            right-hand variant of a modifier key (e.g. ``K_RCTRL``).

    Returns:
        int: The matching ``Keys.K_*`` code, or ``Keys.K_UNKNOWN``.
    """
    if location == 2:
        code = _DOM_RIGHT_KEYS.get(key)
        if code is not None:
            return code
    code = _DOM_NAMED_KEYS.get(key)
    if code is not None:
        return code
    if key and len(key) == 1:
        o = ord(key)
        if 0x41 <= o <= 0x5A:  # 'A'-'Z' -> lowercase code, matching SDL
            return o + 0x20
        return o
    return Keys.K_UNKNOWN


def mod_mask(ctrl, shift, alt, meta):
    """
    Build an eventsys modifier mask from DOM modifier flags.

    Args:
        ctrl (bool): Whether Ctrl is held.
        shift (bool): Whether Shift is held.
        alt (bool): Whether Alt is held.
        meta (bool): Whether Meta/GUI (Cmd/Win) is held.

    Returns:
        int: A mask of ``Keys.KMOD_*`` bits.
    """
    mask = 0
    if shift:
        mask |= Keys.KMOD_LSHIFT
    if ctrl:
        mask |= Keys.KMOD_LCTRL
    if alt:
        mask |= Keys.KMOD_LALT
    if meta:
        mask |= Keys.KMOD_LGUI
    return mask


def chord_matches(chord, keycode, mod):
    """
    Return True if ``(keycode, mod)`` satisfies a ``(key, mod_mask)`` chord.

    Modifier matching is group-aware: a required ``KMOD_CTRL`` is satisfied by
    either left or right Ctrl.  Extra modifiers beyond those required are
    ignored.

    Args:
        chord (tuple | None): A ``(key_code, modifier_mask)`` tuple, or None.
        keycode (int): The pressed key code.
        mod (int): The active modifier mask.

    Returns:
        bool: Whether the chord is satisfied.
    """
    if not chord:
        return False
    chord_key, chord_mod = chord
    if keycode != chord_key:
        return False
    for group in _MOD_GROUPS:
        if (chord_mod & group) and not (mod & group):
            return False
    return True
