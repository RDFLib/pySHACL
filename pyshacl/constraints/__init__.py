# -*- coding: utf-8 -*-

from .value_constraints import ClassConstraintComponent, DatatypeConstraintComponent, NodeKindConstraintComponent
from .cardinality_constraints import MinCountConstraintComponent, MaxCountConstraintComponent
from .value_range_constraints import MinExclusiveConstraintComponent, MinInclusiveConstraintComponent, MaxExclusiveConstraintComponent, MaxInclusiveConstraintComponent
from .string_based_constraints import MinLengthConstraintComponent, MaxLengthConstraintComponent, PatternConstraintComponent
from .property_pair_constraints import EqualsConstraintComponent, DisjointConstraintComponent, LessThanConstraintComponent, LessThanOrEqualsConstraintComponent
from .logical_constraints import NotConstraintComponent, AndConstraintComponent, OrConstraintComponent, XoneConstraintComponent
from .shape_based_constraints import NodeShapeComponent, PropertyShapeComponent, QualifiedValueShapeConstraintComponent
from .other_constraints import ClosedConstraintComponent, InConstraintComponent, HasValueConstraintComponent

ALL_CONSTRAINT_COMPONENTS = [
    ClassConstraintComponent,
    DatatypeConstraintComponent,
    NodeKindConstraintComponent,
    MinCountConstraintComponent,
    MaxCountConstraintComponent,
    MinExclusiveConstraintComponent,
    MinInclusiveConstraintComponent,
    MaxExclusiveConstraintComponent,
    MaxInclusiveConstraintComponent,
    NotConstraintComponent,
    AndConstraintComponent,
    OrConstraintComponent,
    XoneConstraintComponent,
    MinLengthConstraintComponent,
    MaxLengthConstraintComponent,
    PatternConstraintComponent,
    EqualsConstraintComponent,
    DisjointConstraintComponent,
    LessThanConstraintComponent,
    LessThanOrEqualsConstraintComponent,
    NodeShapeComponent,
    PropertyShapeComponent,
    QualifiedValueShapeConstraintComponent,
    ClosedConstraintComponent,
    HasValueConstraintComponent,
    InConstraintComponent,

]

CONSTRAINT_PARAMETERS_MAP = {p: c for c in ALL_CONSTRAINT_COMPONENTS
                             for p in c.constraint_parameters()}

ALL_CONSTRAINT_PARAMETERS = list(CONSTRAINT_PARAMETERS_MAP.keys())
