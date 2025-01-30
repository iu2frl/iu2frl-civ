import logging
from serial import Serial

from .exceptions import CivCommandException, CivTimeoutException


logger = logging.getLogger("iu2frl-civ")


class Utils:
    """List of utilities for the CI-V communication"""
    _ser: Serial # Serial port object
    transceiver_address: bytes # Transceiver address
    controller_address: bytes # Controller address
    _read_attempts: int # Number of read attempts
    fake: bool = False # Fake mode
    debug: bool = False # Debug mode
    
    def __init__(self, serial: Serial, transceiver_address, controller_address, read_attempts, debug=False, fake=False):
        self._ser = serial
        self.transceiver_address = transceiver_address
        self.controller_address = controller_address
        self._read_attempts = read_attempts
        self.fake = fake
        if debug:
            logger.setLevel(logging.DEBUG)

    def encode_2_bytes_value(self, value: int) -> bytes:
        """
        Encodes a integer value into two bytes (little endian)
        """
        return value.to_bytes(2, byteorder="little")

    def encode_int_to_icom_bytes(self, value: int) -> bytes:
        """
        Encodes an integer value to ICOM-expected bytes.
        
        Examples:
            1    => b'\x00\x01'
            10   => b'\x00\x10'
            100  => b'\x01\x00'
            255  => b'\x02\x55'
            1234 => b'\x12\x34'
            9999 => b'\x99\x99'
            10000 => b'\x01\x00\x00'
            123456 => b'\x12\x34\x56'
        """
        if value < 0:
            raise ValueError("Negative values are not supported")
        encoded = []
        while value > 0:
            low = value % 10
            high = (value // 10) % 10
            encoded.append((high << 4) | low)  # Store as two-digit decimal BCD
            value //= 100  # Move to the next two-digit pair
        # Ensure at least two bytes (for numbers < 100)
        while len(encoded) < 2:
            encoded.append(0x00)
        encoded.reverse()
        return bytes(encoded)

    def send_command(self, command: bytes, data=b"", preamble=b"") -> bytes:
        """
        Send a command to the radio transceiver

        Returns: the response from the transceiver
        """
        if command is None or not isinstance(command, bytes):
            raise ValueError("Command must be a non-empty byte string")
        if len(command) not in [1, 2, 3, 4]:
            raise ValueError("Command must be 1-4 bytes long (command with an optional subcommand up to 3 bytes)")
        # The command is composed of:
        # - 0xFE 0xFE is the preamble
        # - the transceiver address
        # - the controller address
        # - 0xFD is the terminator
        command_string = preamble + b"\xfe\xfe" + self.transceiver_address + self.controller_address + command + data + b"\xfd"
        logger.debug("Sending command: %s (length: %i)", self.bytes_to_string(command_string), len(command_string))
        # Send the command to the COM port
        self._ser.write(command_string)
        # Read the response from the transceiver
        reply = ""
        valid_reply = False
        for i in range(self._read_attempts):
            # Read data from the serial port until the terminator byte
            reply = self._ser.read_until(expected=b"\xfd")
            logger.debug("Received message: %s (length: %i)", self.bytes_to_string(reply), len(reply))
            # Check if we received an echo message
            if reply == command_string:
                i -= 1  # Decrement cycles as it is just the echo back
                logger.debug("Ignoring echo message")
            # Check the response
            elif len(reply) > 2:
                target_controller: bytes = reply[2].to_bytes(1, "big")  # Target address of the reply from the transceiver
                source_transceiver: bytes = reply[3].to_bytes(1, "big")  # Source address of the reply from the transceiver
                reply_code: bytes = reply[len(reply) - 2].to_bytes(1, "big")  # Command reply status code
                # Check if the response is for us
                if target_controller != self.controller_address or source_transceiver != self.transceiver_address:
                    logger.debug(
                        "Ignoring message which is not for us " + f"(received: {self.bytes_to_string(source_transceiver)} -> {self.bytes_to_string(target_controller)} " + f"but we are using: {self.bytes_to_string(self.transceiver_address)} -> {self.bytes_to_string(self.controller_address)})"
                    )
                    i -= 1  # Decrement cycles to ignore messages not for us
                # Check the return code (0xFA is only returned in case of error)
                elif reply_code == bytes.fromhex("FA"):  # 0xFA (not good)
                    logger.debug("Reply status: NG (%s)", self.bytes_to_string(reply_code))
                    raise CivCommandException("Reply status: NG", reply_code)
                else:
                    logger.debug("Reply status: OK (0xFB)")
                    valid_reply = True
                    break
            # Check if the respose was empty (timeout)
            else:
                logger.debug("Serial communication timeout (%i/%i)", i + 1, self._read_attempts)
        # Return the result to the user
        if not valid_reply:
            raise CivTimeoutException(f"Communication timeout occurred after {i+1} attempts")
        else:
            return reply

    def decode_frequency(self, bcd_bytes) -> int:
        """Decode BCD-encoded frequency bytes to a frequency in Hz"""
        # Reverse the bytes for little-endian interpretation
        reversed_bcd = bcd_bytes[::-1]
        # Convert each byte to its two-digit BCD representation
        frequency_bcd = "".join(f"{byte:02X}" for byte in reversed_bcd)
        return int(frequency_bcd)  # Convert to integer (frequency in Hz)

    def encode_frequency(self, frequency) -> bytes:
        """Convert the frequency to the CI-V representation"""
        frequency_str = str(frequency).rjust(10, "0")
        inverted_freq = frequency_str[::-1]
        hex_list = [f"0x{inverted_freq[1]}{inverted_freq[0]}"]
        hex_list.append(f"0x{inverted_freq[3]}{inverted_freq[2]}")
        hex_list.append(f"0x{inverted_freq[5]}{inverted_freq[4]}")
        hex_list.append(f"0x{inverted_freq[7]}{inverted_freq[6]}")
        hex_list.append(f"0x{inverted_freq[9]}{inverted_freq[8]}")
        return bytes([int(hx, 16) for hx in hex_list])

    def bytes_to_string(self, bytes_array: bytearray) -> str:
        """Convert a byte array to a string"""
        return "0x" + " 0x".join(f"{byte:02X}" for byte in bytes_array)

    def bytes_to_int(self, first_byte: bytes, second_byte: bytes) -> int:
        """Convert a byte array to an integer"""
        return (int(first_byte) * 100) + int(f"{second_byte:02X}")

    def linear_interpolate(self, raw_value: int, points: list) -> float:
        """
        Perform linear interpolation based on the provided points.

        Args:
            raw_value (int): The raw input value to interpolate.
            points (list): A list of tuples (raw, value) representing the known points.

        Returns:
            float: The interpolated or exact value.
        """
        # Check if raw_value matches any known point
        for point in points:
            if raw_value == point[0]:
                return float(point[1])

        # Perform linear interpolation between points
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 < raw_value < x1:
                return y0 + (y1 - y0) * (raw_value - x0) / (x1 - x0)

        # Handle out-of-range values
        if raw_value < points[0][0]:
            return float(points[0][1])
        if raw_value > points[-1][0]:
            return float(points[-1][1])

        return -1.0  # Return -1 if interpolation is not possible

    def convert_to_range(self, input_value, old_min, old_max, new_min, new_max):
        """Convert an input value from a range to a new one"""
        old_range = old_max - old_min
        if old_range == 0:
            new_value = new_min
        else:
            new_range = new_max - new_min
            new_value = (((input_value - old_min) * new_range) / old_range) + new_min
        return new_value
