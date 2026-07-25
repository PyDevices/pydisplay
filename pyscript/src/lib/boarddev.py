# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Lazy end-device binding for board_devices → board_config.

``board_devices.setup_devices(globals())`` typically calls
``bind_lazy(ns, this_module)``. Apps never import ``boarddev``; they use
``board_config.DEVICES`` and attribute access.
"""


def bind_lazy(ns, devices_mod):
    """Install module ``__getattr__`` / ``__dir__`` on *ns* for lazy roles.

    Each name in ``devices_mod.DEVICES`` maps to a zero-arg factory
    ``devices_mod.<name>()``. First access constructs, caches into
    ``ns[name]``, and returns the object. Further access hits the module
    dict (no ``__getattr__``).
    """
    roles = devices_mod.DEVICES

    def __getattr__(name):
        if name not in roles:
            raise AttributeError("module has no attribute {!r}".format(name))
        factory = getattr(devices_mod, name)
        obj = factory()
        ns[name] = obj  # cache; skips __getattr__ next time
        return obj

    def __dir__():
        # MP/CPython: show real attrs plus lazy roles not yet constructed
        names = list(ns.keys())
        for role in roles:
            if role not in ns:
                names.append(role)
        return sorted(names)

    ns["__getattr__"] = __getattr__
    ns["__dir__"] = __dir__
