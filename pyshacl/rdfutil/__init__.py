# -*- coding: utf-8 -*-
#
"""A collection of handy utility RDF functions, will one day be split out into its own installable module."""

from rdflib import RDF, RDFS, Namespace
from .load import load_from_source, get_rdf_from_web  # noqa: F401
from .stringify import stringify_blank_node, stringify_graph, stringify_literal, stringify_node  # noqa: F401
from .clone import clone_blank_node, clone_literal, clone_graph, clone_node, mix_graphs  # noqa: F401
from .compare import compare_blank_node, order_graph_literal, compare_node, compare_literal  # noqa: F401

RDFS_Resource = RDFS.term('Resource')
RDF_first = RDF.term('first')
SH = Namespace('http://www.w3.org/ns/shacl#')
