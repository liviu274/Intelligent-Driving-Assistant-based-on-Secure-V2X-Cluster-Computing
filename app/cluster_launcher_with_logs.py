#!/usr/bin/env python3
"""
Cluster Launcher with Individual Station Logs

Spawns multiple CAM broadcasting stations, each writing to its own log file.
Run with: sudo python3 cluster_launcher_with_logs.py --stations 5

Logs are saved to: station_1.log, station_2.log, etc.
"""

import argparse
import subprocess
import sys
import time
import signal
import os

def launch_cluster(num_stations: int, script_path: str = "cam_boradcast.py"):
    """Launch N station instances as separate processes with individual log files."""
    processes = []
    log_files = []
    
    print(f"🚀 Launching cluster with {num_stations} stations...")
    print(f"📍 All stations spawn within 500m of Barcelona")
    print(f"📡 Consumer area: 5000m\n")
    
    # Ensure logs directory exists next to this script
    base_dir = os.path.dirname(__file__)
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    for i in range(num_stations):
        try:
            # Create log file for this station inside logs/ directory
            log_filename = os.path.join(logs_dir, f"station_{i+1}.log")
            log_file = open(log_filename, "w")
            log_files.append(log_file)
            
            # Launch each station as a subprocess
            p = subprocess.Popen(
                [sys.executable, script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True
            )
            processes.append(p)
            print(f"✅ Launched station {i+1}/{num_stations} (PID: {p.pid}) → {log_filename}")
            time.sleep(0.5)  # Small delay to avoid race conditions
            
        except Exception as e:
            print(f"❌ Failed to launch station {i+1}: {e}")
            # Clean up already launched processes
            for proc in processes:
                proc.terminate()
            for f in log_files:
                f.close()
            sys.exit(1)
    
    print(f"\n✅ All {num_stations} stations running!")
    print("📝 View logs with: tail -f station_*.log")
    print("Press Ctrl+C to stop the cluster\n")
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down cluster...")
        for i, p in enumerate(processes):
            print(f"Stopping station {i+1}...")
            p.terminate()
        
        # Wait for all to terminate
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        
        # Close log files
        for f in log_files:
            f.close()
        
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
    
    args = parser.parse_args()
    
    # Verify script exists
    script_path = os.path.join(os.path.dirname(__file__), args.script)
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)
    
    # Check if running with sudo
    if os.geteuid() != 0:
        print("⚠️  This script requires root privileges (raw sockets)")
        print(f"Run with: sudo python3 {os.path.basename(__file__)}")
        sys.exit(1)
    
    launch_cluster(args.stations, script_path)


if __name__ == "__main__":
    main()
