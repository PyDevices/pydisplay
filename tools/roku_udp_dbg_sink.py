#!/usr/bin/env python3
"""UDP NDJSON sink for on-device roku_lvgl._dbg_log (host LAN IP:41234).

Run on Windows (or any host the board can reach at 192.168.1.143):

  python.exe tools/roku_udp_dbg_sink.py

Writes to C:/Users/Public/pydisplay_dbg/debug-4c370d.log and stdout.
"""

from __future__ import annotations

import argparse
import socket
import sys
import time


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=41234)
    p.add_argument(
        "--log",
        default=r"C:\Users\Public\pydisplay_dbg\debug-4c370d.log",
        help="Output NDJSON path",
    )
    p.add_argument("--append", action="store_true")
    args = p.parse_args()

    mode = "a" if args.append else "w"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(1.0)
    print("listening UDP :%d -> %s" % (args.port, args.log), flush=True)
    with open(args.log, mode, encoding="utf-8", newline="") as f:
        f.write('{"message":"udp_sink_start","port":%d}\n' % args.port)
        f.flush()
        while True:
            try:
                data, addr = sock.recvfrom(8192)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                break
            line = data.decode("utf-8", errors="replace")
            if not line.endswith("\n"):
                line += "\n"
            f.write(line)
            f.flush()
            sys.stdout.write("%s %s" % (addr, line))
            sys.stdout.flush()
    sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
