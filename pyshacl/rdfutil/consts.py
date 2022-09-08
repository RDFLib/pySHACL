# -*- coding: utf-8 -*-
#
from typing import Union

from rdflib import RDF, RDFS, ConjunctiveGraph, Dataset, Graph, Namespace
from rdflib.term import Node


RDFS_Resource = RDFS.Resource
RDF_first = RDF.first
SH = Namespace('http://www.w3.org/ns/shacl#')

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Node
