# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
`eventsys.devices`
====================================================

Device classes for eventsys's Event System.  May also be used
with other applications.  Devices are objects that poll for events
and return them.  They can be subscribed to and unsubscribed from
to receive events.

Devices can be created with Broker.create_device() or by calling the
constructor of the device class directly.  Devices can be
subscribed to with .subscribe() and unsubscribed from with
.unsubscribe().  Devices can be polled for events with .poll().
Devices can be registered with a broker device with .register_device()
and unregistered with .unregister_device().  Devices can be chained
together by setting the .broker property of a device to another device.

Devices can be created with the following types:
- types.BROKER: A device that polls multiple devices.
- types.QUEUE: A device that returns multiple types of events.
- types.TOUCH: A device that returns MOUSEBUTTONDOWN when touched,
    MOUSEMOTION when moved and MOUSEBUTTONUP when released.
- types.ENCODER: A device that returns MOUSEWHEEL events when turned,
    MOUSEBUTTONDOWN when pressed.
- types.KEYPAD: A device that returns KEYDOWN and KEYUP events when
    keys are pressed or released.
- types.JOYSTICK: A device that returns joystick events (not implemented).
"""

from sys import exit

from micropython import const

from . import events

_DEFAULT_TOUCH_ROTATION_TABLE = (0b000, 0b101, 0b110, 0b011)

SWAP_XY = const(0b001)
REVERSE_X = const(0b010)
REVERSE_Y = const(0b100)


def custom_type(type_name, responses):
    """
    Create a new device type with a list of responses.

    Args:
        type_name (str): The name of the device type.
        responses (list[int]): A list of event types that the device can return.

    Returns:
        (Device): The newly created device type.

    Raises:
        ValueError: If `type_name` is not a string, `responses` is not a list, or any response is not an integer.
        ValueError: If a device type with the same name already exists in the `types` class.
        ValueError: If a device class with the same name already exists.

    Example:
        To create a custom device type and device class:

        ```python
        from eventsys import devices, events

        MyDevice = devices.custom_type("MINE", [events.KEYDOWN, events.KEYUP])
        ```
    """
    if not isinstance(type_name, str):
        raise ValueError("type_name must be a string")
    type_name = type_name.strip().upper()
    if not isinstance(responses, list):
        raise ValueError("responses must be a list")
    if not all(isinstance(event, int) for event in responses):
        raise ValueError("all responses must be integers")

    if hasattr(types, type_name):
        raise ValueError(f"Device type {type_name} already exists in types class.")
    class_name = type_name[0].upper() + type_name[1:].lower() + "Device"
    if class_name in [cls.__name__ for cls in _mapping.values()]:
        raise ValueError(f"Device class {class_name} already exists.")

    value = len(_mapping)
    setattr(types, type_name, value)
    NewClass = type(class_name, (Device,), {"type": value, "responses": responses})
    _mapping[value] = NewClass
    return NewClass


class types:
    """
    Device types for the Event System.
    """

    UNDEFINED = const(-1)
    BROKER = const(0x00)
    QUEUE = const(0x01)
    TOUCH = const(0x02)
    ENCODER = const(0x03)
    KEYPAD = const(0x04)
    JOYSTICK = const(0x05)


class Device:
    """
    Base class for devices.  Must be subclassed. Should not be instantiated directly.

    Attributes:
        type (Devices): The type of the device.
        responses (list): The list of event types that the device can respond to.
    """

    type = types.UNDEFINED
    responses = events.filter

    def __init__(self, read=None, data=None, read2=None, data2=None):
        """
        Create a new device object.

        Args:
            read (callable, optional): A function that returns an event or None.  Defaults to None.
            data (Any, optional): Data to pass to the read function.  Defaults to None.
            read2 (callable, optional): A function that returns a value or None.  Defaults to None.
            data2 (Any, optional): Data to pass to the read2 function.  Defaults to None.
        """
        self._event_callbacks = {}

        self._read = read if read else lambda: None
        self._data = data
        self._read2 = read2 if read2 else lambda: None
        self._data2 = data2

        self._broker = None
        self._state = None
        self._user_data = None  # Can be set and retrieved by user apps

    def poll(self, *args):
        """
        Poll the device for events.

        Args:
            *args: Forwarded to the device read callback when applicable.

        Returns:
            list | None: Matching events, or None if none were received.
        """
        if (dev_events := self._poll()) is not None:
            if isinstance(dev_events, list):
                eventlist = [e for e in dev_events if e.type in events.filter]
            else:
                eventlist = [dev_events] if dev_events.type in events.filter else None

            for event in eventlist:
                if event.type == events.QUIT and self._broker:
                    self._broker.quit()
                if callback_list := self._event_callbacks.get(event.type):
                    for callback in callback_list:
                        callback(event, *args)
            return eventlist if len(eventlist) > 0 else None
        return None

    def subscribe(self, callback, event_types=None):
        """
        Subscribe to events from the device.

        Args:
            callback (function): The function to call when an event is received.
            event_types (list[int] | None): A list of event types to subscribe to.

        Raises:
            ValueError: If `callback` is not callable.
            ValueError: If any event type in `event_types` is not a response from this device.

        Example:
            ```python
            def callback(event):
                print(event)

            device.subscribe(callback, [events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP])
            ```

            This will call `callback` when the device receives a MOUSEBUTTONDOWN or MOUSEBUTTONUP event.
        """
        event_types = event_types or self.responses
        if not callable(callback):
            raise ValueError("callback is not callable.")
        for event_type in event_types:
            if event_type not in self.responses:
                raise ValueError("the specified event_type is not a response from this device")
            callback_set = self._event_callbacks.get(event_type, set())
            callback_set.add(callback)
            self._event_callbacks[event_type] = callback_set

    def unsubscribe(self, callback, event_types=None):
        """
        Unsubscribes a callback function from one or more event types.

        Args:
            callback (function): The callback function to unsubscribe.
            event_types (list): A list of event types to unsubscribe from.
        """
        event_types = event_types or self.responses
        for event_type in event_types:
            if callback_set := self._event_callbacks.get(event_type):
                callback_set.remove(callback)

    @property
    def broker(self):
        """
        The broker that manages this device.
        """
        return self._broker

    @broker.setter
    def broker(self, broker):
        self._broker = broker

    @property
    def user_data(self):
        """
        User data that can be set and retrieved by applications.
        """
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        self._user_data = value


class Broker(Device):
    """
    The Broker class is a device that polls multiple devices for events and forwards them to
    subscribers.

    Attributes:
        type (Devices): The type of the device (set to `types.BROKER`).
        responses (list): The list of event types that the device can respond to.
        events (events): The events class for convenience.
                         Applications can use Broker.events.KEYDOWN, etc.
    """

    type = types.BROKER
    responses = events.filter
    events = events  # Create a reference to the events class for convenience.

    def __init__(self):
        super().__init__()
        self.devices = []  # List of devices to poll
        self._device_callbacks = {}
        # Function to call when the window close button is clicked.
        # Set it like `display_drv.quit_func = cleanup_func` where `cleanup_func` is a
        # function that cleans up resources and calls `sys.exit()`.
        # .poll() must be called periodically to check for the quit event.
        # When left at the default, quit() delegates cleanup + process exit to the
        # registered display driver's polymorphic quit() instead (see quit()).
        self._quit_func = exit
        self._quit_func_customized = False

    def subscribe(self, callback, event_types=None, device_types=None):
        """
        Subscribes a callback function to receive events.

        Args:
            callback (function): The callback function to subscribe.
            event_types (list, optional): The list of event types to subscribe to. Defaults to None.
            device_types (list, optional): The list of device types to subscribe to. Defaults to None.

        Raises:
            ValueError: If the callback is not callable.
            ValueError: If both device_types and event_types are provided.
            ValueError: If neither device_types nor event_types are provided.
        """
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if device_types is not None and event_types is not None:
            raise ValueError("set one of device_types or event_types but not both.")
        if device_types is None and event_types is None:
            raise ValueError("set one of device_types or event_types but not both.")
        if device_types is not None:
            for device_type in device_types:
                callback_set = self._device_callbacks.get(device_type, set())
                callback_set.add(callback)
                self._device_callbacks[device_type] = callback_set
        else:
            super().subscribe(callback, event_types)

    def unsubscribe(self, callback, event_types=None, device_types=None):
        """
        Unsubscribes a callback function from receiving events.

        Args:
            callback (function): The callback function to unsubscribe.
            event_types (list, optional): The list of event types to unsubscribe from. Defaults to None.
            device_types (list, optional): The list of device types to unsubscribe from. Defaults to None.

        Raises:
            ValueError: If both device_types and event_types are provided.
            ValueError: If neither device_types nor event_types are provided.
        """
        if device_types is not None and event_types is not None:
            raise ValueError("set one of device_types or event_types but not both.")
        if device_types is None and event_types is None:
            raise ValueError("set one of device_types or event_types but not both.")
        if device_types is not None:
            for device_type in device_types:
                if callback_set := self._device_callbacks.get(device_type):
                    callback_set.remove(callback)
        else:
            super().unsubscribe(callback, event_types)

    def create_device(self, type=types.QUEUE, **kwargs) -> Device:
        """
        Create a device object.

        Args:
            type (int, optional): The type of device to create. Defaults to types.QUEUE.
            **kwargs (Any): Arbitrary keyword arguments for the class constructor.

        Returns:
            Device: The created device object.

        Raises:
            ValueError: If the device type is invalid.
        """
        if cls := _mapping.get(type):
            dev = cls(**kwargs)
            self.register_device(dev)
            return dev
        raise ValueError("Invalid device type")

    def register_device(self, dev):
        """
        Register a device to be polled.

        Args:
            dev (Device): The device object to register.
        """
        dev.broker = self
        self.devices.append(dev)

    def unregister_device(self, dev):
        """
        Unregister a device.

        Args:
            dev (Device): The device object to unregister.
        """
        if dev in self.devices:
            self.devices.remove(dev)
            dev.broker = None

    @property
    def quit_func(self):
        """
        The function to call when the window close button is clicked.
        """
        return self._quit_func

    @quit_func.setter
    def quit_func(self, value):
        """
        Sets the function to call when the window close button is clicked.

        Args:
            value (function): The function to call when the window close button is clicked.
        """
        if not callable(value):
            raise ValueError("quit_func must be callable")
        self._quit_func = value
        self._quit_func_customized = True

    def quit(self):
        """
        Handle a window-close (QUIT) event.  This runs for every front end
        (LVGL or not), since the QUIT event is handled here in eventsys.

        If the application installed a custom ``quit_func``, it is called first
        for app-specific cleanup.  If it returns (for example because ``sys.exit``
        was swallowed when quit was invoked from a timer or
        ``micropython.schedule`` callback), cleanup falls through to the
        registered display driver's ``quit()``.  With no display registered,
        the broker's fallback ``quit_func`` is used.
        """
        if self._quit_func_customized:
            self._quit_func()
            # A custom handler may call sys.exit(), which is swallowed when quit
            # is invoked from a timer or micropython.schedule callback.  Fall
            # through to the display driver's hard exit when that happens.

        for device in self.devices:
            data = getattr(device, "_data", None)
            if callable(getattr(data, "deinit", None)) and callable(getattr(data, "quit", None)):
                data.quit()  # releases resources and terminates; does not return

        # No display registered to handle the exit; fall back.
        self._quit_func()

    def _poll(self):
        """
        Polls the registered devices for events.

        Returns:
            list: A list of event objects if events are received, otherwise None.
        """
        eventlist = []
        for device in self.devices:
            if (dev_events := device.poll()) is not None:
                eventlist.extend(dev_events)
                if callback_list := self._device_callbacks.get(device.type):
                    for func in callback_list:
                        for event in dev_events:
                            func(event)
        return eventlist if len(eventlist) > 0 else None


class QueueDevice(Device):
    """
    Represents a queue device.

    Attributes:
        type (str): The type of the device.
        responses (list): The list of events that the device can respond to.
    """

    type = types.QUEUE
    responses = events.filter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._data2 is None:
            self._data2 = events.filter
        if hasattr(self._data, "touch_scale"):
            self.scale = self._data.touch_scale
        else:
            self.scale = 1

    def _poll(self):
        """
        Polls the device for events.

        Returns:
            Event or None: The next event from the device, or None if no event is available.
        """
        if (dev_events := self._read()) is not None:
            eventlist = []
            for event in dev_events:
                if event.type in self._data2:
                    if (
                        event.type
                        in (
                            events.MOUSEMOTION,
                            events.MOUSEBUTTONDOWN,
                            events.MOUSEBUTTONUP,
                        )
                        and (scale := self.scale) != 1
                    ):
                        event.pos = (
                            int(event.pos[0] // scale),
                            int(event.pos[1] // scale),
                        )
                        if event.type == events.MOUSEMOTION:
                            event.rel = (event.rel[0] // scale, event.rel[1] // scale)

                    eventlist.append(event)

            return eventlist if len(eventlist) > 0 else None
        return None


class TouchDevice(Device):
    """
    Represents a touch input device.

    This class handles touch input events and provides methods to read touch data
    from the underlying touch driver. It supports reporting mouse button 1 events
    such as mouse motion, mouse button down, and mouse button up.

    Attributes:
        type (str): The type of the device (set to types.TOUCH).
        responses (tuple): The supported event types for the device.

    Args:
        *args (Any): Variable length argument list.
        **kwargs (Any): Arbitrary keyword arguments.
    """

    type = types.TOUCH
    responses = (events.MOUSEMOTION, events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._data is None:
            raise ValueError("TouchDevice requires a display device as 'data'")
        if self._data2 is None:  # self._data is a rotation table
            self._data2 = _DEFAULT_TOUCH_ROTATION_TABLE
        self._data.touch_device = self
        self.rotation = self._data.rotation

    @property
    def rotation(self):
        """
        Get the rotation value of the touch device.

        Returns:
            rotation (int): The rotation value in degrees.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        """
        Set the rotation value of the touch device.

        Args:
            value (int): The rotation value in degrees.
        """
        self._rotation = value % 360

        # _mask is an integer from 0 to 7 (or 0b001 to 0b111, 3 bits)
        # Currently, bit 2 = invert_y, bit 1 is invert_x and bit 0 is swap_xy, but that may change.
        self._mask = self._data2[self._rotation // 90]

    @property
    def rotation_table(self):
        """
        Get the rotation table of the touch device.

        Returns:
            (list): The rotation table.
        """
        return self._data2

    @rotation_table.setter
    def rotation_table(self, value):
        """
        Set the rotation table of the touch device.

        Args:
            value (list): The rotation table.
        """
        self._data2 = value

    def _poll(self):
        """
        Poll the touch device for touch events.

        Returns:
            Event: The touch event generated by the touch device.
        """
        try:  # If called too quickly, the touch driver may raise OSError: [Errno 116] ETIMEDOUT
            touched = self._read()
        except OSError:
            return None
        if touched:
            last_pos = self._state
            # If it looks like a point, use it, otherwise get the first point out of the list / tuple
            (x, y, *_) = touched if isinstance(touched[0], int) else touched[0]

            if self._mask & SWAP_XY:
                x, y = y, x
            if self._mask & REVERSE_X:
                x = self._data.width - x - 1
            if self._mask & REVERSE_Y:
                y = self._data.height - y - 1
            self._state = (x, y)
            if last_pos is not None:
                last_x, last_y = last_pos
                return events.Motion(
                    events.MOUSEMOTION,
                    self._state,
                    (x - last_x, y - last_y),
                    (1, 0, 0),
                    False,
                    None,
                )
            else:
                return events.Button(events.MOUSEBUTTONDOWN, self._state, 1, False, None)
        elif self._state is not None:
            last_pos = self._state
            self._state = None
            return events.Button(events.MOUSEBUTTONUP, last_pos, 1, False, None)
        return None


class EncoderDevice(Device):
    """
    A class representing an encoder device.

    Attributes:
        type (str): The type of the device (ENCODER).
        responses (tuple): The events that the device can respond to (MOUSEWHEEL, MOUSEBUTTONDOWN, MOUSEBUTTONUP).
    """

    type = types.ENCODER
    responses = (events.MOUSEWHEEL, events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP)

    def __init__(self, *args, **kwargs):
        """
        Initializes a new instance of the EncoderDevice class.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Notes:
            - self._data is the mouse button number to report for the switch.
              Default is 2 (middle mouse button). If the mouse button number is even,
              the wheel will report vertical (y) movement. If the mouse button number is odd,
              the wheel will report horizontal (x) movement. This corresponds to a typical mouse
              wheel being button 2 and the wheel moving vertically. It also corresponds to
              scrolling horizontally on a touchpad with two-finger scrolling and using the right button.
        """
        super().__init__(*args, **kwargs)
        self._state = (0, False)  # (position, pressed)
        self._data = self._data if self._data else 2  # Default to middle mouse button

    def _poll(self):
        """
        Polls the encoder device for changes and returns the corresponding event.

        Returns:
            Event: The event generated by the encoder device, or None if no event occurred.
        """
        last_pos, last_pressed = self._state
        pressed = self._read2()
        if pressed != last_pressed:
            self._state = (last_pos, pressed)
            return events.Button(
                events.MOUSEBUTTONDOWN if pressed else events.MOUSEBUTTONUP,
                (0, 0),
                self._data,
                False,
                None,
            )

        pos = self._read()
        if pos != last_pos:
            steps = pos - last_pos
            self._state = (pos, last_pressed)
            if self._data % 2 == 0:
                return events.Wheel(events.MOUSEWHEEL, False, 0, steps, 0, steps, False, None)
            return events.Wheel(events.MOUSEWHEEL, False, steps, 0, steps, 0, False, None)
        return None


class KeypadDevice(Device):
    """
    Represents a keypad device.

    Attributes:
        type (Devices): The type of the device (set to `types.KEYPAD`).
        responses (tuple): The types of events that the device can respond to (set to `(events.KEYDOWN, events.KEYUP)`).

    Methods:
        __init__: Initializes the KeypadDevice object.
        _poll: Polls the keypad for key events.
    """

    type = types.KEYPAD
    responses = (events.KEYDOWN, events.KEYUP)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = set()

    def _poll(self):
        """
        Polls the keypad for key events.

        Returns:
            events.Key or None: An instance of the `events.Key` class representing the key event, or `None` if no key event occurred.
        """
        keys = set(self._read())
        released = self._state - keys
        if released:
            key = released.pop()
            self._state.remove(key)
            return events.Key(events.KEYUP, chr(key), key, 0, 0)
        pressed = keys - self._state
        if pressed:
            key = pressed.pop()
            self._state.add(key)
            return events.Key(events.KEYDOWN, chr(key), key, 0, 0)
        return None


class JoystickDriver:
    def get_instance_id(self):
        raise NotImplementedError("JoystickDriver.get_instance_id() not implemented")

    def get_numaxes(self):
        raise NotImplementedError("JoystickDriver.get_numaxes() not implemented")

    def get_axis(self, axis):
        raise NotImplementedError("JoystickDriver.get_axis() not implemented")

    def get_numballs(self):
        raise NotImplementedError("JoystickDriver.get_numballs() not implemented")

    def get_ball(self, ball):
        raise NotImplementedError("JoystickDriver.get_ball() not implemented")

    def get_numbuttons(self):
        raise NotImplementedError("JoystickDriver.get_numbuttons() not implemented")

    def get_button(self, button):
        raise NotImplementedError("JoystickDriver.get_button() not implemented")

    def get_numhats(self):
        raise NotImplementedError("JoystickDriver.get_numhats() not implemented")

    def get_hat(self, hat):
        raise NotImplementedError("JoystickDriver.get_hat() not implemented")


class JoystickDevice(Device):
    """
    Represents a joystick device.

    Attributes:
        type (Devices): The type of the device, set to `types.JOYSTICK`.
        responses (tuple): A tuple of event types that this device can respond to.

    Methods:
        __init__(*args, **kwargs): Initializes the JoystickDevice instance.
        _poll(): Polls the device for events.

    Args:
        joystick_driver (JoystickDriver): The joystick driver to use.
        emulate_digital [(int,int)]: Emulate digital buttons for the given axis pairs. If set, a hat will be added for each axis pair. The hats will be added after any true hats.
        digital_threshold (float): The threshold to use for digital emulation.
    Raises:
        NotImplementedError: If any of the joystick driver methods are not implemented.
        ValueError: If a hat has an invalid value, e.g. both up and down are true.
    """

    type = types.JOYSTICK
    responses = (
        events.JOYAXISMOTION,
        events.JOYBALLMOTION,
        events.JOYHATMOTION,
        events.JOYBUTTONDOWN,
        events.JOYBUTTONUP,
    )

    def __init__(
        self,
        *args,
        joystick_driver: JoystickDriver,
        emulate_digital=None,
        digital_threshold: float = 0.5,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.joystick_driver = joystick_driver
        self.emulate_digital = emulate_digital
        self.digital_threshold = digital_threshold
        self._state = [
            [0] * self.joystick_driver.get_numaxes(),
            [False] * self.joystick_driver.get_numbuttons(),
            [(0, 0)] * self.joystick_driver.get_numhats(),
            [(0, 0)] * self.joystick_driver.get_numballs(),
        ]
        if self.emulate_digital:
            self._state.append([0] * len(self.emulate_digital))

    def emulate(self, value):
        return (
            -1 if value < -self.digital_threshold else 1 if value > self.digital_threshold else 0
        )

    def _poll(self):
        eventlist = []
        new_state = [
            [self.joystick_driver.get_axis(i) for i in range(self.joystick_driver.get_numaxes())],
            [
                self.joystick_driver.get_button(i)
                for i in range(self.joystick_driver.get_numbuttons())
            ],
            [self.joystick_driver.get_hat(i) for i in range(self.joystick_driver.get_numhats())],
            [self.joystick_driver.get_ball(i) for i in range(self.joystick_driver.get_numballs())],
        ]

        instance_id = self.joystick_driver.get_instance_id()
        # axes
        for i, (old, new) in enumerate(zip(self._state[0], new_state[0])):
            if old != new:
                eventlist.append(events.JoyAxisMotion(events.JOYAXISMOTION, instance_id, i, new))

        # buttons
        for i, (old, new) in enumerate(zip(self._state[1], new_state[1])):
            if old != new:
                eventlist.append(
                    events.JoyButtonDown(events.JOYBUTTONDOWN, instance_id, i)
                    if new
                    else events.JoyButtonUp(events.JOYBUTTONUP, instance_id, i)
                )

        # hats
        for i, (old, new) in enumerate(zip(self._state[2], new_state[2])):
            if old != new:
                eventlist.append(events.JoyHatMotion(events.JOYHATMOTION, instance_id, i, new))

        # balls
        for i, (old, new) in enumerate(zip(self._state[3], new_state[3])):
            if old != new:
                eventlist.append(events.JoyBallMotion(events.JOYBALLMOTION, instance_id, i, new))

        if self.emulate_digital:
            axes = new_state[0]
            new_state.append(
                [(self.emulate(axes[x]), self.emulate(axes[y])) for x, y in self.emulate_digital]
            )
            for i, (old, new) in enumerate(zip(self._state[4], new_state[4])):
                if old != new:
                    eventlist.append(
                        events.JoyHatMotion(
                            events.JOYHATMOTION,
                            instance_id,
                            i + self.joystick_driver.get_numhats(),
                            new,
                        )
                    )

        self._state = new_state
        return eventlist if len(eventlist) > 0 else None


class VirtualDevices:
    class VirtualDevice:
        def __init__(self, virtual_devices, device_type):
            self._virtual_devices = virtual_devices
            self.type = device_type
            self.user_data = None
            self._fifo = []

        def subscribe(self, callback):
            self._callback = callback

        def poll(self, *args):
            self._virtual_devices.poll_queue_device()
            event = self._fifo.pop(0) if self._fifo else None
            self._callback(event, *args)

        def add_event(self, event):
            self._fifo.append(event)

    def __init__(self, queue_device):
        self._queue_device = queue_device
        self._vd_touch = self.VirtualDevice(self, types.TOUCH)
        self._vd_encoder = self.VirtualDevice(self, types.ENCODER)
        self._vd_keypad = self.VirtualDevice(self, types.KEYPAD)
        self.devices = [self._vd_touch, self._vd_encoder, self._vd_keypad]

    def poll_queue_device(self):
        if elist := self._queue_device.poll():
            for e in elist:
                if (
                    e.type == events.MOUSEBUTTONDOWN
                    or e.type == events.MOUSEBUTTONUP
                    or (e.type == events.MOUSEMOTION and e.buttons[0])
                ):
                    self._vd_touch.add_event(e)
                elif e.type == events.MOUSEWHEEL:
                    self._vd_encoder.add_event(e)
                elif e.type == events.KEYDOWN or e.type == events.KEYUP:
                    self._vd_keypad.add_event(e)


_mapping = {
    # Mapping of device types to device classes
    types.BROKER: Broker,
    types.QUEUE: QueueDevice,
    types.TOUCH: TouchDevice,
    types.ENCODER: EncoderDevice,
    types.KEYPAD: KeypadDevice,
    types.JOYSTICK: JoystickDevice,
}
