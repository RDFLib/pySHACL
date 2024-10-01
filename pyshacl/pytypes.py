# -*- coding: utf-8 -*-
#

from dataclasses import dataclass
from typing import List, Optional, Union

from rdflib import ConjunctiveGraph, Dataset, Graph, Literal
from rdflib.term import IdentifiedNode, URIRef

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Union[IdentifiedNode, Literal]


@dataclass
class SHACLExecutor:
    validator: Optional[object] = None
    advanced_mode: bool = False
    abort_on_first: bool = False
    allow_infos: bool = False
    allow_warnings: bool = False
    iterate_rules: bool = False
    debug: bool = False
    sparql_mode: bool = False
    max_validation_depth: int = 15
    focus_nodes: Optional[List[URIRef]] = None
