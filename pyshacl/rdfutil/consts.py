# -*- coding: utf-8 -*-
#
from typing import Union

from rdflib import RDF, RDFS, BNode, ConjunctiveGraph, Dataset, Graph, Literal, Namespace, URIRef


RDFS_Resource = RDFS.Resource
RDF_first = RDF.first
SH = Namespace('http://www.w3.org/ns/shacl#')

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Union[URIRef, Literal, BNode]
