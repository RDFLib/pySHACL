import pytest
from pyshacl import extras


def pytest_runtest_setup(item):
    extras.dev_mode = True

def pytest_runtest_teardown(item, call=None):
    extras.dev_mode = False
