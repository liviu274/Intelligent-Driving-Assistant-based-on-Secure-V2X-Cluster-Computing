"""
Dynamic Location Service for Simulating Vehicle Movement

Generates position updates simulating a vehicle moving at constant speed
in a specified direction (bearing).
"""

import threading
import time
import math
import datetime
from typing import Callable, Tuple


def generate_tpv_dict(latitude: float, longitude: float, speed_mps: float = 0.0, track_deg: float = 0.0) -> dict:
    """
    Generate a TPV dictionary compatible with FlexStack's location service callbacks.
    
    Args:
        latitude: Current latitude
        longitude: Current longitude
        speed_mps: Speed in meters per second
        track_deg: Track/bearing in degrees (0-360)
    
    Returns:
        Dictionary in GPSD TPV format
    """
    current_utc_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
    tt_dt = datetime.datetime.fromtimestamp(current_utc_timestamp, datetime.timezone.utc)
    tt = tt_dt.isoformat()
    tt = tt[:-9] + "Z"
    
    return {
        'class': 'TPV',
        'device': '/dev/ttyACM0',
        'mode': 3,
        'time': tt,
        'ept': 0.005,
        'lat': latitude,
        'lon': longitude,
        'alt': 163.8,
        'epx': 10.0,
        'epy': 10.0,
        'epv': 10.0,
        'track': track_deg,
        'speed': speed_mps,
        'climb': 0.0,
        'eps': 0.0
    }


class DynamicLocationService:
    """Simulates a moving vehicle with constant speed and bearing."""
    
    def __init__(
        self,
        initial_lat: float,
        initial_lon: float,
        speed_mps: float = 13.89,  # m/s (default: 50 km/h)
        bearing_degrees: float = 45.0,  # degrees from north (0=N, 90=E, 180=S, 270=W)
        period_ms: int = 1000,  # update every 1000ms
    ):
        """
        Args:
            initial_lat: Starting latitude
            initial_lon: Starting longitude
            speed_mps: Speed in meters per second
            bearing_degrees: Direction of travel (0° = North, clockwise)
            period_ms: Update period in milliseconds
        """
        self.latitude = initial_lat  # Public property for FlexStack compatibility
        self.longitude = initial_lon  # Public property for FlexStack compatibility
        self.speed_mps = speed_mps
        self.bearing_degrees = bearing_degrees  # Store in degrees for TPV
        self.bearing_rad = math.radians(bearing_degrees)
        self.period_ms = period_ms
        
        self.callbacks = []
        self.stop_event = threading.Event()
        self.location_service_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self.location_service_thread.start()
    
    def add_callback(self, callback: Callable[[dict], None]):
        """Register a callback to receive position updates."""
        self.callbacks.append(callback)
    
    def _update_loop(self):
        """Background thread that updates position periodically."""
        while not self.stop_event.is_set():
            # Move the vehicle
            self._update_position()
            
            # Generate TPV dict with current position
            tpv_dict = generate_tpv_dict(
                self.latitude,
                self.longitude,
                self.speed_mps,
                self.bearing_degrees
            )
            
            # Notify all callbacks with TPV dict
            for callback in self.callbacks:
                try:
                    callback(tpv_dict)
                except Exception as e:
                    print(f"Error in location callback: {e}")
            
            # Wait for next update
            time.sleep(self.period_ms / 1000.0)
    
    def _update_position(self):
        """Calculate new position based on speed and bearing."""
        # Distance traveled in this time step
        distance_m = self.speed_mps * (self.period_ms / 1000.0)
        
        # Earth radius in meters
        earth_radius_m = 6371000.0
        
        # Angular distance
        delta = distance_m / earth_radius_m
        
        # Current position in radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        
        # Calculate new position using great circle formula
        # https://www.movable-type.co.uk/scripts/latlong.html
        lat2 = math.asin(
            math.sin(lat1) * math.cos(delta) +
            math.cos(lat1) * math.sin(delta) * math.cos(self.bearing_rad)
        )
        lon2 = lon1 + math.atan2(
            math.sin(self.bearing_rad) * math.sin(delta) * math.cos(lat1),
            math.cos(delta) - math.sin(lat1) * math.sin(lat2)
        )
        
        # Update position (in degrees)
        self.latitude = math.degrees(lat2)
        self.longitude = math.degrees(lon2)
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position."""
        return (self.latitude, self.longitude)
    
    def set_speed(self, speed_mps: float):
        """Change vehicle speed."""
        self.speed_mps = speed_mps
    
    def set_bearing(self, bearing_degrees: float):
        """Change vehicle direction."""
        self.bearing_degrees = bearing_degrees
        self.bearing_rad = math.radians(bearing_degrees)
    
    def stop(self):
        """Stop the location service."""
        self.stop_event.set()
        self.location_service_thread.join()


if __name__ == "__main__":
    # Test the dynamic location service
    # Start at Barcelona, moving northeast at 50 km/h
    service = DynamicLocationService(
        initial_lat=41.386931,
        initial_lon=2.112104,
        speed_mps=13.89,  # 50 km/h
        bearing_degrees=45.0,  # Northeast
        period_ms=1000
    )
    
    def print_position(tpv):
        print(f"Position: {tpv['lat']:.6f}, {tpv['lon']:.6f} | Speed: {tpv['speed']:.2f} m/s | Track: {tpv['track']:.1f}°")
    
    service.add_callback(print_position)
    
    try:
        print("Simulating vehicle movement...")
        print("Press Ctrl+C to stop")
        time.sleep(30)  # Run for 30 seconds
    except KeyboardInterrupt:
        pass
    
    service.stop()
    print("\nFinal position:", service.get_position())
