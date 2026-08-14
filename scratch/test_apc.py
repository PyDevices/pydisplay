import sys
import time

import uwin32 as win

import multimer

count = 0


def cb(t):
    global count
    count += 1


tim = multimer.Timer(-1)
tim.init(mode=multimer.Timer.PERIODIC, period=50, callback=cb)

start = time.time()
while time.time() - start < 1.0:
    win.SleepEx(100, True)

print("Count after 1.0s of alertable SleepEx loop:", count, flush=True)
tim.deinit()
