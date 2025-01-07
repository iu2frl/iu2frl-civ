from typing import Tuple
from enum import Enum
import serial

class OperatingMode(Enum):
    """Operating mode of the radio transceiver"""
    LSB = 0
    USB = 1
    AM  = 2
    CW  = 3
    RTTY= 4
    FM  = 5
    NFM = 6
    CWR = 7
    RTTYR=8

class SelectedFilter(Enum):
    FIL1 = 1
    FIL2 = 2
    FIL3 = 3

class SquelchStatus(Enum):
    CLOSED = 0
    OPEN   = 1

class PyCom:
    """Create a PyCom object to interact with the radio transceiver"""
    _ser: serial.Serial # Serial port
    _debug: bool # Debug mode
    _address: str # Hexadecimal address of the radio transceiver

    def __init__(self, address: str, port = "/dev/ttyUSB0", baudrate: int = 19200, debug: bool = False):
        self._ser = serial.Serial(port, baudrate, timeout=1)
        self._debug = debug
        if isinstance(address, str) and str(address).startswith("0x"):
            self._address = address[2:]
        else:
            raise ValueError("Address must be in hexadecimal format (0x00)")
        self._address = address
        if self._debug:
            print(f"Opened port: {self._ser.name}")
            print(f"Baudrate: {self._ser.baudrate} bps")

    def _send_command(self, command: bytes, data=b'', preamble=b'') -> bytes:
        """Send a command to the radio transceiver"""
        if command is None or not isinstance(command, bytes):
            raise ValueError("Command must be a non-empty byte string")
        if len(command) not in [1, 2]:
            raise ValueError("Command must be 1 or 2 bytes long (command with an optional subcommand)")
        # In the command, the 0xFE 0xFE is the preamble, then the transceiver address, 0xE0 is the controller address, and 0xFD is the terminator
        command_string = preamble + b'\xfe\xfe' + bytes([int(self._address, 16)]) + b'\xe0' + command + data + b'\xfd'
        if self._debug:
            print(f"Sending command: {self._bytes_to_string(command_string)} (length: {len(command_string)})")
        self._ser.write(command_string)
        # Our cable reads what we send, so we have to remove this from the buffer first
        reply = self._ser.read_until(expected=b'\xfd')
        if reply == command_string:    
            if self._debug:
                print(f"Received echo: {self._bytes_to_string(reply)} (length: {len(reply)})")
            # Now we are reading replies
            reply = self._ser.read_until(expected=b'\xfd')
        # Print some debug information
        if self._debug:
            print(f"Received reply: {self._bytes_to_string(reply)} (length: {len(reply)})")
            if len(reply) > 2:
                if reply[len(reply)-2] == 250: # 0xFA
                    print(f"Reply status: NG ({reply[len(reply)-2]})")
                else:
                    print("Reply status: OK")
        # Check if any reply from the transceiver
        if len(reply) < 3:
            raise ValueError("No reply received")
        return reply

    def _decode_frequency(self, bcd_bytes) -> int:
        """Decode BCD-encoded frequency bytes to a frequency in Hz"""
        # Reverse the bytes for little-endian interpretation
        reversed_bcd = bcd_bytes[::-1]
        # Convert each byte to its two-digit BCD representation
        frequency_bcd = ''.join(f"{byte:02X}" for byte in reversed_bcd)
        return int(frequency_bcd)  # Convert to integer (frequency in Hz)

    def _encode_frequency(self, frequency) -> bytes:
        """Convert the frequency to the CI-V representation"""
        frequency_str = str(frequency).rjust(10, '0')
        inverted_freq = frequency_str[::-1]
        hex_list = [f"0x{inverted_freq[1]}{inverted_freq[0]}"]
        hex_list.append(f"0x{inverted_freq[3]}{inverted_freq[2]}")
        hex_list.append(f"0x{inverted_freq[5]}{inverted_freq[4]}")
        hex_list.append(f"0x{inverted_freq[7]}{inverted_freq[6]}")
        hex_list.append(f"0x{inverted_freq[9]}{inverted_freq[8]}")
        return bytes([int(hx, 16) for hx in hex_list])

    def _bytes_to_string(self, bytes_array: bytearray) -> str:
        """Convert a byte array to a string"""
        return '0x' + ' 0x'.join(f"{byte:02X}" for byte in bytes_array)
    
    def _bytes_to_int(self, first_byte: bytes, second_byte: bytes) -> int:
        """Convert a byte array to an integer"""
        return (int(first_byte) * 100) + int(f"{second_byte:02X}")

    def power_on(self):
        """Power on the radio transceiver"""
        if self._ser.baudrate == 115200:
            wakeup_preamble_count = 150
        elif self._ser.baudrate == 57600:
            wakeup_preamble_count = 75
        elif self._ser.baudrate == 38400:
            wakeup_preamble_count = 50
        elif self._ser.baudrate == 19200:
            wakeup_preamble_count = 25
        elif self._ser.baudrate == 9600:
            wakeup_preamble_count = 13
        else:
            wakeup_preamble_count = 7

        self._send_command(b'\x18\x01', preamble=b'\xfe' * wakeup_preamble_count)

    def power_off(self):
        """Power off the radio transceiver"""
        self._send_command(b'\x18\x00')

    def read_transceiver_id(self) -> str:
        """Read the transceiver address"""
        reply = self._send_command(b'\x19\x00')
        if len(reply) > 0:
            value = reply[-2:-1]
            return '0x' + value.hex().upper()
        return -1

    def read_operating_frequency(self):
        """Read the operating frequency"""
        try:
            reply = self._send_command(b'\x03')
            return self._decode_frequency(reply[5:10])
        except:
            return -1
    
    def read_operating_mode(self) -> Tuple[str, str]:
        """Read the operating mode"""
        reply = self._send_command(b'\x04')
        if len(reply) == 8:
            mode = OperatingMode(int(reply[5:6].hex())).name
            fil = SelectedFilter(int(reply[6:7].hex())).name
            return [mode, fil]
        else:
            return ["ERR", "ERR"]

    def send_operating_frequency(self, frequency_hz: int) -> bool:
        """Send the operating frequency"""
        # Validate input
        if not (10_000 <= frequency_hz <= 74_000_000):  # IC-7300 frequency range in Hz
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")
        # Encode the frequency
        data = self._encode_frequency(frequency_hz)
        
        # Use the provided _send_command method to send the command
        reply = self._send_command(b'\x05', data=data)
        if len(reply) > 0:
            return True
        else:
            return False

    def read_af_volume(self) -> int:
        """
        Read the AF volume
        
        0: min
        255: max
        """
        reply = self._send_command(b'\x14\x01')
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1
    
    def read_rf_gain(self) -> int:
        """
        Read the RF gain
        
        0: min
        255: max
        """
        reply = self._send_command(b'\x14\x02')
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1
    
    def read_squelch_level(self) -> int:
        """
        Read the squelch level
        
        0: min
        255: max
        """
        reply = self._send_command(b'\x14\x03')
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1
    
    def read_nr_level(self) -> int:
        """
        Read the NR level
        
        0: min
        255: max
        """
        reply = self._send_command(b'\x14\x06')
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1
    
    def read_nb_level(self) -> int:
        """
        Read the NB level
        
        0: min
        255: max
        """
        reply = self._send_command(b'\x14\x12')
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_smeter(self) -> int:
        """
        Read the S-meter value
        
        TODO: test if properly working
        """
        reply = self._send_command(b'\x15\x02')
        if len(reply) == 9:
            return int(reply[6:8].hex(), 16)
        return -1

    def read_squelch_status(self):
        """
        Read noise or S-meter squelch status
        
        TODO: test if properly working
        """
        reply = self._send_command(b'\x15\x01')
        return reply

    def read_squelch_status2(self):
        """
        Read various squelch function’s status
        
        TODO: test if properly working
        """
        reply = self._send_command(b'\x15\x05')
        return reply