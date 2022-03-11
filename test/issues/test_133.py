"""
https://github.com/RDFLib/pySHACL/issues/133
"""
from pyshacl import validate
from rdflib import Graph
from rdflib.namespace import RDF, SH


def test_issue133():
    shacl_graph = Graph().parse(
        data=r"""
            @prefix geo: <http://www.opengis.net/ont/geosparql#> .
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
        """,
        format="turtle"
    )

    data_graph = Graph().parse(
        data="""
            @prefix geo: <http://www.opengis.net/ont/geosparql#> .

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
        """,
        format="turtle"
    )

    conforms, results_graph, s = validate(data_graph, shacl_graph=shacl_graph, meta_shacl=True)
    assert not conforms, "This validation should fail"

    # check that only b & c fail
    expected_fails = sorted([
        "https://example.com/geometry-b",
        "https://example.com/geometry-c"
    ])

    actual_fails = sorted([str(o) for o in results_graph.objects(None, SH.focusNode)])

    assert expected_fails == actual_fails, f"The expected fails are {expected_fails} " \
                                           f"but the actual fails are {actual_fails}"


if __name__ == "__main__":
    test_issue133()
