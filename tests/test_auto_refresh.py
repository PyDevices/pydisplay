# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Placeholder for DisplayDriver auto-refresh tests.

Auto-refresh still needs migration to the new multimer API. The old tests used
removed helpers and should not define the new multimer contract.
"""

import unittest


@unittest.skip("auto_refresh migration to Timer/AsyncTimer is pending")
class TestAutoRefresh(unittest.TestCase):
    def test_pending_migration(self):
        pass


if __name__ == "__main__":
    unittest.main()
