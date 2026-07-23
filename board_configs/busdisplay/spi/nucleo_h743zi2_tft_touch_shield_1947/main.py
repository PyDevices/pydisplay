# Boot into LVGL tap-button smoke test.
try:
    with open("/flash/lvgl_test.py") as f:
        exec(f.read())
except OSError:
    with open("lvgl_test.py") as f:
        exec(f.read())
