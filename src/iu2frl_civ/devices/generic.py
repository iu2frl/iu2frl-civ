"""
Custom class to communicate with ICOM devices using CI-V protocol
This class was built using the section 19 of the ICOM IC-7300 User Manual
"""

from typing import Tuple
import logging

from ..enums import OperatingMode, SelectedFilter, VFOOperation, ScanMode, DeviceType
from ..device_base import DeviceBase
from ..utils import Utils

logger = logging.getLogger("iu2frl-civ")


class GenericDevice(DeviceBase):
    """Create a CI-V object to interact with a generic the radio transceiver"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.utils = Utils(self._ser, self.transceiver_address, self.controller_address, self._read_attempts, debug=self.debug, fake=self.fake)

    def power_on(self) -> bytes:
        """
        Power on the radio transceiver

        Returns: the response from the transceiver
        """
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

    def set_operating_mode(self, mode: OperatingMode, filter: SelectedFilter = SelectedFilter.FIL1):
        """Sets the operating mode and filter."""
        # Command 0x06 with mode and filter data
        data = bytes([mode.value, filter.value])
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

    def set_display_font(self, round: bool = True):
        """Set the display font"""
        if round:
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

    def memory_clear(self):
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

    def set_data_mode(self, enable: bool, filter: int = 1) -> bool:
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
        if not (1 <= filter <= 3):
            raise ValueError("Filter must be between 1 and 3")

        value = 1 if enable else 0
        if not enable:
            filter = 0
        reply = self.utils.send_command(b"\x1a\x06", data=bytes([value, filter]))
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


# Required attributes for plugin discovery
device_type = DeviceType.Generic
device_class = GenericDevice
