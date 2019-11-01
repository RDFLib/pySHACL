# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/36
"""
from pyshacl import validate

shacl_file_text = """\
{
    "@context": {
       "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
       "sh": "http://www.w3.org/ns/shacl#",
       "schema": "http://schema.org/"
    },
    "@graph": [
        {
            "@id": "_:forceDatasetShape",
            "@type": "sh:NodeShape",
            "sh:targetNode": "schema:DigitalDocument",
            "sh:property": [
                {
                    "sh:path": [
                        {
                            "sh:inversePath": [{
                                "@id": "rdf:type",
                                "@type": "@id"
                             }]
                        }
                    ],
                    "sh:minCount": 1
                }
            ]
        }
    ]
}
"""

data_file_text_jsonld = """\
{
 
}
"""

def test_036_jsonld():
    res = validate(data_file_text_jsonld, shacl_graph=shacl_file_text,
                   data_graph_format='json-ld', shacl_graph_format='json-ld',
                   inference='rdfs', debug=True)
    conforms, graph, string = res
    assert not conforms


if __name__ == "__main__":
    test_036_jsonld()
