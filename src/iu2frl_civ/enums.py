from enum import Enum


class DeviceType(Enum):
    """Custom implementation for different transceiver"""

    Generic = 0
    IC_706_MK2 = 1
    IC_7300 = 2


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


class ScanMode(Enum):
    """Scan mode of the transceiver"""

    STOP = b"\x00"  # Stop scan
    MEMORY = b"\x01"  # Programmed/memory scan start
    PROGRAMMED = b"\x02"  # Programmed scan start
    F = b"\x03"  # F scan start
    FINE_PROGRAMMED = b"\x12"  # Fine programmed scan start
    FINE_FREQUENCY = b"\x13"  # Fine ∂F scan start
    MEMORY_SCAN = b"\x22"  # Memory scan start
    SELECT_MEMORY = b"\x23"  # Select memory scan start
    SELECT_DF_SPAN_5KHZ = b"\xA1"  # Select ∂F scan span ±5 kHz
    SELECT_DF_SPAN_10KHZ = b"\xA2"  # Select ∂F scan span ±10 kHz
    SELECT_DF_SPAN_20KHZ = b"\xA3"  # Select ∂F scan span ±20 kHz
    SELECT_DF_SPAN_50KHZ = b"\xA4"  # Select ∂F scan span ±50 kHz
    SELECT_DF_SPAN_100KHZ = b"\xA5"  # Select ∂F scan span ±100 kHz
    SELECT_DF_SPAN_500KHZ = b"\xA6"  # Select ∂F scan span ±500 kHz
    SELECT_DF_SPAN_1MHZ = b"\xA7"  # Select ∂F scan span ±1 MHz
    SET_NON_SELECT_CHANNEL = b"\xB0"  # Set as non-select channel
    SET_SELECT_CHANNEL = b"\xB1"  # Set as select channel
    SET_SELECT_MEMORY_SCAN = b"\xB2"  # Set for select memory scan
    SCAN_RESUME_OFF = b"\xD0"  # Set Scan resume OFF
    SCAN_RESUME_ON = b"\xD3"  # Set Scan resume ON


class VFOOperation(Enum):
    """VFO operation commands"""

    SELECT_VFO_A = b"\x00"  # Select VFO A
    SELECT_VFO_B = b"\x01"  # Select VFO B
    EQUALIZE_VFO_A_B = b"\xA0"  # Equalize VFO A and VFO B
    EXCHANGE_VFO_A_B = b"\xB0"  # Exchange VFO A and VFO B


class TuningStep(Enum):
    OFF = b"\x00"  # default: 10 Hz
    ON = b"\x01"  # 100Hz
    TS_1KHz = b"\x02"
    TS_5KHz = b"\x03"
    TS_9KHz = b"\x04"
    TS_10KHz = b"\x05"
    TS_12_5KHz = b"\x06"
    TS_20KHz = b"\x07"
    TS_25KHz = b"\x08"
    TS_100KHz = b"\x09"
