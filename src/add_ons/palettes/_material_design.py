_colors = (
    # black
    b"\x00\x00\x00"
    # white
    b"\xff\xff\xff"
    # red
    b"\xff\xeb\xee"  # 50
    b"\xff\xcd\xd2"  # 100
    b"\xef\x9a\x9a"  # 200
    b"\xe5\x73\x73"  # 300
    b"\xef\x53\x50"  # 400
    b"\xf4\x43\x36"  # 500
    b"\xe5\x39\x35"  # 600
    b"\xd3\x2f\x2f"  # 700
    b"\xc6\x28\x28"  # 800
    b"\xb7\x1c\x1c"  # 900
    b"\xff\x8a\x80"  # A100
    b"\xff\x52\x52"  # A200
    b"\xff\x17\x44"  # A400
    b"\xd5\x00\x00"  # A700
    # pink
    b"\xfc\xeb\xee"  # 50
    b"\xf8\xbb\xd0"  # 100
    b"\xf4\x8f\xb1"  # 200
    b"\xf0\x62\x92"  # 300
    b"\xec\x40\x7a"  # 400
    b"\xe9\x1e\x63"  # 500
    b"\xd8\x1b\x60"  # 600
    b"\xc2\x18\x5b"  # 700
    b"\xad\x14\x57"  # 800
    b"\x88\x0e\x4f"  # 900
    b"\xff\x80\xab"  # A100
    b"\xff\x40\x81"  # A200
    b"\xf5\x00\x57"  # A400
    b"\xc5\x11\x62"  # A700
    # purple
    b"\xf3\xe5\xf5"  # 50
    b"\xe1\xbe\xe7"  # 100
    b"\xce\x93\xd8"  # 200
    b"\xba\x68\xc8"  # 300
    b"\xab\x47\xbc"  # 400
    b"\x9c\x27\xb0"  # 500
    b"\x8e\x24\xaa"  # 600
    b"\x7b\x1f\xa2"  # 700
    b"\x6a\x1b\x9a"  # 800
    b"\x4a\x14\x8c"  # 900
    b"\xea\x80\xfc"  # A100
    b"\xe0\x40\xfb"  # A200
    b"\xd5\x00\xf9"  # A400
    b"\xaa\x00\xff"  # A700
    # deep_purple
    b"\xed\xe7\xf6"  # 50
    b"\xd1\xc4\xe9"  # 100
    b"\xb3\x9d\xdb"  # 200
    b"\x95\x75\xcd"  # 300
    b"\x7e\x57\xc2"  # 400
    b"\x67\x3a\xb7"  # 500
    b"\x5e\x35\xb1"  # 600
    b"\x51\x2d\xa8"  # 700
    b"\x45\x27\xa0"  # 800
    b"\x31\x1b\x92"  # 900
    b"\xb3\x88\xff"  # A100
    b"\x7c\x4d\xff"  # A200
    b"\x65\x1f\xff"  # A400
    b"\x62\x00\xea"  # A700
    # indigo
    b"\xe8\xea\xf6"  # 50
    b"\xc5\xca\xe9"  # 100
    b"\x9f\xa8\xda"  # 200
    b"\x79\x86\xcb"  # 300
    b"\x5c\x6b\xc0"  # 400
    b"\x3f\x51\xb5"  # 500
    b"\x39\x49\xab"  # 600
    b"\x30\x3f\x9f"  # 700
    b"\x28\x35\x93"  # 800
    b"\x1a\x23\x7e"  # 900
    b"\x8c\x9e\xff"  # A100
    b"\x53\x6d\xfe"  # A200
    b"\x3d\x5a\xfe"  # A400
    b"\x30\x4f\xfe"  # A700
    # blue
    b"\xe3\xf2\xfd"  # 50
    b"\xbb\xde\xfb"  # 100
    b"\x90\xca\xf9"  # 200
    b"\x64\xb5\xf6"  # 300
    b"\x42\xa5\xf5"  # 400
    b"\x21\x96\xf3"  # 500
    b"\x1e\x88\xe5"  # 600
    b"\x19\x76\xd2"  # 700
    b"\x15\x65\xc0"  # 800
    b"\x0d\x47\xa1"  # 900
    b"\x82\xb1\xff"  # A100
    b"\x44\x8a\xff"  # A200
    b"\x29\x79\xff"  # A400
    b"\x29\x62\xff"  # A700
    # light_blue
    b"\xe1\xf5\xfe"  # 50
    b"\xb3\xe5\xfc"  # 100
    b"\x81\xd4\xfa"  # 200
    b"\x4f\xc3\xf7"  # 300
    b"\x29\xb6\xf6"  # 400
    b"\x03\xa9\xf4"  # 500
    b"\x03\x9b\xe5"  # 600
    b"\x02\x88\xd1"  # 700
    b"\x02\x77\xbd"  # 800
    b"\x01\x57\x9b"  # 900
    b"\x80\xd8\xff"  # A100
    b"\x40\xc4\xff"  # A200
    b"\x00\xb0\xff"  # A400
    b"\x00\x91\xea"  # A700
    # cyan
    b"\xe0\xf7\xfa"  # 50
    b"\xb2\xeb\xf2"  # 100
    b"\x80\xde\xea"  # 200
    b"\x4d\xd0\xe1"  # 300
    b"\x26\xc6\xda"  # 400
    b"\x00\xbc\xd4"  # 500
    b"\x00\xac\xc1"  # 600
    b"\x00\x97\xa7"  # 700
    b"\x00\x83\x8f"  # 800
    b"\x00\x60\x64"  # 900
    b"\x84\xff\xff"  # A100
    b"\x18\xff\xff"  # A200
    b"\x00\xe5\xff"  # A400
    b"\x00\xb8\xd4"  # A700
    # teal
    b"\xe0\xf2\xf1"  # 50
    b"\xb2\xdf\xdb"  # 100
    b"\x80\xcb\xc4"  # 200
    b"\x4d\xb6\xac"  # 300
    b"\x26\xa6\x9a"  # 400
    b"\x00\x96\x88"  # 500
    b"\x00\x89\x7b"  # 600
    b"\x00\x79\x6b"  # 700
    b"\x00\x69\x5c"  # 800
    b"\x00\x4d\x40"  # 900
    b"\xa7\xff\xeb"  # A100
    b"\x64\xff\xda"  # A200
    b"\x1d\xe9\xb6"  # A400
    b"\x00\xbf\xa5"  # A700
    # green
    b"\xe8\xf5\xe9"  # 50
    b"\xc8\xe6\xc9"  # 100
    b"\xa5\xd6\xa7"  # 200
    b"\x81\xc7\x84"  # 300
    b"\x66\xbb\x6a"  # 400
    b"\x4c\xaf\x50"  # 500
    b"\x43\xa0\x47"  # 600
    b"\x38\x8e\x3c"  # 700
    b"\x2e\x7d\x32"  # 800
    b"\x1b\x5e\x20"  # 900
    b"\xb9\xf6\xca"  # A100
    b"\x69\xf0\xae"  # A200
    b"\x00\xe6\x76"  # A400
    b"\x00\xc8\x53"  # A700
    # light_green
    b"\xf1\xf8\xe9"  # 50
    b"\xdc\xed\xc8"  # 100
    b"\xc5\xe1\xa5"  # 200
    b"\xae\xd5\x81"  # 300
    b"\x9c\xcc\x65"  # 400
    b"\x8b\xc3\x4a"  # 500
    b"\x7c\xb3\x42"  # 600
    b"\x68\x9f\x38"  # 700
    b"\x55\x8b\x2f"  # 800
    b"\x33\x69\x1e"  # 900
    b"\xcc\xff\x90"  # A100
    b"\xb2\xff\x59"  # A200
    b"\x76\xff\x03"  # A400
    b"\x64\xdd\x17"  # A700
    # lime
    b"\xf9\xfb\xe7"  # 50
    b"\xf0\xf4\xc3"  # 100
    b"\xe6\xee\x9c"  # 200
    b"\xdc\xe7\x75"  # 300
    b"\xd4\xe1\x57"  # 400
    b"\xcd\xdc\x39"  # 500
    b"\xc0\xca\x33"  # 600
    b"\xaf\xb4\x2b"  # 700
    b"\x9e\x9d\x24"  # 800
    b"\x82\x77\x17"  # 900
    b"\xf4\xff\x81"  # A100
    b"\xee\xff\x41"  # A200
    b"\xc6\xff\x00"  # A400
    b"\xae\xea\x00"  # A700
    # yellow
    b"\xff\xfd\xe7"  # 50
    b"\xff\xf9\xc4"  # 100
    b"\xff\xf5\x9d"  # 200
    b"\xff\xf1\x76"  # 300
    b"\xff\xee\x58"  # 400
    b"\xff\xeb\x3b"  # 500
    b"\xfd\xd8\x35"  # 600
    b"\xfb\xc0\x2d"  # 700
    b"\xf9\xa8\x25"  # 800
    b"\xf5\x7f\x17"  # 900
    b"\xff\xff\x8d"  # A100
    b"\xff\xff\x00"  # A200
    b"\xff\xea\x00"  # A400
    b"\xff\xd6\x00"  # A700
    # amber
    b"\xff\xf8\xe1"  # 50
    b"\xff\xec\xb3"  # 100
    b"\xff\xe0\x82"  # 200
    b"\xff\xd5\x4f"  # 300
    b"\xff\xca\x28"  # 400
    b"\xff\xc1\x07"  # 500
    b"\xff\xb3\x00"  # 600
    b"\xff\xa0\x00"  # 700
    b"\xff\x8f\x00"  # 800
    b"\xff\x6f\x00"  # 900
    b"\xff\xe5\x7f"  # A100
    b"\xff\xd7\x40"  # A200
    b"\xff\xc4\x00"  # A400
    b"\xff\xab\x00"  # A700
    # orange
    b"\xff\xf3\xe0"  # 50
    b"\xff\xe0\xb2"  # 100
    b"\xff\xcc\x80"  # 200
    b"\xff\xb7\x4d"  # 300
    b"\xff\xa7\x26"  # 400
    b"\xff\x98\x00"  # 500
    b"\xfb\x8c\x00"  # 600
    b"\xf5\x7c\x00"  # 700
    b"\xef\x6c\x00"  # 800
    b"\xe6\x51\x00"  # 900
    b"\xff\xd1\x80"  # A100
    b"\xff\xab\x40"  # A200
    b"\xff\x91\x00"  # A400
    b"\xff\x6d\x00"  # A700
    # deep_orange
    b"\xfb\xe9\xe7"  # 50
    b"\xff\xcc\xbc"  # 100
    b"\xff\xab\x91"  # 200
    b"\xff\x8a\x65"  # 300
    b"\xff\x70\x43"  # 400
    b"\xff\x57\x22"  # 500
    b"\xf4\x51\x1e"  # 600
    b"\xe6\x4a\x19"  # 700
    b"\xd8\x43\x15"  # 800
    b"\xbf\x36\x0c"  # 900
    b"\xff\x9e\x80"  # A100
    b"\xff\x6e\x40"  # A200
    b"\xff\x3d\x00"  # A400
    b"\xdd\x2c\x00"  # A700
    # brown
    b"\xef\xeb\xe9"  # 50
    b"\xd7\xcc\xc8"  # 100
    b"\xbc\xaa\xa4"  # 200
    b"\xa1\x88\x7f"  # 300
    b"\x8d\x6e\x63"  # 400
    b"\x79\x55\x48"  # 500
    b"\x6d\x4c\x41"  # 600
    b"\x5d\x40\x37"  # 700
    b"\x4e\x34\x2e"  # 800
    b"\x3e\x27\x23"  # 900
    # grey
    b"\xfa\xfa\xfa"  # 50
    b"\xf5\xf5\xf5"  # 100
    b"\xee\xee\xee"  # 200
    b"\xe0\xe0\xe0"  # 300
    b"\xbd\xbd\xbd"  # 400
    b"\x9e\x9e\x9e"  # 500
    b"\x75\x75\x75"  # 600
    b"\x61\x61\x61"  # 700
    b"\x42\x42\x42"  # 800
    b"\x21\x21\x21"  # 900
    # blue_grey
    b"\xec\xef\xf1"  # 50
    b"\xcf\xd8\xdc"  # 100
    b"\xb0\xbe\xc5"  # 200
    b"\x90\xa4\xae"  # 300
    b"\x78\x90\x9c"  # 400
    b"\x60\x7d\x8b"  # 500
    b"\x54\x6e\x7a"  # 600
    b"\x45\x5a\x64"  # 700
    b"\x37\x47\x4f"  # 800
    b"\x26\x32\x38"  # 900
)

FAMILIES = [
    "black",
    "white",
    "red",
    "pink",
    "purple",
    "deep_purple",
    "indigo",
    "blue",
    "light_blue",
    "cyan",
    "teal",
    "green",
    "light_green",
    "lime",
    "yellow",
    "amber",
    "orange",
    "deep_orange",
    "brown",
    "grey",
    "blue_grey",
]

LENGTHS = [
    1,
    1,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    14,
    10,
    10,
    10,
]

COLORS = memoryview(_colors)
