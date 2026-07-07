#!/usr/bin/env python3
"""Generate RGB565 BMP assets for tower_climb.py (run once on CPython).

Temporary generator — remove after assets are approved.
  .venv/bin/python src/examples/assets/gen_tower_assets.py
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src" / "lib"))

from graphics._bmp565 import write_bmp565_file  # noqa: E402

OUT = Path(__file__).resolve().parent
REF_W = 320


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def buf(w, h, fill=0):
    b = bytearray(w * h * 2)
    lo, hi = fill & 0xFF, fill >> 8
    for i in range(0, len(b), 2):
        b[i] = lo
        b[i + 1] = hi
    return b


def put_px(data, w, x, y, c):
    if 0 <= x < w and 0 <= y < len(data) // (2 * w):
        i = (y * w + x) * 2
        data[i] = c & 0xFF
        data[i + 1] = c >> 8


def fill_rect(data, w, x, y, rw, rh, c):
    for j in range(y, y + rh):
        for i in range(x, x + rw):
            put_px(data, w, i, j, c)


def circle(data, w, cx, cy, r, c, fill=False):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if fill and d2 <= r * r:
                put_px(data, w, x, y, c)
            elif not fill and abs(math.sqrt(d2) - r) < 1.1:
                put_px(data, w, x, y, c)


def line(data, w, x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put_px(data, w, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def save(name, data, w, h):
    path = OUT / name
    with open(path, "wb") as f:
        write_bmp565_file(f, data, w, h)
    print(f"wrote {path} ({w}x{h})")


def gen_climber():
    # 4 frames x 3 poses (climb, jump, idle) @ 32x40
    # Top-left pixel (magenta) is the transparency key for blit_transparent.
    fw, fh = 32, 40
    cols, rows = 4, 3
    w, h = fw * cols, fh * rows
    TRANSPARENT = rgb565(255, 0, 255)
    data = buf(w, h, TRANSPARENT)

    SKIN = rgb565(255, 210, 160)
    COAT = rgb565(40, 120, 220)
    COAT_HI = rgb565(120, 200, 255)
    PANTS = rgb565(60, 40, 120)
    BOOT = rgb565(40, 30, 30)
    MALLET = rgb565(180, 180, 200)
    HELMET = rgb565(255, 80, 40)

    def draw_frame(ox, oy, pose, frame):
        # body
        fill_rect(data, w, ox + 10, oy + 14, 12, 16, COAT)
        fill_rect(data, w, ox + 11, oy + 15, 10, 4, COAT_HI)
        fill_rect(data, w, ox + 11, oy + 28, 4, 10, PANTS)
        fill_rect(data, w, ox + 17, oy + 28, 4, 10, PANTS)
        fill_rect(data, w, ox + 10, oy + 36, 5, 4, BOOT)
        fill_rect(data, w, ox + 17, oy + 36, 5, 4, BOOT)
        circle(data, w, ox + 16, oy + 10, 7, SKIN, True)
        fill_rect(data, w, ox + 10, oy + 4, 12, 5, HELMET)
        fill_rect(data, w, ox + 12, oy + 9, 3, 2, rgb565(20, 20, 40))
        fill_rect(data, w, ox + 18, oy + 9, 3, 2, rgb565(20, 20, 40))

        arm_swing = (frame % 4) - 1
        if pose == 0:  # climb
            fill_rect(data, w, ox + 4 + arm_swing, oy + 12, 4, 12, COAT)
            fill_rect(data, w, ox + 24 - arm_swing, oy + 16, 4, 10, COAT)
            fill_rect(data, w, ox + 2, oy + 8, 14, 4, MALLET)
        elif pose == 1:  # jump
            fill_rect(data, w, ox + 6, oy + 14, 4, 8, COAT)
            fill_rect(data, w, ox + 22, oy + 10, 4, 8, COAT)
            fill_rect(data, w, ox + 8, oy + 30, 4, 6, PANTS)
            fill_rect(data, w, ox + 20, oy + 30, 4, 6, PANTS)
        else:  # idle
            fill_rect(data, w, ox + 6, oy + 16, 4, 10, COAT)
            fill_rect(data, w, ox + 22, oy + 16, 4, 10, COAT)
            fill_rect(data, w, ox + 22, oy + 6, 10, 4, MALLET)

    for fr in range(cols):
        draw_frame(fr * fw, 0, 0, fr)
        draw_frame(fr * fw, fh, 1, fr)
        draw_frame(fr * fw, fh * 2, 2, fr)

    save("climber.bmp", data, w, h)


def gen_tiles():
    tw = 16
    cols, rows = 8, 4
    w, h = tw * cols, tw * rows
    data = buf(w, h, 0)

    BARK = rgb565(90, 55, 30)
    BARK_D = rgb565(60, 35, 18)
    BARK_L = rgb565(130, 85, 45)
    BRANCH = rgb565(70, 130, 50)
    BRANCH_L = rgb565(110, 200, 70)
    ICE = rgb565(160, 220, 255)
    ICE_D = rgb565(80, 160, 220)
    LEAF = rgb565(30, 170, 60)
    GEM = rgb565(255, 40, 180)
    GEM_HI = rgb565(255, 200, 255)
    SPIKE = rgb565(200, 200, 210)
    CLOUD = rgb565(240, 245, 255)

    tiles = [
        # bark trunk
        lambda ox, oy: (
            fill_rect(data, w, ox, oy, tw, tw, BARK),
            [fill_rect(data, w, ox + 2, oy + n, 2, 1, BARK_D) for n in range(0, tw, 4)],
            [fill_rect(data, w, ox + 10, oy + n, 2, 1, BARK_L) for n in range(2, tw, 5)],
        ),
        # branch L
        lambda ox, oy: (
            fill_rect(data, w, ox, oy + 8, tw, 6, BRANCH),
            fill_rect(data, w, ox, oy + 7, tw - 4, 2, BRANCH_L),
            fill_rect(data, w, ox, oy + 14, tw - 2, 2, BARK_D),
        ),
        # branch R
        lambda ox, oy: (
            fill_rect(data, w, ox, oy + 8, tw, 6, BRANCH),
            fill_rect(data, w, ox + 4, oy + 7, tw - 4, 2, BRANCH_L),
            fill_rect(data, w, ox + 2, oy + 14, tw - 2, 2, BARK_D),
        ),
        # ice block
        lambda ox, oy: (
            fill_rect(data, w, ox, oy, tw, tw, ICE),
            fill_rect(data, w, ox + 1, oy + 1, tw - 2, 2, ICE_D),
            fill_rect(data, w, ox + 2, oy + 4, tw - 6, 1, rgb565(255, 255, 255)),
        ),
        # leafy platform
        lambda ox, oy: (
            fill_rect(data, w, ox, oy + 10, tw, 4, BRANCH),
            [fill_rect(data, w, ox + i * 4, oy + 4, 5, 6, LEAF) for i in range(4)],
        ),
        # gem tile (collectible sparkle)
        lambda ox, oy: (
            fill_rect(data, w, ox + 4, oy + 2, 8, 12, GEM),
            fill_rect(data, w, ox + 6, oy + 4, 4, 8, GEM_HI),
            line(data, w, ox + 8, oy, ox + 8, oy + 15, rgb565(255, 255, 200)),
        ),
        # hazard spike
        lambda ox, oy: (
            fill_rect(data, w, ox, oy + 12, tw, 4, SPIKE),
            [line(data, w, ox + 2 + i * 3, oy + 12, ox + 5 + i * 3, oy, rgb565(255, 60, 80)) for i in range(4)],
        ),
        # cloud puff
        lambda ox, oy: (
            fill_rect(data, w, ox, oy + 8, tw, 6, CLOUD),
            circle(data, w, ox + 4, oy + 8, 4, CLOUD, True),
            circle(data, w, ox + 10, oy + 6, 5, CLOUD, True),
            circle(data, w, ox + 14, oy + 9, 3, CLOUD, True),
        ),
    ]

    for idx, draw in enumerate(tiles):
        ox = (idx % cols) * tw
        oy = (idx // cols) * tw
        draw(ox, oy)

    save("tower_tiles.bmp", data, w, h)


def gen_background():
    w = REF_W
    screens = 10
    h = 480 * screens
    data = buf(w, h, rgb565(8, 12, 40))

    for y in range(h):
        t = y / h
        r = int(8 + t * 40)
        g = int(12 + t * 80)
        b = int(40 + t * 120)
        c = rgb565(r, g, b)
        fill_rect(data, w, 0, y, w, 1, c)

    # distant tower silhouettes (Nebulus vibe)
    for tower in range(5):
        tx = 40 + tower * 58
        th = 120 + (tower * 37) % 80
        base = h - 200 - tower * 310
        for y in range(th):
            shade = rgb565(20 + tower * 8, 30 + tower * 6, 60 + tower * 10)
            width_at = 8 + (th - y) // 8
            fill_rect(data, w, tx - width_at // 2, base + y, width_at, 1, shade)

    # magical tree trunk center
    trunk_x = w // 2 - 18
    for y in range(h):
        wave = int(math.sin(y / 42) * 4)
        fill_rect(data, w, trunk_x + wave, y, 36, 1, rgb565(70, 42, 22))
        fill_rect(data, w, trunk_x + 6 + wave, y, 4, 1, rgb565(110, 70, 35))

    # foliage blobs climbing upward
    for n in range(80):
        fy = (n * 53) % h
        fx = w // 2 + int(math.sin(n * 1.7) * 90)
        rad = 10 + (n % 5) * 3
        c = rgb565(20 + (n % 3) * 20, 120 + (n % 4) * 20, 40)
        circle(data, w, fx, fy, rad, c, True)
        circle(data, w, fx - 4, fy - 3, rad - 4, rgb565(60, 200, 80), True)

    # stars higher up
    for n in range(120):
        sy = (n * 97) % (h // 2)
        sx = (n * 43) % w
        put_px(data, w, sx, sy, rgb565(255, 255, 220))

    # clouds
    for n in range(30):
        cy = (n * 151) % h
        cx = (n * 89) % (w - 60)
        for dx in range(50):
            put_px(data, w, cx + dx, cy, rgb565(230, 240, 255))
        circle(data, w, cx + 10, cy, 12, rgb565(240, 248, 255), True)
        circle(data, w, cx + 30, cy - 4, 16, rgb565(245, 250, 255), True)

    save("tower_bg.bmp", data, w, h)


def main():
    gen_climber()
    gen_tiles()
    gen_background()
    print("done")


if __name__ == "__main__":
    main()
