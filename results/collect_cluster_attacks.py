#!/usr/bin/env python3
"""Collect CAM trace data by running a cluster and periodic spoofing attacks.

The script:
- cleans the raw CAM trace at app/data/cam_trace.csv
- starts the app cluster launcher
- launches attacker/attack_orchestrator.py at evenly spread intervals between 1 and 5 seconds
- keeps the capture running for 120 seconds before shutting down
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
DATA_FILE = ROOT / "data" / "cam_trace.csv"
CLUSTER_SCRIPT = APP_DIR / "cluster_launcher.py"
ATTACK_SCRIPT = ROOT / "attacker" / "attack_orchestrator.py"
ATTACK_EVENTS_FILE = ROOT / "results" / "attack_events.jsonl"
HEADER = "ts_ms,station_rd,mac,station_id,lat,lon,speed_mps,heading_deg,label\n"

DEFAULT_INTERVALS = [1.0, 2.0, 3.0, 4.0, 5.0]
DEFAULT_DURATION_S = 120.0


def clean_cam_trace() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(HEADER, encoding="utf-8")
    print(f"Cleaned raw CAM trace: {DATA_FILE}")


def _build_attack_schedule(duration_s: float, intervals: list[float]) -> list[float]:
    schedule: list[float] = []
    elapsed = 0.0
    index = 0
    while True:
        interval = intervals[index % len(intervals)]
        if elapsed + interval > duration_s:
            break
        elapsed += interval
        schedule.append(elapsed)
        index += 1
    return schedule


def start_cluster(stations: int, location: str, random_motion: bool) -> subprocess.Popen:
    cmd = [
        sys.executable,
        str(CLUSTER_SCRIPT),
        "--stations",
        str(stations),
        "--location",
        location,
    ]
    if random_motion:
        cmd.append("--random-motion")

    print(f"Starting cluster: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=str(APP_DIR), env=os.environ.copy())
    time.sleep(1.0)
    if proc.poll() is not None:
        raise RuntimeError("Cluster launcher exited immediately; check the cluster log for errors.")
    return proc


def launch_attack(instance: int, attack_type: int) -> None:
    cmd = [
        sys.executable,
        str(ATTACK_SCRIPT),
        "--interface",
        "lo",
        "--count",
        "1",
        "--attack-type",
        str(attack_type),
    ]
    env = os.environ.copy()
    env["ATTACK_EVENTS_PATH"] = str(ATTACK_EVENTS_FILE)

    print(f"Launching attack #{instance} with command: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=False)


def run_collection(
    stations: int,
    location: str,
    duration_s: float,
    attack_type: int,
    random_motion: bool,
    intervals: list[float],
) -> None:
    clean_cam_trace()
    ATTACK_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ATTACK_EVENTS_FILE.write_text("", encoding="utf-8")

    cluster_proc = start_cluster(stations, location, random_motion)
    attack_schedule = _build_attack_schedule(duration_s, intervals)

    start_time = time.monotonic()
    try:
        for attempt, target in enumerate(attack_schedule, start=1):
            now = time.monotonic()
            remaining = target - (now - start_time)
            if remaining > 0:
                time.sleep(remaining)
            launch_attack(attempt, attack_type)

        elapsed = time.monotonic() - start_time
        remaining = duration_s - elapsed
        if remaining > 0:
            print(f"Waiting additional {remaining:.1f}s to complete capture period.")
            time.sleep(remaining)
    finally:
        if cluster_proc.poll() is None:
            print("Stopping cluster process...")
            cluster_proc.send_signal(signal.SIGINT)
            try:
                cluster_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cluster_proc.kill()
                cluster_proc.wait(timeout=5)
        print("Capture finished.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect CAM trace data with periodic spoofing attacks.")
    parser.add_argument("--stations", type=int, default=3, help="Number of cluster stations to launch")
    parser.add_argument("--location", default="dtr", help="Cluster location key (dtr, bcn, etc.)")
    parser.add_argument("--duration-s", type=float, default=DEFAULT_DURATION_S, help="Total capture duration in seconds")
    parser.add_argument("--attack-type", type=int, default=1, help="Attack type numeric value (default: 1)")
    parser.add_argument("--no-random-motion", action="store_true", help="Disable random motion for cluster stations")
    parser.add_argument(
        "--intervals",
        default=','.join(str(x) for x in DEFAULT_INTERVALS),
        help="Comma-separated attack intervals in seconds (default: 1,2,3,4,5)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    intervals = [float(x.strip()) for x in args.intervals.split(",") if x.strip()]
    if not intervals:
        raise ValueError("At least one interval must be specified.")

    run_collection(
        stations=args.stations,
        location=args.location,
        duration_s=args.duration_s,
        attack_type=args.attack_type,
        random_motion=not args.no_random_motion,
        intervals=intervals,
    )


if __name__ == "__main__":
    main()
