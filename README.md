# IU2FRL ICOM CI-V Python Library

Python library for communicating with iCOM radios using CI-V.

## Compatible devices

Theorically speaking, all ICOM devices implementing the CI-V protocol should be compatible, in particular, the following devices were tested:

- IC-7300 (fw: 1.42)
- IC-706 MKII

## Usage

### 1. Installing dependencies

- Install the package using `pip install iu2frl-civ`

### 2. Importing the module

- Import the module using `from iu2frl_civ.device_factory import DeviceFactory`

### 3. Creating the device object

- Initialize the target device using `radio = DeviceFactory.get_repository(radio_address="0x94", device_type=DeviceType.Generic, port="COM10", debug=True)`

> [!TIP]
> Usage of named arguments (like `radio_address="0x94"`) over positional arguments is **highly recommended** as it provides better support for future releases or library code reviews

Where:

- `device_type = DeviceType.Generic` is the type of device you want to control
- `radio_address = 0x94` is the transceiver address

Then, additional arguments can be passed:

- `port = "/dev/ttyUSB0"`: communication port of the transceiver
- `baudrate: int = 19200`: baudrate of the device
- `debug = False`: useful to troubleshoot communication issues
- `controller_address = "0xE0"`: address of the controller (this library)
- `timeout = 1`: serial port communication timeout in seconds
- `attempts = 3`: how many attempts to perform in case of timeout or errors
- `fake = False`: if set to True, the library will use a fake connection to the transceiver (serial commands will be printed to the console and not sent to any port)

### 4. Use the radio object

Once the device object is created, any supported method can be used, for example:

- Power on the transceiver: `device.power_on()`
- Get the current frequency: `device.read_operating_frequency()`

### 5. Check the command output

Some commands have an expected value to be returned (like the `device.read_operating_frequency()`), most returns a boolean value, while other returns nothing (`void`). If the device does not support a command (or it was not yet implemented), or if some error occurred, an exception is thrown:

- `NotImplementedError`: the current device does not implement this feature yet
- `CivCommandException`: something went wrong in the data exchange between the transceiver and the library (probably due to device misconfiguration, faulty cables, etc)
- `CivTimeoutException`: the communication timed out (something wrong with wiring or connection parameters like port or baudrate)

## Sample code

> [!IMPORTANT]
> Do not rename the `tests` folder or the `fake_generic.py` file, as those are used for testing the library.

Some sample commands are available in the `tests` folder.

- `ic7300.py`: A simple test script that demonstrates how to use the library to communicate with the IC-7300 transceiver.
- `ic706_mkii.py`: A simple test script that demonstrates how to use the library to communicate with the IC-706 MKII transceiver.
- `fake_generic.py`: A simple test script that fakes a connection to transceiver, used to validate builds.

## Developer info

Any help is welcome to either add more devices or improve existing ones, please see the developers section, accessible via [relative link](./CONTRIBUTING.md) or [GitHub Link](https://github.com/iu2frl/iu2frl-civ/blob/main/CONTRIBUTING.md)

## Project info

### Original project

This project was forked and then improved from: [siyka-au/pycom](https://github.com/siyka-au/pycom)

### Contributors

- [IU2FRL](https://github.com/iu2frl) as owner of the library and the initial implementation for IC-7300
- [IU1LCU](https://www.qrz.com/db/IU1LCU) for extensive testing on the IC-7300
- [ch3p4ll3](https://github.com/ch3p4ll3) for implementing the `DeviceFactory` code and testing on the IC-706 MKII
