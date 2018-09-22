# -*- coding: utf-8 -*-

from pyshacl.constraints.core.value_constraints import ClassConstraintComponent, DatatypeConstraintComponent, NodeKindConstraintComponent
from pyshacl.constraints.core.cardinality_constraints import MinCountConstraintComponent, MaxCountConstraintComponent
from pyshacl.constraints.core.value_range_constraints import MinExclusiveConstraintComponent, MinInclusiveConstraintComponent, MaxExclusiveConstraintComponent, MaxInclusiveConstraintComponent
from pyshacl.constraints.core.string_based_constraints import MinLengthConstraintComponent, MaxLengthConstraintComponent, PatternConstraintComponent, LanguageInConstraintComponent, UniqueLangConstraintComponent
from pyshacl.constraints.core.property_pair_constraints import EqualsConstraintComponent, DisjointConstraintComponent, LessThanConstraintComponent, LessThanOrEqualsConstraintComponent
from pyshacl.constraints.core.logical_constraints import NotConstraintComponent, AndConstraintComponent, OrConstraintComponent, XoneConstraintComponent
from pyshacl.constraints.core.shape_based_constraints import NodeConstraintComponent, PropertyConstraintComponent, QualifiedValueShapeConstraintComponent
from pyshacl.constraints.core.other_constraints import ClosedConstraintComponent, InConstraintComponent, HasValueConstraintComponent
from pyshacl.constraints.sparql.sparql_based_constraints import SPARQLBasedConstraint
from pyshacl.constraints.sparql.sparql_based_constraint_components import SPARQLConstraintComponent

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
    LanguageInConstraintComponent,
    UniqueLangConstraintComponent,
    EqualsConstraintComponent,
    DisjointConstraintComponent,
    LessThanConstraintComponent,
    LessThanOrEqualsConstraintComponent,
    NodeConstraintComponent,
    PropertyConstraintComponent,
    QualifiedValueShapeConstraintComponent,
    ClosedConstraintComponent,
    HasValueConstraintComponent,
    InConstraintComponent,
    SPARQLBasedConstraint,
    # SPARQLConstraintComponent
    # This one is deliberately not included
    # Because it gets matched to shapes manually
]

CONSTRAINT_PARAMETERS_MAP = {p: c for c in ALL_CONSTRAINT_COMPONENTS
                             for p in c.constraint_parameters()}

ALL_CONSTRAINT_PARAMETERS = list(CONSTRAINT_PARAMETERS_MAP.keys())
