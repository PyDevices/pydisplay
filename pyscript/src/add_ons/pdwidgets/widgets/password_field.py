# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PasswordField — TextInput that masks glyphs."""

from .text_input import TextInput


class PasswordField(TextInput):
    """Single-line password entry; drawn text is replaced with ``*`` masks."""

    def __init__(self, *args, mask="*", **kwargs):
        self.mask = mask
        super().__init__(*args, **kwargs)

    def _display_text(self):
        n = len(self._value or "")
        return self.mask * n if n else ""
