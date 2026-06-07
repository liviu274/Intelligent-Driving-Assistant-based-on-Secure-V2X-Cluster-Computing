# A CAM type message broadcast using random vehicle coordinates around Barcelona
# Based on existing v2x CAMs example
#!/usr/bin/env python3
"""
FlexStack® CAM Example

A simple V2X application that broadcasts Cooperative Awareness Messages (CAMs)
and listens for CAMs from nearby vehicles.

Run with: sudo python cam_example.py
"""

import logging
import random
import time
import argparse
from pathlib import Path

# FlexStack imports
from flexstack.linklayer.raw_link_layer import RawLinkLayer
from flexstack.geonet.router import Router as GNRouter
from flexstack.geonet.mib import MIB
from flexstack.geonet.gn_address import GNAddress, M, ST, MID
from flexstack.btp.router import Router as BTPRouter
from flexstack.utils.static_location_service import ThreadStaticLocationService
from flexstack.facilities.local_dynamic_map.factory import LDMFactory
from flexstack.facilities.local_dynamic_map.ldm_constants import CAM
from flexstack.facilities.local_dynamic_map.ldm_classes import (
    AccessPermission,
    Circle,
    ComparisonOperators,
    Filter,
    FilterStatement,
    GeometricArea,
    Location,
    OrderTupleValue,
    OrderingDirection,
    RegisterDataConsumerReq,
    RegisterDataConsumerResp,
    RequestDataObjectsResp,
    SubscribeDataobjectsReq,
    SubscribeDataObjectsResp,
    SubscribeDataobjectsResult,
    TimestampIts,
)
from flexstack.facilities.ca_basic_service.ca_basic_service import (
    CooperativeAwarenessBasicService,
)
from flexstack.facilities.ca_basic_service.cam_transmission_management import (
    VehicleData,
)

# Locals
from modules import CustomStation, DynamicLocationService

# Enable logging
logging.basicConfig(level=logging.INFO)

# logs
import json
import logging

# Data collection + labeling pipelines

from modules.DataCollector import DataCollector
from modules.telemetry_client import StationTelemetryPublisher


# Cluster Configuration
# BASE_COORDINATES = (41.386931, 2.112104)  # Barcelona, Spain

COORDINATES = {
    'dtr' : (44.422157, 26.034846), # Bucharest, Drumul Taberei
    'bcn' : (41.386931, 2.112104) # Barcelona, UPC Campus Nord
}

SPAWN_AREA = 500  # Spawn area radius in meters

# Movement Configuration
ENABLE_MOVEMENT = True  # Set to True to simulate moving vehicle
SPEED_KMH = 50.0  # Vehicle speed in km/h
BEARING_DEGREES = 45.0  # Direction: 0=N, 90=E, 180=S, 270=W


logger = logging.getLogger(__name__)

class CAMDataLogger:
    def __init__(self, station_id: str):
        self.station_id = station_id
        self.log_file = f"station_{station_id}.jsonl"
    
    def log_cam(self, cam_data: dict):
        """Log CAM with timestamp, position, speed, heading"""
        record = {
            "ts_ms": int(time.time() * 1000),
            "station_id": self.station_id,
            "lat": cam_data.get("lat"),
            "lon": cam_data.get("lon"),
            "speed_mps": cam_data.get("speed_mps"),
            "heading_deg": cam_data.get("heading_deg"),
            "source": "tx"  # transmitted by this station
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record) + "\n")




