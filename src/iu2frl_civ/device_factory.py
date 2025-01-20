from .enums import DeviceType

from .devices.generic import GenericDevice
from .devices.ic706_mkii import IC706MKII
from .device_base import DeviceBase


mapping = {
    DeviceType.Generic: GenericDevice,
    DeviceType.IC_706_MK2: IC706MKII
}


class DeviceFactory:
    @staticmethod
    def get_repository(device_type: DeviceType = DeviceType.Generic) -> DeviceBase:
        return mapping.get(device_type, DeviceBase)
