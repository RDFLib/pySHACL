# -*- coding: utf-8 -*-
#
from typing import Union

from rdflib import ConjunctiveGraph, Dataset, Graph

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
