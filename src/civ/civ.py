"""
Custom class to communicate with ICOM devices using CI-V protocol
"""

from typing import Tuple
from enum import Enum
import serial
import sys
import logging


logger = logging.getLogger(__name__)


class OperatingMode(Enum):
    """Operating mode of the radio transceiver"""

    LSB = 0
    USB = 1
    AM = 2
    CW = 3
    RTTY = 4
    FM = 5
    NFM = 6
    CWR = 7
    RTTYR = 8

class SelectedFilter(Enum):
    """The filter being selected on the transceiver"""

    FIL1 = 1
    FIL2 = 2
    FIL3 = 3

class SquelchStatus(Enum):
    """Status of the squelch of the transceiver"""

    CLOSED = 0
    OPEN = 1

class CivCommandException(BaseException):
    """
    This exception is generated when the CI-V response is NG 
    """
    message: str
    error_code: bytes

    def __init__(self, message, error_code):
        self.message = message
        self.error_code = error_code
    def __str__(self):
        return f"{self.message} (0x{self.error_code:02X})"

class CivTimeoutException(BaseException):
    """
    This exception is generated when the CI-V read gets over the timeout
    """
    pass

class Device:
    """Create a CI-V object to interact with the radio transceiver"""

    _ser: serial.Serial  # Serial port object
    _read_attempts: int # How many attempts before giving up the read process
    transceiver_address: str  # Hexadecimal address of the radio transceiver
    controller_address: str # Hexadecimal address of the controller (this code)

    def __init__(
        self,
        radio_address: str,
        port = "/dev/ttyUSB0",
        baudrate: int = 19200,
        debug = False,
        controller_address = "0xE0",
        timeout = 1,
        attempts = 3):
        self._ser = serial.Serial(port, baudrate, timeout = timeout)
        self._read_attempts = attempts
        # Validate the transceiver address
        if isinstance(radio_address, str) and str(radio_address).startswith("0x"):
            self.transceiver_address = radio_address[2:]
        else:
            raise ValueError("Transceiver address must be in hexadecimal format (0x00)")
        self.transceiver_address = radio_address
        # Validate the controller address
        if isinstance(controller_address, str) and str(controller_address).startswith("0x"):
            self.controller_address = controller_address[2:]
        else:
            raise ValueError("Controller address must be in hexadecimal format (0x00)")
        # Configure logging if needed
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            sys.tracebacklimit = 0
        # Print some information if debug is enabled
        logger.debug(f"Opened port: {self._ser.name}")
        logger.debug(f"Baudrate: {self._ser.baudrate} bps")

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
        logger.debug(f"Sending power-on command with {wakeup_preamble_count} wakeup preambles")
        return self._send_command(b"\x18\x01", preamble=b"\xfe" * wakeup_preamble_count)

    def power_off(self) -> bytes:
        """
        Power off the radio transceiver

        Returns: the response from the transceiver
        """
        return self._send_command(b"\x18\x00")

    def read_transceiver_id(self) -> int:
        """
        Read the transceiver address
        
        Returns: the address of the transceiver
        """
        reply = self._send_command(b"\x19\x00")
        if len(reply) > 0:
            value = reply[-2:-1]
            return int(value)
        return -1

    def read_operating_frequency(self) -> int:
        """
        Read the operating frequency
        
        Returns: the currently tuned frequency in Hz
        """
        try:
            reply = self._send_command(b"\x03")
            return self._decode_frequency(reply[5:10])
        except:
            return -1

    def read_operating_mode(self) -> Tuple[str, str]:
        """
        Read the operating mode
        
        Returns: a tuple containing
            - the current mode
            - the current filter
        """
        reply = self._send_command(b"\x04")
        if len(reply) == 8:
            mode = OperatingMode(int(reply[5:6].hex())).name
            fil = SelectedFilter(int(reply[6:7].hex())).name
            return [mode, fil]
        else:
            return ["ERR", "ERR"]

    def send_operating_frequency(self, frequency_hz: int) -> bool:
        """
        Send the operating frequency
        
        Returns: True if the frequency was properly sent
        """
        # Validate input
        if not (10_000 <= frequency_hz <= 74_000_000):  # IC-7300 frequency range in Hz
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")
        # Encode the frequency
        data = self._encode_frequency(frequency_hz)

        # Use the provided _send_command method to send the command
        reply = self._send_command(b"\x05", data=data)
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
        reply = self._send_command(b"\x14\x01")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_rf_gain(self) -> int:
        """
        Read the RF gain

        0: min
        255: max
        """
        reply = self._send_command(b"\x14\x02")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_squelch_level(self) -> int:
        """
        Read the squelch level

        0: min
        255: max
        """
        reply = self._send_command(b"\x14\x03")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_nr_level(self) -> int:
        """
        Read the NR level

        0: min
        255: max
        """
        reply = self._send_command(b"\x14\x06")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_nb_level(self) -> int:
        """
        Read the NB level

        0: min
        255: max
        """
        reply = self._send_command(b"\x14\x12")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_smeter(self) -> int:
        """
        Read the S-meter value

        0: min
        255: max

        0000=S0, 0120=S9, 0241=S9+60dB

        TODO: test if properly working
        """
        reply = self._send_command(b"\x15\x02")
        if len(reply) == 9:
            return self._bytes_to_int(reply[6], reply[7])
        return -1

    def read_squelch_status(self):
        """
        Read noise or S-meter squelch status

        TODO: test if properly working
        """
        reply = self._send_command(b"\x15\x01")
        return reply

    def read_squelch_status2(self):
        """
        Read various squelch function’s status

        TODO: test if properly working
        """
        reply = self._send_command(b"\x15\x05")
        return reply

    # TODO: test all methods starting from this one

    def set_operating_mode(
        self, mode: OperatingMode, filter: SelectedFilter = SelectedFilter.FIL1
    ):
        """Sets the operating mode and filter."""
        # Command 0x06 with mode and filter data
        data = bytes([mode.value, filter.value])
        self._send_command(b"\x06", data=data)

    def read_po_meter(self) -> int:
        """
        Read the PO meter level.
        0: 0%
        143: 50%
        213: 100%
        """
        reply = self._send_command(b"\x15\x11")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def read_swr_meter(self) -> int:
        """
        Read the SWR meter level.
        0: SWR1.0,
        48: SWR1.5,
        80: SWR2.0,
        120: SWR3.0
        """
        reply = self._send_command(b"\x15\x12")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def read_alc_meter(self) -> int:
        """
        Read the ALC meter level.
        0: Min
        120: Max
        """
        reply = self._send_command(b"\x15\x13")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def read_comp_meter(self) -> int:
        """
        Read the COMP meter level.
        0: 0 dB,
        130: 15 dB,
        241: 30 dB
        """
        reply = self._send_command(b"\x15\x14")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def read_vd_meter(self) -> int:
        """
        Read the Vd meter level.
        0: 0 V,
        13: 10 V,
        241: 16 V
        """
        reply = self._send_command(b"\x15\x15")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def read_id_meter(self) -> int:
        """
        Read the Id meter level.
        0: 0,
        97: 10,
        146: 15,
        241: 25
        """
        reply = self._send_command(b"\x15\x16")
        if len(reply) == 9:
            return self._bytes_to_int(reply[7], reply[6])
        return -1

    def set_antenna_tuner(self, on: bool):
        """Turns the antenna tuner on or off."""
        if on:
            self._send_command(b"\x1C\x01\x01")  # Turn tuner ON
        else:
            self._send_command(b"\x1C\x01\x00")  # Turn tuner OFF

    def tune_antenna_tuner(self):
        """Starts the antenna tuner tuning process."""
        self._send_command(b"\x1C\x01\x02")

    def start_scan(self, scan_type: int = 1):
        """Starts scanning, different types available according to the sub command"""
        # 01 Programmed/memory scan start
        # 02 Programmed scan start
        # 03 F scan start
        # 12 Fine programmed scan start
        # 13 Fine ∂F scan start
        # 22 Memory scan start
        # 23 Select memory scan start
        if scan_type in [1 - 3, 10 - 13]:
            self._send_command(b"\x0E", data=bytes([scan_type]))
        else:
            raise ValueError("Invalid scan type")

    def stop_scan(self):
        """Stops the scan."""
        self._send_command(b"\x0E\x00")

    def set_scan_resume(self, on: bool):
        """Set scan resume on or off"""
        if on:
            self._send_command(b"\x0E\xD3")
        else:
            self._send_command(b"\x0E\xD0")

    def set_scan_speed(self, high: bool):
        """Sets the scan speed"""
        if high:
            self._send_command(b"\x1A\x05\x01\x78\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x78\x00")

    def set_speech_synthesizer(self, speech_type: int = 1):
        """
        Set which speech data is used

        00 Speech all data with voice synthesizer
        01 Speech the operating frequency and S meter
        level by voice synthesizer
        02 Speech the operating mode by voice synthesizer
        """
        if speech_type in [1, 2]:
            self._send_command(b"\x13", data=bytes([speech_type]))
        else:
            raise ValueError("Invalid speech type")

    def set_speech_level(self, level: int):
        """Sets the speech level from 0 to 255"""
        if not (0 <= level <= 255):
            raise ValueError("Level must be between 0 and 255")
        level_bytes = level.to_bytes(2, "little")
        self._send_command(b"\x1A\x05\x00\x43", data=level_bytes)

    def set_speech_language(self, english: bool = True):
        """Sets the speech language, True for english, false for japanese"""
        if english:
            self._send_command(b"\x1A\x05\x00\x39\x00")
        else:
            self._send_command(b"\x1A\x05\x00\x39\x01")

    def set_speech_speed(self, high: bool = True):
        """Sets the speech speed"""
        if high:
            self._send_command(b"\x1A\x05\x00\x40\x01")
        else:
            self._send_command(b"\x1A\x05\x00\x40\x00")

    def read_band_edge_frequencies(self):
        """Reads the band edge frequencies. This command requires further implementation due to its complex data structure"""
        reply = self._send_command(b"\x02")
        return reply

    def set_vfo_mode(self, vfo_mode: int):
        """Sets the VFO mode."""
        # 00 Select VFO A
        # 01 Select VFO B
        # A0 Equalize VFO A and VFO B
        # B0 Exchange VFO A and VFO B
        if vfo_mode in [0, 1, 0xA0, 0xB0]:
            self._send_command(b"\x07", data=bytes([vfo_mode]))
        else:
            raise ValueError("Invalid vfo_mode")

    def set_memory_mode(self, memory_channel: int):
        """Sets the memory mode, accepts values from 1 to 101"""
        if not (1 <= memory_channel <= 101):
            raise ValueError("Memory channel must be between 1 and 101")
        # 0001 to 0109 Select the Memory channel *(0001=M-CH01, 0099=M-CH99)
        # 0100 Select program scan edge channel P1
        # 0101 Select program scan edge channel P2
        data = memory_channel.to_bytes(2, byteorder="big")

        self._send_command(b"\x08", data=data)

    def memory_write(self):
        """Write to memory, implementation is very complex due to the large amount of data"""
        # Requires memory address, frequency, mode, name, etc.
        pass

    def memory_copy_to_vfo(self):
        """Copies memory to VFO"""
        self._send_command(b"\x0A")

    def memory_clear(self):
        """Clears the memory"""
        self._send_command(b"\x0B")

    def send_cw_message(self, message: str):
        """Send a CW message. Limited to 30 characters"""
        if len(message) > 30:
            raise ValueError("Message must be 30 characters or less")
        # convert the string to bytes
        message_bytes = message.encode("ascii")
        self._send_command(b"\x17", data=message_bytes)

    def set_lcd_brightness(self, level: int):
        """Sets the LCD brightness, from 0 to 255"""
        if not (0 <= level <= 255):
            raise ValueError("Level must be between 0 and 255")
        level_bytes = level.to_bytes(2, "little")
        self._send_command(b"\x1A\x05\x00\x81", data=level_bytes)

    def set_display_image_type(self, type: bool = True):
        """Set display image type"""
        if type:
            self._send_command(b"\x1A\x05\x00\x82\x01")
        else:
            self._send_command(b"\x1A\x05\x00\x82\x00")

    def set_display_font(self, round: bool = True):
        """Set the display font"""
        if round:
            self._send_command(b"\x1A\x05\x00\x83\x01")
        else:
            self._send_command(b"\x1A\x05\x00\x83\x00")

    def read_scope_waveform_data(self):
        """Reads the scope waveform data"""
        # command is complex and requires further investigation
        reply = self._send_command(b"\x27\x00")
        return reply

    def set_scope_mode(self, fixed_mode: bool = False):
        """Sets the scope mode, True for Fixed, False for Center"""
        if fixed_mode:
            self._send_command(b"\x27\x14\x01")
        else:
            self._send_command(b"\x27\x14\x00")

    def set_scope_span(self, span_hz: int):
        """Sets the scope span in Hz"""
        # Valid values are 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000
        span_bytes = b""
        if span_hz == 2500:
            span_bytes = b"\x0a\x00\x00\x00"
        elif span_hz == 5000:
            span_bytes = b"\x14\x00\x00\x00"
        elif span_hz == 10000:
            span_bytes = b"\x27\x10\x00\x00"
        elif span_hz == 25000:
            span_bytes = b"\x27\x50\x00\x00"
        elif span_hz == 50000:
            span_bytes = b"\x4e\x20\x00\x00"
        elif span_hz == 100000:
            span_bytes = b"\x40\x42\x00\x00"
        elif span_hz == 250000:
            span_bytes = b"\x64\x74\x00\x00"
        elif span_hz == 500000:
            span_bytes = b"\x50\x9c\x00\x00"
        else:
            raise ValueError("Invalid scope span")
        self._send_command(b"\x27\x15", data=span_bytes)

    def set_scope_sweep_speed(self, speed: int):
        """Sets the sweep speed of the scope, 0: fast, 1: mid, 2: slow"""
        if speed in [1, 2]:
            self._send_command(b"\x27\x1A", data=bytes([speed]))
        else:
            raise ValueError("Invalid speed value, must be 0, 1, or 2")

    def set_scope_reference_level(self, level: float):
        """Sets the scope reference level, range is -20.0 to +20.0 dB in 0.5 dB steps"""
        if not (-20.0 <= level <= 20.0):
            raise ValueError("Level must be between -20.0 and +20.0 dB")
        if level % 0.5 != 0:
            raise ValueError("Level must be in 0.5 dB increments")

        # Convert the level to the required format
        level_int = int(level * 20)
        level_bytes = level_int.to_bytes(2, byteorder="little")

        if level >= 0:
            self._send_command(b"\x27\x19", data=b"\x00" + level_bytes)
        else:
            self._send_command(b"\x27\x19", data=b"\x01" + level_bytes)

    def set_scope_fixed_edge_frequencies(
        self, edge_number: int, lower_frequency: int, higher_frequency: int
    ):
        """Sets the fixed edge frequencies for the scope
        edge_number is 1, 2, or 3
        lower_frequency and higher_frequency are in Hz
        """
        if edge_number not in [1 - 3]:
            raise ValueError("Edge number must be 1, 2, or 3")

        if not (10_000 <= lower_frequency <= 74_000_000) or not (
            10_000 <= higher_frequency <= 74_000_000
        ):
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")

        data = b""
        lower_freq_bytes = self._encode_frequency(lower_frequency)
        higher_freq_bytes = self._encode_frequency(higher_frequency)

        data = bytes([edge_number]) + lower_freq_bytes + higher_freq_bytes

        self._send_command(b"\x27\x1E", data=data)

    def set_scope_vbw(self, wide: bool = True):
        """Sets the scope VBW (Video Band Width), True for wide, false for narrow"""
        if wide:
            self._send_command(b"\x27\x1D\x01")
        else:
            self._send_command(b"\x27\x1D\x00")

    def set_scope_waterfall_display(self, on: bool):
        """Turns the waterfall display on or off for the scope"""
        if on:
            self._send_command(b"\x1A\x05\x01\x07\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x07\x00")

    def set_memory_name(self, memory_channel: int, name: str):
        """Sets the memory name, max 10 characters
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

        data = (
            channel_bytes
            + b"\x00"
            + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + name_bytes
        )

        self._send_command(b"\x1A\x00", data=data)

    def set_rtty_mark_frequency(self, frequency: int):
        """Sets the RTTY mark frequency, 0=1275 Hz, 1=1615 Hz, 2=2125 Hz"""
        if frequency not in [1, 2]:
            raise ValueError("Invalid RTTY mark frequency")
        self._send_command(b"\x1A\x05\x00\x36", data=bytes([frequency]))

    def set_rtty_shift_width(self, width: int):
        """Sets the RTTY shift width, 0=170 Hz, 1=200 Hz, 2=425 Hz"""
        if width not in [1, 2]:
            raise ValueError("Invalid RTTY shift width")
        self._send_command(b"\x1A\x05\x00\x37", data=bytes([width]))

    def set_rtty_keying_polarity(self, reverse: bool = False):
        """Sets the RTTY keying polarity, True for reverse, False for normal"""
        if reverse:
            self._send_command(b"\x1A\x05\x00\x38\x01")
        else:
            self._send_command(b"\x1A\x05\x00\x38\x00")

    def set_rtty_decode_usos(self, on: bool = False):
        """Set RTTY decode USOS"""
        if on:
            self._send_command(b"\x1A\x05\x01\x68\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x68\x00")

    def set_rtty_decode_newline_code(self, crlf: bool = True):
        """Set RTTY decode new line code"""
        if crlf:
            self._send_command(b"\x1A\x05\x01\x69\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x69\x00")

    def set_rtty_tx_usos(self, on: bool = False):
        """Sets RTTY tx USOS"""
        if on:
            self._send_command(b"\x1A\x05\x01\x70\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x70\x00")

    def set_rtty_log(self, on: bool = False):
        """Set RTTY log function"""
        if on:
            self._send_command(b"\x1A\x05\x01\x73\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x73\x00")

    def set_rtty_log_file_format(self, html: bool = False):
        """Set the file format for the RTTY log, True for HTML, False for text"""
        if html:
            self._send_command(b"\x1A\x05\x01\x74\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x74\x00")

    def set_rtty_log_time_stamp(self, on: bool = False):
        """Set RTTY time stamp"""
        if on:
            self._send_command(b"\x1A\x05\x01\x75\x01")
        else:
            self._send_command(b"\x1A\x05\x01\x75\x00")

    def set_rtty_log_time_stamp_local(self, local: bool = True):
        """Set the RTTY Log Time Stamp local or UTC"""
        if local:
            self._send_command(b"\x1A\x05\x01\x76\x00")
        else:
            self._send_command(b"\x1A\x05\x01\x76\x01")

    def set_rtty_log_frequency_stamp(self, enable: bool) -> bool:
        """
        Sets the RTTY frequency stamp.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self._send_command(b"\x1a\x05\x01\x77", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x80", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x81", data=bytes([interval]))
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
        reply = self._send_command(b"\x1a\x05\x01\x82", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x83", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x84", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x85", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x86", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x05\x01\x87", data=bytes([rx_audio_time]))
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
        reply = self._send_command(b"\x1a\x05\x01\x88", data=bytes([skip_time]))
        return len(reply) > 0

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
        reply = self._send_command(b"\x1a\x05\x01\x89", data=bytes([depth - 1]))
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
        if not (1 <= width <= 100):
            raise ValueError("Width must be between 1 and 100")

        width_bytes = self._encode_2_bytes_value(width - 1)
        reply = self._send_command(b"\x1a\x05\x01\x90", data=width_bytes)
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
        reply = self._send_command(b"\x1a\x05\x01\x91", data=bytes([delay]))
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
        reply = self._send_command(b"\x1a\x05\x01\x92", data=bytes([voice_delay]))
        return len(reply) > 0

    def set_mf_band_attenuator(self, enable: bool) -> bool:
        """
        Sets the MF band attenuator setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self._send_command(b"\x1a\x05\x01\x93", data=bytes([value]))
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
        reply = self._send_command(b"\x1a\x06", data=bytes([value, filter]))
        return len(reply) > 0

    def set_ip_plus_function(self, enable: bool) -> bool:
        """
        Sets the IP+ function setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        value = 1 if enable else 0
        reply = self._send_command(b"\x1a\x07", data=bytes([value]))
        return len(reply) > 0

    # Private methods

    def _encode_2_bytes_value(self, value: int) -> bytes:
        """
        Encodes a integer value into two bytes (little endian)
        """
        return value.to_bytes(2, byteorder="little")

    def _send_command(self, command: bytes, data=b"", preamble=b"") -> bytes:
        """
        Send a command to the radio transceiver
        
        Returns: the response from the transceiver
        """
        if command is None or not isinstance(command, bytes):
            raise ValueError("Command must be a non-empty byte string")
        if len(command) not in [1, 2]:
            raise ValueError("Command must be 1 or 2 bytes long (command with an optional subcommand)")
        # The command is composed of:
        # - 0xFE 0xFE is the preamble
        # - the transceiver address
        # - the controller address
        # - 0xFD is the terminator
        command_string = (
            preamble
            + b"\xfe\xfe"
            + bytes([int(self.transceiver_address, 16)])
            + bytes([int(self.controller_address, 16)])
            + command
            + data
            + b"\xfd"
        )
        logger.debug(f"Sending command: {self._bytes_to_string(command_string)} (length: {len(command_string)})")
        # Send the command to the COM port
        self._ser.write(command_string)
        # Read the response from the transceiver
        reply = ""
        valid_reply = False
        for i in range(self._read_attempts):
            # Read data from the serial port until the terminator byte
            reply = self._ser.read_until(expected=b"\xfd")
            # Check if we received an echo message
            if reply == command_string:
                i -= 1 # Decrement cycles as it is just the echo back
                logger.debug(f"Received echo: {self._bytes_to_string(reply)} (length: {len(reply)})")
            # Check the response
            elif len(reply) > 2:
                target_controller = reply[2] # Target of the reply from the transceiver
                reply_code = reply[len(reply) - 2] # Command reply status code
                # Check if the response is for us
                if target_controller == int(self.controller_address):
                    logger.debug("Ignoring message which is not for us")
                    i -= 1 # Decrement cycles to ignore messages not for us
                # Check the return code
                elif reply_code == 251:  # 0xFB (good)
                    logger.debug("Reply status: OK (0xFB)")
                    valid_reply = True
                    break
                else:
                    logger.debug(f"Reply status: NG ({self._bytes_to_string(reply_code)}")
                    raise CivCommandException("Reply status: NG", reply_code)
            # Check if the respose was empty (timeout)
            else:
                logger.debug(f"Serial communication timeout ({i+1}/{self._read_attempts})")
        # Return the result to the user
        if not valid_reply:
            raise CivTimeoutException(f"Communication timeout occurred after {i+1} attempts")
        else:
            return reply

    def _decode_frequency(self, bcd_bytes) -> int:
        """Decode BCD-encoded frequency bytes to a frequency in Hz"""
        # Reverse the bytes for little-endian interpretation
        reversed_bcd = bcd_bytes[::-1]
        # Convert each byte to its two-digit BCD representation
        frequency_bcd = "".join(f"{byte:02X}" for byte in reversed_bcd)
        return int(frequency_bcd)  # Convert to integer (frequency in Hz)

    def _encode_frequency(self, frequency) -> bytes:
        """Convert the frequency to the CI-V representation"""
        frequency_str = str(frequency).rjust(10, "0")
        inverted_freq = frequency_str[::-1]
        hex_list = [f"0x{inverted_freq[1]}{inverted_freq[0]}"]
        hex_list.append(f"0x{inverted_freq[3]}{inverted_freq[2]}")
        hex_list.append(f"0x{inverted_freq[5]}{inverted_freq[4]}")
        hex_list.append(f"0x{inverted_freq[7]}{inverted_freq[6]}")
        hex_list.append(f"0x{inverted_freq[9]}{inverted_freq[8]}")
        return bytes([int(hx, 16) for hx in hex_list])

    def _bytes_to_string(self, bytes_array: bytearray) -> str:
        """Convert a byte array to a string"""
        return "0x" + " 0x".join(f"{byte:02X}" for byte in bytes_array)

    def _bytes_to_int(self, first_byte: bytes, second_byte: bytes) -> int:
        """Convert a byte array to an integer"""
        return (int(first_byte) * 100) + int(f"{second_byte:02X}")
