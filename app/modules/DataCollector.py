import time
import threading
from pathlib import Path
from typing import Optional

class DataCollector:
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Default: use data folder inside root directory
            root_dir = Path(__file__).resolve().parent.parent.parent
            output_dir = root_dir / "data"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.output_dir / "cam_trace.csv"
        self.prev_state = {}  # {station_id: (ts_ms, lat, lon, speed, heading)}
        self._lock = threading.Lock()

        # minimal CAM trace schema: only raw identifiers and measured fields
        header = "ts_ms,station_rd,station_id,lat,lon,speed_mps,heading_deg,label\n"
        if not self.csv_file.exists() or self.csv_file.stat().st_size == 0:
            with open(self.csv_file, "w") as f:
                f.write(header)

    def log_cam(
        self,
        station_id: int,
        lat: float,
        lon: float,
        speed: float,
        heading: float,
        station_rd: Optional[str] = None,
        label: int = 0,
        ts_ms: Optional[int] = None,
    ):
        """Log minimal CAM fields into the raw trace CSV."""
        if ts_ms is None:
            ts_ms = int(time.time() * 1000)
        else:
            ts_ms = int(ts_ms)

        # normalize station id and station_rd
        sid = str(station_id)
        srd = station_rd if station_rd is not None else sid

        self.prev_state[sid] = (ts_ms, lat, lon, speed, heading)

        row = (
            f"{ts_ms},{srd},{sid},{lat:.6f},{lon:.6f},{float(speed):.2f},{float(heading):.1f},{label}\n"
        )
        with self._lock:
            with open(self.csv_file, "a") as f:
                f.write(row)