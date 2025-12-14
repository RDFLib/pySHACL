import subprocess
from rdflib import Graph
from pyshacl import validate

def test_jelly_api_valid(tmp_path):
    data_ttl = """
    @prefix ex: <http://example.org/> .
    ex:Alice ex:name "Alice" .
    """

    shapes_ttl = """
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix ex: <http://example.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ex:PersonShape a sh:NodeShape ;
        sh:targetClass ex:Alice ;
        sh:property [
            sh:path ex:name ;
            sh:datatype xsd:string ;
        ] .
    """

    # save ttl
    data_ttl_path = tmp_path / "data.ttl"
    shapes_ttl_path = tmp_path / "shapes.ttl"
    data_ttl_path.write_text(data_ttl)
    shapes_ttl_path.write_text(shapes_ttl)

    # convert to jelly
    g_data = Graph().parse(data_ttl_path)
    g_shapes = Graph().parse(shapes_ttl_path)
    data_jelly_path = tmp_path / "data.jelly"
    shapes_jelly_path = tmp_path / "shapes.jelly"
    g_data.serialize(data_jelly_path, format="jelly")
    g_shapes.serialize(shapes_jelly_path, format="jelly")

    # API validation
    conforms, report_graph, _ = validate(
        data_graph=g_data,
        shacl_graph=g_shapes,
        data_graph_format="jelly",
        shacl_graph_format="jelly",
    )

    assert conforms
    assert len(report_graph) > 0


def test_jelly_api_invalid(tmp_path):
    data_ttl = """
    @prefix ex: <http://example.org/> .
    ex:Bob ex:age "notANumber" .
    """

    shapes_ttl = """
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix ex: <http://example.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ex:PersonShape a sh:NodeShape ;
        sh:targetNode ex:Bob ;
        sh:property [
            sh:path ex:age ;
            sh:datatype xsd:integer ;
        ] .
    """

    data_ttl_path = tmp_path / "data.ttl"
    shapes_ttl_path = tmp_path / "shapes.ttl"
    data_ttl_path.write_text(data_ttl)
    shapes_ttl_path.write_text(shapes_ttl)

    g_data = Graph().parse(data_ttl_path)
    g_shapes = Graph().parse(shapes_ttl_path)
    data_jelly_path = tmp_path / "data.jelly"
    shapes_jelly_path = tmp_path / "shapes.jelly"
    g_data.serialize(data_jelly_path, format="jelly")
    g_shapes.serialize(shapes_jelly_path, format="jelly")

    conforms, report_graph, _ = validate(
        data_graph=g_data,
        shacl_graph=g_shapes,
        data_graph_format="jelly",
        shacl_graph_format="jelly",
    )

    assert not conforms
    assert len(report_graph) > 0


def test_jelly_cli_valid(tmp_path):
    data_ttl = "@prefix ex: <http://example.org/> . ex:X ex:name \"X\" ."
    shapes_ttl = """
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix ex: <http://example.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ex:Shape a sh:NodeShape ;
        sh:targetClass ex:X ;
        sh:property [
            sh:path ex:name ;
            sh:datatype xsd:string ;
        ] .
    """

    data_ttl_path = tmp_path / "d.ttl"
    shapes_ttl_path = tmp_path / "s.ttl"
    data_ttl_path.write_text(data_ttl)
    shapes_ttl_path.write_text(shapes_ttl)

    g_data = Graph().parse(data_ttl_path)
    g_shapes = Graph().parse(shapes_ttl_path)

    data_jelly = tmp_path / "d.jelly"
    shapes_jelly = tmp_path / "s.jelly"
    g_data.serialize(data_jelly, format="jelly")
    g_shapes.serialize(shapes_jelly, format="jelly")

    # run CLI
    result = subprocess.run(
        [
            "pyshacl",
            str(data_jelly),
            "-s", str(shapes_jelly),
            "-df", "jelly",
            "-sf", "jelly"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    assert result.returncode == 0
    assert "Conforms: True" in result.stdout
