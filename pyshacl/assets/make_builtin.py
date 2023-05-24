import pickle

from rdflib import Graph, URIRef
from rdflib.plugins.stores.memory import Memory

from pyshacl.monkey import apply_patches

apply_patches()
identifier = URIRef("http://datashapes.org/schema")
store = Memory(identifier=identifier)
with open("./schema.ttl", "rb") as f:
    g = Graph(store=store, identifier=identifier, bind_namespaces='core').parse(file=f)
with open("./schema.pickle", "wb") as f:
    pickle.dump((store, identifier), f, protocol=4)  # protocol 5 only works in python 3.8+

identifier = URIRef("http://www.w3.org/ns/shacl#")
store = Memory(identifier=identifier)
with open("./shacl.ttl", "rb") as f:
    g = Graph(store=store, identifier=identifier, bind_namespaces='core').parse(file=f)
with open("./shacl.pickle", "wb") as f:
    pickle.dump((store, identifier), f, protocol=4)  # protocol 5 only works in python 3.8+

identifier = URIRef("http://www.w3.org/ns/shacl-shacl#")
store = Memory(identifier=identifier)
with open("./shacl-shacl.ttl", "rb") as f:
    g = Graph(store=store, identifier=identifier, bind_namespaces='core').parse(file=f)
with open("./shacl-shacl.pickle", "wb") as f:
    pickle.dump((store, identifier), f, protocol=4)  # protocol 5 only works in python 3.8+
