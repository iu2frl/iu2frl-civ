"""
Custom class to communicate with ICOM devices using CI-V protocol
This class was built using the section 19 of the ICOM IC-7300 User Manual
"""

from typing import Tuple
import logging
import datetime
import time

from ..enums import OperatingMode, SelectedFilter, VFOOperation, ScanMode, DeviceType, ToneType
from ..device_base import DeviceBase
from ..utils import Utils

logger = logging.getLogger("iu2frl-civ")


class IC7300(DeviceBase):
    """Create a CI-V object to interact with a generic the radio transceiver"""

    valid_rpt_tones = [67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2, 192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3, 254.1]
    allowed_memory_Name_characters = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '!', '#', '$', '%', '&', '\\', '?', '"', '\'', '`', '^', '+', '-', '*', '/', '.', ',', ':', ';', '=', '<', '>', '(', ')', '[', ']', '{', '}', '|', '_', '~', '@', ' '
    ]
    memory_keyer_characters = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',  # Numeri
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', # Lettere maiuscole
        ' ',  # Spazio (word space)
        '/',  # Symbol
        '?',  # Symbol
        ',',   # Symbol
        '.',   # Symbol
        '@',   # Symbol
        '^',   # Symbol
        '*'
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the IC7300 object"""
        super().__init__(*args, **kwargs)
        self.utils = Utils(self._ser, self.transceiver_address, self.controller_address, self._read_attempts, debug=self.debug, fake=self.fake)

    def power_on(self) -> bytes:
        """
        Power on the radio transceiver

        Returns: the response from the transceiver
        """
        # Preamble counts for different baudrates
        preamble_counts = {115200: 150, 57600: 75, 38400: 50, 19200: 25, 9600: 13}
        wakeup_preamble_count = preamble_counts.get(self._ser.baudrate, 7)
        logger.debug("Sending power-on command with %i wakeup preambles", wakeup_preamble_count)
        return self.utils.send_command(b"\x18\x01", preamble=b"\xfe" * wakeup_preamble_count)

    def power_off(self) -> bytes:
        """
        Power off the radio transceiver

        Returns: the response from the transceiver
        """
        return self.utils.send_command(b"\x18\x00")

    def read_transceiver_id(self) -> bytes:
        """
        Read the transceiver address

        Returns: the address of the transceiver, 0x00 if error
        """
        reply = self.utils.send_command(b"\x19\x00")
        if len(reply) > 0:
            return reply[-2:-1]
        return b"\x00"

    def read_operating_frequency(self) -> int:
        """
        Read the operating frequency

        Returns: the currently tuned frequency in Hz
        """
        try:
            reply = self.utils.send_command(b"\x03")
            return self.utils.decode_frequency(reply[5:10])
        except:
            return -1

    def read_operating_mode(self) -> Tuple[str, str]:
        """
        Read the operating mode

        Returns: a tuple containing
            - the current mode
            - the current filter
        """
        reply = self.utils.send_command(b"\x04")
        if len(reply) == 8:
            mode = OperatingMode(int(reply[5:6].hex())).name
            fil = SelectedFilter(int(reply[6:7].hex())).name
            return [mode, fil]
        else:
            return ["ERR", "ERR"]

    def send_operating_frequency(self, frequency_hz: int | float) -> bool:
        """
        Send the operating frequency

        Returns: True if the frequency was properly sent
        """
        if isinstance(frequency_hz, float):  # fix for using scientific notation ex: 14.074e6
            frequency_hz = int(frequency_hz)

        # Validate input
        if not (10_000 <= frequency_hz <= 74_000_000):  # IC-7300 frequency range in Hz
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")
        # Encode the frequency
        data = self.utils.encode_frequency(frequency_hz)

        # Use the provided _send_command method to send the command
        reply = self.utils.send_command(b"\x05", data=data)
        if len(reply) > 0:
            return True
        else:
            return False

    def read_af_volume(self) -> int:
        """
        Read the AF volume

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the volume being set
        """
        reply = self.utils.send_command(b"\x14\x01")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            return self.utils.convert_to_range(raw_value, 0, 255, 0, 100)
        return -1

    def read_rf_gain(self) -> int:
        """
        Read the RF gain

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the RF gain being set
        """
        reply = self.utils.send_command(b"\x14\x02")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            return self.utils.convert_to_range(raw_value, 0, 255, 0, 100)
        return -1

    def read_squelch_level(self) -> int:
        """
        Read the squelch level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the squelch being set
        """
        reply = self.utils.send_command(b"\x14\x03")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            return self.utils.convert_to_range(raw_value, 0, 255, 0, 100)
        return -1

    def read_nr_level(self) -> int:
        """
        Read the NR level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the NR being set
        """
        reply = self.utils.send_command(b"\x14\x06")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            return self.utils.convert_to_range(raw_value, 0, 255, 0, 100)
        return -1

    def read_nb_level(self) -> float:
        """
        Read the NB level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the NB being set
        """
        reply = self.utils.send_command(b"\x14\x12")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            return self.utils.convert_to_range(raw_value, 0, 255, 0, 100)
        return -1

    def read_smeter(self) -> int:
        """
        Read the S-meter value

        0: min
        255: max

        0000=S0, 0120=S9, 0241=S9+60dB

        TODO: test if properly working
        """
        reply = self.utils.send_command(b"\x15\x02")
        if len(reply) == 9:
            return self.utils.bytes_to_int(reply[6], reply[7])
        return -1

    def read_squelch_status(self):
        """
        Read noise or S-meter squelch status

        Returns: True if squelch is enabled (audio is silent)
        """
        reply = self.utils.send_command(b"\x15\x01")
        return not bool(reply[6])

    def read_squelch_status2(self):
        """
        Read various squelch function’s status

        Returns: True if squelch is enabled (audio is silent)
        """
        reply = self.utils.send_command(b"\x15\x05")
        return not bool(reply[6])

    def set_operating_mode(self, mode: OperatingMode, new_filter: SelectedFilter = SelectedFilter.FIL1):
        """Sets the operating mode and filter."""
        # Command 0x06 with mode and filter data
        data = bytes([mode.value, new_filter.value])
        self.utils.send_command(b"\x06", data=data)

    def read_po_meter(self) -> float:
        """
        Read the PO meter level.
        0: 0%
        143: 50%
        213: 100%
        """
        reply = self.utils.send_command(b"\x15\x11")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # Known points (raw -> PO%)
            points = [(0, 0), (143, 50), (213, 100)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1

    def read_swr_meter(self) -> float:
        """
        Read the SWR meter level.
        0: SWR1.0,
        48: SWR1.5,
        80: SWR2.0,
        120: SWR3.0
        """
        reply = self.utils.send_command(b"\x15\x12")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # Known points (raw -> SWR)
            points = [(0, 1), (48, 1.5), (80, 2.0), (120, 3.0), (255, 99)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1

    def read_alc_meter(self) -> float:
        """
        Read the ALC meter level.
        0: Min
        120: Max
        """
        reply = self.utils.send_command(b"\x15\x13")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # Known points (raw -> ALC%)
            points = [(0, 0), (120, 100)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1

    def read_comp_meter(self) -> float:
        """
        Read the COMP meter level.
        0: 0 dB,
        130: 15 dB,
        241: 30 dB
        """
        reply = self.utils.send_command(b"\x15\x14")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # Known points (raw -> dB)
            points = [(0, 0), (130, 15), (241, 30)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1

    def read_vd_meter(self) -> float:
        """
        Read the Vd meter level.

        Raw values from CI-V:
        - 0: 0 V
        - 13: 10 V
        - 241: 16 V

        Returns:
            float: The voltage in volts measured on the amplifier.
        """
        reply = self.utils.send_command(b"\x15\x15")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # Known points (raw -> A)
            points = [(0, 0), (13, 10), (241, 16)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1.0  # Return -1 in case of error

    def read_id_meter(self) -> float:
        """
        Read the Id meter level.

        Raw values from CI-V:
        - 0: 0A,
        - 97: 10A,
        - 146: 15A,
        - 241: 25A

        Returns: the current in Ampere being mesured on the amplifier
        """
        reply = self.utils.send_command(b"\x15\x16")
        if len(reply) == 9:
            raw_value = self.utils.bytes_to_int(reply[6], reply[7])
            # List of known points (from the manual - byte -> Ampere)
            points = [(0, 0), (97, 10), (146, 15), (241, 25)]
            return self.utils.linear_interpolate(raw_value, points)
        return -1.0  # Return -1 in case of error

    def set_antenna_tuner(self, on: bool):
        """Turns the antenna tuner on or off."""
        if on:
            self.utils.send_command(b"\x1C\x01", b"\x01")  # Turn tuner ON
        else:
            self.utils.send_command(b"\x1C\x01", b"\x00")  # Turn tuner OFF

    def tune_antenna_tuner(self):
        """Starts the antenna tuner tuning process."""
        self.utils.send_command(b"\x1C\x01", b"\x02")

    def stop_scan(self):
        """Stops the scan."""
        self.utils.send_command(b"\x0E\x00")

    def send_cw_message(self, message: str):
        """Send a CW message. Limited to 30 characters"""
        if len(message) > 30:
            raise ValueError("Message must be 30 characters or less")
        # convert the string to bytes
        message_bytes = message.encode("ascii")
        self.utils.send_command(b"\x17", data=message_bytes)

    def set_ip_plus_function(self, enable: bool) -> bool:
        """
        Sets the IP+ function setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self.utils.send_command(b"\x1a\x07", data=bytes([value]))
        return len(reply) > 0

    def set_mf_band_attenuator(self, enable: bool) -> bool:
        """
        Sets the MF band attenuator setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        reply = self.utils.send_command(b"\x1a\x05\x01\x93", data=bytes([int(enable)]))
        return len(reply) > 0

    def set_vfo_mode(self, vfo_mode: VFOOperation = VFOOperation.SELECT_VFO_A):
        """Sets the VFO mode."""
        if vfo_mode in VFOOperation:
            self.utils.send_command(b"\x07", data=vfo_mode.value)
        else:
            raise ValueError("Invalid vfo_mode")

    def set_memory_mode(self, memory_channel: int):
        """Sets the memory mode, accepts values from 1 to 101"""
        if not (1 <= memory_channel <= 101):
            raise ValueError("Memory channel must be between 1 and 101")
        # 0001 to 0109 Select the Memory channel *(0001=M-CH01, 0099=M-CH99)
        # 0100 Select program scan edge channel P1
        # 0101 Select program scan edge channel P2

        if 0 < memory_channel < 100:
            hex_list = ["0x00"]
        elif memory_channel in [100, 101]:
            hex_list = ["0x01"]
        else:
            raise ValueError("Memory channel must be between 1 and 101")
        number_as_string = str(memory_channel).rjust(3, "0")
        hex_list.append(f"0x{number_as_string[1]}{number_as_string[2]}")
        self.utils.send_command(b"\x08", data=bytes([int(hx, 16) for hx in hex_list]))

    def set_mox(self, transmit: bool):
        """Turns the MOX on or off"""
        if transmit:
            self.utils.send_command(b"\x1C\x00", b"\x01")
        else:
            self.utils.send_command(b"\x1C\x00", b"\x00")

    def set_lcd_brightness(self, level: int):
        """Sets the LCD brightness, from 0 to 255"""
        if not (0 <= level <= 255):
            raise ValueError("Level must be between 0 and 255")
        level_bytes = self.utils.encode_int_to_icom_bytes(level)
        self.utils.send_command(b"\x1A\x05\x00\x81", data=level_bytes)

    def set_display_font(self, round_font: bool = True):
        """Set the display font"""
        if round_font:
            self.utils.send_command(b"\x1A\x05\x00\x83", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x00\x83", b"\x00")

    def set_scope_mode_fixed(self, fixed_mode: bool = False):
        """Sets the scope mode, True for Fixed, False for Center"""
        if fixed_mode:
            self.utils.send_command(b"\x27\x14", b"\x00\x01")
        else:
            self.utils.send_command(b"\x27\x14", b"\x00\x00")

    def set_scope_enabled(self, enabled: bool) -> bool:
        """
        Set the Scope ON/OFF status
        """
        if enabled:
            self.utils.send_command(b"\x27\x10", b"\x01")
        else:
            self.utils.send_command(b"\x27\x10", b"\x00")
        return True

    def set_scope_data_out(self, enabled: bool) -> bool:
        """
        Enables scope data output to the COM port
        """
        if enabled:
            self.utils.send_command(b"\x27\x11", b"\x01")
        else:
            self.utils.send_command(b"\x27\x11", b"\x00")
        return True

    def set_scope_span(self, span_hz: int):
        """
        Sets the scope span in ±Hz
        Valid values are: 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000
        Example: 50000 => ±50000Hz => 100000Hz
        """
        valid_values = [2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000]
        if span_hz not in valid_values:
            raise ValueError(f"Invalid value: {span_hz}")
        span_bytes = b"\x00"
        span_bytes += self.utils.encode_frequency(span_hz)
        self.utils.send_command(b"\x27\x15", data=span_bytes)

    def set_scope_sweep_speed(self, speed: int):
        """Sets the sweep speed of the scope, 0: fast, 1: mid, 2: slow"""
        if speed in [0, 1, 2]:
            data_bytes = b"\x00"
            data_bytes += bytes([speed])
            self.utils.send_command(b"\x27\x1A", data=data_bytes)
        else:
            raise ValueError("Invalid speed value, must be 0, 1, or 2")

    def memory_copy_to_vfo(self):
        """Copies memory to VFO"""
        self.utils.send_command(b"\x0A")

    def set_display_image_type(self, blue_background: bool = True):
        """Set display image type"""
        if blue_background:
            self.utils.send_command(b"\x1A\x05\x00\x82", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x00\x82", b"\x00")

    def clear_current_memory(self):
        """Clears the current memory"""
        self.utils.send_command(b"\x0B")

    def set_nb_depth(self, depth: int) -> bool:
        """
        Sets the NB depth.

        Args:
            depth (int): The NB depth (1-10).

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the depth is not within the valid range (1 to 10)
        """
        if not (1 <= depth <= 10):
            raise ValueError("Depth must be between 1 and 10")
        reply = self.utils.send_command(b"\x1a\x05\x01\x89", data=bytes([depth - 1]))
        return len(reply) > 0

    def set_nb_width(self, width: int) -> bool:
        """
        Sets the NB width.

        Args:
            width (int): The NB width (1-100).

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the width is not within the valid range (1 to 100)
        """
        if not (0 <= width <= 100):
            raise ValueError("Width must be between 0 and 100")
        width = int(self.utils.convert_to_range(width, 0, 100, 0, 255))
        width_bytes = self.utils.encode_int_to_icom_bytes(width)
        reply = self.utils.send_command(b"\x1a\x05\x01\x90", data=width_bytes)
        return len(reply) > 0

    def set_data_mode(self, enable: bool, new_filter: int = 1) -> bool:
        """
        Sets the data mode.

        Args:
            enable (bool): True to enable, False to disable.
            filter (int, optional): The filter to select (1-3). Defaults to 1

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the filter is not within the valid range (1 to 3)
        """
        if not (1 <= new_filter <= 3):
            raise ValueError("Filter must be between 1 and 3")

        value = 1 if enable else 0
        if not enable:
            new_filter = 0
        reply = self.utils.send_command(b"\x1a\x06", data=bytes([value, new_filter]))
        return len(reply) > 0

    def set_vox_delay(self, delay: int) -> bool:
        """
        Sets the VOX delay.

        Args:
            delay (int): The VOX delay in tenths of a second (0-20, representing 0.0 to 2.0 seconds).

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the delay is not within the valid range (0 to 20).
        """
        if not (0 <= delay <= 20):
            raise ValueError("Delay must be between 0 and 20")
        reply = self.utils.send_command(b"\x1a\x05\x01\x91", data=bytes([delay]))
        return len(reply) > 0

    def set_vox_voice_delay(self, voice_delay: int) -> bool:
        """
        Sets the VOX voice delay.

        Args:
            voice_delay (int): The VOX voice delay.
                0: OFF
                1: Short
                2: Mid.
                3: Long

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the value is not between 0 and 3
        """
        if not (0 <= voice_delay <= 3):
            raise ValueError("Value must be between 0 and 3")
        reply = self.utils.send_command(b"\x1a\x05\x01\x92", data=bytes([voice_delay]))
        return len(reply) > 0

    def start_scan(self, scan_type: ScanMode = ScanMode.SELECT_DF_SPAN_100KHZ):
        """
        Starts scanning, different types available according to the sub command

        Note:
            if no memories are programmed, and the memory mode is invoked,
            an exception is returned
        """
        if scan_type in ScanMode:
            self.utils.send_command(b"\x0E", data=scan_type.value)
        else:
            raise ValueError("Invalid scan type")

    def set_scan_speed(self, high: bool):
        """Sets the scan speed"""
        if high:
            self.utils.send_command(b"\x1A\x05\x01\x78", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x78", b"\x00")

    def set_scope_reference_level(self, level: float):
        """Sets the scope reference level, range is -20.0 to +20.0 dB in 0.5 dB steps"""
        if not (-20.0 <= level <= 20.0):
            raise ValueError("Level must be between -20.0 and +20.0 dB")
        if level % 0.5 != 0:
            raise ValueError("Level must be in 0.5 dB increments")

        # Convert the level to the required format
        level_bytes = b"\x00"
        level_bytes += self.utils.encode_int_to_icom_bytes(abs(level * 100))
        if level >= 0:
            level_bytes += b"\x00"
        else:
            level_bytes += b"\x01"

        self.utils.send_command(b"\x27\x19", data=level_bytes)

    def set_scope_vbw(self, wide: bool = True):
        """Sets the scope VBW (Video Band Width), True for wide, false for narrow"""
        if wide:
            self.utils.send_command(b"\x27\x1D", b"\x00\x01")
        else:
            self.utils.send_command(b"\x27\x1D", b"\x00\x00")

    def set_scope_waterfall_display(self, on: bool):
        """Turns the waterfall display on or off for the scope"""
        if on:
            self.utils.send_command(b"\x1A\x05\x01\x07", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x07", b"\x00")

    def set_memory_keyer_message(self, channel: int, text: str) -> bool:
        """
        Sends a message to the radio transceiver's memory keyer.
            channel (int): Memory channel number (1-8) where the message will be stored.
            text (str): Message text to store, using ASCII characters as specified in the manual.
                    Special characters:
                    - "^": Send without spaces between characters
                    - "*": Insert contest number (can only be used in one channel)
            bool: True if the message was sent successfully, False otherwise
        Raises:
            ValueError: If channel number is not between 1 and 8
        Examples:
            >>> radio.send_memory_keyer_message(1, "CQ TEST IU2FRL") 
            True
            >>> radio.send_memory_keyer_message(2, "5NN*")  # Contest message with number
            True
        """
        if not 1 <= channel <= 8:
            raise ValueError("Channel number must be between 1 and 8")

        encoded_text = channel.to_bytes(1, 'big')
        for char in text:
            if char in self.memory_keyer_characters:
                encoded_text += bytes([ord(char)])
            else:
                raise ValueError(f"Invalid character: {char}")
        
        command = b'\x1a\x02'

        reply = self.utils.send_command(command, data=encoded_text)
    
        if len(reply) > 0:
            return True
        else:
            return False
    
    def read_memory_keyer_message(self, channel: int) -> bytes:
        """
        Read the content of a memory keyer channel.
        This function retrieves the stored text from one of the eight memory keyer channels
        of the IC-7300 transceiver.
        Args:
            channel (int): The memory keyer channel number (1-8)
        Returns:
            str: The ASCII decoded content of the memory keyer channel,
                 or None if no data is received
        Raises:
            ValueError: If channel number is not between 1 and 8
        Example:
            >>> radio.read_memory_keyer_content(1)
            'CQ CQ DE IU2FRL'
        """
        if not 1 <= channel <= 8:
            raise ValueError("Il canale deve essere un numero tra 1 e 8")

        channel_bytes = channel.to_bytes(1, 'big')

        reply = self.utils.send_command(b'\x1a\x02', data=channel_bytes)
    
        if len(reply) > 0:
            return reply[7:-2].decode('ascii').strip()
        
        return None

    def clear_memory(self, memory_channel: int):
        """
        Clears the specified memory channel.

        Args:
            memory_channel: The memory channel number (1-99).
        """
        if not 1 <= memory_channel <= 99:
            raise ValueError("Memory channel must be between 1 and 99")
        
        command_data = memory_channel.to_bytes(2, 'big') + b'\xFF' 
        
        reply = self.utils.send_command(b'\x1a\x00', data=command_data)
        return len(reply) > 0

    def sync_clock(self, utc: bool = False):
        """
        Synchronizes the radio's clock with the PC's time.

        Args:
            utc: If True, sets the clock to UTC, otherwise uses local time.
        """
        if utc:
            now = datetime.datetime.now(datetime.timezone.utc)
        else:
            now = datetime.datetime.now()

        # Set the time
        formatted_date = (now.year * 10000) + (now.month * 100) + now.day
        date_bytes = self.utils.encode_int_to_icom_bytes(formatted_date)
        self.utils.send_command(b'\x1a\x05\x00\x94', data=date_bytes)

        # Set the date
        time_str = now.hour * 100 + now.minute
        time_bytes = self.utils.encode_int_to_icom_bytes(time_str)
        self.utils.send_command(b'\x1a\x05\x00\x95', data=time_bytes)

        if not utc:
            # Calculate UTC offset
            utc_offset_seconds = int(time.timezone) * -1 # UTC+1 = 3600
            utc_offset_hours = utc_offset_seconds // 3600 # UTC+1 = 1
            utc_offset_minutes = (utc_offset_seconds % 3600) // 60 # UTC+1 = 0

            # Time offset must be between -14 and +14 hours
            if utc_offset_hours > 14:
                utc_offset_hours = 14
            if utc_offset_hours < -14:
                utc_offset_hours = -14

            # Determine the direction of the offset
            if utc_offset_hours >= 0 :
                direction_byte = b'\x00' # positive
            else:
                direction_byte = b'\x01' # negative

            # Convert the offset to the ICOM format
            offset = utc_offset_hours * 100 + utc_offset_minutes
            offset_bytes = self.utils.encode_int_to_icom_bytes(abs(offset))

        else:
            # Set the offset to 0
            direction_byte = b'\x00'
            offset_bytes = b'\x00\x00'
            
        # Send the offset to the radio
        self.utils.send_command(b'\x1a\x05\x00\x96', data=offset_bytes+direction_byte)

    # TODO: test all methods starting from this one

    def set_scan_resume(self, on: bool):
        """Set scan resume on or off"""
        if on:
            self.utils.send_command(b"\x0E\xD3")
        else:
            self.utils.send_command(b"\x0E\xD0")

    def set_speech_synthesizer(self, speech_type: int = 1):
        """
        Set which speech data is used

        00 Speech all data with voice synthesizer
        01 Speech the operating frequency and S meter
        level by voice synthesizer
        02 Speech the operating mode by voice synthesizer
        """
        if speech_type in [1, 2]:
            self.utils.send_command(b"\x13", data=bytes([speech_type]))
        else:
            raise ValueError("Invalid speech type")

    def set_speech_level(self, level: int):
        """Sets the speech level from 0 to 255"""
        if not (0 <= level <= 255):
            raise ValueError("Level must be between 0 and 255")
        level_bytes = level.to_bytes(2, "little")
        self.utils.send_command(b"\x1A\x05\x00\x43", data=level_bytes)

    def set_speech_language(self, english: bool = True):
        """Sets the speech language, True for english, false for japanese"""
        if english:
            self.utils.send_command(b"\x1A\x05\x00\x39", b"\x00")
        else:
            self.utils.send_command(b"\x1A\x05\x00\x39", b"\x01")

    def set_speech_speed(self, high: bool = True):
        """Sets the speech speed"""
        if high:
            self.utils.send_command(b"\x1A\x05\x00\x40", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x00\x40", b"\x00")

    def read_band_edge_frequencies(self):
        """
        Reads the band edge frequencies.
        This command requires further implementation due to its complex data structure
        """
        raise NotImplementedError()
        reply = self.utils.send_command(b"\x02")
        return reply

    def read_scope_waveform_data(self) -> bytes:
        """
        Reads the scope waveform data
        Note, this only works if:
        - Baudrate is set to 115200bps
        - Scope Data Output is enabled
        - Scope is enabled
        """
        # Command is complex and requires further investigation
        reply = self.utils.send_command(b"\x27\x00")
        return reply[6:-1]

    def set_scope_fixed_edge_frequencies(self, edge_number: int, lower_frequency: int, higher_frequency: int):
        """Sets the fixed edge frequencies for the scope
        edge_number is 1, 2, or 3
        lower_frequency and higher_frequency are in Hz
        """
        if edge_number not in [1 - 3]:
            raise ValueError("Edge number must be 1, 2, or 3")

        if not (10_000 <= lower_frequency <= 74_000_000) or not (10_000 <= higher_frequency <= 74_000_000):
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")

        data = b""
        lower_freq_bytes = self.utils.encode_frequency(lower_frequency)
        higher_freq_bytes = self.utils.encode_frequency(higher_frequency)

        data = bytes([edge_number]) + lower_freq_bytes + higher_freq_bytes

        self.utils.send_command(b"\x27\x1E", data=data)

    def set_memory_name(self, memory_channel: int, name: str):
        """
        Sets the memory name, max 10 characters
        memory_channel 1 to 99
        """
        if not (1 <= memory_channel <= 99):
            raise ValueError("Memory channel must be between 1 and 99")
        if len(name) > 10:
            raise ValueError("Memory name must be 10 characters or less")

        # Convert the memory channel to a byte array
        channel_bytes = memory_channel.to_bytes(2, "big")
        # convert the string to bytes
        name_bytes = b""

        for char in name:
            name_bytes += bytes([ord(char)])

        # pad the name with spaces if it is less than 10
        while len(name_bytes) < 10:
            name_bytes += b"\x20"

        data = channel_bytes + b"\x00" + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" + name_bytes

        self.utils.send_command(b"\x1A\x00", data=data)

    def set_rtty_mark_frequency(self, frequency: int):
        """Sets the RTTY mark frequency, 0=1275 Hz, 1=1615 Hz, 2=2125 Hz"""
        if frequency not in [1, 2]:
            raise ValueError("Invalid RTTY mark frequency")
        self.utils.send_command(b"\x1A\x05\x00\x36", data=bytes([frequency]))

    def set_rtty_shift_width(self, width: int):
        """Sets the RTTY shift width, 0=170 Hz, 1=200 Hz, 2=425 Hz"""
        if width not in [1, 2]:
            raise ValueError("Invalid RTTY shift width")
        self.utils.send_command(b"\x1A\x05\x00\x37", data=bytes([width]))

    def set_rtty_keying_polarity(self, reverse: bool = False):
        """Sets the RTTY keying polarity, True for reverse, False for normal"""
        if reverse:
            self.utils.send_command(b"\x1A\x05\x00\x38", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x00\x38", b"\x00")

    def set_rtty_decode_usos(self, on: bool = False):
        """Set RTTY decode USOS"""
        if on:
            self.utils.send_command(b"\x1A\x05\x01\x68", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x68", b"\x00")

    def set_rtty_decode_newline_code(self, crlf: bool = True):
        """Set RTTY decode new line code"""
        if crlf:
            self.utils.send_command(b"\x1A\x05\x01\x69", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x69", b"\x00")

    def set_rtty_tx_usos(self, on: bool = False):
        """Sets RTTY tx USOS"""
        if on:
            self.utils.send_command(b"\x1A\x05\x01\x70", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x70", b"\x00")

    def set_rtty_log(self, on: bool = False):
        """Set RTTY log function"""
        if on:
            self.utils.send_command(b"\x1A\x05\x01\x73", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x73", b"\x00")

    def set_rtty_log_file_format(self, html: bool = False):
        """Set the file format for the RTTY log, True for HTML, False for text"""
        if html:
            self.utils.send_command(b"\x1A\x05\x01\x74", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x74", b"\x00")

    def set_rtty_log_time_stamp(self, on: bool = False):
        """Set RTTY time stamp"""
        if on:
            self.utils.send_command(b"\x1A\x05\x01\x75", b"\x01")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x75", b"\x00")

    def set_rtty_log_time_stamp_local(self, local: bool = True):
        """Set the RTTY Log Time Stamp local or UTC"""
        if local:
            self.utils.send_command(b"\x1A\x05\x01\x76", b"\x00")
        else:
            self.utils.send_command(b"\x1A\x05\x01\x76", b"\x01")

    def set_rtty_log_frequency_stamp(self, enable: bool) -> bool:
        """
        Sets the RTTY frequency stamp.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self.utils.send_command(b"\x1a\x05\x01\x77", data=bytes([value]))
        return len(reply) > 0

    def set_auto_monitor_voice_memory(self, enable: bool) -> bool:
        """
        Sets the auto monitor function when transmitting a recorded voice memory.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self.utils.send_command(b"\x1a\x05\x01\x80", data=bytes([value]))
        return len(reply) > 0

    def set_repeat_interval_voice_memory(self, interval: int) -> bool:
        """
        Sets the repeat interval to transmit recorded voice audio.

        Args:
            interval (int): Repeat interval in seconds (1-15).

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
            ValueError: If the interval is not within the valid range (1 to 15)
        """
        if not (1 <= interval <= 15):
            raise ValueError("Interval must be between 1 and 15 seconds")
        reply = self.utils.send_command(b"\x1a\x05\x01\x81", data=bytes([interval]))
        return len(reply) > 0

    def set_qso_recorder_mode(self, tx_rx: bool) -> bool:
        """
        Sets the recording mode for QSO recorder (TX&RX or RX Only).

        Args:
            tx_rx (bool): True for TX & RX, False for RX only.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 0 if tx_rx else 1
        reply = self.utils.send_command(b"\x1a\x05\x01\x82", data=bytes([value]))
        return len(reply) > 0

    def set_qso_recorder_tx_audio(self, mic_audio: bool) -> bool:
        """
        Sets the recording TX audio source for QSO recorder (Microphone audio or TX monitor audio).

        Args:
            mic_audio (bool): True for Microphone audio, False for TX monitor audio.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 0 if mic_audio else 1
        reply = self.utils.send_command(b"\x1a\x05\x01\x83", data=bytes([value]))
        return len(reply) > 0

    def set_qso_recorder_squelch_relation(self, always_record: bool) -> bool:
        """
        Sets the squelch relation to recording RX audio for QSO recorder.

        Args:
            always_record (bool): True to always record, False for Squelch Auto.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 0 if always_record else 1
        reply = self.utils.send_command(b"\x1a\x05\x01\x84", data=bytes([value]))
        return len(reply) > 0

    def set_qso_record_file_split(self, enable: bool) -> bool:
        """
        Sets the QSO record file split function.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self.utils.send_command(b"\x1a\x05\x01\x85", data=bytes([value]))
        return len(reply) > 0

    def set_ptt_automatic_recording(self, enable: bool) -> bool:
        """
        Sets the PTT automatic recording function.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self.utils.send_command(b"\x1a\x05\x01\x86", data=bytes([value]))
        return len(reply) > 0

    def set_ptt_automatic_recording_rx_audio(self, rx_audio_time: int) -> bool:
        """
        Sets the RX audio recording status for PTT Automatic Recording function.

         Args:
             rx_audio_time (int): The RX audio recording time.
             0: OFF (records no RX audio)
             1: Records the RX audio just before 5 sec.
             2: Records the RX audio just before 10 sec.
             3: Records the RX audio just before 15 sec.

         Returns:
             bool: True if the command was successful, False otherwise.

         Raises:
            ValueError: If the value is not between 0 and 3
        """
        if not (0 <= rx_audio_time <= 3):
            raise ValueError("Value must be between 0 and 3")
        reply = self.utils.send_command(b"\x1a\x05\x01\x87", data=bytes([rx_audio_time]))
        return len(reply) > 0

    def set_qso_play_skip_time(self, skip_time: int) -> bool:
        """
         Sets the QSO Play skip time

         Args:
             skip_time (int): The skip time in seconds
                0: 3 sec.
                1: 5 sec.
                2: 10 sec.
                3: 30 sec.

        Returns:
            bool: True if the command was successful, False otherwise.

        Raises:
             ValueError: If the skip time is not within the valid range
        """
        if not (0 <= skip_time <= 3):
            raise ValueError("Value must be between 0 and 3")
        reply = self.utils.send_command(b"\x1a\x05\x01\x88", data=bytes([skip_time]))
        return len(reply) > 0

    def set_memory(
        self,
        memory_channel: int,
        frequency_hz: int,
        operating_mode: OperatingMode,
        rtx_filter: SelectedFilter,
        memory_name: str,
        data_mode: bool = False, # 0=OFF, 1=ON
        tone_type: ToneType = ToneType.OFF, #0=OFF, 1=TONE, 2=TSQL
        repeater_tone: float = 0,
        tone_squelch: float = 0,
        memory_setting: int = 0 #0=OFF, 1=☆1, 2=☆2, 3=☆3
    ):
        """
        Sets a memory channel with specified parameters on the IC-7300.
        
        Args:
            memory_channel (int): Memory channel number (1-99)
            frequency_hz (int): Frequency in Hz (10,000,000 - 74,800,000)
            operating_mode (OperatingMode): Operating mode enum value
            rtx_filter (SelectedFilter): Selected filter enum value 
            memory_name (str): Memory name (max 10 characters)
            data_mode (bool, optional): Data mode enabled. Defaults to False.
            tone_type (ToneType, optional): Tone type (OFF/TONE/TSQL). Defaults to ToneType.OFF.
            repeater_tone (float, optional): Repeater tone frequency. Defaults to 0.
            tone_squelch (float, optional): Tone squelch frequency. Defaults to 0.
            memory_setting (int, optional): Star memory setting (0=OFF,1=☆1,2=☆2,3=☆3). Defaults to 0.
        
        Returns:
            bool: True if command was successful, False otherwise
        
        Raises:
            ValueError: If memory channel is not 1-99
            ValueError: If frequency is not within valid range
            ValueError: If memory setting is invalid
            ValueError: If repeater tone is invalid
            ValueError: If tone squelch is invalid
            ValueError: If memory name is longer than 10 characters
            ValueError: If memory name contains invalid characters
        """

        if not 1 <= memory_channel <= 99:
            raise ValueError("Memory channel must be between 1 and 99")

        # Format memory channel
        memory_channel_str = f"{memory_channel:04d}" #aggiunge zeri iniziali

        # Validate frequency
        if not 10_000_000 <= frequency_hz <= 74_800_000:
            raise ValueError("Frequency must be between 10,000,000 and 74,800,000 Hz")

        # Convert frequency to bytes
        frequency_bytes = self.utils.encode_frequency(frequency_hz)

        # Validate memory setting
        if memory_setting not in [0, 1, 2, 3]:
            raise ValueError("Invalid star memory setting")

        # Convert operating mode and filter to bytes
        mode_byte = bytes([operating_mode.value])
        filter_byte = bytes([rtx_filter.value])

        # Handle data mode and tone type settings
        data_tone_byte = bytes([(int(data_mode) << 4) | (tone_type.value)]) # combina data mode e tone type

        # Validate repeater tone and tone squelch
        if repeater_tone not in self.valid_rpt_tones:
            raise ValueError("Invalid repeater tone")
        if tone_squelch not in self.valid_rpt_tones:
            raise ValueError("Invalid tone squelch")

        # Convert repeater and squelch tones to bytes        
        repeater_bytes = self.utils.encode_int_to_icom_bytes(int(repeater_tone * 10))
        repeater_bytes = bytes([0]) * (3 - len(repeater_bytes)) + repeater_bytes  # pad with leading zeros to 3 bytes

        squelch_bytes = self.utils.encode_int_to_icom_bytes(int(tone_squelch * 10))
        squelch_bytes = bytes([0]) * (3 - len(squelch_bytes)) + squelch_bytes  # pad with leading zeros to 3 bytes

        # Convert memory name to bytes
        if len(memory_name) > 10:
            raise ValueError("Memory name must be 10 characters or less")
        # Validate if all characters are in the allowed list
        for char in memory_name:
            if char not in self.allowed_memory_Name_characters:
                raise ValueError(f"Invalid character '{char}' in memory name")

        memory_name_bytes = b""
        for char in memory_name:
            memory_name_bytes += bytes([ord(char)]) #converte i caratteri in ascii

        # Pad the memory name with spaces if less than 10 characters
        memory_name_bytes += b' ' * (10 - len(memory_name))

        # Format the full command data
        command_data = (
            bytes([int(memory_channel_str[0:2])])
            + bytes([int(memory_channel_str[2:4])])
            + bytes([memory_setting]) # star
            + frequency_bytes
            + mode_byte
            + filter_byte
            + data_tone_byte
            + repeater_bytes
            + squelch_bytes
            + memory_name_bytes
        )

        # Send the command
        reply = self.utils.send_command(b'\x1a\x00', data=command_data)
        return len(reply) > 0

# Required attributes for plugin discovery
device_type = DeviceType.IC_7300
device_class = IC7300
