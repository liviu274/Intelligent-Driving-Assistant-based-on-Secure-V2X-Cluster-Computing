#!/usr/bin/env python3
"""
Cluster Launcher for V2X GeoNetworking Simulation

Spawns multiple CAM broadcasting stations for position spoofing detection testing.
Run with: sudo python3 cluster_launcher.py --stations 5
"""

import argparse
import subprocess
import sys
import time
import signal
import os
from typing import List, Optional

def launch_cluster(
    num_stations: int,
    location: str,
    script_path: str = "cam_boradcast.py",
    telemetry_url: Optional[str] = None,
    random_motion: bool = False,
    min_speed_kmh: float = 20.0,
    max_speed_kmh: float = 50.0,
):
    """Launch N station instances as separate processes."""
    processes = []
    child_env = os.environ.copy()
    if telemetry_url:
        child_env["STATION_TELEMETRY_URL"] = telemetry_url
    
    print(f"🚀 Launching cluster with {num_stations} stations...")
    print(f"📍 All stations spawn within 500m of Barcelona")
    print(f"📡 Consumer area: 5000m\n")
    if telemetry_url:
        print(f"🌍 Telemetry feed: {telemetry_url}\n")
    if random_motion:
        print(
            f"🎲 Random motion enabled: speed range {min_speed_kmh:.1f}-{max_speed_kmh:.1f} km/h, "
            "heading range 0-360°\n"
        )
    
    for i in range(num_stations):
        try:
            # Launch each station as a subprocess
            # stdout/stderr inherit from parent (mixed output to terminal)
            station_cmd = [sys.executable, script_path, "--location", location]
            if random_motion:
                station_cmd.extend(
                    [
                        "--random-motion",
                        "--min-speed-kmh",
                        str(min_speed_kmh),
                        "--max-speed-kmh",
                        str(max_speed_kmh),
                    ]
                )
            p = subprocess.Popen(
                station_cmd,
                env=child_env,
                text=True
            )
            processes.append(p)
            print(f"✅ Launched station {i+1}/{num_stations} (PID: {p.pid})")
            time.sleep(0.5)  # Small delay to avoid race conditions
            
        except Exception as e:
            print(f"❌ Failed to launch station {i+1}: {e}")
            # Clean up already launched processes
            for proc in processes:
                proc.terminate()
            sys.exit(1)
    
    print(f"\n✅ All {num_stations} stations running!")
    print("Press Ctrl+C to stop the cluster\n")
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down cluster...")
        for i, p in enumerate(processes):
            print(f"Stopping station {i+1}...")
            p.terminate()
        
        # Wait for all to terminate
        for p in processes:
            p.wait(timeout=5)
        
        print("👋 Cluster stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor processes
    try:
        while True:
            # Check if any process died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"⚠️  Station {i+1} (PID {p.pid}) exited with code {p.returncode}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(None, None)


def main():
    parser = argparse.ArgumentParser(
        description="Launch a cluster of V2X stations for GeoNetworking simulation"
    )
    parser.add_argument(
        "--stations",
        "-n",
        type=int,
        default=3,
        help="Number of stations to launch (default: 3)"
    )
    parser.add_argument(
        "--script",
        "-s",
        type=str,
        default="cam_boradcast.py",
        help="Path to the CAM broadcast script (default: cam_boradcast.py)"
    )
    parser.add_argument(
        "--location",
        "-l",
        type=str,
        default="dtr",
        help="Cluster location (dtr - Bucharest Drumul Tabere, bcn - Barcelona))"
    )
    parser.add_argument(
        "--telemetry-url",
        type=str,
        default="",
        help="Optional telemetry endpoint, e.g. http://127.0.0.1:8000/api/telemetry"
    )
    parser.add_argument(
        "--random-motion",
        action="store_true",
        help="Randomize each station's speed and heading on startup"
    )
    parser.add_argument(
        "--min-speed-kmh",
        type=float,
        default=20.0,
        help="Minimum random speed in km/h (used with --random-motion)"
    )
    parser.add_argument(
        "--max-speed-kmh",
        type=float,
        default=50.0,
        help="Maximum random speed in km/h (used with --random-motion)"
    )
    
    args = parser.parse_args()
    
    # Verify script exists
    script_path = os.path.join(os.path.dirname(__file__), args.script)
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)
    
    # Check if running with sudo
    if os.geteuid() != 0:
        print("⚠️  This script requires root privileges (raw sockets)")
        print("Run with: sudo python3 cluster_launcher.py")
        sys.exit(1)

    if args.min_speed_kmh < 0 or args.max_speed_kmh < 0:
        parser.error("--min-speed-kmh and --max-speed-kmh must be non-negative")
    if args.min_speed_kmh > args.max_speed_kmh:
        parser.error("--min-speed-kmh must be <= --max-speed-kmh")
    
    telemetry_url = args.telemetry_url.strip() or None
    launch_cluster(
        args.stations,
        args.location,
        script_path,
        telemetry_url=telemetry_url,
        random_motion=args.random_motion,
        min_speed_kmh=args.min_speed_kmh,
        max_speed_kmh=args.max_speed_kmh,
    )


if __name__ == "__main__":
    main()
