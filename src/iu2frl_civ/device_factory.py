import os
import sys
import pkgutil
import importlib
from pathlib import Path
from importlib.metadata import entry_points
from typing import Dict, Type
import logging

from .enums import DeviceType
from .device_base import DeviceBase

logger = logging.getLogger("iu2frl-civ")


class DeviceFactory:
    """
    A factory class for creating and managing radio device instances.
    This class provides functionality to dynamically load and instantiate radio device plugins,
    either from pip-installed packages or local directories. It manages device types and their
    corresponding implementation classes through a mapping system.
    Class Attributes:
        _device_mapping (Dict[DeviceType, Type[DeviceBase]]): A dictionary mapping device types
            to their corresponding implementation classes.
    Methods:
        _load_pip_plugins(group: str) -> None:
            Discovers and loads plugins from pip-installed packages using entry points.
        _load_local_plugins(package: str) -> None:
            Discovers and loads plugins from local package directories.
        is_local(module_name: str) -> bool:
            Determines if a module is loaded from a local directory or pip-installed package.
        get_repository(
            port: str = "/dev/ttyUSB0",
            debug: bool = False,
            controller_address: str = "0xE0",
            timeout: int = 1,
            attempts: int = 3,
            Creates and returns a device instance based on the specified device type and parameters.
    Example:
        >>> factory = DeviceFactory()
        >>> device = factory.get_repository(
        ...     device_type=DeviceType.IC7300,
        ...     radio_address="0x94",
        ...     port="/dev/ttyUSB0"
        ... )
    """

    _device_mapping: Dict[DeviceType, Type[DeviceBase]] = {}

    @classmethod
    def _load_pip_plugins(cls, group: str) -> None:
        """
        Discover and load plugins using entry points defined in the package's metadata.

        Args:
            group (str): The entry point group name (e.g., "my_project.plugins").
        """
        for entry_point in entry_points().select(group=group):
            try:
                # Load the plugin
                plugin = entry_point.load()

                # Ensure the plugin provides the required attributes
                if hasattr(plugin, "device_type") and hasattr(plugin, "device_class"):
                    device_type = getattr(plugin, "device_type")
                    device_class = getattr(plugin, "device_class")

                    # Validate and register the plugin
                    if issubclass(device_class, DeviceBase):
                        cls._device_mapping[device_type] = device_class
                        logger.debug("Loaded plugin: %s (%s)", entry_point.name, device_type)
                    else:
                        logger.error("Invalid plugin class in %s: %s", entry_point.name, device_class)
                else:
                    logger.error("Plugin %s is missing 'device_type' or 'device_class'", entry_point.name)
            except Exception as e:
                logger.error("Failed to load plugin %s: %s", entry_point.name, e)

    @classmethod
    def _load_local_plugins(cls, package: str) -> None:
        """
        Discover and load plugins in the given package dynamically.

        Args:
            package (str): The package name (e.g., "my_project.devices").
        """
        # Convert package to a directory path
        package_path = package.replace(".", os.sep)

        # Ensure the package is in sys.path
        if package_path not in sys.path:
            sys.path.append(package_path)

        # Locate the package's directory
        package_dir = os.path.join(os.getcwd(), package_path)
        if not os.path.isdir(package_dir):
            logger.debug("Cannot find the devices folder in %s (are you using a Jupyter Notebook?), trying with a different approach", package_dir)
            package_dir = os.path.abspath(f"../{package_path}")
            if not os.path.isdir(package_dir):
                raise ValueError(f"Package path not found: {package_dir}")

        # Iterate over all modules in the package directory
        for finder, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
            module_path = f"{package}.{module_name}"
            try:
                # Dynamically import the module
                module = importlib.import_module(module_path)

                # Check for required attributes
                if hasattr(module, "device_type") and hasattr(module, "device_class"):
                    device_type = getattr(module, "device_type")
                    device_class = getattr(module, "device_class")

                    # Validate and register the plugin
                    if issubclass(device_class, DeviceBase):
                        cls._device_mapping[device_type] = device_class
                        logging.debug("Loaded plugin: %s (%s)", module_name, device_type)
                    else:
                        logging.debug("Invalid plugin class in %s: %s", module_name, device_class)
                else:
                    logging.error("Module %s is missing 'device_type' or 'device_class'", module_name)
            except Exception as e:
                logging.error("Failed to load plugin %s: %s", module_path, e)

    @classmethod
    def is_local(cls, module_name: str) -> bool:
        """
        Determine if a module is loaded from a local directory or a pip-installed package.

        Args:
            module_name (str): The name of the module to check.

        Returns:
            bool: True if the module is loaded from a local directory, False if from pip.
        """
        try:
            # Import the module dynamically
            module = importlib.import_module(module_name)

            # Get the path of the module
            module_path = getattr(module, "__file__", None)

            if module_path:
                # Check if the module is in a local directory (relative to the current project)
                if "site-packages" in module_path:
                    # If it's in site-packages, it's installed via pip
                    return False
                else:
                    # If it's not in site-packages, it's likely local
                    return True
            else:
                logger.debug(f"Module '{module_name}' has no __file__ attribute")
                return False
        except ModuleNotFoundError:
            logger.debug(f"Module '{module_name}' not found.")
            return True

    @staticmethod
    def get_repository(radio_address: str, device_type: DeviceType = DeviceType.Generic, port="/dev/ttyUSB0", baudrate: int = 19200, debug=False, controller_address="0xE0", timeout=1, attempts=3, fake=False, *args, **kwargs) -> DeviceBase:
        """Create and return a device repository instance based on the specified device type.
        Args:
            device_type (DeviceType): The type of device to create.
            radio_address (str): The radio address for the device.
            port (str, optional): The serial port to use. Defaults to "/dev/ttyUSB0".
            baudrate (int, optional): The serial baudrate. Defaults to 19200.
            debug (bool, optional): Enable debug mode. Defaults to False.
            controller_address (str, optional): Controller address. Defaults to "0xE0".
            timeout (int, optional): Communication timeout in seconds. Defaults to 1.
            attempts (int, optional): Number of retry attempts. Defaults to 3.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            DeviceBase: An instance of the requested device type.
        Raises:
            ValueError: If the specified device type is not supported.
        """

        if not DeviceFactory.is_local("iu2frl_civ.devices"):
            DeviceFactory._load_pip_plugins("iu2frl_civ.devices")
        else:
            DeviceFactory._load_local_plugins("src.iu2frl_civ.devices")

        if device_type not in DeviceFactory._device_mapping:
            raise ValueError(f"Unsupported device type: {device_type}")

        return DeviceFactory._device_mapping.get(device_type, DeviceBase)(
            radio_address=radio_address,
            port=port,
            baudrate=baudrate,
            debug=debug,
            controller_address=controller_address,
            timeout=timeout,
            attempts=attempts,
            fake=fake,
            *args,
            **kwargs,
        )
