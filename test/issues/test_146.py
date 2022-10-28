# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/146
"""

import warnings


def test_146() -> None:
    # Ensure that importing pyshacl triggers no warnings.
    with warnings.catch_warnings(record=True) as warning_context:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        # Import pyshacl, which should not trigger any warnings
        import pyshacl
        # Verify some things
        assert len(warning_context) == 0


if __name__ == "__main__":
    test_146()
