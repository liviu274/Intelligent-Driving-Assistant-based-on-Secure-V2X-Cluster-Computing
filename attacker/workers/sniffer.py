from scapy.all import sniff, Ether
import argparse

# GeoNetworking EtherType (ETSI standard)
GEONETWORKING_ETHERTYPE = 0x8947


class CAMSniffer:
    """Sniff and parse V2X CAM messages."""
    
    def __init__(self, interface="lo", count=0):
        self.interface = interface
        self.count = count
        self.discovered_stations = {}  # {mac_address : packet_payload}
    
    def start(self):
        """Start sniffing. count=0 means infinite."""
        print(f"🔍 Sniffing CAMs on {self.interface}...")
        print(f"   Filtering for EtherType: {hex(GEONETWORKING_ETHERTYPE)}")
        
        sniff(
            iface=self.interface,
            prn=self.process_packet,
            filter=f"ether proto {GEONETWORKING_ETHERTYPE}",
            count=self.count,
            store=False  # Don't store packets in memory
        )
        
    def process_packet(self, packet):
        """Process each captured GeoNetworking packet."""
        if not packet.haslayer(Ether):
            return
        
        src_mac = packet[Ether].src
        payload = bytes(packet[Ether].payload)
        
        # Parse GeoNetworking header (simplified)
        # Full parsing would require understanding ETSI EN 302 636-4-1
        if len(payload) != 85:  # frame.len = 99 for all packets
            print(f"⚠️  Differemt payload detected")
            return
        
        # Extract basic info (this is simplified - real parsing is complex)
        print(f"   CAM received:")
        print(f"   Source MAC: {src_mac}")
        print(f"   Payload size: {len(payload)} bytes")
        print(f"   First 32 bytes: {payload[:32].hex()}")
        print("-" * 60)
        
        # Store discovered station
        self.discovered_stations[src_mac] = payload
    
    def get_discovered_stations(self):
        """Return all discovered stations."""
        return self.discovered_stations

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
        default=0,
        help="Number of packets to sniff (default: infinite)"
    )
    args = parser.parse_args()
    sniffer = CAMSniffer(args.interface, args.count)
    sniffer.start()
    for mac, payload in sniffer.get_discovered_stations().items():
        print(f"Station with MAC {mac} has payload: {payload}")

if __name__ == '__main__':
    main()