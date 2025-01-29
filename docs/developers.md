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
device_type = DeviceType.NewDevice # As specified in the DeviceType enum
device_class = NewDevice # Name of the class defined above
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
generic = "iu2frl_civ.devices.generic"
ic7300 = "iu2frl_civ.devices.ic7300"
ic706_mkii = "iu2frl_civ.devices.ic706_mkii"
new_device = "iu2frl_civ.devices.new_device"  # New entry for the plugin
```

### 4. Create a test script

To test the new device, create a new test script in the `tests` folder. This script should import the new device and test its functionality. Testing should be done without building the package.

- You can copy the `fake.py` script as a template.
- If you have a real device, you can test the new device by running the test script and checking the output.
  - Make sure the `Fake` parameter is set to **False** in the `DeviceFactory.get_repository` method.
- Test the new device by running the test script and checking the output (without building the package yet).
  - Make sure to uninstall any version of the library that was previously installed using `pip uninstall iu2frl-civ`

### 5. Manual build procedure

Before sending the merge request, please try to build the package locally and make sure everything works

1. Move to the root directory of the project (where the `pyproject.toml` file is located)
2. Install the build tools: `python -m pip install --upgrade build`
3. Build the wheel package: `python -m build`
4. Install the package that was just built: `pip install ./dist/iu2frl_civ-0.0.0.tar.gz`
5. Test the package using the test code in the `tests/fake.py` file (the script will now use the newly built package)
6. Test the package using the code in the test file you just created
