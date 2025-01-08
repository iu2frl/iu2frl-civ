"""Sample code to show how the library works"""
import iu2frl_civ

def main():
    """Connect to the transceiver and get some data"""
    radio = iu2frl_civ.Device("0x94", port="/dev/tty", debug=True)
    print(f"- Connected to the transceiver at {radio._ser.port} with baudrate {radio._ser.baudrate}bps")
    print ("- Turning on the transceiver")
    radio.power_on()
    print(f"- Current frequency: {radio.read_operating_frequency()}Hz")
    radio.send_operating_frequency(14123456)
    print(f"- Transceiver address: {radio.read_transceiver_id()}")
    print(f"- Operating mode: {radio.read_operating_mode()}")
    print(f"- S-Meter level: {radio.read_smeter()}")
    print(f"- Squelch status: {radio.read_squelch_status()}")    
    print(f"- Squelch status: {radio.read_squelch_status2()}")
    print(f"- Volume level: {radio.read_af_volume()}")
    print(f"- RF gain level: {radio.read_rf_gain()}")
    print(f"- Squelch level: {radio.read_squelch_level()}")
    print(f"- NR level: {radio.read_nr_level()}")
    #radio.power_off() # works

if __name__ == "__main__":
    main()
