import random
from modules import CustomMacAddress, CoordinatesGenerator
from flexstack.geonet.gn_address import ST

class Station:
    
    def __init__(self, TYPE: ST, BASE_COORDINATES: tuple[float, float], AREA=500):
        self.ID = random.randint(1, 2147483647)
        self.TYPE = TYPE
        self.POSITION_COORDINATES = CoordinatesGenerator.random_location_within_radius(center=BASE_COORDINATES, radius_m=500)
        self.MAC_ADDRESS = CustomMacAddress.Macs.generate_unique_mac()
        
if __name__ == '__main__':
    # Testing IDs
    s = Station(None, None, None)
    print(s.ID)