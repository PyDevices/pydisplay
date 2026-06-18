import os
from pathlib import Path

from png import Reader  # noqa: E402

from graphics import MONO_HLSB, FrameBuffer
import lib.path  # noqa: E402, F401

# Source path is in the format:
#     ~/github/material-design-icons/png/action/3d_rotation/materialicons/18dp/1x/baseline_3d_rotation_black_18dp.png
# f"{source}/{category}/{short_name}/{family}/{size}/{scale}"

ROOT = Path(__file__).resolve().parent.parent
_default_source = Path.home() / "github/material-design-icons/png"
source = (
    Path(os.environ["MATERIAL_DESIGN_ICONS_DIR"])
    if "MATERIAL_DESIGN_ICONS_DIR" in os.environ
    else _default_source
)
dest = ROOT / "icons"
scale = "1x"
threshold = 160


def png_to_pbm(filename, dest_file):
    """
    Convert a PNG file to a PBM file
    """
    print(f"\t{dest_file}")
    width, height, pixels, metadata = Reader(filename=str(filename)).read_flat()
    if not metadata["greyscale"] or metadata["bitdepth"] != 8:
        print(f"Only 8-bit greyscale PNGs are supported: {filename}")
        return

    # Create the FrameBuffer
    bytes_per_row = (width + 7) // 8
    array_size = bytes_per_row * height
    buffer = memoryview(bytearray(array_size))
    fbuf = FrameBuffer(buffer, width, height, MONO_HLSB)

    # Convert the pixels
    alpha = 1 if metadata["alpha"] else 0
    planes = metadata["planes"]
    for y in range(height):
        for x in range(width):
            c = 1 if pixels[(y * width + x) * planes + alpha] > threshold else 0
            fbuf.pixel(x, y, c)
    fbuf.save(str(dest_file))


for category in os.listdir(source):
    for short_name in os.listdir(source / category):
        for family in os.listdir(source / category / short_name):
            for size in os.listdir(source / category / short_name / family):
                in_dir = source / category / short_name / family / size / scale
                if not in_dir.is_dir():
                    continue
                out_dir = dest / family / size / category
                in_file = os.listdir(in_dir)[0]
                out_file = in_file.replace(".png", ".pbm")
                out_dir.mkdir(parents=True, exist_ok=True)
                png_to_pbm(in_dir / in_file, out_dir / out_file)
