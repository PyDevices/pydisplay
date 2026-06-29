from eventsys import poll_quit_discarding_others

# multimer types: queued, sync
import os
from collections import namedtuple

import png
from board_config import broker
from color_setup import ssd
from displaybuf import alloc_buffer
from multimer import capabilities, pump, sleep_ms

png_image = namedtuple("png_image", ["width", "height", "pixels", "metadata"])

PNG_DIR = "~/material-design-icons/png"


def _home_dir():
    try:
        return os.environ["HOME"]
    except (AttributeError, ImportError, KeyError, TypeError):
        pass
    getenv = getattr(os, "getenv", None)
    if getenv is not None:
        return getenv("HOME")
    return None


def _expand_user(path):
    if path.startswith("~/"):
        home = _home_dir()
        if not home:
            raise RuntimeError("Cannot expand ~ in png path (HOME not set)")
        return home + "/" + path[2:]
    return path


def _join_path(a, b):
    return a.rstrip("/") + "/" + b


def _rel_path(path, base):
    prefix = base.rstrip("/") + "/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    return path


def png_files(directory):
    """Yield .png paths under directory (no os.walk — works on MicroPython)."""
    directory = directory.rstrip("/")
    stack = [directory]
    while stack:
        root = stack.pop()
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in sorted(names):
            path = _join_path(root, name)
            if name.endswith(".png"):
                yield path
            else:
                try:
                    os.listdir(path)
                    stack.append(path)
                except OSError:
                    pass


try:
    import pydisplay_test_mode

    _max_pngs = 2 if pydisplay_test_mode.ENABLED else None
except ImportError:
    _max_pngs = None

png_path = _expand_user(PNG_DIR)
if not png_path.endswith("/"):
    png_path += "/"

fg_color = 0xFFFF
bg_color = 0x001F

ssd.fill(bg_color)
ssd.show()

shown = 0
while True:
    for file_name in png_files(png_path):
        p = png_image(*png.Reader(filename=file_name).read())
        if not p.metadata["greyscale"] or p.metadata["bitdepth"] != 8:
            print(f"Only 8-bit PNGs are supported {file_name}")
            continue
        pos_x, pos_y = (ssd.width - p.width) // 2, (ssd.height - p.height) // 2
        offset = 1 if p.metadata["alpha"] else 0
        planes = p.metadata["planes"]
        buf = alloc_buffer(p.width * p.height * 2)
        for y, row in enumerate(p.pixels):
            for x in range(p.width):
                if row[x * planes + offset] > 127:
                    buf[(y * p.width + x) * 2 : (y * p.width + x) * 2 + 2] = fg_color.to_bytes(
                        2, "little"
                    )
                else:
                    buf[(y * p.width + x) * 2 : (y * p.width + x) * 2 + 2] = bg_color.to_bytes(
                        2, "little"
                    )
        ssd.blit_rect(buf, pos_x, pos_y, p.width, p.height)
        rel = _rel_path(file_name, png_path)
        lines = rel.rpartition("/")
        ssd.text16(lines[0] + "/", 0, 0, 0xFFFF)
        ssd.text16("    " + lines[2], 0, 16, 0xFFFF)
        ssd.show()
        shown += 1
        if poll_quit_discarding_others(broker):
            break
        if _max_pngs is not None and shown >= _max_pngs:
            break
        sleep_ms(1000)
        ssd.fill_rect(pos_x, pos_y, p.width, p.height, bg_color)
        ssd.fill_rect(0, 0, ssd.width, 32, bg_color)
        if capabilities()["schedule_queue"]:
            pump()
    if poll_quit_discarding_others(broker):
        break
    if _max_pngs is not None and shown >= _max_pngs:
        break
