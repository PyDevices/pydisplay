import os
import lib.path  # noqa: E402, F401
from png import Reader  # noqa: E402
from graphics import FrameBuffer, MONO_HLSB


# Source path is in the format:
#     /home/brad/gh2/material-design-icons/png/action/3d_rotation/materialicons/18dp/1x/baseline_3d_rotation_black_18dp.png
# f"{source}/{category}/{short_name}/{family}/{size}/{scale}"

source = "/home/brad/gh2/material-design-icons/png"
dest = "/home/brad/gh/pydisplay/icons"
scale = "1x"
threshold = 160


def png_to_pbm(filename, dest_file):
    """
    Convert a PNG file to a PBM file
    """
    print(f"\t{dest_file}")
    width, height, pixels, metadata = Reader(filename=filename).read_flat()
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
            if pixels[(y * width + x) * planes + alpha] > threshold:
                c = 1
            else:
                c = 0
            fbuf.pixel(x, y, c)
    fbuf.save(dest_file)


for category in os.listdir(source):
    for short_name in os.listdir(f"{source}/{category}"):
        for family in os.listdir(f"{source}/{category}/{short_name}"):
            for size in os.listdir(f"{source}/{category}/{short_name}/{family}"):
                in_dir = f"{source}/{category}/{short_name}/{family}/{size}/{scale}"
                if not os.path.exists(in_dir):
                    continue
                out_dir = f"{dest}/{family}/{size}/{category}"
                in_file = os.listdir(in_dir)[0]
                out_file = in_file.replace(".png", ".pbm")
                os.makedirs(out_dir, exist_ok=True)
                png_to_pbm(f"{in_dir}/{in_file}", f"{out_dir}/{out_file}")
