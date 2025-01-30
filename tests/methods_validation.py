"""
This code is an automated testing mechanism to validate the syntax of all
device types. It is not meant to be used as an example of the library.
"""

import sys
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

try:
    # Import the library installed using pip
    from iu2frl_civ.device_factory import DeviceFactory
    from iu2frl_civ.enums import DeviceType

    print("Calling test using installed library")
except ImportError:
    # Use this block if working with source code
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from src.iu2frl_civ.device_factory import DeviceFactory
    from src.iu2frl_civ.enums import DeviceType

    print("Calling test using local library files")


# Main program
def main() -> int:
    """
    Test all the available devices using the 'fake' mode
    """

    failed_tests = 0
    logging.info("Connecting to the transceiver")

    # Loop through all device types
    for device_type in DeviceType:
        logging.info("Testing device type: %s", device_type.name)
        try:
            # Device initialization
            radio = DeviceFactory.get_repository(radio_address="0x00", device_type=device_type, port="COM10", debug=False, fake=True)

            logging.info("Connected to the fake transceiver at %s with baudrate %sbps", radio._ser.port, radio._ser.baudrate)
            logging.info("Testing all radio methods")

            # Test all methods for this device type
            for method_name in dir(radio):
                if not method_name.startswith("_"):  # Skip private methods
                    method = getattr(radio, method_name)
                    if callable(method):
                        try:
                            logging.info("Testing %s...", method_name)
                            if method.__code__.co_argcount == 1:  # Only self parameter
                                method()
                        except Exception as e:
                            if isinstance(e, NotImplementedError):
                                logging.warning("%s -> Cannot execute %s: not implemented", device_type.name, method_name)
                            else:
                                logging.error("%s -> Error executing %s: %s", device_type.name, method_name, e)
                                failed_tests += 1

        except Exception as e:
            logging.critical("Error initializing device type %s: %s", device_type.name, e)

    logging.info("Device testing complete")
    return failed_tests


if __name__ == "__main__":
    print("Starting methods testing using fake mode\n\n")

    failures = main()

    if failures > 0:
        print(f"\n\n{failures} tests were failed")
        sys.exit(1)
    else:
        print("\n\nAll tests were passed")
        sys.exit(0)
