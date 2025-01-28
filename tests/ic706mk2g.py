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
    radio = DeviceFactory.get_repository(radio_address="0x4E", device_type=DeviceType.IC_706_MK2, port="COM10", debug=True, fake=False)
    # Transceiver commands
    print(f"- Connected to the transceiver at {radio._ser.port} with baudrate {radio._ser.baudrate}bps")
    new_frequency = 28202000
    print(f"- Setting new frequency to {new_frequency}")
    radio.send_operating_frequency(new_frequency)
    print(f"- Current frequency: {radio.read_operating_frequency()} Hz")
    new_mode = OperatingMode.USB
    print(f"- Setting new mode to {new_mode.name}")
    radio.set_operating_mode(new_mode)
    print(f"- Operating mode: {radio.read_operating_mode()}")

    print("Memory and VFO modes")
    print("- Setting memory mode")
    for i in range(100):
        print(f"-- Memory {i+1}")
        radio.set_memory_mode(i + 1)
        time.sleep(0.2)
    print("- Setting VFO A")
    radio.set_vfo_mode(VFOOperation.SELECT_VFO_A)
    time.sleep(1)
    print("- Setting VFO B")
    radio.set_vfo_mode(VFOOperation.SELECT_VFO_B)
    time.sleep(1)

    print("Scanning memories")
    radio.start_scan()


if __name__ == "__main__":
    main()
