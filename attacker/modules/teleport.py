import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.modules import CoordinatesGenerator

def teleport(lat: int, lon: int):
    """Teleport coordinates 2km away from current position."""
    # Convert from ETSI format (1/10 microdegrees) to decimal degrees
    lat_degrees = lat / 10_000_000.0
    lon_degrees = lon / 10_000_000.0
    
    print(f"      Original position: ({lat_degrees:.6f}, {lon_degrees:.6f})")
    
    # Generate new position 2km away using spherical geometry
    new_lat, new_lon = CoordinatesGenerator.random_location_within_radius(
        (lat_degrees, lon_degrees), 
        radius_m=2000  # 2km
    )
    
    print(f"      Spoofed position:  ({new_lat:.6f}, {new_lon:.6f})")
    
    # Convert back to ETSI format (1/10 microdegrees)
    lat = int(new_lat * 10_000_000)
    lon = int(new_lon * 10_000_000)
    
    print(f"   ✅ Teleportation complete:~{_calculate_distance(lat_degrees, lon_degrees, new_lat, new_lon):.0f}m away")
    return lat, lon
    
        
def _calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
    
if __name__ == '__main__':
    lat, lon = 413869310, 21121040 # Barcelona
    new_lat, new_lon = teleport(lat, lon)
    print(lat, lon)
    print(new_lat, new_lon)