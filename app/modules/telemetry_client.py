import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class StationTelemetryPublisher:
    endpoint: str
    timeout_s: float = 0.3
    source: str = "tx"

    @classmethod
    def from_env(cls) -> Optional["StationTelemetryPublisher"]:
        endpoint = os.getenv("STATION_TELEMETRY_URL", "").strip()
        if not endpoint:
            return None
        return cls(endpoint=endpoint)

    def _post(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                response.read()
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return

    def publish(self, payload: dict[str, Any]) -> None:
        if not payload:
            return
        payload = dict(payload)
        payload.setdefault("source", self.source)
        payload.setdefault("ts_ms", int(time.time() * 1000))
        self._post(payload)

    def build_callback(self, station_id: Any, station_type: Any = None) -> Callable[[dict], None]:
        station_id_str = str(station_id)

        def _callback(tpv: dict) -> None:
            lat = tpv.get("lat")
            lon = tpv.get("lon")
            if lat is None or lon is None:
                return

            payload = {
                "station_id": station_id_str,
                "station_type": station_type,
                "lat": lat,
                "lon": lon,
                "speed_mps": tpv.get("speed", tpv.get("speed_mps")),
                "heading_deg": tpv.get("track", tpv.get("heading_deg")),
                "ts_ms": int(time.time() * 1000),
                "role": "live",
            }
            self.publish(payload)

        return _callback

    def publish_snapshot(
        self,
        station_id: Any,
        lat: float,
        lon: float,
        speed_mps: float = 0.0,
        heading_deg: float = 0.0,
        station_type: Any = None,
        role: str = "live",
    ) -> None:
        payload = {
            "station_id": str(station_id),
            "station_type": station_type,
            "lat": lat,
            "lon": lon,
            "speed_mps": speed_mps,
            "heading_deg": heading_deg,
            "ts_ms": int(time.time() * 1000),
            "role": role,
        }
        self.publish(payload)