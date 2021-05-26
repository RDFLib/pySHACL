# -*- coding: utf-8 -*-
#

from typing import Union

from rdflib import BNode, ConjunctiveGraph, Dataset, Graph, Literal, URIRef


ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Union[URIRef, Literal, BNode]
