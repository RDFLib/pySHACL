# -*- coding: utf-8 -*-
#

from typing import Union
from rdflib import Graph, ConjunctiveGraph, Dataset

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
