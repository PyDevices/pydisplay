#!/usr/bin/env python3
"""Apply in-process settings, then run a script in the same interpreter.

Usage (cwd is ``lib/``)::

    <python> ../tools/multimer_backend_preload.py [--env NAME=VALUE]... BACKEND SCRIPT [ARGS...]

``BACKEND`` is a name from ``multimer.backends()``, or ``-`` to keep the
platform's own choice.

Environment variables cover direct runs, but Windows MicroPython / CPython
launched from WSL cannot see exported ones, so a sweep across runtimes has to
apply its settings inside the child: ``multimer.use_backend()`` for the timer
backend and ``displaydev.env_set()`` for ``--env`` values, both before the
script imports ``board_config``. The target script keeps the real command line
(``sys.argv`` is read-only on CircuitPython), so scripts must locate their own
flags anywhere in ``sys.argv`` rather than at a fixed index.

Exits 2 on bad usage and 3 when the backend is unavailable on this host.
"""

import sys

USAGE = "usage: multimer_backend_preload.py [--env NAME=VALUE]... BACKEND SCRIPT [ARGS...]"


def _bootstrap_path():
    """Mirror ``utils/path.py``: make ``lib`` / ``utils`` importable from ``src``."""
    for directory in ("utils", "lib", "."):
        if directory not in sys.path:
            sys.path.insert(0, directory)


def _parse(argv):
    """Split ``argv`` into (env pairs, backend, script). Returns None on bad usage."""
    env = []
    rest = argv[1:]
    while rest and rest[0] == "--env":
        if len(rest) < 2 or "=" not in rest[1]:
            return None
        name, _, value = rest[1].partition("=")
        env.append((name, value))
        rest = rest[2:]
    if len(rest) < 2:
        return None
    return env, rest[0], rest[1]


def main(argv):
    parsed = _parse(argv)
    if parsed is None:
        print(USAGE)
        return 2
    env, backend, script = parsed

    _bootstrap_path()

    if env:
        from displaydev import env_set

        for name, value in env:
            env_set(name, value)
            print(f"PRELOAD_ENV={name}={value}")

    if backend != "-":
        import multimer

        try:
            active = multimer.use_backend(backend)
        except (ImportError, ValueError) as exc:
            print(f"MULTIMER_BACKEND_UNAVAILABLE={backend!r}: {exc}")
            return 3
        print(f"MULTIMER_BACKEND_FORCED={active}")

    with open(script) as fh:
        code = fh.read()
    globals_ = {"__name__": "__main__", "__file__": script}
    exec(compile(code, script, "exec"), globals_)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
