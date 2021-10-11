import pickle

from rdflib import Graph

from pyshacl.monkey import apply_patches
from pyshacl.monkey.memory2 import Memory2


apply_patches()
identifier = "http://datashapes.org/schema"
store = Memory2(identifier=identifier)
with open("./schema.ttl", "rb") as f:
    g = Graph(store=store, identifier=identifier).parse(file=f)
with open("./schema.pickle", "wb") as f:
    pickle.dump((store, identifier), f, protocol=4)  # protocol 5 only works in python 3.8+
