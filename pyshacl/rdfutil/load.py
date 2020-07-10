# -*- coding: utf-8 -*-
#
import platform

from io import BytesIO, IOBase, UnsupportedOperation
from pathlib import Path
from typing import BinaryIO, List, Optional, Union
from urllib import request
from urllib.error import HTTPError

import rdflib

from pyshacl.pytypes import GraphLike


try:
    import rdflib_jsonld  # noqa: F401

    has_json_ld = True
except IndexError:
    has_json_ld = False

is_windows = platform.system() == "Windows"


def get_rdf_from_web(url: Union[rdflib.URIRef, str]):
    """

    :param url:
    :type url: rdflib.URIRef | str
    :return:
    """
    headers = {
        'Accept': 'text/turtle, application/rdf+xml, ' 'application/ld+json, application/n-triples,' 'text/plain'
    }
    r = request.Request(url, headers=headers)
    resp = request.urlopen(r)
    code = resp.getcode()
    if not (200 <= code <= 210):
        raise RuntimeError("Cannot pull RDF URL from the web: {}, code: {}".format(url, str(code)))
    known_format = None
    content_type = resp.headers.get('Content-Type', None)
    if content_type:
        if content_type.startswith("text/turtle"):
            known_format = "turtle"
        elif content_type.startswith("application/rdf+xml"):
            known_format = "xml"
        elif content_type.startswith("application/xml"):
            known_format = "xml"
        elif content_type.startswith("application/ld+json"):
            known_format = "json-ld"
        elif content_type.startswith("application/n-triples"):
            known_format = "nt"
    return resp, known_format


