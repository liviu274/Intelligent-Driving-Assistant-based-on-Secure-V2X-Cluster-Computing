#!/usr/bin/env python3
"""
GeoNetworking Example

Demonstrates sending and receiving GN packets over a Raw Link Layer.
"""

import time
from flexstack.linklayer.raw_link_layer import RawLinkLayer
from flexstack.geonet.router import Router as GNRouter
from flexstack.geonet.mib import MIB
from flexstack.geonet.gn_address import GNAddress, M, ST, MID
from flexstack.geonet.service_access_point import (
   GNDataRequest,
   GNDataIndication,
   CommonNH,
   PacketTransportType,
   CommunicationProfile,
   SecurityProfile,
   TrafficClass,
)

MAC_ADDRESS = b'\x00\x11\x22\x33\x44\x55'


def on_gn_packet_received(indication: GNDataIndication):
   """Handle incoming GeoNetworking packets."""
   print(f"📥 Received GN packet: {indication.data[:20].hex()}...")


def main():
   # Step 1: Configure MIB
   mib = MIB(
      itsGnLocalGnAddr=GNAddress(
            m=M.GN_MULTICAST,
            st=ST.CYCLIST,
            mid=MID(MAC_ADDRESS),
      ),
   )

   # Step 2: Create GN Router
   gn_router = GNRouter(mib=mib, sign_service=None)
   gn_router.register_indication_callback(on_gn_packet_received)

#  Step 3: Provide position (manual for this example)
   position = {
      'time': "2005-07-08T11:28:07.114Z",
      'lat': 23.902704,
      'lon': 44.284856,
      'alt': 34.0,
      'speed': 0.0,
      'climb': 0.0,
      'track': 0.0,
      'mode': 3
   }
   gn_router.refresh_ego_position_vector(position)
   
   # Step 4: Connect Link Layer
   link_layer = RawLinkLayer(
      iface="lo",
      mac_address=MAC_ADDRESS,
      receive_callback=gn_router.gn_data_indicate
   )
   gn_router.link_layer = link_layer

   print("✅ GeoNetworking router active")
   print("📡 Sending packets every second...")
   print("Press Ctrl+C to exit\n")

   try:
      while True:
            # Create payload
            payload = payload = b"Hello, GeoNetworking!"

            # Build GN request
            gn_request = GNDataRequest(
               upper_protocol_entity=CommonNH.ANY,
               packet_transport_type=PacketTransportType(),
               communication_profile=CommunicationProfile.UNSPECIFIED,
               security_profile=SecurityProfile.NO_SECURITY,
               its_aid=0,
               security_permissions=b"\x00",
               traffic_class=TrafficClass(),
               length=len(payload),
               data=payload,
            )

            # Send packet
            gn_router.gn_data_request(gn_request)
            print(f"📤 Sent GN packet: {payload[:20]}...")

            time.sleep(1)

   except KeyboardInterrupt:
      print("\n👋 Shutting down...")
   print("✅ Shutdown complete")


if __name__ == "__main__":
   main()