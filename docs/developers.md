# IU2FRL ICOM CI-V Python Library

## Developers instructions

This chapter covers the steps required for developers to add new components to this library. Please review all the points before starting editing the library and submitting a MR.

> [!IMPORTANT]
> Do not rename the `tests` folder or the `fake.py` file, as those are used for testing the library.

### Device Types

The `DeviceType` enum is a custom implementation for categorizing different types of transceivers.

It currently includes:

- `Generic`:  A generic device type (built using the IC-7300 CI-V manual).
- `IC_706_MK2`: Represents the IC-706 MKII transceiver model.
- `IC_7300`: Represents the IC-7300 transceiver model.

### Adding a new device to the library

This process involves three main steps:

- **Update DeviceType Enum**: A new entry will be added to the `DeviceType` enum to reflect the newly added device.
- **Create a Device class**: You will define a new class that will serve as your device plugin.
- **Update package info**: Add an entry in the `pyproject.toml` to register the plugin.
- **Create a test script**: Create a new test script in the `tests` folder to test the new device.
- **Manual build procedure**: Before sending the merge request, please try to build the package locally and make sure everything works.

#### 1. Add Device to the DeviceType Enum

To include your new device in the `DeviceType` enum, update the `iu2frl_civ.enums` file by adding a new member for the new device.

For example:

```python
from enum import Enum


class DeviceType(Enum):
    """Custom implementation for different transceiver"""
    Generic = 0
    IC_706_MK2 = 1
    NewDevice = 99  # New device added here
 
 ...
```

#### 2. Create a new Device class

A plugin is a class that represents a specific device. To create a new plugin:

- Create a new file in the `iu2frl_civ/devices/` directory, for example: `iu2frl_civ/devices/newdevice.py`.
  - Naming convention: `devicename_revision.py`, for example: `ic706_mkii.py` (IC-706 with MKII revision) or `ic7300.py` (IC-7300 with no revision)
- Define a new class in the new python file that extends `iu2frl_civ.device_base` for your device and add the required attributes at the end of the file (`device_type`, `device_class`, see below)

The result should be something like this:

```python
"""
Custom class to communicate with ICOM devices using CI-V protocol
This class was built using the section XX of the ICOM AA-BCDEF User Manual
"""

from ..device_base import DeviceBase  # Import the base class

class NewDevice(DeviceBase):
    """Representation of the new device."""
    
    def __init__(self, *args, **kwargs):
        # Inherits the setup procedure from the prototype class
        super().__init__(*args, **kwargs)
        # Pass the parameters to the utils library to start the device
        self.utils = Utils(
            self._ser,
            self.transceiver_address,
            self.controller_address,
            self._read_attempts, 
            debug=self.debug, 
            fake=self.fake
        )

    # Implement device-specific methods here (see topic below)
    [...]

# Required attributes for plugin discovery
device_type = DeviceType.NewDevice # As specified in the DeviceType enum
device_class = NewDevice # Name of the class defined above
```

> [!TIP]
> If your device does not support certain functions (e.g., `power_on()`, `power_off()`, etc.), you do not need to implement them. The library will automatically raise a `NotImplementedError` when any unsupported method is called.

##### Adding methods to the new device

The CI-V documentation will report all the required command bytes to trigger a specific action, for example to start the tuning procedure on an IC-7300, the manual states:

| Cmd. | Sub cmd. | Data |            Description          |
|------|----------|------|---------------------------------|
| 0x1C |   0x01   | 0x00 | Send/read the antenna tuner OFF |
| 0x1C |   0x01   | 0x01 | Send/read the antenna tuner ON  |
| 0x1C |   0x02   | 0x02 | Send/read tuning procedure      |

We can see that the transceiver starts the tuning process when receiving the command bytes `0x1C, 0x01` and the data byte `0x02`, this translates to:

```python
[...]

class NewDevice(DeviceBase):
    """Representation of the new device."""

    [...]

    def tune_antenna_tuner(self) -> bool:
      """
      Starts the antenna tuner tuning process.
      
      Returns:
        True: if command was accepted from the transceiver

      Exceptions:
        CivTimeoutException: if transceiver does not reply within the specified time
      """
      return len(self.utils.send_command(b"\x1C\x01", b"\x02")) > 0

    [...]
```

#### 3. Update pyproject.toml

> [!IMPORTANT]
> Do not edit the line with `version = "v0.0.0"` as this is automatically set by GitHub when building the new release

Next, you need to register your new device in the `pyproject.toml` file so that it can be discovered and loaded as a plugin.

Open your `pyproject.toml` file and add a new entry under the `[project.entry-points]` section to register your plugin.

for example:

```toml
[project.entry-points."iu2frl_civ.devices"]
generic = "iu2frl_civ.devices.generic"
ic7300 = "iu2frl_civ.devices.ic7300"
ic706_mkii = "iu2frl_civ.devices.ic706_mkii"
newdevice = "iu2frl_civ.devices.newdevice"  # New device that was just added
```

### 4. Create a test script

To test the new device, create a new test script in the `tests` folder. This script should import the new device and test its functionality. Testing should be done without building the package.

> [!WARNING]
> Make sure to uninstall any version of the library that was previously installed using `pip uninstall iu2frl-civ` or the newly created device will be ignored

- Copy the `fake.py` script as a template and paste it as `newdevice.py` in the `tests` folder.
- Test the new device by running the `newdevice.py` test script and checking the output (without building the package yet).
  - If you have a real device, you can test the new device by running the test script and checking the output by setting the `Fake` parameter to **False** in the `DeviceFactory.get_repository` method.

### 5. Manual build procedure

Before sending the merge request, please try to build the package locally and make sure everything works

> [!WARNING]
> Make sure to uninstall any version of the library that was previously installed using `pip uninstall iu2frl-civ` or the newly created device will be ignored

1. Move to the root directory of the project (where the `pyproject.toml` file is located)
2. Install the build tools: `python -m pip install --upgrade build`
3. Build the wheel package: `python -m build`
4. Install the package that was just built: `pip install ./dist/iu2frl_civ-0.0.0.tar.gz`
5. Test the package using the test code in the `tests/fake.py` file (the script will now use the newly built package)
6. Test the package using the code in the test file you just created
