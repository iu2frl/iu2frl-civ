"""IC-821H transceiver CI-V commands and responses"""

from ..device_base import DeviceBase
from ..utils import Utils
from ..enums import OperatingMode, VFOOperation, TuningStep, DeviceType


class IC821H(DeviceBase):
    """Create a CI-V object to interact with an IC-821H transceiver"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix for digirig
        self._ser.rts = False
        self._ser.dtr = False

        self.utils = Utils(self._ser, self.transceiver_address, self.controller_address, self._read_attempts)

    # Tested methods

    def send_operating_frequency(self, frequency_hz: int | float) -> bool:
        """
        Send the operating frequency
        
        Please note: 
        - The IC-821H supports frequencies between 136 MHz and 174 MHz or between 420 MHz and 460 MHz.
        - No feedback is expected from the transceiver after sending the command.

        Returns: True if the frequency was properly sent
        """
        if isinstance(frequency_hz, float):  # fix for using scientific notation ex: 14.074e6
            frequency_hz = int(frequency_hz)

        # Validate input
        if not (136_000_000 <= frequency_hz <= 174_000_000 or 420_000_000 <= frequency_hz <= 460_000_000):  # IC-821H frequency range in Hz
            raise ValueError("Frequency must be between 136 MHz and 174 MHz or between 420 MHz and 460 MHz")
        # Encode the frequency
        data = self.utils.encode_frequency(frequency_hz)

        # Use the provided _send_command method to send the command
        self.utils.send_command(b"\x05", data=data, no_reply=True)

    def read_operating_frequency(self) -> int:
        """
        Read the operating frequency
        
        Raises:
            NotImplementedError: This method is not supported by the IC-821H transceiver.
        """

        self.utils.logger.error("This method is not supported by the IC-821H transceiver.")

    def set_operating_mode(self, mode: OperatingMode) -> None:
        """
        Sets the operating mode and filter.
        
        Args:
            mode (OperatingMode): The operating mode to set. Supported modes are: LSB, USB, CW, CWR, FM.
        Raises:
            ValueError: If the provided mode is not a valid OperatingMode.
        """
        # Command 0x06 with mode data
        if mode is OperatingMode.LSB:
            data = b"\x00"
        elif mode is OperatingMode.USB:
            data = b"\x01"
        elif mode is OperatingMode.CW:
            data = b"\x03\x01"
        elif mode is OperatingMode.CWR:
            data = b"\x03\x02"
        elif mode is OperatingMode.FM:
            data = b"\x05\x01"
        else:
            raise ValueError(f"Unsupported mode: {mode.name}. Supported modes are: LSB, USB, CW, CWR, FM.")
        # Send the command with the data
        self.utils.send_command(b"\x06", data=data, no_reply=True)

    def set_vfo_mode(self, vfo_mode: VFOOperation = VFOOperation.SELECT_VFO_A) -> None:
        """
        Sets the VFO mode.
        Args:
            vfo_mode (VFOOperation): The VFO operation to set. Defaults to VFOOperation.SELECT_VFO_A.
        Raises:
            ValueError: If the provided vfo_mode is not a valid VFOOperation.
        """

        if vfo_mode in VFOOperation:
            if vfo_mode is VFOOperation.VFO_MODE:
                self.utils.send_command(b"\x07", no_reply=True)
            else:
                # Send the command with the specific VFO operation
                self.utils.send_command(b"\x07", data=vfo_mode.value, no_reply=True)
        else:
            raise ValueError("Invalid vfo_mode")

    def set_memory_mode(self, memory_channel: int | str) -> None:
        """
        Sets the memory mode, accepts values from 1 to 80 or special strings "P1", "P2", "CALL".
        
        Warning: do not loop trough channels too fast, the transceiver may not respond correctly.
        
        Args:
            memory_channel (int | str): Memory channel number (1-80) or special strings "P1", "P2", "CALL".
        """
        if isinstance(memory_channel, int):
            # 0001 to 0109 Select the Memory channel *(0001=M-CH01, 0099=M-CH99)
            if not (1 <= memory_channel <= 80):
                raise ValueError("Memory channel must be between 1 and 80")
        elif isinstance(memory_channel, str):
            # 0100 Select program scan edge channel P1
            # 0101 Select program scan edge channel P2
            # 0102 Select channel CALL
            if memory_channel == "P1":
                memory_channel = 100
            elif memory_channel == "P2":
                memory_channel = 101
            elif memory_channel == "CALL":
                memory_channel = 102

        if 0 < memory_channel < 100:
            hex_list = ["0x00"]
        else:
            hex_list = ["0x01"]

        number_as_string = str(memory_channel).rjust(3, "0")
        hex_list.append(f"0x{number_as_string[1]}{number_as_string[2]}")
        self.utils.send_command(b"\x08", no_reply=True)
        self.utils.send_command(b"\x08", data=bytes([int(hx, 16) for hx in hex_list]), no_reply=True)

    def stop_scan(self) -> None:
        """Stops the scan."""
        self.utils.send_command(b"\x0E\x00", no_reply=True)

    def start_scan(self) -> None:
        """
        Starts scanning, different types available according to the sub command
        """
        self.utils.send_command(b"\x0E\x01", no_reply=True)

    def memory_copy_to_vfo(self):
        """Copies memory to VFO"""
        self.utils.send_command(b"\x0A", no_reply=True)

    def clear_current_memory(self):
        """Clears the memory"""
        self.utils.send_command(b"\x0B", no_reply=True)

    def memory_write(self):
        """Writes the current VFO to memory"""
        self.utils.send_command(b"\x09", no_reply=True)

    def set_duplex_mode(self, duplex: int) -> None:
        """
        Sets the duplex mode.

        Args:
            duplex (int): Duplex mode, 0 for off, -1 for DUP-, 1 for DUP+.
        Raises:
            ValueError: If the duplex value is not 0 or 1.
        """
        if duplex not in (-1, 0, 1):
            raise ValueError("Duplex must be -1 (DUP-), 0 (off), or 1 (DUP+).")

        if duplex == -1:
            self.utils.send_command(b"\x0F", data=b"\x11", no_reply=True)
        elif duplex == -1:
            self.utils.send_command(b"\x0F", data=b"\x11", no_reply=True)
        else:
            self.utils.send_command(b"\x0F", data=b"\x10", no_reply=True)

    # Untested methods

    def split_off(self) -> None:
        """
        Disables split mode.
        """

        self.utils.logger.warning("The `split_off` method is not tested yet, please report any issues.")
        self.utils.send_command(b"\x0F", b"\x00", no_reply=True)

    def split_on(self) -> None:
        """
        Enables split mode.
        """

        self.utils.logger.warning("The `split_on` method is not tested yet, please report any issues.")
        self.utils.send_command(b"\x0F", b"\x01", no_reply=True)

    def offset_read(self) -> int:
        """
        Reads the offset frequency.

        Returns:
            int: The offset frequency in Hz.
        """

        self.utils.logger.warning("The `offset_read` method is not tested yet, please report any issues.")
        response = self.utils.send_command(b"\x0C", no_reply=False)
        return self.utils.decode_frequency(response[5:7])

    def offset_write(self, frequency_hz: int | float):
        """
        Writes the offset frequency.

        Args:
            frequency_hz (int | float): The offset frequency in Hz.

        Raises:
            ValueError: If the frequency is not within the valid range.
        """

        if isinstance(frequency_hz, float):
            frequency_hz = int(frequency_hz)

        self.utils.logger.warning("The `offset_write` method is not tested yet, use with caution.")
        data = self.utils.encode_frequency(frequency_hz)
        response = self.utils.send_command(b"\x0D", data=data, no_reply=True)


# Required attributes for plugin discovery
device_type = DeviceType.IC_821_H
device_class = IC821H
