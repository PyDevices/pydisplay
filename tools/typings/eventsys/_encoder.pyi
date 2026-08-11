from ._device import Device as Device, register_device_class as register_device_class, types as types
from _typeshed import Incomplete

class EncoderDevice(Device):
    type: Incomplete
    responses: Incomplete
    def __init__(self, *args, **kwargs) -> None: ...
