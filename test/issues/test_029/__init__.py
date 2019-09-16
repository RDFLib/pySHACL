#
#
from pyshacl import validate
from pyshacl.rdfutil.load import load_from_source

data_graph = load_from_source("./test/issues/test_029/simpleData.ttl")
shacl_graph = load_from_source("./test/issues/test_029/simpleOnto.ttl")


def test_029():
    res = validate(data_graph, shacl_graph=shacl_graph, ont_graph=shacl_graph,
                   inference='none', debug=True)
    conforms, graph, string = res
    assert not conforms

if __name__ == "__main__":
    test_029()

