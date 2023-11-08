# -*- coding: utf-8 -*-
#
import http.client
import os
import pickle
import platform
import sys
from io import BufferedIOBase, BytesIO, TextIOBase, UnsupportedOperation
from logging import WARNING, Logger, getLogger
from pathlib import Path
from typing import IO, BinaryIO, List, Optional, Union, cast
from urllib import request
from urllib.error import HTTPError

import rdflib
from rdflib.namespace import NamespaceManager

from .clone import clone_dataset, clone_graph

ConjunctiveLike = Union[rdflib.ConjunctiveGraph, rdflib.Dataset]
GraphLike = Union[ConjunctiveLike, rdflib.Graph]

is_windows = platform.system() == "Windows"
MAX_OWL_IMPORT_DEPTH = 3
baked_in = {}


def add_baked_in(url, graph_path):
    baked_in[url] = graph_path


def get_rdf_from_web(url: Union[rdflib.URIRef, str]):
    """

    :param url:
    :type url: rdflib.URIRef | str
    :return:
    """
    no_hash_url: str = str(url).rstrip("#")
    if no_hash_url in baked_in:
        g = baked_in[no_hash_url]
        if isinstance(g, str):
            if g[-7:] == ".pickle":
                with open(g, 'rb') as g_pickle:
                    u = pickle.Unpickler(g_pickle, fix_imports=False)
                    g_store, identifier = u.load()
                graph = rdflib.Graph(store=g_store, identifier=identifier)
                kind = "graph"
            else:
                graph = rdflib.Graph()
                graph.parse(g)
                kind = None
        else:
            graph = g
            kind = None
        return graph, None, kind, False

    # Ask for everything we know about
    headers = {
        'Accept': 'text/turtle, application/rdf+xml, application/ld+json, application/n-triples, text/plain',
        'Accept-Encoding': 'identity',
    }
    known_format = None

    r: request.Request = request.Request(url, headers=headers)
    resp: http.client.HTTPResponse = request.urlopen(r)
    code: int = resp.getcode()
    if not (200 <= code <= 210):
        raise RuntimeError("Cannot pull RDF URL from the web: {}, code: {}".format(url, str(code)))

    filename = None
    content_dispositions: List[str] = resp.headers.get_all("Content-Disposition", [])
    for c_d in content_dispositions:
        cd_parts = [s.strip() for s in str(c_d).split(',')]
        for cd_part in cd_parts:
            if "filename=" in cd_part:
                filename = [f.strip() for f in str(cd_part).rsplit('filename=')][-1]
    if filename is None:
        try:
            filename = resp.geturl()
        except Exception:
            pass

    content_types: List[str] = resp.headers.get_all('Content-Type', [])
    for content_type in content_types:
        ct_parts = [s.strip() for s in str(content_type).split(',')]
        for ct_part in ct_parts:
            if ct_part.startswith("application/octet-stream"):
                known_format = 'auto'
            elif ct_part.startswith("text/turtle"):
                known_format = "turtle"
            elif ct_part.startswith("application/rdf+xml"):
                known_format = "xml"
            elif ct_part.startswith("application/xml"):
                known_format = "xml"
            elif ct_part.startswith("application/ld+json"):
                known_format = "json-ld"
            elif ct_part.startswith("application/n-triples"):
                known_format = "nt"
            else:
                continue
            break

    transfer_encodings: List[str] = resp.headers.get_all('Transfer-Encoding', [])
    for t_e in transfer_encodings:
        te_parts = [s.strip() for s in str(t_e).split(',')]
        for check in ('chunked', 'compress', 'deflate', 'gzip', 'x-gzip'):
            if check in te_parts:
                return resp, filename, known_format, False

    return resp, filename, known_format, True


