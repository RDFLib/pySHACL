# -*- coding: utf-8 -*-
#

from typing import Union, Optional, Dict, Tuple
from rdflib import Graph, ConjunctiveGraph, Dataset

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
