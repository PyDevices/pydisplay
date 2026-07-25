touch_drivers
=============
Drivers for touch screens.

Canonical duck-type method: ``read_points()`` → ``()`` when up, else a
sequence of ``(x, y[, id[, …]])`` tuples (never a bare ``(x, y)`` for a
single contact — wrap as ``((x, y),)``).

``board_config`` wires ``Runtime(touch_read=touch.read_points, …)``. Legacy
per-board multi→single collapse helpers are being removed.
