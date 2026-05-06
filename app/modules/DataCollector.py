import json
import time
import threading
import os
from pathlib import Path
from typing import Optional
from math import radians, sin, cos, sqrt, atan2

EARTH_R = 6371000.0

def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in meters between two points"""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * EARTH_R * atan2(sqrt(a), sqrt(1-a))

class DataCollector:
    def __init__(self, output_dir="data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.csv_file = self.output_dir / "cam_trace.csv"
        self.prev_state = {}  # {station_id: (ts_ms, lat, lon, speed, heading)}
        self._lock = threading.Lock()

        header = "ts_ms,station_id,lat,lon,speed_mps,heading_deg,dist_m,dt_s,accel_mps2,yaw_rate_dps,label\n"
        # write header only if file missing or empty
        if not self.csv_file.exists() or self.csv_file.stat().st_size == 0:
            with open(self.csv_file, "w") as f:
                f.write(header)

    def log_cam(self, station_id: int, lat: float, lon: float, speed: float, heading: float, label: int = 0, ts_ms: Optional[int] = None):
        """Log CAM and compute delta features. Use ts_ms from CAM if provided."""
        if ts_ms is None:
            ts_ms = int(time.time() * 1000)
        else:
            ts_ms = int(ts_ms)

        # normalize station id
        sid = str(station_id)

        dist_m = 0.0
        dt_s = 0.0
        accel_mps2 = 0.0
        yaw_rate_dps = 0.0

        prev = self.prev_state.get(sid)
        if prev:
            prev_ts, prev_lat, prev_lon, prev_speed, prev_heading = prev
            dt_s = (ts_ms - int(prev_ts)) / 1000.0
            if dt_s > 0:
                dist_m = haversine_m(prev_lat, prev_lon, lat, lon)
                accel_mps2 = (float(speed) - float(prev_speed)) / dt_s
                yaw_rate_dps = (float(heading) - float(prev_heading)) / dt_s
            else:
                # avoid division by zero; keep dt_s==0 and deltas at zero
                dt_s = 0.0

        self.prev_state[sid] = (ts_ms, lat, lon, speed, heading)

        row = f"{ts_ms},{sid},{lat:.6f},{lon:.6f},{float(speed):.2f},{float(heading):.1f},{dist_m:.2f},{dt_s:.3f},{accel_mps2:.3f},{yaw_rate_dps:.1f},{label}\n"
        with self._lock:
            with open(self.csv_file, "a") as f:
                f.write(row)