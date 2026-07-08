"""NeoPixel / DotStar matrix simulator board config.

Renders an addressable-LED grid to a scaled desktop window via ``pixel_sim``.
Point your run at this board config (e.g. copy it to the working directory, or
prepend ``examples/pixel_sim`` to ``sys.path`` so it shadows the default
``board_config``) and draw with the usual RGB565 DisplayDriver API.
"""

from pixel_sim import display_drv, runtime  # noqa: F401
