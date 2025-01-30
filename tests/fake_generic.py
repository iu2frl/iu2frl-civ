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
    radio = DeviceFactory.get_repository(radio_address="0x94", device_type=DeviceType.Generic, port="COM10", debug=True, fake=True)
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
    print("Setting transceiver frequency and mode")
    print(f"- Transceiver address: {transceiver_address}")
    new_frequency = 28202000
    print(f"- Setting new frequency to {new_frequency}")
    radio.send_operating_frequency(new_frequency)
    print(f"- Current frequency: {radio.read_operating_frequency()} Hz")
    new_mode = OperatingMode.USB
    new_filter = SelectedFilter.FIL2
    print(f"- Setting new mode to {new_mode.name} with filter {new_filter.name}")
    radio.set_operating_mode(new_mode, new_filter)
    print(f"- Operating mode: {radio.read_operating_mode()}")
    print("Reading transceiver parameters")
    print(f"- S-Meter level: {radio.read_smeter()}")
    print(f"- Squelch opened: {radio.read_squelch_status()}")
    print(f"- Squelch opened: {radio.read_squelch_status2()}")
    print(f"- Volume level: {radio.read_af_volume():.1f} %")
    print(f"- RF gain level: {radio.read_rf_gain():.1f} %")
    print(f"- Squelch level: {radio.read_squelch_level():.1f} %")
    print(f"- NR level: {radio.read_nr_level():.1f} %")
    print(f"- NB level: {radio.read_nb_level():.1f} %")
    print(f"- ID meter: {radio.read_id_meter():.2f} A")
    print(f"- COMP meter: {radio.read_comp_meter():.1f} dB")
    print(f"- PO meter: {radio.read_po_meter():.1f}")
    print(f"- ALC meter: {radio.read_alc_meter():.1f}")
    print(f"- SWR meter: {radio.read_swr_meter():.1f}")
    print(f"- VD meter: {radio.read_vd_meter():.2f} V")

    print("ICOM IP+ Feature")
    print("- Turning ON IP+")
    radio.set_ip_plus_function(True)
    print("- Turning OFF IP+")
    radio.set_ip_plus_function(False)

    print("MF band attenuator")
    print("- Turning ON MF attenuator")
    radio.set_mf_band_attenuator(True)
    print("- Turning OFF MF attenuator")
    radio.set_mf_band_attenuator(False)

    print("Tuning the antenna")
    print("- Turning ON the internal tuner")
    radio.set_antenna_tuner(True)
    print("- Tuning the antenna")
    radio.tune_antenna_tuner()
    print("- Waiting for tuner to complete")
    print("- Returning to RX mode")
    radio.set_mox(False)

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
    radio.start_scan(ScanMode.SELECT_DF_SPAN_50KHZ)
    
    radio.read_band_edge_frequencies()
    # radio.power_off() # works


if __name__ == "__main__":
    main()
