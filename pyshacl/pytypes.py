# -*- coding: utf-8 -*-
#

from typing import Union

from rdflib import ConjunctiveGraph, Dataset, Graph, Literal
from rdflib.term import IdentifiedNode, Node

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Union[IdentifiedNode, Literal]
BaseNode = Node
