import random

class Macs:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.used = set()
        return cls._instance
    
    def generate_unique_mac(self) -> bytes:
        while True:
            mac = random_locally_administered_mac()
            if mac not in self.used:
                self.used.add(mac)
                return mac
            
def random_locally_administered_mac() -> bytes:
    octets = [random.randint(0x00, 0xFF) for _ in range(6)]
    octets[0] = (octets[0] & 0b11111110) | 0b00000010
    return bytes(octets)

macs = Macs()  # singleton instance