# IU2FRL ICOM CI-V Library

Python library for communicating with iCOM radios using CI-V.

## Compatible devices

- IC-7300 (fw: 1.42)
- IC-706 MKII

## Usage

### 1. Installing dependencies

- Install the package using `pip install iu2frl-civ`

### 2. Importing the module

- Import the module using `rom src.iu2frl_civ.device_factory import DeviceFactory`

### 3. Creating the device object

- Initialize the target device using `device = DeviceFactory.get_repository(DeviceType.Generic, "0x94", port="/dev/tty", debug=True)`

Where:

- `DeviceType.Generic` is the type of device you want to control
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

## Device Types
The `DeviceType` enum is a custom implementation for categorizing different types of transceivers.

It currently includes:

- `Generic`: A generic device type.
- `IC_706_MK2`: Represents the IC-706 MKII transceiver model.

### Device Creation
This process involves three main steps:

- **Update DeviceType Enum**: A new entry will be added to the `DeviceType` enum to reflect the newly added device.
- **Create a Device**: You will define a new class that will serve as your device plugin.
- **Update pyproject.toml**: Add an entry in the `pyproject.toml` to register the plugin.

#### 1. Add Device to the DeviceType Enum
To include your new device in the `DeviceType` enum, update the `iu2frl_civ.enums` file by adding a new member for the new device.

ex:
```python
from enum import Enum


class DeviceType(Enum):
    """Custom implementation for different transceiver"""
    Generic = 0
    IC_706_MK2 = 1
    NewDevice = 2
 
 ...
```

#### 2. Create a Device
A plugin is a class that represents a specific device. To create a new plugin:

- Create a new file in the `iu2frl_civ/devices/` directory.
- Define a new class that extends `iu2frl_civ.device_base` for your device and add the required attributes (`device_type`, `device_class`)

ex:
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

Note: If your device does not support certain functions (e.g., `power_on()`, `power_off()`, etc.), you do not need to implement them. The library will automatically raise a `NotImplementedError` when any unsupported method is called.

#### 3. Update pyproject.toml
Next, you need to register your new device in the `pyproject.toml` file so that it can be discovered and loaded as a plugin.

Open your `pyproject.toml` file and add a new entry under the `[project.entry-points]` section to register your plugin.

ex:
```toml
[project.entry-points."iu2frl_civ.devices"]
ic706_mkii = "iu2frl_civ.devices.ic706_mkii"
generic = "iu2frl_civ.devices.generic"
new_device = "iu2frl_civ.devices.new_device"  # New entry for the plugin
```

## Some test code

Some sample commands are available in the `tests/main.py` file

## Original project

This project was forked and then improved from: [siyka-au/pycom](https://github.com/siyka-au/pycom)
