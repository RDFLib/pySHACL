# -*- coding: utf-8 -*-
"""
https://github.com/RDFLib/pySHACL/issues/133
"""

import rdflib

from pyshacl import validate


shacl_file = r"""@prefix geo: <http://www.opengis.net/ont/geosparql#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@base <http://www.opengis.net/def/geosparql/validator/> .

<S16-wkt-content>
	a sh:NodeShape ;
	sh:property <S16-wkt-content-sub-start> ;
	sh:targetSubjectsOf geo:asWKT ;
.

<S16-wkt-content-sub-start>
	a sh:PropertyShape ;
	sh:path geo:asWKT ;
	sh:pattern "^\\s*$|^\\s*(P|C|S|L|T|<)" ;
	sh:flags "i" ;
	sh:message "The content of an RDF literal with an incoming geo:asWKT relation must conform to a well-formed WKT string, as defined by its official specification (Simple Features Access)."@en ;
.
"""


data_file = """@prefix geo: <http://www.opengis.net/ont/geosparql#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<https://example.com/geometry-a>
    geo:asWKT "POINT (153.084231 -27.322738)"^^geo:wktLiteral ;
.

<https://example.com/geometry-b>
    geo:asWKT "xPOINT (153.084231 -27.322738)"^^geo:wktLiteral ;
.

<https://example.com/geometry-c>
    geo:asWKT "(153.084231 -27.322738)"^^geo:wktLiteral ;
.

<https://example.com/geometry-d>
    geo:asWKT "     POINT (153.084231 -27.322738)"^^geo:wktLiteral ;
.

<https://example.com/geometry-e>
    geo:asWKT "     "^^geo:wktLiteral ;
.

<https://example.com/geometry-f>
    geo:asWKT ""^^geo:wktLiteral ;
.
"""


def test_133() -> None:
    data = rdflib.Graph()
    data.parse(data=data_file, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(data=shacl_file, format="turtle")
    shapes.print()
    res = validate(
        data,
        shacl_graph=shapes,
        data_graph_format='turtle',
        shacl_graph_format='turtle',
        debug=True,
    )
    conforms, graph, string = res
    assert False == conforms
    assert "geometry-b" in string
    assert "geometry-c" in string
    assert "geometry-a" not in string
    assert "geometry-d" not in string
    assert "geometry-e" not in string
    assert "geometry-f" not in string


if __name__ == "__main__":
    test_133()
