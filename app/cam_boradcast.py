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

from modules import CustomStation
# Enable logging
logging.basicConfig(level=logging.INFO)


# Cluster Configuration
BASE_COORDINATES = (41.386931, 2.112104)  # Barcelona, Spain
SPAWN_AREA = 500 # Consumer area
station = CustomStation.Station(ST.PASSENGER_CAR, BASE_COORDINATES, SPAWN_AREA)

# POSITION_RADIUS_M = 500.0
# POSITION_COORDINATES = CoordinatesGenerator.random_location_within_radius(
#     BASE_COORDINATES[0], BASE_COORDINATES[1], POSITION_RADIUS_M
# )
# MAC_ADDRESS = CustomMacAddress.Macs.generate_unique_mac()
# STATION_ID = random.randint(1, 2147483647)
# STATION_TYPE = ST.PASSENGER_CAR


def main():
    # ========== Step 2: Location Service ==========
    location_service = ThreadStaticLocationService(
        period=1000,
        latitude=POSITION_COORDINATES[0],
        longitude=POSITION_COORDINATES[1],
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
        latitude=int(POSITION_COORDINATES[0] * 10**7),
        longitude=int(POSITION_COORDINATES[1] * 10**7),
    )
    ldm_area = GeometricArea(
        circle=Circle(radius=5000),  # Concumer area
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
        station_id = data.data_objects[0]["dataObject"]["header"]["stationId"]
        print(f"🚗 Received CAM from station: {station_id}")

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
                    STATION_ID,
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
        station_id=STATION_ID,
        station_type=STATION_TYPE,
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

    # ========== Step 7: Link Layer ==========
    btp_router.freeze_callbacks()
    link_layer = RawLinkLayer(
        "lo",
        MAC_ADDRESS,
        receive_callback=gn_router.gn_data_indicate,
    )
    gn_router.link_layer = link_layer

    # ========== Step 8: Run ==========
    print("✅ CA Basic Service is running!")
    print("📡 Broadcasting CAMs and listening for nearby vehicles...")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    location_service.stop_event.set()
    location_service.location_service_thread.join()
    link_layer.sock.close()


if __name__ == "__main__":
    main()