def load_from_source(
    source: Union[GraphLike, BinaryIO, Union[str, bytes]],
    g: Optional[GraphLike] = None,
    rdf_format: Optional[str] = None,
    multigraph: bool = False,
    do_owl_imports: Union[bool, int] = False,
    import_chain: Optional[List[Union[rdflib.URIRef, str]]] = None,
):
    """

    :param source:
    :param g:
    :type g: rdflib.Graph
    :param rdf_format:
    :type rdf_format: str
    :param multigraph:
    :type multigraph: bool
    :param do_owl_imports:
    :type do_owl_imports: bool|int
    :param import_chain:
    :type import_chain: list | None
    :return:
    """
    source_is_graph = False
    source_is_open = False
    source_was_open = False
    source_is_file = False
    source_is_bytes = False
    filename = None
    public_id = None
    uri_prefix = None
    is_imported_graph = do_owl_imports and isinstance(do_owl_imports, int) and do_owl_imports > 1
    if isinstance(source, (rdflib.Graph, rdflib.ConjunctiveGraph, rdflib.Dataset)):
        source_is_graph = True
        if g is None:
            g = source
        else:
            raise RuntimeError("Cannot pass in both target=rdflib.Graph/Dataset and g=graph.")
    elif isinstance(source, IOBase):
        source_is_file = True
        if hasattr(source, 'closed'):
            source_is_open = not bool(source.closed)
            source_was_open = source_is_open
        else:
            # Assume it is open now and it was open when we started.
            source_is_open = True
            source_was_open = True
        if hasattr(source, 'name'):
            filename = source.name  # type: ignore
            public_id = Path(filename).resolve().as_uri() + "#"
    elif isinstance(source, str):
        if is_windows and source.startswith('file:///'):
            public_id = source
            source_is_file = True
            filename = source[8:]
        elif not is_windows and source.startswith('file://'):
            public_id = source
            source_is_file = True
            filename = source[7:]
        elif source.startswith('http:') or source.startswith('https:'):
            public_id = source
            try:
                resp, rdf_format = get_rdf_from_web(source)
            except HTTPError:
                if is_imported_graph:
                    return g
                else:
                    raise
            filename = resp.geturl()
            source = resp.fp
            source_was_open = False
            source_is_open = True
        else:
            first_char = source[0]
            if is_windows and (first_char == '\\' or (len(source) > 3 and source[1:3] == ":\\")):
                source_is_file = True
                filename = source
            elif first_char == '/' or source[0:3] == "./":
                source_is_file = True
                filename = source
            elif (
                first_char == '#'
                or first_char == '@'
                or first_char == '<'
                or first_char == '\n'
                or first_char == '{'
                or first_char == '['
            ):
                # Contains some JSON or XML or Turtle stuff
                source_is_file = False
            elif len(source) < 140:
                source_is_file = True
                filename = source
        # TODO: Do we still need this? Not sure why this was added, but works better without it
        #  if public_id and not public_id.endswith('#'):
        #     public_id = "{}#".format(public_id)
        if not source_is_file and not source_is_open and isinstance(source, str):
            # source is raw RDF data.
            source = source.encode('utf-8')
            source_is_bytes = True
    elif isinstance(source, bytes):
        if source.startswith(b'file:') or source.startswith(b'http:') or source.startswith(b'https:'):
            raise ValueError("file:// and http:// strings should be given as str, not bytes.")
        first_char_b: bytes = source[0:1]
        if (
            first_char_b == b'#'
            or first_char_b == b'@'
            or first_char_b == b'<'
            or first_char_b == b'\n'
            or first_char_b == b'{'
            or first_char_b == b'['
        ):
            # Contains some JSON or XML or Turtle stuff
            source_is_file = False
        elif len(source) < 140:
            filename = source.decode('utf-8')
            source_is_file = True
        if not source_is_file and not source_is_open:
            source_is_bytes = True
    else:
        raise ValueError("Cannot determine the format of the input graph")
    if g is None:
        g = rdflib.Dataset() if multigraph else rdflib.Graph()
    else:
        if not isinstance(g, (rdflib.Graph, rdflib.Dataset, rdflib.ConjunctiveGraph)):
            raise RuntimeError("Passing in g must be a Graph.")
    if filename:
        if filename.endswith('.ttl'):
            rdf_format = rdf_format or 'turtle'
        elif filename.endswith('.nt'):
            rdf_format = rdf_format or 'nt'
        elif filename.endswith('.n3'):
            rdf_format = rdf_format or 'n3'
        elif filename.endswith('.json'):
            rdf_format = rdf_format or 'json-ld'
        elif filename.endswith('.nq') or filename.endswith('.nquads'):
            rdf_format = rdf_format or 'nquads'
        elif filename.endswith('.trig'):
            rdf_format = rdf_format or 'trig'
        elif filename.endswith('.xml') or filename.endswith('.rdf'):
            rdf_format = rdf_format or 'xml'
    if source_is_file and filename is not None and not source_is_open:
        filename = str(Path(filename).resolve())
        if not public_id:
            public_id = Path(filename).as_uri() + "#"
        source = open(filename, mode='rb')
        source_is_open = True
    if not source_is_open and source_is_bytes:
        source = BytesIO(source)
        source_is_open = True
    if source_is_open:
        # Check if we can seek
        try:
            source.seek(0)
        except (AttributeError, UnsupportedOperation):
            # Read it all into memory
            new_bytes = BytesIO(source.read())
            if not source_was_open:
                source.close()
            source = new_bytes
            source_was_open = False
        if (rdf_format == "json-ld" or rdf_format == "json") and not has_json_ld:
            raise RuntimeError("Cannot load a JSON-LD file if rdflib_jsonld is not installed.")
        if rdf_format == 'turtle' or rdf_format == 'n3':
            # SHACL Shapes files and Data files can have extra RDF Metadata in the
            # Top header block, including #BaseURI and #Prefix.
            # The @base line is not read here, but it is parsed in the n3 parser
            while True:
                try:
                    line = source.readline()
                    assert line is not None and len(line) > 0
                except AssertionError:
                    break
                # Strip line from start
                while len(line) > 0 and line[0:1] in b' \t\n\r\x0B\x0C\x85\xA0':
                    line = line[1:]
                # We reached the end of the line, check the next line
                if len(line) < 1:
                    continue
                # If this is not a comment, then this is the first non-comment line, we're done.
                if not line[0:1] == b'#':
                    break
                # Strip from start again, but now removing hashes too.
                while len(line) > 0 and line[0:1] in b'# \t\xA0':
                    line = line[1:]
                # Strip line from end
                while len(line) > 0 and line[-1:] in b' \t\n\r\x0B\x0C\x85\xA0':
                    line = line[:-1]
                spl = line.split(b':', 1)
                if len(spl) < 2:
                    continue
                keyword = spl[0].lower()
                # Strip keyword end
                while len(keyword) > 0 and keyword[-1:] in b' \t\n\r\x0B\x0C\x85\xA0':
                    keyword = keyword[:-1]
                if len(keyword) < 1:
                    continue
                wordval = spl[1]
                # Strip wordval start
                while len(wordval) > 0 and wordval[0:1] in b' \t\n\r\x0B\x0C\x85\xA0':
                    wordval = wordval[1:]
                if len(wordval) < 1:
                    continue
                wordval = wordval.decode('utf-8')
                if keyword == b"baseuri":
                    public_id = wordval
                elif keyword == b"prefix":
                    uri_prefix = wordval
            try:
                source.seek(0)
            except (AttributeError, UnsupportedOperation):
                print("here")
                raise
        g.parse(source=source, format=rdf_format, publicID=public_id)
        # If the target was open to begin with, leave it open.
        if not source_was_open:
            source.close()
        elif hasattr(source, 'seek'):
            try:
                source.seek(0)
            except (AttributeError, UnsupportedOperation):
                pass
        source_is_graph = True

    if not source_is_graph:
        raise RuntimeError("Error opening graph from source.")

    if public_id:
        if uri_prefix:
            if is_imported_graph and uri_prefix == '':
                # Don't reassign blank prefix, when importing subgraph
                pass
            else:
                has_named_prefix = g.store.namespace(uri_prefix)
                if not has_named_prefix:
                    g.namespace_manager.bind(uri_prefix, public_id)
        elif not is_imported_graph:
            existing_blank_prefix = g.store.namespace('')
            if not existing_blank_prefix:
                g.namespace_manager.bind('', public_id)
    if do_owl_imports:
        if isinstance(do_owl_imports, int):
            if do_owl_imports > 3:
                return g
        else:
            do_owl_imports = 1

        if import_chain is None:
            import_chain = []
        if public_id and (public_id.endswith('#') or public_id.endswith('/')):
            root_id = rdflib.URIRef(public_id[:-1])
        else:
            root_id = rdflib.URIRef(public_id) if public_id else None
        done_imports = 0
        if root_id is not None:
            if isinstance(g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(g.contexts())
            else:
                gs = [g]
            for ng in gs:
                owl_imports = list(ng.objects(root_id, rdflib.OWL.imports))
                if len(owl_imports) > 0:
                    import_chain.append(root_id)
                for o in owl_imports:
                    if o in import_chain:
                        continue
                    load_from_source(
                        o, g=g, multigraph=multigraph, do_owl_imports=do_owl_imports + 1, import_chain=import_chain
                    )
                    done_imports += 1
        if done_imports < 1 and public_id is not None and root_id != public_id:
            public_id_uri = rdflib.URIRef(public_id)
            if isinstance(g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(g.contexts())
            else:
                gs = [g]
            for ng in gs:
                owl_imports = list(ng.objects(public_id_uri, rdflib.OWL.imports))
                if len(owl_imports) > 0:
                    import_chain.append(public_id_uri)
                for o in owl_imports:
                    if o in import_chain:
                        continue
                    load_from_source(
                        o, g=g, multigraph=multigraph, do_owl_imports=do_owl_imports + 1, import_chain=import_chain
                    )
                    done_imports += 1
        if done_imports < 1:
            if isinstance(g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(g.contexts())
            else:
                gs = [g]
            for ng in gs:
                ontologies = ng.subjects(rdflib.RDF.type, rdflib.OWL.Ontology)
                for ont in ontologies:
                    if ont == root_id or ont == public_id:
                        continue
                    if ont in import_chain:
                        continue
                    owl_imports = list(ng.objects(ont, rdflib.OWL.imports))
                    if len(owl_imports) > 0:
                        import_chain.append(ont)
                    for o in owl_imports:
                        if o in import_chain:
                            continue
                        load_from_source(
                            o, g=g, multigraph=multigraph, do_owl_imports=do_owl_imports + 1, import_chain=import_chain
                        )
                        done_imports += 1
    return g
