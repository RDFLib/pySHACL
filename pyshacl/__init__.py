# -*- coding: latin-1 -*-
#
from pyshacl.validate import Validator, validate


# version compliant with https://www.python.org/dev/peps/pep-0440/
__version__ = '0.12.2'
# Don't forget to change the version number in pyproject.toml along with this one

__all__ = ['validate', 'Validator', '__version__']
