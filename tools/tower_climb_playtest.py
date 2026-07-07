#!/usr/bin/env python3
"""Run tower_climb with the built-in bot until summit or timeout."""

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.environ.get(
    "TOWER_CLIMB_TRACE", os.path.join(ROOT, ".cursor", "tower-climb-playtest.jsonl")
)
TIMEOUT_S = int(os.environ.get("TOWER_CLIMB_PLAYTEST_TIMEOUT", "180"))


def analyze(path):
    won = False
    max_alt = 0
    min_y = 9999
    life_lost = 0
    frames = 0
    last = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["kind"] == "win":
                won = True
            if d["kind"] == "life_lost":
                life_lost += 1
            if d["kind"] == "frame":
                frames += 1
                y = d["player"]["y"]
                min_y = min(min_y, y)
                alt = 400 - y  # rough; init has goal_y
                max_alt = max(max_alt, int(400 - y))
                last = d
    return {
        "won": won,
        "frames": frames,
        "life_lost": life_lost,
        "min_y": min_y if min_y < 9999 else None,
        "last_y": last["player"]["y"] if last else None,
        "last_lives": last["player"]["lives"] if last else None,
        "last_score": last["player"]["score"] if last else None,
    }


def main():
    os.makedirs(os.path.dirname(TRACE), exist_ok=True)
    if os.path.exists(TRACE):
        os.remove(TRACE)
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PYTHONPATH"] = os.path.join(ROOT, "src", "lib")
    env["TOWER_CLIMB_BOT"] = "1"
    env["TOWER_CLIMB_TRACE"] = TRACE
    proc = subprocess.Popen(
        [os.path.join(ROOT, ".venv", "bin", "python"), "examples/tower_climb.py"],
        cwd=os.path.join(ROOT, "src"),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.time() + TIMEOUT_S
    while proc.poll() is None and time.time() < deadline:
        if os.path.exists(TRACE):
            with open(TRACE, encoding="utf-8") as f:
                if any('"kind":"win"' in line for line in f):
                    proc.terminate()
                    break
        time.sleep(0.25)
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)
    out = proc.stdout.read() if proc.stdout else ""
    if not os.path.exists(TRACE):
        print("FAIL: no trace written", file=sys.stderr)
        if out:
            print(out[-2000:], file=sys.stderr)
        return 1
    result = analyze(TRACE)
    print(json.dumps(result, indent=2))
    print(f"trace: {TRACE}")
    if not result["won"]:
        print("FAIL: bot did not reach summit", file=sys.stderr)
        return 1
    print("OK: summit reached")
    return 0


if __name__ == "__main__":
    sys.exit(main())
