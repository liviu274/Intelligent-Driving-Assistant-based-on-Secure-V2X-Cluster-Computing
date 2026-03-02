import socket
import struct
import os


class CAMlauncher:
    """Launch raw CAM packets on the network without FlexStack API."""
    
    # GeoNetworking EtherType (ETSI standard)
    GEONETWORKING_ETHERTYPE = 0x8947
    
    def __init__(self, payload, mac, dst='ff:ff:ff:ff:ff:ff', interface='lo'):
        """
        Initialize packet launcher.
        
        Args:
            payload: bytes or bytearray containing the GeoNetworking packet
            mac: source MAC address (bytes or str like 'aa:bb:cc:dd:ee:ff')
            dst: destination MAC (default: broadcast)
            interface: network interface (default: loopback)
        """
        self.payload = bytes(payload) if isinstance(payload, bytearray) else payload
        self.src_mac = self._parse_mac(mac)
        self.dst_mac = self._parse_mac(dst)
        self.interface = interface
        self.socket = None
    
    def _parse_mac(self, mac_addr):
        """Convert MAC address from string or bytes format to bytes."""
        if isinstance(mac_addr, bytes):
            if len(mac_addr) != 6:
                raise ValueError("MAC address must be 6 bytes")
            return mac_addr
        
        if isinstance(mac_addr, str):
            # Parse 'aa:bb:cc:dd:ee:ff' format
            parts = mac_addr.split(':')
            if len(parts) != 6:
                raise ValueError("MAC address must have 6 octets (e.g., 'aa:bb:cc:dd:ee:ff')")
            return bytes(int(part, 16) for part in parts)
        
        raise TypeError("MAC address must be string or bytes")
    
    def launch(self, count=1):
        """
        Launch packet(s) on the network.
        
        Args:
            count: number of times to send the packet
            
        Returns:
            Number of packets successfully sent
        """
        if os.geteuid() != 0:
            raise PermissionError("Packet launching requires root privileges (sudo)")
        
        sent = 0
        try:
            # Create raw socket
            self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.GEONETWORKING_ETHERTYPE))
            self.socket.bind((self.interface, 0))
            
            # Build Ethernet frame
            frame = self._build_ethernet_frame()
            
            # Send packets
            for i in range(count):
                bytes_sent = self.socket.send(frame)
                sent += 1
                print(f"   📤 Packet {i+1}/{count} sent: {bytes_sent} bytes")
            
            return sent
            
        except Exception as e:
            print(f"   ❌ Error sending packet: {e}")
            return sent
        
        finally:
            if self.socket:
                self.socket.close()
    
    def _build_ethernet_frame(self):
        """Build Ethernet frame with GeoNetworking payload."""
        # Ethernet header: 14 bytes
        # - Destination MAC (6 bytes)
        # - Source MAC (6 bytes)
        # - EtherType (2 bytes)
        
        eth_header = struct.pack(
            '!6s6sH',
            self.dst_mac,
            self.src_mac,
            self.GEONETWORKING_ETHERTYPE
        )
        
        return eth_header + self.payload
    
    def get_frame_info(self):
        """Get information about the frame that will be sent."""
        frame = self._build_ethernet_frame()
        
        return {
            'source_mac': ':'.join(f'{b:02x}' for b in self.src_mac),
            'dest_mac': ':'.join(f'{b:02x}' for b in self.dst_mac),
            'ethertype': f'0x{self.GEONETWORKING_ETHERTYPE:04x}',
            'payload_size': len(self.payload),
            'frame_size': len(frame),
            'interface': self.interface,
        }


# Example usage
if __name__ == '__main__':
    import sys
    
    # Example: Create a dummy payload
    dummy_payload = b'\x00' * 85  # Typical GeoNetworking payload size
    
    # Create launcher
    launcher = CAMlauncher(
        payload=dummy_payload,
        mac=b'\x00\x11\x22\x33\x44\x55',  # Source MAC
        dst='ff:ff:ff:ff:ff:ff',  # Broadcast destination
        interface='lo'
    )
    
    # Show frame info
    info = launcher.get_frame_info()
    print("Packet Information:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Launch packet (requires sudo)
    print("\n🚀 Launching packet...")
    if os.geteuid() == 0:
        launcher.launch(count=1)
    else:
        print("   ⚠️  Requires sudo to send raw packets")