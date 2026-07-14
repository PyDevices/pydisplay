# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Form binder: named fields, validate / values / commit (no chrome of its own)."""


class Form:
    """Register named field widgets and collect/validate their values.

    Depends on existing controls (:class:`FormRow`, :class:`TextInput`,
    :class:`Switch`, …). Optional ``error_label`` receives the first error
    string when :meth:`validate` fails.
    """

    def __init__(self, on_commit=None, error_label=None):
        self._fields = {}
        self._validators = {}
        self.on_commit = on_commit
        self.error_label = error_label

    def add(self, name, widget, validator=None):
        """Bind ``widget`` under ``name``; optional ``validator(value) -> err|None``."""
        self._fields[name] = widget
        if validator is not None:
            self._validators[name] = validator
        return widget

    def get(self, name):
        """Return the widget registered as ``name``, or ``None``."""
        return self._fields.get(name)

    def values(self):
        """Return ``{name: widget.value}`` for all registered fields."""
        return {name: w.value for name, w in self._fields.items()}

    def validate(self):
        """Run validators; return ``{name: error_str}`` (empty if ok).

        Updates ``error_label.value`` with the first error when present.
        """
        errors = {}
        for name, validator in self._validators.items():
            widget = self._fields.get(name)
            if widget is None:
                continue
            err = validator(widget.value)
            if err:
                errors[name] = err
        if self.error_label is not None:
            if errors:
                self.error_label.value = next(iter(errors.values()))
            else:
                self.error_label.value = ""
        return errors

    def commit(self):
        """Validate then invoke ``on_commit(values)`` when valid.

        Returns:
            bool: ``True`` if validation passed (and commit ran).
        """
        if self.validate():
            return False
        if self.on_commit is not None:
            self.on_commit(self.values())
        return True
