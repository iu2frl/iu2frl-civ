"""Sample code to show how the library works"""

import time
import logging

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
    from src.iu2frl_civ.devices import ic821h
    from src.iu2frl_civ.enums import DeviceType, OperatingMode, VFOOperation

    print("Using local library")


# Main program
def main():
    logger = logging.getLogger("iu2frl-civ")
    logger.setLevel(logging.DEBUG)
    
    """Connect to the transceiver and get some data"""
    print("Connecting to the transceiver")
    # Device initialization
    radio: ic821h = DeviceFactory.get_repository(radio_address="0x4C", device_type=DeviceType.IC_821_H, baudrate=19200, port="COM5", fake=False)
    # Transceiver commands
    print(f"- Connected to the transceiver at {radio._ser.port} with baudrate {radio._ser.baudrate}bps")
    new_frequency = 144880000
    print(f"- Setting new frequency to {new_frequency}")
    radio.send_operating_frequency(new_frequency)
    #print(f"- Current frequency: {radio.read_operating_frequency()} Hz")
    new_mode = OperatingMode.USB
    print(f"- Setting new mode to {new_mode.name}")
    print("- Setting VFO Mode")
    radio.set_vfo_mode(VFOOperation.VFO_MODE)
    time.sleep(1)
    radio.set_operating_mode(new_mode)
    print("- Setting VFO A")
    radio.set_vfo_mode(VFOOperation.SELECT_VFO_A)
    time.sleep(1)
    print("- Setting VFO B")
    radio.set_vfo_mode(VFOOperation.SELECT_VFO_B)
    time.sleep(1)
    print("- Setting VFO A=B")
    radio.set_vfo_mode(VFOOperation.EQUALIZE_VFO_A_B)
    time.sleep(1)
    print("- Setting VFO SUB")
    radio.set_vfo_mode(VFOOperation.SUB_BAND)
    time.sleep(1)
    print("- Toggling VFO MAIN/SUB")
    radio.set_vfo_mode(VFOOperation.EXCHANGE_VFO_A_B)
    time.sleep(1)
    print("- Setting VFO MAIN")
    radio.set_vfo_mode(VFOOperation.MAIN_BAND)
    time.sleep(1)
    print("Memory and VFO modes")
    print("- Setting memory mode")
    radio.set_memory_mode("CALL")
    time.sleep(1)
    radio.set_memory_mode("P1")
    time.sleep(1)
    radio.set_memory_mode("P2")
    time.sleep(1)
    print("- Looping through memories")
    for i in range(80):
        print(f"-- Memory {i+1}")
        radio.set_memory_mode(i + 1)
        time.sleep(1)
    print("- Starting scan")
    radio.start_scan()
    time.sleep(5)
    print("- Stopping scan")
    radio.stop_scan()
    time.sleep(1)
    print("Enabling split")
    radio.split_on()
    time.sleep(5)
    print("Disabling split")
    radio.split_off()
    time.sleep(1)
    print("- Copying memory to VFO")
    radio.set_memory_mode(1)
    time.sleep(1)
    radio.memory_copy_to_vfo()
    time.sleep(1)
    print("- Writing 145.600 MHz to memory 79")
    radio.set_memory_mode(79)
    time.sleep(1)
    radio.send_operating_frequency(145600000)
    time.sleep(1)
    radio.set_operating_mode(OperatingMode.FM)
    time.sleep(1)
    radio.memory_write()
    time.sleep(1)
    radio.clear_current_memory()
    time.sleep(1)
    radio.set_duplex_mode(-1)
    time.sleep(5)
    radio.set_duplex_mode(0)
    time.sleep(5)
    radio.set_duplex_mode(1)
    time.sleep(5)

if __name__ == "__main__":
    main()
