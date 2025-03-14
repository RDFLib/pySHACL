# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/286
"""
import sys

import rdflib

import pyshacl

shapes_data = '''\
@prefix sh: <http://www.w3.org/ns/shacl#>.
@prefix gx: <https://registry.lab.gaia-x.eu/development/api/trusted-shape-registry/v1/shapes/jsonld/trustframework#>.
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

gx:LicenseShape a sh:NodeShape ;
    sh:property [
        sh:path gx:license ;
        sh:datatype xsd:string ;
        sh:in ("0BSD" "AAL" "EPL-2.0") ;
    ] ;
    sh:targetClass gx:License .
'''

data_shapes_in_xsd_string = '''\
@prefix sh: <http://www.w3.org/ns/shacl#>.
@prefix gx: <https://registry.lab.gaia-x.eu/development/api/trusted-shape-registry/v1/shapes/jsonld/trustframework#>.
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

gx:LicenseShape a sh:NodeShape ;
    sh:property [
        sh:path gx:license ;
        sh:datatype xsd:string ;
        sh:in ("0BSD"^^xsd:string
                  "AAL"^^xsd:string
                  "EPL-2.0"^^xsd:string) ;
    ] ;
    sh:targetClass gx:License .
'''

data_g_text = '''\
{
    "@context": {
      "gx": "https://registry.lab.gaia-x.eu/development/api/trusted-shape-registry/v1/shapes/jsonld/trustframework#",
      "xsd": "http://www.w3.org/2001/XMLSchema#"
    },
    "@type": "gx:License",
    "gx:license": {
        "@value": "EPL-2.0",
        "@type": "xsd:string"
    }
}
'''


def test_286_a():
    shape_g = rdflib.Graph().parse(data=shapes_data, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="json-ld")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shape_g,
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
    )
    assert not conforms
    assert "Results (1)" in results_text

def test_286_b():
    shape_g = rdflib.Graph().parse(data=data_shapes_in_xsd_string, format='turtle')
    data_g = rdflib.Graph().parse(data=data_g_text, format="json-ld")
    conforms, results_graph, results_text = pyshacl.validate(
        data_g,
        shacl_graph=shape_g,
        debug=True,
        inference='none',
        advanced=False,
        meta_shacl=False,
    )
    assert conforms

if __name__ == "__main__":
    test_286_b()
    sys.exit(test_286_b())