def main(
    location: str,
    random_motion: bool = False,
    min_speed_kmh: float = 20.0,
    max_speed_kmh: float = 50.0,
):
    if COORDINATES[location] is not None:
        coords = COORDINATES[location]
    else:
        print(f"⚠️ Warning location: {location} is not valid, using default")
        coords = COORDINATES["dtr"]
        
    station = CustomStation.Station(ST.PASSENGER_CAR, coords, SPAWN_AREA)

    speed_kmh = SPEED_KMH
    bearing_degrees = BEARING_DEGREES
    if random_motion and ENABLE_MOVEMENT:
        speed_kmh = random.uniform(min_speed_kmh, max_speed_kmh)
        bearing_degrees = random.uniform(0.0, 360.0)
        print(
            f"🎲 Random motion for station {station.STATION_ID}: "
            f"speed={speed_kmh:.2f} km/h, heading={bearing_degrees:.1f}°"
        )
    
    collector = DataCollector()
    telemetry_publisher = StationTelemetryPublisher.from_env()
    
    # ========== Step 2: Location Service ==========
    if ENABLE_MOVEMENT:
        # Dynamic location: vehicle moves at constant speed
        location_service = DynamicLocationService.DynamicLocationService(
            initial_lat=station.POSITION_COORDINATES[0],
            initial_lon=station.POSITION_COORDINATES[1],
            speed_mps=speed_kmh / 3.6,  # Convert km/h to m/s
            bearing_degrees=bearing_degrees,
            period_ms=1000,
        )
        print(f"🚗 Vehicle moving at {speed_kmh:.2f} km/h, bearing {bearing_degrees:.1f}°")
        # Ensure the dynamic service thread/loop is started if the class exposes start()
        start_fn = getattr(location_service, "start", None)
        if callable(start_fn):
            start_fn()
        # optionally print dynamic service internals for debugging
        lat_attr = getattr(location_service, "current_lat", None)
        lon_attr = getattr(location_service, "current_lon", None)
        if lat_attr is not None and lon_attr is not None:
            print(f"   DynamicLocationService initial pos: {lat_attr:.6f}, {lon_attr:.6f}")
    else:
        # Static location: vehicle stays at spawn position
        location_service = ThreadStaticLocationService(
            period=1000,
            latitude=station.POSITION_COORDINATES[0],
            longitude=station.POSITION_COORDINATES[1],
        )
        print(f"📍 Vehicle static at ({station.POSITION_COORDINATES[0]:.6f}, {station.POSITION_COORDINATES[1]:.6f})")

    if telemetry_publisher is not None:
        location_service.add_callback(
            telemetry_publisher.build_callback(
                station_id=station.STATION_ID,
                station_type=station.STATION_TYPE.value,
            )
        )
        telemetry_publisher.publish_snapshot(
            station_id=station.STATION_ID,
            lat=station.POSITION_COORDINATES[0],
            lon=station.POSITION_COORDINATES[1],
            speed_mps=speed_kmh / 3.6 if ENABLE_MOVEMENT else 0.0,
            heading_deg=bearing_degrees if ENABLE_MOVEMENT else 0.0,
            station_type=station.STATION_TYPE.value,
            role="live",
        )

    # ========== Step 3: GeoNetworking ==========
    mib = MIB(
        itsGnLocalGnAddr=GNAddress(
            m=M.GN_MULTICAST,
            st=station.STATION_TYPE,
            mid=MID(station.MAC_ADDRESS),
        ),
    )
    gn_router = GNRouter(mib=mib, sign_service=None)
    location_service.add_callback(gn_router.refresh_ego_position_vector)

    # ========== Step 4: BTP ==========
    btp_router = BTPRouter(gn_router)
    gn_router.register_indication_callback(btp_router.btp_data_indication)

    # ========== Step 5: Local Dynamic Map ==========
    ldm_location = Location.initializer(
        latitude=int(station.POSITION_COORDINATES[0] * 10**7),
        longitude=int(station.POSITION_COORDINATES[1] * 10**7),
    )
    ldm_area = GeometricArea(
        circle=Circle(radius=5000),  # Consumer area: 5km
        rectangle=None,
        ellipse=None,
    )
    ldm_factory = LDMFactory()
    ldm = ldm_factory.create_ldm(
        ldm_location,
        ldm_maintenance_type="Reactive",
        ldm_service_type="Reactive",
        ldm_database_type="Dictionary",
    )
    location_service.add_callback(ldm_location.location_service_callback)

    # Register with LDM
    register_response: RegisterDataConsumerResp = ldm.if_ldm_4.register_data_consumer(
        RegisterDataConsumerReq(
            application_id=CAM,
            access_permisions=(AccessPermission.CAM,),
            area_of_interest=ldm_area,
        )
    )
    if register_response.result == 2:
        print("Failed to register with LDM!")
        exit(1)

    # CAM received callback
    def on_cam_received(data: RequestDataObjectsResp) -> None:
        try:
            if not data.data_objects:
                return
            
            cam_obj = data.data_objects[0]["dataObject"]
            logger.debug(cam_obj)
            
            # cam_obj is a dict, not an object
            try:
                station_id = cam_obj["header"]["stationId"]
                lat = cam_obj["cam"]["camParameters"]["basicContainer"]["referencePosition"]["latitude"] / 1e7
                lon = cam_obj["cam"]["camParameters"]["basicContainer"]["referencePosition"]["longitude"] / 1e7
                
                # highFrequencyContainer is a tuple ("basicVehicleContainerHighFrequency", { ... })
                high_freq = cam_obj["cam"]["camParameters"]["highFrequencyContainer"]
                if isinstance(high_freq, tuple) and len(high_freq) > 1 and isinstance(high_freq[1], dict):
                    high_freq = high_freq[1]
                elif isinstance(high_freq, tuple) and len(high_freq) > 0 and isinstance(high_freq[0], dict):
                    high_freq = high_freq[0]

                # Extract heading and speed using the actual fields found in the CAM
                heading_val = 0.0
                speed = 0.0
                if isinstance(high_freq, dict):
                    # headingValue unit: 0.1 degrees -> multiply by 0.1
                    h = high_freq.get("heading")
                    if isinstance(h, dict):
                        heading_val = h.get("headingValue", 0) * 0.1
                    # speedValue unit: 0.01 m/s -> divide by 100 to get m/s
                    s = high_freq.get("speed")
                    if isinstance(s, dict):
                        speed = s.get("speedValue", 0) / 100.0
                
                logger.info(f"📍 CAM from {station_id}: lat={lat:.6f}, lon={lon:.6f}, heading={heading_val:.1f}°, speed={speed}")
                print(f"📍 CAM from {station_id}: lat={lat:.6f}, lon={lon:.6f}, heading={heading_val:.1f}°, speed={speed}")
                # pass MAC and set station_rd to the station identifier for formal recording
                collector.log_cam(
                    station_id,
                    lat,
                    lon,
                    speed,
                    heading_val,
                    station_rd=str(station_id),
                    label=0,
                )
            except (KeyError, TypeError) as e:
                logger.error(f"Error accessing CAM dict structure: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Failed to extract CAM data: {e}", exc_info=True)

    # Subscribe to CAMs
    subscribe_response: SubscribeDataObjectsResp = ldm.if_ldm_4.subscribe_data_consumer(
        SubscribeDataobjectsReq(
            application_id=CAM,
            data_object_type=(CAM,),
            priority=1,
            filter=Filter(
                filter_statement_1=FilterStatement(
                    "header.stationId",
                    ComparisonOperators.NOT_EQUAL,
                    station.STATION_ID,
                )
            ),
            notify_time=TimestampIts(0),
            multiplicity=1,
            order=(
                OrderTupleValue(
                    attribute="cam.generationDeltaTime",
                    ordering_direction=OrderingDirection.ASCENDING,
                ),
            ),
        ),
        on_cam_received,
    )
    if subscribe_response.result != SubscribeDataobjectsResult.SUCCESSFUL:
        print("Failed to subscribe to CAM messages!")
        exit(1)

    # ========== Step 6: CA Basic Service ==========
    vehicle_data = VehicleData(
        station_id=station.STATION_ID,
        station_type=station.STATION_TYPE.value,  # Extract integer from enum
        drive_direction="forward",
        vehicle_length={
            "vehicleLengthValue": 1023,
            "vehicleLengthConfidenceIndication": "unavailable",
        },
        vehicle_width=62,
    )
    ca_basic_service = CooperativeAwarenessBasicService(
        btp_router=btp_router,
        vehicle_data=vehicle_data,
        ldm=ldm,
    )
    location_service.add_callback(
        ca_basic_service.cam_transmission_management.location_service_callback
    )
    
    # ========== Ensure vehicle_data is refreshed from DynamicLocationService ==========
    def refresh_vehicle_data_from_location_service():
        # Try multiple common attribute names / methods exposed by DynamicLocationService
        lat = getattr(location_service, "current_lat", None)
        lon = getattr(location_service, "current_lon", None)
        if lat is None or lon is None:
            get_pos = getattr(location_service, "get_position", None)
            if callable(get_pos):
                pos = get_pos()
                try:
                    lat, lon = pos[0], pos[1]
                except Exception:
                    lat = getattr(pos, "lat", None) or getattr(pos, "latitude", None)
                    lon = getattr(pos, "lon", None) or getattr(pos, "longitude", None)

        speed = getattr(location_service, "current_speed_mps", None) or getattr(location_service, "speed_mps", None) or getattr(location_service, "speed", None)
        bearing = getattr(location_service, "current_bearing_deg", None) or getattr(location_service, "bearing_degrees", None) or getattr(location_service, "bearing", None)

        # --- Primary: push a Location object into the registered callbacks ---
        try:
            if lat is not None and lon is not None:
                loc_obj = Location.initializer(
                    latitude=int(lat * 1e7),
                    longitude=int(lon * 1e7),
                )
                # Force GNRouter / CA basic service to refresh using the same API
                try:
                    gn_router.refresh_ego_position_vector(loc_obj)
                except Exception:
                    pass
                try:
                    # transmission manager expects location callbacks too
                    tx_cb = getattr(ca_basic_service.cam_transmission_management, "location_service_callback", None)
                    if callable(tx_cb):
                        tx_cb(loc_obj)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Update vehicle_data fields if available (best-effort)
        try:
            if lat is not None and lon is not None:
                # many internal usages store ints as 1e7
                # set multiple possible attribute names / keys to ensure FlexStack reads them
                int_lat = int(lat * 1e7)
                int_lon = int(lon * 1e7)
                for name in ("latitude","lat","reference_latitude","referencePosition_latitude","position_latitude"):
                    try:
                        setattr(ca_basic_service.vehicle_data, name, int_lat)
                    except Exception:
                        try:
                            ca_basic_service.vehicle_data[name] = int_lat
                        except Exception:
                            pass
                for name in ("longitude","lon","reference_longitude","referencePosition_longitude","position_longitude"):
                    try:
                        setattr(ca_basic_service.vehicle_data, name, int_lon)
                    except Exception:
                        try:
                            ca_basic_service.vehicle_data[name] = int_lon
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            if speed is not None:
                for name in ("speed","speed_mps","velocity","vehicle_speed"):
                    try:
                        setattr(ca_basic_service.vehicle_data, name, float(speed))
                    except Exception:
                        try:
                            ca_basic_service.vehicle_data[name] = float(speed)
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            if bearing is not None:
                for name in ("heading","heading_deg","bearing","drive_direction_deg"):
                    try:
                        setattr(ca_basic_service.vehicle_data, name, float(bearing))
                    except Exception:
                        try:
                            ca_basic_service.vehicle_data[name] = float(bearing)
                        except Exception:
                            pass
        except Exception:
            pass

        # Best-effort: also try to push values to cam_transmission_management internals
        try:
            tx = getattr(ca_basic_service, "cam_transmission_management", None)
            if tx is not None:
                # set same fields on the transmission manager
                if lat is not None and lon is not None:
                    try:
                        tx.vehicle_latitude = int_lat
                        tx.vehicle_longitude = int_lon
                    except Exception:
                        pass
                if speed is not None:
                    try:
                        tx.vehicle_speed = float(speed)
                    except Exception:
                        pass
                if bearing is not None:
                    try:
                        tx.vehicle_heading = float(bearing)
                    except Exception:
                        pass
        except Exception:
            pass
        # Debug: print raw position objects so we can see whether location JSONs change per loop
        try:
            get_pos = getattr(location_service, "get_position", None)
            if callable(get_pos):
                pos = get_pos()
                logger.debug("location_service.get_position() -> %s", pos)
        except Exception:
            logger.exception("location_service.get_position() failed")

        try:
            # Dump VehicleData as used by CA service to confirm transmitted fields
            logger.debug("ca_basic_service.vehicle_data snapshot -> %s", getattr(ca_basic_service, "vehicle_data", None))
        except Exception:
            pass

    # Prime initial vehicle data
    refresh_vehicle_data_from_location_service()

    # ========== Step 7: Link Layer ==========
    btp_router.freeze_callbacks()
    link_layer = RawLinkLayer(
        "lo",
        station.MAC_ADDRESS,
        receive_callback=gn_router.gn_data_indicate,
    )
    gn_router.link_layer = link_layer

    # ========== Step 8: Run ==========
    print("✅ CA Basic Service is running!")
    print("📡 Broadcasting CAMs and listening for nearby vehicles...")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            # refresh vehicle_data every loop so CAM generator receives up-to-date motion
            try:
                refresh_vehicle_data_from_location_service()
            except Exception:
                logger.exception("refresh_vehicle_data_from_location_service failed")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    # Stop location service gracefully if supported
    stop_fn = getattr(location_service, "stop", None)
    if callable(stop_fn):
        stop_fn()
    else:
        # fallback to existing stop_event pattern
        try:
            location_service.stop_event.set()
            location_service.location_service_thread.join()
        except Exception:
            pass
    link_layer.sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Launch a cluster of V2X stations for GeoNetworking simulation"
    )
    parser.add_argument(
        "--location",
        "-l",
        type=str,
        default="dtr",
        help="Cluster location (dtr - Bucharest Drumul Tabere, bcn - Barcelona))"
    )
    parser.add_argument(
        "--random-motion",
        action="store_true",
        help="Randomize speed and heading for this station on startup"
    )
    parser.add_argument(
        "--min-speed-kmh",
        type=float,
        default=20.0,
        help="Minimum random speed in km/h (used with --random-motion)"
    )
    parser.add_argument(
        "--max-speed-kmh",
        type=float,
        default=90.0,
        help="Maximum random speed in km/h (used with --random-motion)"
    )
    args = parser.parse_args()
    if args.min_speed_kmh < 0 or args.max_speed_kmh < 0:
        parser.error("--min-speed-kmh and --max-speed-kmh must be non-negative")
    if args.min_speed_kmh > args.max_speed_kmh:
        parser.error("--min-speed-kmh must be <= --max-speed-kmh")

    main(
        args.location,
        random_motion=args.random_motion,
        min_speed_kmh=args.min_speed_kmh,
        max_speed_kmh=args.max_speed_kmh,
    )