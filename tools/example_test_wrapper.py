#!/usr/bin/env python3
"""
Subprocess entry point for one cross-runtime example smoke test.

Invoked from src/ by example_test_kit.py:

    micropython ../tools/example_test_wrapper.py pydisplay_demo \\
        --script examples/pydisplay_demo.py --kind loop --duration 5

Prints EXAMPLE_RESULT={...} on stdout before exit.
"""

import json
import os
import sys
import time


def _dir_of(path):
    path = path.replace("\\", "/")
    if "/" in path:
        return path.rsplit("/", 1)[0]
    return "."


def _join(*parts):
    if not parts:
        return ""
    out = str(parts[0]).replace("\\", "/")
    for part in parts[1:]:
        if not part:
            continue
        part = str(part).replace("\\", "/").strip("/")
        if not out.endswith("/"):
            out += "/"
        out += part
    return out


def _isdir(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False


def _isfile(path):
    try:
        with open(path):
            pass
        return True
    except OSError:
        return False


def _env_get(key):
    environ = getattr(os, "environ", None)
    if environ is None:
        return None
    try:
        return environ.get(key)
    except Exception:
        return None


_TOOLS = _dir_of(__file__)
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

RESULT_PREFIX = "EXAMPLE_RESULT="


def _trace(msg):
    if _env_get("PYDISPLAY_TEST_TRACE"):
        print("example_test_wrapper: {}".format(msg), file=sys.stderr)


def _print_result(payload):
    line = RESULT_PREFIX + json.dumps(payload, separators=(",", ":"))
    print(line)
    try:
        sys.stdout.flush()
    except Exception:
        pass


def _sleep(seconds):
    try:
        from multimer import sleep_ms

        sleep_ms(int(seconds * 1000))
    except ImportError:
        time.sleep(seconds)


def _system_exit_code(exc):
    return getattr(exc, "code", None)


def _exec_script(script_path):
    with open(script_path, encoding="utf-8") as f:
        code = f.read()
    namespace = {"__name__": "__main__", "__file__": script_path}
    exec(code, namespace)


def _run_script_in_thread(script_path):
    """Run script_path in a background thread when _thread is available."""
    try:
        import _thread
    except ImportError:
        _thread = None

    state = {"error": None, "done": False}

    def target():
        try:
            _exec_script(script_path)
        except SystemExit as exc:
            code = _system_exit_code(exc)
            if code not in (0, None):
                state["error"] = "exit_{}".format(code)
        except Exception as exc:
            state["error"] = "{}: {}".format(type(exc).__name__, exc)
        finally:
            state["done"] = True

    if _thread is not None:
        _thread.start_new_thread(target, ())
        return state, True

    target()
    return state, False


def _monotonic():
    if hasattr(time, "monotonic"):
        return time.monotonic()
    return time.time()


def _wait_thread(state, threaded, timeout_s):
    if not threaded:
        return state.get("error")

    deadline = _monotonic() + timeout_s
    while _monotonic() < deadline:
        if state.get("done"):
            return state.get("error")
        _sleep(0.05)
    return "thread_timeout"


def _backend_name():
    try:
        import quit_inject

        return quit_inject.display_backend_name()
    except Exception:
        return "?"


def _run_oneshot(script_path, timeout_s):
    try:
        _exec_script(script_path)
        return None
    except SystemExit as exc:
        code = _system_exit_code(exc)
        if code in (0, None):
            return None
        return "exit_{}".format(code)
    except Exception as exc:
        return "{}: {}".format(type(exc).__name__, exc)


def _use_main_thread_for_bounded():
    try:
        name = sys.implementation.name
    except AttributeError:
        return False
    return name in ("cpython", "micropython")


def _run_bounded_main_thread(script_path, kind, duration_s, timeout_s, quit_mode):
    import quit_inject

    injected = [False]

    def delayed_inject():
        touch_delay = min(duration_s * 0.2, max(0.5, duration_s - 1.0))
        if quit_mode == "inject" and touch_delay > 0:
            _sleep(touch_delay)
            quit_inject.inject_synthetic_touch(broker_poll=False)
        _sleep(max(0, duration_s - touch_delay))
        lvgl = kind == "lvgl"
        if quit_inject.inject_quit(
            broker_poll=False,
            pump_count=20,
            pump_delay=0.02,
            lvgl=lvgl,
        ):
            injected[0] = True

    try:
        import threading

        threading.Thread(target=delayed_inject, daemon=True).start()
    except ImportError:
        if not _start_daemon(delayed_inject):
            touch_delay = min(duration_s * 0.2, max(0.5, duration_s - 1.0))
            if quit_mode == "inject" and touch_delay > 0:
                _sleep(touch_delay)
                quit_inject.inject_synthetic_touch(broker_poll=False)
            _sleep(max(0, duration_s - touch_delay))
            lvgl = kind == "lvgl"
            if quit_inject.inject_quit(
                broker_poll=False,
                pump_count=20,
                pump_delay=0.02,
                lvgl=lvgl,
            ):
                injected[0] = True

    try:
        _exec_script(script_path)
        return None, injected[0]
    except SystemExit as exc:
        code = _system_exit_code(exc)
        if code in (0, None):
            return None, injected[0]
        return "exit_{}".format(code), injected[0]
    except Exception as exc:
        return "{}: {}".format(type(exc).__name__, exc), injected[0]


def _start_daemon(target):
    try:
        import threading

        threading.Thread(target=target, daemon=True).start()
        return True
    except ImportError:
        pass
    try:
        import _thread

        _thread.start_new_thread(target, ())
        return True
    except ImportError:
        return False


def _run_interactive(script_path, duration_s, example, kind):
    """Run on main thread (SDL); pass after duration_s even if script blocks in help()/REPL."""

    def finisher():
        _sleep(duration_s)
        backend = _backend_name()
        _print_result(
            {
                "example": example,
                "status": "ok",
                "kind": kind,
                "backend": backend,
                "duration_s": duration_s,
                "quit_injected": False,
            }
        )
        _subprocess_hard_exit(0)

    if not _start_daemon(finisher):
        return "interactive_requires_thread"

    try:
        _exec_script(script_path)
        return None
    except SystemExit as exc:
        code = _system_exit_code(exc)
        if code in (0, None):
            return None
        return "exit_{}".format(code)
    except Exception as exc:
        return "{}: {}".format(type(exc).__name__, exc)


def _run_bounded(script_path, kind, duration_s, timeout_s, quit_mode):
    if _use_main_thread_for_bounded():
        return _run_bounded_main_thread(script_path, kind, duration_s, timeout_s, quit_mode)

    import quit_inject

    state, threaded = _run_script_in_thread(script_path)
    if not threaded:
        err = state.get("error")
        if err:
            return err, False
        return "hang_no_thread", False

    _trace("running {}s before quit injection".format(duration_s))
    touch_delay = min(duration_s * 0.2, max(0.5, duration_s - 1.0))
    if quit_mode == "inject" and touch_delay > 0:
        _sleep(touch_delay)
        quit_inject.inject_synthetic_touch(broker_poll=False)
    _sleep(max(0, duration_s - touch_delay))

    lvgl = kind == "lvgl"
    injected = quit_inject.inject_quit(
        broker_poll=False,
        pump_count=20,
        pump_delay=0.02,
        lvgl=lvgl,
    )
    if not injected:
        return "no_queue_device", False

    err = _wait_thread(state, threaded, timeout_s=min(10, timeout_s))
    if err:
        return err, True
    if not state.get("done"):
        return "quit_not_handled", True
    return None, True


def _parse_args(argv):
    if len(argv) < 2:
        raise ValueError("usage: example_test_wrapper.py EXAMPLE --script PATH --kind KIND")
    out = {
        "example": argv[1],
        "script": None,
        "kind": None,
        "quit": "poll",
        "duration": 5.0,
        "timeout": 30.0,
    }
    i = 2
    while i < len(argv):
        arg = argv[i]
        if arg == "--script" and i + 1 < len(argv):
            out["script"] = argv[i + 1]
            i += 2
        elif arg == "--kind" and i + 1 < len(argv):
            out["kind"] = argv[i + 1]
            i += 2
        elif arg == "--quit" and i + 1 < len(argv):
            out["quit"] = argv[i + 1]
            i += 2
        elif arg == "--duration" and i + 1 < len(argv):
            out["duration"] = float(argv[i + 1])
            i += 2
        elif arg == "--timeout" and i + 1 < len(argv):
            out["timeout"] = float(argv[i + 1])
            i += 2
        else:
            raise ValueError("unknown argument: {}".format(arg))
    if not out["script"] or not out["kind"]:
        raise ValueError("--script and --kind are required")
    return out


def _subprocess_hard_exit(code):
    """SDL on desktop CPython/MicroPython can block normal interpreter shutdown."""
    try:
        name = sys.implementation.name
    except AttributeError:
        return False
    if name not in ("cpython", "micropython"):
        return False
    if not hasattr(os, "_exit"):
        return False
    try:
        from board_config import display_drv

        display_drv.quit(code, force=True)
    except SystemExit:
        raise
    except Exception:
        pass
    os._exit(code)
    return False


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    try:
        args = _parse_args(argv)
    except ValueError as exc:
        print("example_test_wrapper: {}".format(exc), file=sys.stderr)
        return 2

    src = os.getcwd()
    if src not in sys.path:
        sys.path.insert(0, src)
    if not _isdir(_join(src, "lib")):
        print("example_test_wrapper: cwd must be pydisplay/src", file=sys.stderr)
        return 2

    script_path = args["script"]
    if not script_path.startswith("/"):
        script_path = _join(src, script_path)
    if not _isfile(script_path):
        payload = {
            "example": args["example"],
            "status": "error",
            "error": "script not found: {}".format(args["script"]),
            "backend": "?",
        }
        _print_result(payload)
        return 1

    try:
        import pydisplay_test_mode

        pydisplay_test_mode.ENABLED = True
    except Exception:
        pass

    try:
        import lib.path  # noqa: F401
    except Exception as exc:
        payload = {
            "example": args["example"],
            "status": "error",
            "error": "lib.path: {}".format(exc),
            "backend": "?",
        }
        _print_result(payload)
        return 1

    backend = _backend_name()
    quit_injected = False
    error = None

    if args["kind"] == "oneshot":
        error = _run_oneshot(script_path, args["timeout"])
    elif args["kind"] == "interactive":
        error = _run_interactive(script_path, args["duration"], args["example"], args["kind"])
    elif args["kind"] in ("loop", "async", "lvgl", "pdwidgets", "legacy"):
        error, quit_injected = _run_bounded(
            script_path, args["kind"], args["duration"], args["timeout"], args["quit"]
        )
    else:
        error = "unknown kind {}".format(args["kind"])

    status = "ok" if error is None else "error"
    payload = {
        "example": args["example"],
        "status": status,
        "kind": args["kind"],
        "backend": backend,
        "duration_s": args["duration"],
        "quit_injected": quit_injected,
    }
    if error:
        payload["error"] = error

    _print_result(payload)
    code = 0 if status == "ok" else 1
    if _subprocess_hard_exit(code):
        return code
    return code


if __name__ == "__main__":
    sys.exit(main())
