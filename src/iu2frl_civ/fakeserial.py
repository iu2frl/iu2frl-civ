"""Fake serial port for testing purposes"""

class FakeSerial:
    """Fake serial port for testing purposes"""
    transceiver_address: bytes = b"\x94"
    controller_address: bytes = b"\xE0"
    name: str = "FakeSerial"
    baudrate: int = 19200
    port: str = "/dev/ttyUSB0"

    def __init__(self, transceiver_address, controller_address, baudrate, port, *args, **kwargs):
        self.transceiver_address = transceiver_address
        self.controller_address = controller_address
        self.baudrate = baudrate
        self.port = port

    def write(self, *args, **kwargs):
        """Fake writing of serial port data"""
        pass

    def read_until(self, *args, **kwargs):
        """Fake readings of serial port data from the serial port until the terminator byte"""
        return_list = [0xFE, 0xFE, int.from_bytes(self.controller_address, 'big'), int.from_bytes(self.transceiver_address, 'big'), 0x00, 0x00, 0x00, 0x00, 0xFB, 0xFD]
        return bytes(return_list)

    def close(self):
        """Fake closing of the serial port"""
        pass