import rdflib
from pyshacl import validate
from pyshacl.errors import ConstraintLoadError

"""
https://github.com/RDFLib/pySHACL/issues/58
"""
data = """
@prefix asdf: <http://example.org/asdf/> .
@prefix ex: <http://example.org/> .

asdf:e2e a ex:termA ;
    ex:child asdf:23e .

asdf:23e a ex:termB .
"""

shaclData = """
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:termShape a sh:NodeShape ;
    sh:ignoredProperties ( rdf:type ) ;
    sh:targetClass ex:termB .
"""



def test_058():
    dataGraph = rdflib.Graph().parse(data=data, format='ttl')
    shaclGraph = rdflib.Graph().parse(data=shaclData, format='ttl')
    exc = None
    try:
        conforms, g, s = validate(dataGraph, shacl_graph=shaclGraph, abort_on_first=False, meta_shacl=False, debug=False, advanced=True)
    except Exception as e:
        assert isinstance(e, ConstraintLoadError)
        exc = e
    assert exc is not None
    assert "ignoredProperties" in str(exc)



if __name__ == "__main__":
    test_058()
