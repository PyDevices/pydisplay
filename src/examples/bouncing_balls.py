# pyscript gallery: all
"""
bouncing_balls.py
=================

Animate colored balls bouncing inside the display.

Inspired by Pimoroni's ``balls_demo.py``, adapted for pydisplay's
``board_config.display_drv`` and ``graphics`` module so the same script runs on
desktop (SDL/Pygame), MCU, and PyScript.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `displaysys`
    - `graphics`
    - `multimer`

"""

from random import getrandbits

from board_config import display_drv, runtime
from multimer import sleep_ms
import graphics

WIDTH = display_drv.width
HEIGHT = display_drv.height
BG = 0x2828  # dark gray (RGB565)
NUM_BALLS = min(30, max(8, (WIDTH * HEIGHT) // 8000))


def randint(a, b):
    span = b - a + 1
    if span <= 1:
        return a
    bits = 0
    n = span - 1
    while n:
        bits += 1
        n >>= 1
    return a + getrandbits(bits) % span


def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class Ball:
    __slots__ = ("x", "y", "r", "dx", "dy", "color")

    def __init__(self, x, y, r, dx, dy, color):
        self.x = x
        self.y = y
        self.r = r
        self.dx = dx
        self.dy = dy
        self.color = color


def make_balls():
    balls = []
    for _ in range(NUM_BALLS):
        r = randint(3, 13)
        balls.append(
            Ball(
                randint(r, WIDTH - r),
                randint(r, HEIGHT - r),
                r,
                (14 - r) / 2,
                (14 - r) / 2,
                color565(getrandbits(8), getrandbits(8), getrandbits(8)),
            )
        )
    return balls


def step(ball):
    ball.x += ball.dx
    ball.y += ball.dy
    xmin, xmax = ball.r, WIDTH - ball.r
    ymin, ymax = ball.r, HEIGHT - ball.r
    if ball.x < xmin or ball.x > xmax:
        ball.dx *= -1
        ball.x = max(xmin, min(xmax, ball.x))
    if ball.y < ymin or ball.y > ymax:
        ball.dy *= -1
        ball.y = max(ymin, min(ymax, ball.y))


def main():
    balls = make_balls()
    while True:
        graphics.fill(display_drv, BG)
        for ball in balls:
            step(ball)
            graphics.circle(display_drv, int(ball.x), int(ball.y), ball.r, ball.color, True)
        display_drv.show()
        if runtime:
            runtime.poll()
        if runtime.quit_requested if runtime else False:
            break
        sleep_ms(10)


main()
