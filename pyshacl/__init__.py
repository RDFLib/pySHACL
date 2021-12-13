# -*- coding: latin-1 -*-
#
from .shape import Shape
from .shapes_graph import ShapesGraph
from .validate import Validator, validate


# version compliant with https://www.python.org/dev/peps/pep-0440/
__version__ = '0.17.3'
# Don't forget to change the version number in pyproject.toml and CITATION.cff along with this one

__all__ = ['validate', 'Validator', '__version__', 'Shape', 'ShapesGraph']
