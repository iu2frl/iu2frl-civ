# IU2FRL ICOM CI-V Library

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

### 4. Use the radio object

Once the device object is created, any supported method can be used, for example:

- Power on the transceiver: `device.power_on()`
- Get the current frequency: `device.read_operating_frequency()`

## Developer info

### Device Types

The `DeviceType` enum is a custom implementation for categorizing different types of transceivers.

It currently includes:

- `Generic`:  A generic device type (tested with IC-7300).
- `IC_706_MK2`: Represents the IC-706 MKII transceiver model.

### Adding a new device to the library

This process involves three main steps:

- **Update DeviceType Enum**: A new entry will be added to the `DeviceType` enum to reflect the newly added device.
- **Create a Device**: You will define a new class that will serve as your device plugin.
- **Update pyproject.toml**: Add an entry in the `pyproject.toml` to register the plugin.

#### 1. Add Device to the DeviceType Enum

To include your new device in the `DeviceType` enum, update the `iu2frl_civ.enums` file by adding a new member for the new device.

For example:

```python
from enum import Enum


class DeviceType(Enum):
    """Custom implementation for different transceiver"""
    Generic = 0
    IC_706_MK2 = 1
    NewDevice = 2
 
 ...
```

#### 2. Create a new Device class

A plugin is a class that represents a specific device. To create a new plugin:

- Create a new file in the `iu2frl_civ/devices/` directory.
- Define a new class that extends `iu2frl_civ.device_base` for your device and add the required attributes (`device_type`, `device_class`)

for example:

```python
# iu2frl_civ/devices/new_device.py

from ..device_base import DeviceBase  # Import the base class

class NewDevice(DeviceBase):
    """Representation of the new device."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.utils = Utils(
            self._ser,
            self.transceiver_address,
            self.controller_address,
            self._read_attempts
        )
    
    def read_operating_frequency(self) -> int:
        # Implement device-specific logic here
        pass


# Required attributes for plugin discovery
device_type = DeviceType.NewDevice
device_class = NewDevice
```

**Note**: If your device does not support certain functions (e.g., `power_on()`, `power_off()`, etc.), you do not need to implement them. The library will automatically raise a `NotImplementedError` when any unsupported method is called.

#### 3. Update pyproject.toml

> [!IMPORTANT]
> Do not edit the line with `version = "v0.0.0"` as this is automatically set by GitHub when building the new release

Next, you need to register your new device in the `pyproject.toml` file so that it can be discovered and loaded as a plugin.

Open your `pyproject.toml` file and add a new entry under the `[project.entry-points]` section to register your plugin.

for example:

```toml
[project.entry-points."iu2frl_civ.devices"]
ic706_mkii = "iu2frl_civ.devices.ic706_mkii"
generic = "iu2frl_civ.devices.generic"
new_device = "iu2frl_civ.devices.new_device"  # New entry for the plugin
```

### Manual build procedure

Before sending the merge request, please try to build the package locally and make sure everything works

1. Move to the root directory of the project (where the `pyproject.toml` file is located)
2. Install the build tools: `python -m pip install --upgrade build`
3. Build the wheel package: `python -m build`
4. Install the package that was just built: `pip install ./dist/iu2frl_civ-0.0.0.tar.gz`
5. Test the package using the test code in the `tests/main.py` file

## Sample code

Some sample commands are available in the `tests` folder.

- `ic7300.py`: A simple test script that demonstrates how to use the library to communicate with the IC-7300 transceiver.
- `fake.py`: A simple test script that fakes a connection to transceiver, used to validate builds.

## Project info

### Original project

This project was forked and then improved from: [siyka-au/pycom](https://github.com/siyka-au/pycom)

### Contributors

- [IU2FRL](https://github.com/iu2frl) as owner of the library and the initial implementation for IC-7300
- [IU1LCU](https://www.qrz.com/db/IU1LCU) for extensive testing on the IC-7300
- [ch3p4ll3](https://github.com/ch3p4ll3) for implementing the `DeviceFactory` code and testing on the IC-706 MKII
