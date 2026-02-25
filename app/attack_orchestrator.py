#!/usr/bin/env python3
"""
Attack Scenario Orchestrator

Launches a V2X network simulation with:
- N legitimate stations (moving vehicles)
- 1 attacker station (position spoofing)

This simulates the threat model described in your research notebook:
cryptographically valid but semantically false CAMs.

Usage:
    sudo python attack_orchestrator.py --legitimate 5 --attack-type teleport
"""

import argparse
import subprocess
import sys
import time
import signal
import os


def launch_attack_scenario(num_legitimate: int, attack_type: str):
    """Launch legitimate stations + attacker."""
    processes = []
    
    print("="*60)
    print("   V2X Position Spoofing Attack Simulation")
    print("="*60)
    print(f"📍 Scenario: Barcelona (500m cluster)")
    print(f"✅ Legitimate stations: {num_legitimate}")
    print(f"💀 Attacker stations: 1 ({attack_type} attack)")
    print(f"🔍 Goal: Test plausibility-based detection\n")
    
    # Launch legitimate stations
    print(f"🚀 Launching {num_legitimate} legitimate stations...")
    for i in range(num_legitimate):
        try:
            p = subprocess.Popen(
                [sys.executable, "cam_boradcast.py"],
                text=True
            )
            processes.append(("legitimate", p))
            print(f"   ✅ Station {i+1}/{num_legitimate} (PID: {p.pid})")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            cleanup(processes)
            sys.exit(1)
    
    time.sleep(2)  # Let legitimate stations stabilize
    
    # Launch attacker
    print(f"\n💀 Launching ATTACKER ({attack_type})...")
    try:
        p = subprocess.Popen(
            [sys.executable, "cam_attacker.py", "--attack-type", attack_type],
            text=True
        )
        processes.append(("attacker", p))
        print(f"   ✅ Attacker active (PID: {p.pid})\n")
    except Exception as e:
        print(f"   ❌ Failed to launch attacker: {e}")
        cleanup(processes)
        sys.exit(1)
    
    print("="*60)
    print("📡 Simulation running!")
    print(f"   - Legitimate vehicles: Broadcasting honest CAMs")
    print(f"   - Attacker: Broadcasting SPOOFED CAMs")
    print(f"   - All stations: Receiving each other's CAMs")
    print("\n🔍 Observe:")
    print(f"   - Position inconsistencies in attacker's CAMs")
    print(f"   - Impossible speed/teleportation patterns")
    print(f"   - Detection opportunities for plausibility checks")
    print("\nPress Ctrl+C to stop simulation")
    print("="*60 + "\n")
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Stopping simulation...")
        cleanup(processes)
        print("👋 Simulation stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Monitor processes
    try:
        while True:
            for ptype, p in processes:
                if p.poll() is not None:
                    print(f"⚠️  {ptype.capitalize()} station (PID {p.pid}) exited with code {p.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


def cleanup(processes):
    """Terminate all processes."""
    for ptype, p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate a V2X position spoofing attack scenario"
    )
    parser.add_argument(
        "--legitimate",
        "-l",
        type=int,
        default=5,
        help="Number of legitimate stations (default: 5)"
    )
    parser.add_argument(
        "--attack-type",
        "-a",
        type=str,
        default="static",
        choices=["static", "teleport", "impossible-speed", "random"],
        help="Type of position spoofing attack (default: static)"
    )
    
    args = parser.parse_args()
    
    # Check if running with sudo
    if os.geteuid() != 0:
        print("⚠️  This script requires root privileges (raw sockets)")
        print(f"Run with: sudo python3 {os.path.basename(__file__)}")
        sys.exit(1)
    
    # Verify scripts exist
    for script in ["cam_boradcast.py", "cam_attacker.py"]:
        if not os.path.exists(script):
            print(f"❌ Script not found: {script}")
            sys.exit(1)
    
    launch_attack_scenario(args.legitimate, args.attack_type)


if __name__ == "__main__":
    main()
