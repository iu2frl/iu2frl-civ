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

### 4. Use the radio object

Once the device object is created, any supported method can be used, for example:

- Power on the transceiver: `device.power_on()`
- Get the current frequency: `device.read_operating_frequency()`

## Some test code

Some sample commands are available in the `tests/main.py` file

## Original project

This project was forked and then improved from: [siyka-au/pycom](https://github.com/siyka-au/pycom)
