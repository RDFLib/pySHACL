# -*- coding: utf-8 -*-
#

from dataclasses import dataclass
from typing import Optional, Union

from rdflib import ConjunctiveGraph, Dataset, Graph, Literal
from rdflib.term import IdentifiedNode, Node

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Union[IdentifiedNode, Literal]
BaseNode = Node


@dataclass
class SHACLExecutor:
    validator: Optional[object] = None
    abort_on_first: bool = False
    allow_infos: bool = False
    allow_warnings: bool = False
    iterate_rules: bool = False
    debug: bool = False
    max_validation_depth: int = 15
