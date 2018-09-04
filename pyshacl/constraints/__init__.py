# -*- coding: utf-8 -*-

from .value_constraints import ClassConstraintComponent

ALL_CONSTRAINT_COMPONENTS = [
    ClassConstraintComponent
]

CONSTRAINT_PARAMETERS_MAP = {p: c for c in ALL_CONSTRAINT_COMPONENTS
                             for p in c.constraint_parameters()}

ALL_CONSTRAINT_PARAMETERS = list(CONSTRAINT_PARAMETERS_MAP.keys())
