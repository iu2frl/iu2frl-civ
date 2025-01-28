from .enums import DeviceType
from typing import Dict, Type

from .device_base import DeviceBase

import sys
import os
import pkgutil
import importlib
from importlib.metadata import entry_points

import logging

logger = logging.getLogger(__name__)


class DeviceFactory:
    _device_mapping: Dict[DeviceType, Type[DeviceBase]] = {}

    @classmethod
    def _load_pip_plugins(cls, group: str) -> None:
        """
        Discover and load plugins using entry points defined in the package's metadata.

        Args:
            group (str): The entry point group name (e.g., "my_project.plugins").
        """
        for entry_point in entry_points().get(group, []):
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
                        logger.debug(f"Loaded plugin: {entry_point.name} ({device_type})")
                    else:
                        logger.error(f"Invalid plugin class in {entry_point.name}: {device_class}")
                else:
                    logger.error(f"Plugin {entry_point.name} is missing 'device_type' or 'device_class'")
            except Exception as e:
                logger.error(f"Failed to load plugin {entry_point.name}: {e}")
    
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
                        print(f"Loaded plugin: {module_name} ({device_type})")
                    else:
                        print(f"Invalid plugin class in {module_name}: {device_class}")
                else:
                    print(f"Module {module_name} is missing 'device_type' or 'device_class'")
            except Exception as e:
                print(f"Failed to load plugin {module_path}: {e}")

    def is_local(module_name: str) -> bool:
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
                print(f"Module '{module_name}' has no __file__ attribute")
                return False
        except ModuleNotFoundError:
            print(f"Module '{module_name}' not found.")
            return True

    @staticmethod
    def get_repository(
        device_type: DeviceType,
        radio_address: str,
        port = "/dev/ttyUSB0",
        baudrate: int = 19200,
        debug = False,
        controller_address = "0xE0",
        timeout = 1,
        attempts = 3,
        *args,
        **kwargs
        ) -> DeviceBase:

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
            *args,
            **kwargs,
        )
