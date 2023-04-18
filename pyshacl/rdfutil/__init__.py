# -*- coding: utf-8 -*-
#
"""A collection of handy utility RDF functions, will one day be split out into its own installable module."""

from .clone import clone_blank_node, clone_graph, clone_literal, clone_node, mix_datasets, mix_graphs  # noqa: F401
from .compare import compare_blank_node, compare_literal, compare_node, order_graph_literal  # noqa: F401
from .inoculate import inoculate, inoculate_dataset  # noqa: F401
from .load import add_baked_in, get_rdf_from_web, load_from_source  # noqa: F401
from .stringify import stringify_blank_node, stringify_graph, stringify_literal, stringify_node  # noqa: F401
