# IU2FRL ICOM CI-V Library

Python library for communicating with iCOM radios using CI-V.

## Compatible devices

- IC-7300 (fw: 1.42)

## Usage

### 1. Installing dependencies

- Install the package using `pip install iu2frl-civ`

### 2. Importing the module

- Import the module using `from iu2frl_civ import iu2frl_civ`

### 3. Creating the device object

- Initialize the target device using `device = iu2frl_civ.Device("0x94", port="/dev/tty", debug=True)`

Where:

- `0x94` is the transceiver address

Then, additional arguments can be passed:

- `port = "/dev/ttyUSB0"`: communication port of the transceiver
- `baudrate: int = 19200`: baudrate of the device
- `debug = False`: useful to troubleshoot communication issues
- `controller_address = "0xE0"`: address of the controller (this library)
- `timeout = 1`: serial port communication timeout in seconds
- `attempts = 3`: how many attempts to perform in case of timeout or errors

### 4. Use the radio object

Once the device object is created, any supported method can be used, for example:

- Power on the transceiver: `device.power_on()`
- Get the current frequency: `device.read_operating_frequency()`

## Some test code

Some sample commands are available in the `tests/main.py` file

## Original project

This project was forked and then improved from: [siyka-au/pycom](https://github.com/siyka-au/pycom)
