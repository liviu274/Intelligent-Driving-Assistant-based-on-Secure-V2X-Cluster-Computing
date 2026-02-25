import random
from modules import CustomMacAddress, CoordinatesGenerator
from flexstack.geonet.gn_address import ST

class Station:
    
    def __init__(self, TYPE: ST, BASE_COORDINATES: tuple[float, float], AREA=500):
        self.STATION_ID = random.randint(1, 2147483647)
        self.STATION_TYPE = TYPE
        self.POSITION_COORDINATES = CoordinatesGenerator.random_location_within_radius(
            BASE_COORDINATES, AREA
        )
        self.MAC_ADDRESS = CustomMacAddress.macs.generate_unique_mac()
        
if __name__ == '__main__':
    # Testing IDs
    s = Station(None, None, None)
    print(s.ID)