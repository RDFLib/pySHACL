# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/298
"""
import sys

from rdflib import Graph
from rdflib.plugins.parsers.jsonld import to_rdf

import pyshacl


def test_298():
    shapes_graph = to_rdf(
        {
            "@context": {
                "ex": "http://example.org/",
                "sh": "http://www.w3.org/ns/shacl#",
            },
            "@graph": [
                {
                    "@id": "ex:PersonShape",
                    "@type": "sh:NodeShape",
                    "sh:targetClass": {"@id": "ex:Person"},
                    "sh:property": [
                        {
                            "@id": "ex:NameProperty",
                            "sh:path": {"@id": "ex:name"},
                            "sh:minCount": 1,
                        },
                        {
                            "@id": "ex:AgeProperty",
                            "sh:path": {"@id": "ex:age"},
                            "sh:minInclusive": 18,
                        },
                    ],
                }
            ],
        },
        Graph(),
    )

    data_graph = to_rdf(
        {
            "@context": {
                "ex": "http://example.org/",
            },
            "@id": "ex:person1",
            "@type": "ex:Person",
            "ex:name": "John Doe",
            "ex:age": 25,
        },
        Graph(),
    )

    conforms, report_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        use_shapes=[
            "http://example.org/PersonShape",
            "http://example.org/NameProperty",
        ],
    )
    assert conforms
    assert "Validation Report" in results_text


if __name__ == "__main__":
    sys.exit(test_298())
