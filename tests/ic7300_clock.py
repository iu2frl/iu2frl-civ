"""Sample code to show how the library works"""

import time

try:
    # Import the library installed using pip
    from iu2frl_civ.device_factory import DeviceFactory
    from iu2frl_civ.enums import DeviceType, OperatingMode, SelectedFilter, VFOOperation, ScanMode
    from iu2frl_civ.exceptions import CivTimeoutException

    print("Using installed library")
except ImportError:
    # Use this block if working with source code
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from src.iu2frl_civ.device_factory import DeviceFactory
    from src.iu2frl_civ.exceptions import CivTimeoutException
    from src.iu2frl_civ.enums import DeviceType, OperatingMode, SelectedFilter, VFOOperation, ScanMode

    print("Using local library")


# Main program
def main():
    """Connect to the transceiver and get some data"""
    print("Connecting to the transceiver")
    # Device initialization
    radio = DeviceFactory.get_repository(radio_address="0x94", device_type=DeviceType.IC_7300, port="COM10", debug=False, fake=False)
    # Transceiver commands
    print(f"- Connected to the transceiver at {radio._ser.port} with baudrate {radio._ser.baudrate}bps")
    print("- Turning on the transceiver")
    radio.power_on()
    print("- Waiting for the transceiver to be ready..", end="")
    transceiver_address = b"\x00"
    while transceiver_address == b"\x00":
        print(".", end="")
        try:
            transceiver_address = radio.read_transceiver_id()
        except CivTimeoutException:
            pass
    print()
    print("- Syncing the clock to the PC")
    radio.sync_clock()   
    print("- Clock synced")


if __name__ == "__main__":
    main()
