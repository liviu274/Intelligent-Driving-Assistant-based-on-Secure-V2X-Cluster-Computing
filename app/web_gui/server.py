#!/usr/bin/env python3
"""Live station map server for the GeoNetworking simulation."""

from __future__ import annotations

import argparse
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "index.html"
STATE_LOCK = threading.Lock()
STATIONS: dict[str, dict] = {}


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _station_list() -> list[dict]:
    now_ms = int(time.time() * 1000)
    with STATE_LOCK:
        stations = []
        for station in STATIONS.values():
            record = dict(station)
            updated_at = int(record.get("updated_at_ms", now_ms))
            record["age_ms"] = max(0, now_ms - updated_at)
            stations.append(record)
    stations.sort(key=lambda item: str(item.get("station_id", "")))
    return stations


def _store_station(payload: dict) -> dict:
    now_ms = int(time.time() * 1000)
    station_id = str(payload.get("station_id") or payload.get("stationId") or payload.get("id") or "").strip()
    if not station_id:
        raise ValueError("station_id is required")

    record = {
        "station_id": station_id,
        "station_type": payload.get("station_type"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
        "speed_mps": payload.get("speed_mps", payload.get("speed")),
        "heading_deg": payload.get("heading_deg", payload.get("heading", payload.get("track"))),
        "ts_ms": int(payload.get("ts_ms") or now_ms),
        "updated_at_ms": now_ms,
        "source": payload.get("source", "tx"),
        "role": payload.get("role", "live"),
        "scenario": payload.get("scenario", "live"),
        "metadata": payload.get("metadata", {}),
    }

    with STATE_LOCK:
        STATIONS[station_id] = record
    return record


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "GeoNetMap/1.0"

    def _set_headers(self, status: int, content_type: str, length: int | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(HTTPStatus.NO_CONTENT, "text/plain; charset=utf-8", 0)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            content = INDEX_FILE.read_bytes()
            self._set_headers(HTTPStatus.OK, "text/html; charset=utf-8", len(content))
            self.wfile.write(content)
            return

        if path == "/api/health":
            content = _json_bytes({"ok": True, "stations": len(_station_list())})
            self._set_headers(HTTPStatus.OK, "application/json; charset=utf-8", len(content))
            self.wfile.write(content)
            return

        if path == "/api/stations":
            content = _json_bytes({"stations": _station_list()})
            self._set_headers(HTTPStatus.OK, "application/json; charset=utf-8", len(content))
            self.wfile.write(content)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in ("/api/telemetry", "/api/stations/update"):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            record = _store_station(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            content = _json_bytes({"ok": False, "error": str(exc)})
            self._set_headers(HTTPStatus.BAD_REQUEST, "application/json; charset=utf-8", len(content))
            self.wfile.write(content)
            return

        content = _json_bytes({"ok": True, "station": record})
        self._set_headers(HTTPStatus.OK, "application/json; charset=utf-8", len(content))
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the live GeoNetworking station map")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"🌍 Live map UI available at http://{args.host}:{args.port}")
    print(f"📡 Station telemetry endpoint: http://{args.host}:{args.port}/api/telemetry")
    server.serve_forever()


if __name__ == "__main__":
    main()