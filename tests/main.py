"""Sample code to show how the library works"""
try:
    # Import the library installed using pip
    from iu2frl_civ import iu2frl_civ
except ImportError:
    # Use this block if working with source code
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from src.iu2frl_civ import iu2frl_civ

# Main program
def main():
    """Connect to the transceiver and get some data"""
    radio = iu2frl_civ.Device("0x94", port="COM10", debug=False)
    print(f"- Connected to the transceiver at {radio._ser.port} with baudrate {radio._ser.baudrate}bps")
    print ("- Turning on the transceiver")
    radio.power_on()
    print("- Waiting for the transceiver to be ready..", end="")
    transceiver_address = b'\x00'
    while transceiver_address == b'\x00':
        print(".", end="")
        try:
            transceiver_address = radio.read_transceiver_id()
        except iu2frl_civ.CivTimeoutException:
            pass
    print()
    print(f"- Transceiver address: {transceiver_address}")
    print(f"- Current frequency: {radio.read_operating_frequency()} Hz")
    radio.send_operating_frequency(28202000)
    print(f"- Operating mode: {radio.read_operating_mode()}")
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
    #radio.power_off() # works

if __name__ == "__main__":
    main()
