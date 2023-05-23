# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Type

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.constraints.core.cardinality_constraints import MaxCountConstraintComponent, MinCountConstraintComponent
from pyshacl.constraints.core.logical_constraints import (
    AndConstraintComponent,
    NotConstraintComponent,
    OrConstraintComponent,
    XoneConstraintComponent,
)
from pyshacl.constraints.core.other_constraints import (
    ClosedConstraintComponent,
    HasValueConstraintComponent,
    InConstraintComponent,
)
from pyshacl.constraints.core.property_pair_constraints import (
    DisjointConstraintComponent,
    EqualsConstraintComponent,
    LessThanConstraintComponent,
    LessThanOrEqualsConstraintComponent,
)
from pyshacl.constraints.core.shape_based_constraints import (
    NodeConstraintComponent,
    PropertyConstraintComponent,
    QualifiedValueShapeConstraintComponent,
)
from pyshacl.constraints.core.string_based_constraints import (
    LanguageInConstraintComponent,
    MaxLengthConstraintComponent,
    MinLengthConstraintComponent,
    PatternConstraintComponent,
    UniqueLangConstraintComponent,
)
from pyshacl.constraints.core.value_constraints import (
    ClassConstraintComponent,
    DatatypeConstraintComponent,
    NodeKindConstraintComponent,
)
from pyshacl.constraints.core.value_range_constraints import (
    MaxExclusiveConstraintComponent,
    MaxInclusiveConstraintComponent,
    MinExclusiveConstraintComponent,
    MinInclusiveConstraintComponent,
)
from pyshacl.constraints.sparql.sparql_based_constraint_components import SPARQLConstraintComponent  # noqa: F401
from pyshacl.constraints.sparql.sparql_based_constraints import SPARQLBasedConstraint

ALL_CONSTRAINT_COMPONENTS: List[Type[ConstraintComponent]] = [
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
    # ^ ^ This one is deliberately not included in this
    # list because it gets matched to shapes manually later
]

CONSTRAINT_PARAMETERS_MAP: Dict[Any, Type[ConstraintComponent]] = {
    p: c for c in ALL_CONSTRAINT_COMPONENTS for p in c.constraint_parameters()
}

ALL_CONSTRAINT_PARAMETERS: List[Any] = list(CONSTRAINT_PARAMETERS_MAP.keys())
