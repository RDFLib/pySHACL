# -*- coding: utf-8 -*-

from .value_constraints import ClassConstraintComponent, DatatypeConstraintComponent, NodeKindConstraintComponent
from .cardinality_constraints import MinCountConstraintComponent, MaxCountConstraintComponent
from .string_based_constraints import MinLengthConstraintComponent, MaxLengthConstraintComponent, PatternConstraintComponent
from .shape_based_constraints import NodeShapeComponent, PropertyShapeComponent

ALL_CONSTRAINT_COMPONENTS = [
    ClassConstraintComponent,
    DatatypeConstraintComponent,
    NodeKindConstraintComponent,
    MinCountConstraintComponent,
    MaxCountConstraintComponent,
    MinLengthConstraintComponent,
    MaxLengthConstraintComponent,
    PatternConstraintComponent,
    NodeShapeComponent,
    PropertyShapeComponent
]

CONSTRAINT_PARAMETERS_MAP = {p: c for c in ALL_CONSTRAINT_COMPONENTS
                             for p in c.constraint_parameters()}

ALL_CONSTRAINT_PARAMETERS = list(CONSTRAINT_PARAMETERS_MAP.keys())
