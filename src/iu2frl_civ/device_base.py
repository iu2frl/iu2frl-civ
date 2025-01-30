"""
Custom class to communicate with ICOM devices using CI-V protocol
"""

from abc import ABC
import sys
import logging
from typing import Tuple
import serial

from .enums import OperatingMode, SelectedFilter, TuningStep, VFOOperation, ScanMode
from .fakeserial import FakeSerial


logger = logging.getLogger("iu2frl-civ")


class DeviceBase(ABC):
    """Create a CI-V object to interact with the radio transceiver"""

    _ser: serial.Serial  # Serial port object
    _read_attempts: int  # How many attempts before giving up the read process
    transceiver_address: bytes  # Hexadecimal address of the radio transceiver
    controller_address: bytes  # Hexadecimal address of the controller (this code)
    fake: bool  # If the device is fake or not (used for testing)
    debug: bool  # If debug mode is enabled

    def __init__(self, radio_address: str, port="/dev/ttyUSB0", baudrate: int = 19200, debug=False, controller_address="0xE0", timeout=1, attempts=3, fake=False):

        self._read_attempts = attempts
        # Validate the transceiver address
        if isinstance(radio_address, str) and str(radio_address).startswith("0x"):
            self.transceiver_address = bytes.fromhex(radio_address[2:])
        else:
            raise ValueError("Transceiver address must be in hexadecimal format (0x00)")
        # Validate the controller address
        if isinstance(controller_address, str) and str(controller_address).startswith("0x"):
            self.controller_address = bytes.fromhex(controller_address[2:])
        else:
            raise ValueError("Controller address must be in hexadecimal format (0x00)")
        # Open the serial port
        if not fake:
            self._ser = serial.Serial(port, baudrate, timeout=timeout, dsrdtr=False)
        else:
            self._ser = FakeSerial(self.transceiver_address, self.controller_address, baudrate, port)
        # Configure logging if needed
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            sys.tracebacklimit = 0
        # Print some information if debug is enabled
        self.fake = fake
        self.debug = debug
        logger.debug("Opened port: %s", self._ser.name)
        logger.debug("Baudrate: %s bps", self._ser.baudrate)

    def set_tuning_step(self, ts: TuningStep) -> bytes:
        """
        Set the tuning step on the radio transceiver

        Returns: the response from the transceiver
        """
        raise NotImplementedError()

    def split_off(self) -> bytes:
        """
        Set split mode off on the radio transceiver

        Returns: the response from the transceiver
        """
        raise NotImplementedError()

    def split_on(self) -> bytes:
        """
        Set split mode on on the radio transceiver

        Returns: the response from the transceiver
        """
        raise NotImplementedError()

    def power_on(self) -> bytes:
        """
        Power on the radio transceiver

        Returns: the response from the transceiver
        """
        raise NotImplementedError()

    def power_off(self) -> bytes:
        """
        Power off the radio transceiver

        Returns: the response from the transceiver
        """
        raise NotImplementedError()

    def read_transceiver_id(self) -> bytes:
        """
        Read the transceiver address

        Returns: the address of the transceiver, 0x00 if error
        """
        raise NotImplementedError()

    def read_operating_frequency(self) -> int:
        """
        Read the operating frequency

        Returns: the currently tuned frequency in Hz
        """
        raise NotImplementedError()

    def read_operating_mode(self) -> Tuple[str, str]:
        """
        Read the operating mode

        Returns: a tuple containing
            - the current mode
            - the current filter
        """
        raise NotImplementedError()

    def send_operating_frequency(self, frequency_hz: int) -> bool:
        """
        Send the operating frequency

        Returns: True if the frequency was properly sent
        """
        # Validate input
        raise NotImplementedError()

    def read_af_volume(self) -> int:
        """
        Read the AF volume

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the volume being set
        """
        raise NotImplementedError()

    def read_rf_gain(self) -> int:
        """
        Read the RF gain

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the RF gain being set
        """
        raise NotImplementedError()

    def read_squelch_level(self) -> int:
        """
        Read the squelch level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the squelch being set
        """
        raise NotImplementedError()

    def read_nr_level(self) -> int:
        """
        Read the NR level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the NR being set
        """
        raise NotImplementedError()

    def read_nb_level(self) -> float:
        """
        Read the NB level

        Raw values from CI-V
        0: min
        255: max

        Returns: The percentage of the NB being set
        """
        raise NotImplementedError()

    def read_smeter(self) -> int:
        """
        Read the S-meter value

        0: min
        255: max

        0000=S0, 0120=S9, 0241=S9+60dB

        TODO: test if properly working
        """
        raise NotImplementedError()

    def read_squelch_status(self):
        """
        Read noise or S-meter squelch status

        Returns: True if squelch is enabled (audio is silent)
        """
        raise NotImplementedError()

    def read_squelch_status2(self):
        """
        Read various squelch function’s status

        Returns: True if squelch is enabled (audio is silent)
        """
        raise NotImplementedError()

    def set_operating_mode(self, mode: OperatingMode, filter: SelectedFilter = SelectedFilter.FIL1):
        """Sets the operating mode and filter."""
        # Command 0x06 with mode and filter data
        raise NotImplementedError()

    def read_po_meter(self) -> float:
        """
        Read the PO meter level.
        0: 0%
        143: 50%
        213: 100%
        """
        raise NotImplementedError()

    def read_swr_meter(self) -> float:
        """
        Read the SWR meter level.
        0: SWR1.0,
        48: SWR1.5,
        80: SWR2.0,
        120: SWR3.0
        """
        raise NotImplementedError()

    def read_alc_meter(self) -> float:
        """
        Read the ALC meter level.
        0: Min
        120: Max
        """
        raise NotImplementedError()

    def read_comp_meter(self) -> float:
        """
        Read the COMP meter level.
        0: 0 dB,
        130: 15 dB,
        241: 30 dB
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def set_antenna_tuner(self, on: bool):
        """Turns the antenna tuner on or off."""
        raise NotImplementedError()

    def tune_antenna_tuner(self):
        """Starts the antenna tuner tuning process."""
        raise NotImplementedError()

    def stop_scan(self):
        """Stops the scan."""
        raise NotImplementedError()

    def send_cw_message(self, message: str):
        """Send a CW message. Limited to 30 characters"""
        raise NotImplementedError()

    def set_ip_plus_function(self, enable: bool) -> bool:
        """
        Sets the IP+ function setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_mf_band_attenuator(self, enable: bool) -> bool:
        """
        Sets the MF band attenuator setting.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_vfo_mode(self, vfo_mode: VFOOperation = VFOOperation.SELECT_VFO_A):
        """Sets the VFO mode."""
        raise NotImplementedError()

    def set_memory_mode(self, memory_channel: int):
        """Sets the memory mode, accepts values from 1 to 101"""
        raise NotImplementedError()

    # TODO: test all methods starting from this one

    def start_scan(self, scan_type: ScanMode = ScanMode.SELECT_DF_SPAN_100KHZ):
        """
        Starts scanning, different types available according to the sub command

        Note: this always returns some error
        """
        raise NotImplementedError()

    def set_mox(self, transmit: bool):
        """Turns the MOX on or off"""
        raise NotImplementedError()

    def set_scan_resume(self, on: bool):
        """Set scan resume on or off"""
        raise NotImplementedError()

    def set_scan_speed(self, high: bool):
        """Sets the scan speed"""
        raise NotImplementedError()

    def set_speech_synthesizer(self, speech_type: int = 1):
        """
        Set which speech data is used

        00 Speech all data with voice synthesizer
        01 Speech the operating frequency and S meter
        level by voice synthesizer
        02 Speech the operating mode by voice synthesizer
        """
        raise NotImplementedError()

    def set_speech_level(self, level: int):
        """Sets the speech level from 0 to 255"""
        raise NotImplementedError()

    def set_speech_language(self, english: bool = True):
        """Sets the speech language, True for english, false for japanese"""
        raise NotImplementedError()

    def set_speech_speed(self, high: bool = True):
        """Sets the speech speed"""
        raise NotImplementedError()

    def read_band_edge_frequencies(self):
        """
        Reads the band edge frequencies.
        This command requires further implementation due to its complex data structure
        """
        raise NotImplementedError()

    def memory_write(self):
        """Write to memory, implementation is very complex due to the large amount of data"""
        # Requires memory address, frequency, mode, name, etc.
        pass

    def memory_copy_to_vfo(self):
        """Copies memory to VFO"""
        raise NotImplementedError()

    def memory_clear(self):
        """Clears the memory"""
        raise NotImplementedError()

    def set_lcd_brightness(self, level: int):
        """Sets the LCD brightness, from 0 to 255"""
        raise NotImplementedError()

    def set_display_image_type(self, type: bool = True):
        """Set display image type"""
        raise NotImplementedError()

    def set_display_font(self, round: bool = True):
        """Set the display font"""
        raise NotImplementedError()

    def read_scope_waveform_data(self):
        """Reads the scope waveform data"""
        # command is complex and requires further investigation
        raise NotImplementedError()

    def set_scope_mode_fixed(self, fixed_mode: bool = False):
        """Sets the scope mode, True for Fixed, False for Center"""
        raise NotImplementedError()

    def set_scope_span(self, span_hz: int):
        """Sets the scope span in Hz"""
        # Valid values are 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000
        raise NotImplementedError()

    def set_scope_sweep_speed(self, speed: int):
        """Sets the sweep speed of the scope, 0: fast, 1: mid, 2: slow"""
        raise NotImplementedError()

    def set_scope_reference_level(self, level: float):
        """Sets the scope reference level, range is -20.0 to +20.0 dB in 0.5 dB steps"""
        raise NotImplementedError()

    def set_scope_fixed_edge_frequencies(self, edge_number: int, lower_frequency: int, higher_frequency: int):
        """Sets the fixed edge frequencies for the scope
        edge_number is 1, 2, or 3
        lower_frequency and higher_frequency are in Hz
        """
        raise NotImplementedError()

    def set_scope_vbw(self, wide: bool = True):
        """Sets the scope VBW (Video Band Width), True for wide, false for narrow"""
        raise NotImplementedError()

    def set_scope_waterfall_display(self, on: bool):
        """Turns the waterfall display on or off for the scope"""
        raise NotImplementedError()

    def set_memory_name(self, memory_channel: int, name: str):
        """
        Sets the memory name, max 10 characters
        memory_channel 1 to 99
        """
        raise NotImplementedError()

    def set_rtty_mark_frequency(self, frequency: int):
        """Sets the RTTY mark frequency, 0=1275 Hz, 1=1615 Hz, 2=2125 Hz"""
        raise NotImplementedError()

    def set_rtty_shift_width(self, width: int):
        """Sets the RTTY shift width, 0=170 Hz, 1=200 Hz, 2=425 Hz"""
        raise NotImplementedError()

    def set_rtty_keying_polarity(self, reverse: bool = False):
        """Sets the RTTY keying polarity, True for reverse, False for normal"""
        raise NotImplementedError()

    def set_rtty_decode_usos(self, on: bool = False):
        """Set RTTY decode USOS"""
        raise NotImplementedError()

    def set_rtty_decode_newline_code(self, crlf: bool = True):
        """Set RTTY decode new line code"""
        raise NotImplementedError()

    def set_rtty_tx_usos(self, on: bool = False):
        """Sets RTTY tx USOS"""
        raise NotImplementedError()

    def set_rtty_log(self, on: bool = False):
        """Set RTTY log function"""
        raise NotImplementedError()

    def set_rtty_log_file_format(self, html: bool = False):
        """Set the file format for the RTTY log, True for HTML, False for text"""
        raise NotImplementedError()

    def set_rtty_log_time_stamp(self, on: bool = False):
        """Set RTTY time stamp"""
        raise NotImplementedError()

    def set_rtty_log_time_stamp_local(self, local: bool = True):
        """Set the RTTY Log Time Stamp local or UTC"""
        raise NotImplementedError()

    def set_rtty_log_frequency_stamp(self, enable: bool) -> bool:
        """
        Sets the RTTY frequency stamp.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_auto_monitor_voice_memory(self, enable: bool) -> bool:
        """
        Sets the auto monitor function when transmitting a recorded voice memory.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def set_qso_recorder_mode(self, tx_rx: bool) -> bool:
        """
        Sets the recording mode for QSO recorder (TX&RX or RX Only).

        Args:
            tx_rx (bool): True for TX & RX, False for RX only.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_qso_recorder_tx_audio(self, mic_audio: bool) -> bool:
        """
        Sets the recording TX audio source for QSO recorder (Microphone audio or TX monitor audio).

        Args:
            mic_audio (bool): True for Microphone audio, False for TX monitor audio.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_qso_recorder_squelch_relation(self, always_record: bool) -> bool:
        """
        Sets the squelch relation to recording RX audio for QSO recorder.

        Args:
            always_record (bool): True to always record, False for Squelch Auto.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_qso_record_file_split(self, enable: bool) -> bool:
        """
        Sets the QSO record file split function.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

    def set_ptt_automatic_recording(self, enable: bool) -> bool:
        """
        Sets the PTT automatic recording function.

        Args:
            enable (bool): True to enable, False to disable.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()
