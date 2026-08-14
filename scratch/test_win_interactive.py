import sys

sys.path.insert(0, "lib")
import examples.lv_interactive_test as test

import multimer

print("Testing Windows APC timer over 3 seconds using multimer.sleep_ms...", flush=True)
initial_angle = test._angle
for i in range(1, 4):
    multimer.sleep_ms(1000)
    print(f"Time +{i}s: arc angle = {test._angle}, taps = {test._taps}", flush=True)

if test._angle != initial_angle:
    print(
        "SUCCESS: Windows APC timer actively updated the LVGL arc in the background!", flush=True
    )
else:
    print("FAILURE: Timer did not advance.", flush=True)
