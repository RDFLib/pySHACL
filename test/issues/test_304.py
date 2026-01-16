# -*- coding: utf-8 -*-
#
"""
https://github.com/RDFLib/pySHACL/issues/304
"""
import os
import subprocess
import sys
import textwrap


DATA_TTL = """\
@prefix ex: <http://example.org/> .

ex:node1 a ex:Thing ;
    ex:list ( "a" "b" ) ;
    ex:code "X-1" ;
    ex:flag true .

ex:node2 a ex:Thing ;
    ex:list ( "c" "d" ) ;
    ex:code "BAD" .

ex:node3 a ex:Thing ;
    ex:list ( "e" ) .

ex:node4 a ex:Other ;
    ex:label 42 ;
    ex:ref ex:node1 .

ex:node5 a ex:Other ;
    ex:label "ok" ;
    ex:ref ex:node2 ;
    ex:ref ex:node3 .
"""

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:ThingShape
    a sh:NodeShape ;
    sh:targetClass ex:Thing ;
    sh:property [
        sh:path ex:list ;
        sh:datatype xsd:integer ;
        sh:message "List items must be integers." ;
    ] ;
    sh:property [
        sh:path ex:code ;
        sh:pattern "^X-" ;
        sh:message "Code must start with X-" ;
    ] ;
    sh:property [
        sh:path ex:flag ;
        sh:minCount 1 ;
        sh:message "Flag is required." ;
    ] .

ex:OtherShape
    a sh:NodeShape ;
    sh:targetClass ex:Other ;
    sh:property [
        sh:path ex:label ;
        sh:datatype xsd:string ;
        sh:message "Label must be a string." ;
    ] ;
    sh:property [
        sh:path ex:ref ;
        sh:maxCount 1 ;
        sh:message "Only one ref allowed." ;
    ] .
"""


def _run_validate_with_seed(seed: str) -> str:
    script = textwrap.dedent(
        f"""
        from rdflib import Graph
        from pyshacl import validate

        data = {DATA_TTL!r}
        shapes = {SHAPES_TTL!r}
        data_g = Graph().parse(data=data, format="turtle")
        shapes_g = Graph().parse(data=shapes, format="turtle")
        conforms, report_graph, results_text = validate(
            data_g,
            shacl_graph=shapes_g,
            advanced=False,
            debug=False,
        )
        print(results_text)
        """
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = seed
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout


def test_304():
    out_a = _run_validate_with_seed("1")
    out_b = _run_validate_with_seed("2")
    out_c = _run_validate_with_seed("3")
    assert "Results (" in out_a
    assert out_a == out_b
    assert out_a == out_c

if __name__ == "__main__":
    sys.exit(test_304())