def load_from_source(
    source: Union[GraphLike, BufferedIOBase, TextIOBase, BinaryIO, Union[str, bytes]],
    g: Optional[GraphLike] = None,
    rdf_format: Optional[str] = None,
    multigraph: bool = False,
    do_owl_imports: Union[bool, int] = False,
    import_chain: Optional[List[Union[rdflib.URIRef, str]]] = None,
    logger: Optional[Logger] = None,
):
    """

    :param source:
    :param g:
    :type g: rdflib.Graph | None
    :param rdf_format:
    :type rdf_format: str | None
    :param multigraph:
    :type multigraph: bool
    :param do_owl_imports:
    :type do_owl_imports: bool|int
    :param import_chain:
    :type import_chain: list | None
    :param logger:
    :type logger: Logger | None
    :return:
    """
    source_is_graph = False
    open_source: Optional[Union[BufferedIOBase, BinaryIO]] = None
    source_was_open: bool = False
    source_as_file: Optional[Union[BufferedIOBase, BinaryIO]] = None
    source_as_filename: Optional[str] = None
    source_as_bytes: Optional[bytes] = None
    filename = None
    public_id = None
    uri_prefix = None
    if logger is None:
        logger = getLogger("rdfutil.load")
        logger.setLevel(WARNING)
    is_imported_graph = do_owl_imports and isinstance(do_owl_imports, int) and do_owl_imports > 1
    if isinstance(source, (rdflib.Graph, rdflib.ConjunctiveGraph, rdflib.Dataset)):
        source_is_graph = True
        if g is None:
            g = source
        else:
            raise RuntimeError("Cannot pass in both target=rdflib.Graph/Dataset and g=graph.")
    elif isinstance(source, (BufferedIOBase, TextIOBase)):
        if hasattr(source, 'name'):
            filename = source.name  # type: ignore
            public_id = Path(filename).resolve().as_uri() + "#"
        if isinstance(source, TextIOBase):
            buf = getattr(source, "buffer")  # type: BufferedIOBase
            source_as_file = source = buf
        else:
            source_as_file = source
        if hasattr(source, 'closed'):
            if not bool(source.closed):
                open_source = source
                source_was_open = True
        else:
            # Assume it is open now and it was open when we started.
            open_source = source
            source_was_open = True

    elif isinstance(source, str):
        if source == "stdin" or source == "-" or source == "/dev/stdin":
            public_id = "/dev/stdin"
            filename = "/dev/stdin"
            source_as_filename = filename
        elif is_windows and source.startswith('file:///'):
            public_id = source
            filename = source[8:]
            source_as_filename = filename
        elif not is_windows and source.startswith('file://'):
            public_id = source
            filename = source[7:]
            source_as_filename = filename
        elif source.startswith('http:') or source.startswith('https:'):
            public_id = source
            try:
                resp, resp_filename, web_format, raw_fp = get_rdf_from_web(source)
            except HTTPError:
                if is_imported_graph:
                    return g
                else:
                    raise
            if web_format == 'graph':
                source = resp
                source_is_graph = True
            elif web_format in ('auto', None):
                if resp_filename:
                    filename = resp_filename
                source_was_open = False
                source = open_source = resp
            else:
                rdf_format = web_format
                filename = resp_filename
                fp = resp.fp if raw_fp else resp
                source_was_open = False
                source = open_source = fp
        else:
            first_char = source[0]
            if is_windows and (first_char == '\\' or (len(source) > 3 and source[1:3] == ":\\")):
                filename = source
                source_as_filename = filename
            elif first_char == '/' or (len(source) > 2 and source[0:2] == "./"):
                filename = source
                source_as_filename = filename
            elif (
                first_char == '#'
                or first_char == '@'
                or first_char == '<'
                or first_char == '\n'
                or first_char == '{'
                or first_char == '['
            ):
                # Contains some JSON or XML or Turtle chars, it's not a path
                source_as_file = None
                source_as_filename = None
            elif len(source) >= 32 and '\n' in source[:32]:
                # Contains a new line near the start of the file, can't be a path
                source_as_file = None
                source_as_filename = None
            elif len(source) < 140:
                filename = source
                source_as_filename = filename
        if source_as_filename and filename:
            pid = os.getpid()
            fd0 = "/proc/{}/fd/0".format(str(pid))
            if filename == "/dev/stdin" or filename == fd0:
                source = source_as_file = open_source = sys.stdin.buffer
                source_was_open = True
            else:
                try:
                    filename = os.readlink(filename)
                    if filename == fd0 or filename == "/dev/stdin":
                        source = source_as_file = open_source = sys.stdin.buffer
                        source_was_open = True
                except OSError:
                    pass
        # TODO: Do we still need this? Not sure why this was added, but works better without it
        #  if public_id and not public_id.endswith('#'):
        #     public_id = "{}#".format(public_id)
        if not source_as_file and not source_as_filename and not open_source and isinstance(source, str):
            # source is raw RDF data.
            source_as_bytes = source = source.encode('utf-8')
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
            source_as_file = None
            source_as_filename = None
        elif len(source) < 140:
            filename = source.decode('utf-8')
            source_as_filename = filename
        if not source_as_file and not source_as_filename and not open_source:
            source_as_bytes = source
    else:
        raise ValueError("Cannot determine the format of the input graph")
    if g is None:
        if source_is_graph:
            target_g: Union[rdflib.Graph, rdflib.ConjunctiveGraph, rdflib.Dataset] = source  # type: ignore
        else:
            if multigraph:
                target_ds = rdflib.Dataset(default_graph_base=public_id)
                target_ds.namespace_manager = NamespaceManager(target_ds, 'core')
                target_ds.default_context.namespace_manager = target_ds.namespace_manager
                default_g = target_ds.default_context
                target_ds.graph(default_g)
                target_g = target_ds
            else:
                target_g = rdflib.Graph(bind_namespaces='core')
    else:
        if not isinstance(g, (rdflib.Graph, rdflib.Dataset, rdflib.ConjunctiveGraph)):
            raise RuntimeError("Passing in 'g' must be a rdflib Graph or Dataset.")
        target_g = g

    if filename and not rdf_format:
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
    if source_as_filename and filename is not None and not open_source:
        filename = str(Path(filename).resolve())
        if not public_id:
            public_id = Path(filename).as_uri() + "#"
        source = open_source = open(filename, mode='rb')
    if not open_source and source_as_bytes:
        source = open_source = BytesIO(source_as_bytes)  # type: ignore
    if open_source:
        _source = open_source
        # Check if we can seek
        try:
            _source.seek(0)  # type: ignore
        except (AttributeError, ValueError, UnsupportedOperation):
            # Read it all into memory
            new_bytes = BytesIO(_source.read())
            if not source_was_open:
                _source.close()
            source = _source = new_bytes
            source_was_open = False
        if rdf_format is None:
            line = _source.readline().lstrip()
            line_len = len(line) if line is not None else 0
            while (
                (line is not None and line_len == 0)
                or (line_len == 1 and line[0] == "\n")
                or (line_len == 2 and line[0:2] == "\r\n")
            ):
                line = _source.readline().lstrip()
                line_len = len(line) if line is not None else 0
            if line_len > 15:
                line = line[:15]
            line = line.lower()
            if line.startswith(b"<!doctype html") or line.startswith(b"<html"):
                raise RuntimeError("Attempted to load a HTML document as RDF.")
            if line.startswith(b"<?xml") or line.startswith(b"<xml") or line.startswith(b"<rdf:"):
                rdf_format = "xml"
            if line.startswith(b"@base ") or line.startswith(b"@prefix ") or line.startswith(b"PREFIX "):
                rdf_format = "turtle"
            try:
                _source.seek(0)
            except (AttributeError, UnsupportedOperation):
                raise RuntimeError("Seek failed while identifying file type.")
            except ValueError:
                raise RuntimeError("File closed while identifying file type.")
        if rdf_format == 'turtle' or rdf_format == 'n3':
            # SHACL Shapes files and Data files can have extra RDF Metadata in the
            # Top header block, including #BaseURI and #Prefix.
            # The @base line is not read here, but it is parsed in the n3 parser
            while True:
                try:
                    line = _source.readline()
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
                wordval_str = wordval.decode('utf-8')
                if keyword == b"baseuri":
                    public_id = wordval_str
                elif keyword == b"prefix":
                    uri_prefix = wordval_str
            try:
                _source.seek(0)
            except (AttributeError, UnsupportedOperation):
                raise RuntimeError("Seek failed while pre-parsing Turtle File.")
            except ValueError:
                raise RuntimeError("File closed while pre-parsing Turtle File.")
        if isinstance(target_g, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            default_g = target_g.default_context
            default_g.base = public_id
            default_g.parse(source=cast(IO[bytes], _source), format=rdf_format, publicID=public_id)
        else:
            target_g.parse(source=cast(IO[bytes], _source), format=rdf_format, publicID=public_id)
        # If the target was open to begin with, leave it open.
        if not source_was_open:
            _source.close()
        elif hasattr(_source, 'seek'):
            try:
                _source.seek(0)
            except (AttributeError, UnsupportedOperation):
                pass
            except ValueError:
                # The parser closed our file!
                pass
        source_is_graph = True
    elif source_is_graph and (target_g != source):
        # clone source into g
        if isinstance(target_g, (rdflib.Dataset, rdflib.ConjunctiveGraph)) and isinstance(
            source, (rdflib.Dataset, rdflib.ConjunctiveGraph)
        ):
            clone_dataset(source, target_g)
        elif isinstance(target_g, rdflib.Graph) and isinstance(source, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            raise RuntimeError("Cannot load a Dataset source into a Graph target.")
        elif isinstance(target_g, (rdflib.Dataset, rdflib.ConjunctiveGraph)) and isinstance(source, rdflib.Graph):
            _temp_target = rdflib.Graph(store=target_g.store, identifier=public_id)
            clone_graph(source, _temp_target)
        elif isinstance(target_g, rdflib.Graph) and isinstance(source, rdflib.Graph):
            clone_graph(source, target_g)
        else:
            raise RuntimeError("Cannot merge source graph into target graph.")

    if not source_is_graph:
        raise RuntimeError("Error opening graph from source.")

    if public_id:
        if uri_prefix:
            if is_imported_graph and uri_prefix == '':
                # Don't reassign blank prefix, when importing subgraph
                pass
            else:
                has_named_prefix = target_g.store.namespace(uri_prefix)
                if not has_named_prefix:
                    target_g.namespace_manager.bind(uri_prefix, public_id)
        elif not is_imported_graph:
            existing_blank_prefix = target_g.store.namespace('')
            if not existing_blank_prefix:
                target_g.namespace_manager.bind('', public_id)
    if do_owl_imports:
        if isinstance(do_owl_imports, int):
            if do_owl_imports > MAX_OWL_IMPORT_DEPTH:
                return target_g
        else:
            do_owl_imports = 1

        if import_chain is None:
            import_chain = []
        if public_id and (public_id.endswith('#') or public_id.endswith('/')):
            root_id: Union[rdflib.URIRef, None] = rdflib.URIRef(public_id[:-1])
        else:
            root_id = rdflib.URIRef(public_id) if public_id else None
        done_imports = 0
        if root_id is not None:
            if isinstance(target_g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(target_g.contexts())
            else:
                gs = [target_g]
            for ng in gs:
                owl_imports = list(ng.objects(root_id, rdflib.OWL.imports))
                if len(owl_imports) > 0:
                    import_chain.append(str(root_id))
                for i in owl_imports:
                    imp_str = str(i)
                    if imp_str in import_chain:
                        continue
                    load_from_source(
                        imp_str,
                        g=target_g,
                        multigraph=multigraph,
                        do_owl_imports=do_owl_imports + 1,
                        import_chain=import_chain,
                    )
                    done_imports += 1
        if done_imports < 1 and public_id is not None and root_id != public_id:
            public_id_uri = rdflib.URIRef(public_id)
            if isinstance(target_g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(target_g.contexts())
            else:
                gs = [target_g]
            for ng in gs:
                owl_imports = list(ng.objects(public_id_uri, rdflib.OWL.imports))
                if len(owl_imports) > 0:
                    import_chain.append(str(public_id_uri))
                for i in owl_imports:
                    imp_str = str(i)
                    if imp_str in import_chain:
                        continue
                    load_from_source(
                        imp_str,
                        g=target_g,
                        multigraph=multigraph,
                        do_owl_imports=do_owl_imports + 1,
                        import_chain=import_chain,
                    )
                    done_imports += 1
        if done_imports < 1:
            if isinstance(target_g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
                gs = list(target_g.contexts())
            else:
                gs = [target_g]
            for ng in gs:
                ontologies = ng.subjects(rdflib.RDF.type, rdflib.OWL.Ontology)
                for ont in ontologies:
                    if ont == root_id or ont == public_id:
                        continue
                    ont_str = str(ont)
                    if ont_str in import_chain:
                        continue
                    import_chain.append(ont_str)
                    owl_imports = list(ng.objects(ont, rdflib.OWL.imports))
                    for i in owl_imports:
                        imp_str = str(i)
                        if imp_str in import_chain:
                            continue
                        load_from_source(
                            imp_str,
                            g=target_g,
                            multigraph=multigraph,
                            do_owl_imports=do_owl_imports + 1,
                            import_chain=import_chain,
                        )
                        done_imports += 1
    return target_g
