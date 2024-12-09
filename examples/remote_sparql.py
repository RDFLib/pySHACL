from pyshacl import validate
from rdflib import Dataset, Graph
from rdflib.plugins.stores.sparqlstore import SPARQLStore

# Remote sparql endpoint:
my_sparql_endpoint = "https://my.service.com/repo/data/sparql"
store = SPARQLStore(my_sparql_endpoint, auth=('username', 'password'))
data_dataset = Dataset(store, default_union=True)

# Shapes graph:
shapes_graph = Graph().parse("my_shapes.ttl", format="turtle")

# Validate:
result_tuple = validate(data_dataset, shacl_graph=shapes_graph, sparql_mode=True)
conforms, results_graph, results_text = result_tuple
