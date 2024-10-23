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
from typing import IO, List, Optional, Union, cast
from urllib import request
from urllib.error import HTTPError

import rdflib
from rdflib.namespace import SDO, NamespaceManager

from .clone import clone_dataset, clone_graph

SCHEMA = SDO

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
    kind: Optional[str]
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


# What's the difference between PublicID and BaseURI?
# The BaseURI is a part of Turtle and SPARQL spec, it is used to resolve relative URIs.
# The BaseURI usually ends with a filename (eg, https://example.com/validators/shapes)
# BaseURI can sometimes end with a / if URIs are relative to a directory.
# You will rarely see a BaseURI with a # on the end.
# The PublicID is the Identifier of a Graph. It is the canonical name of the graph,
# regardless of its hosted location. It is used to refer to the graph in a Dataset
# and this is the name referenced in the owl:imports [ schema:name <publicID> ] statement.
# PublicID is not found in the Turtle file, it is known outside the file only.
# PublicID can end with a / or a # if you want consistency with the graph's base prefix.
# Alternatively, PublicID may not have a symbol at the end.


def load_from_source(
    source: Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes],
    g: Optional[GraphLike] = None,
    rdf_format: Optional[str] = None,
    identifier: Optional[str] = None,
    multigraph: bool = False,
    do_owl_imports: Union[bool, int] = False,
    import_chain: Optional[List[Union[rdflib.URIRef, str]]] = None,
    logger: Optional[Logger] = None,
):
    """

    :param source:
    :param g: The Graph to load into, optional. If not given, a new Dataset or Graph will be created.
    :type g: rdflib.Graph | None
    :param rdf_format:
    :type rdf_format: str | None
    :param multigraph:
    :type multigraph: bool
    :param identifier: formerly "public_id"
    :type identifier: str | None
    :param do_owl_imports:
    :type do_owl_imports: bool|int
    :param import_chain:
    :type import_chain: list | None
    :param logger:
    :type logger: Logger | None
    :return:
    """
    source_is_graph = False
    open_source: Optional[BufferedIOBase] = None
    source_was_open: bool = False
    source_as_file: Optional[BufferedIOBase] = None
    source_as_filename: Optional[str] = None
    source_as_bytes: Optional[bytes] = None
    filename = None
    identifier = str(identifier)  # This is our passed-in id (formerly public_id)
    _maybe_id: Optional[str] = None  # For default-graph identifier
    base_uri: Optional[str] = None  # Base URI for relative URIs
    uri_prefix = None  # URI Prefix to bind to public ID
    if logger is None:
        logger = getLogger("rdfutil.load")
        logger.setLevel(WARNING)
    is_imported_graph = do_owl_imports and isinstance(do_owl_imports, int) and do_owl_imports > 1
    if isinstance(source, (rdflib.Graph, rdflib.ConjunctiveGraph, rdflib.Dataset)):
        source_is_graph = True
        if g is None:
            g = source
        else:
            raise RuntimeError(
                "Cannot pass in both source=rdflib.Graph/Dataset and g=graph."
                "Source and dest cannot be the same graph."
            )
    elif isinstance(source, (BufferedIOBase, TextIOBase)):
        if hasattr(source, 'name'):
            filename = source.name  # type: ignore
            file_uri = Path(filename).resolve().as_uri()
            _maybe_id = file_uri
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
            _maybe_id = "/dev/stdin"
            # Don't set base_uri, it is not used for /dev/stdin
            filename = "/dev/stdin"
            source_as_filename = filename
        elif is_windows and source.startswith('file:///'):
            # A local file name cannot end with # or with /, so
            # identifier always has no symbol at the end.
            _maybe_id = source
            filename = source[8:]
            source_as_filename = filename
        elif not is_windows and source.startswith('file://'):
            _maybe_id = source  # See local file comment above
            filename = source[7:]
            source_as_filename = filename
        elif source.startswith('http:') or source.startswith('https:'):
            # It can be tricky to guess public_id from a web URL.
            # In this case we will always simply use the URL as the public_id as given.
            _maybe_id = source
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
                source = source_as_file = open_source = cast(BufferedIOBase, sys.stdin.buffer)
                source_was_open = True
            else:
                try:
                    filename = os.readlink(filename)
                    if filename == fd0 or filename == "/dev/stdin":
                        source = source_as_file = open_source = cast(BufferedIOBase, sys.stdin.buffer)
                        source_was_open = True
                except OSError:
                    pass

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
            default_graph_base: Union[str, None] = identifier if identifier else None
            if multigraph:
                target_ds = rdflib.Dataset(default_graph_base=default_graph_base, default_union=True)
                target_ds.namespace_manager = NamespaceManager(target_ds, 'core')
                if identifier:  # if identifier is explicitly given, use that as a new named graph id
                    old_default_context = target_ds.default_context
                    named_g = target_ds.graph(default_graph_base)
                    named_g.base = default_graph_base
                    target_ds.default_context = named_g
                    target_ds.remove_graph(old_default_context)
                else:
                    target_ds.default_context.namespace_manager = target_ds.namespace_manager
                    default_g = target_ds.default_context
                    target_ds.graph(default_g)
                target_g = target_ds
            else:
                target_g = rdflib.Graph(bind_namespaces='core', base=default_graph_base)
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
        elif filename.endswith('.hext'):
            rdf_format = rdf_format or 'hext'
    if source_as_filename and filename is not None and not open_source:
        filename = str(Path(filename).resolve())
        if not _maybe_id:
            _maybe_id = Path(filename).as_uri()
        source = open_source = cast(BufferedIOBase, open(filename, mode='rb'))
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
            line: Union[bytes, None] = _source.readline()
            line = None if line is None else line.lstrip()
            line_len: int = len(line) if line is not None else 0
            while line is not None and line_len == 0:
                line = _source.readline()
                line = None if line is None else line.lstrip()
                line_len = len(line) if line is not None else 0
            if line is not None:
                if line_len > 15:
                    line = line[:15]
                line = line.lower()
                if line.startswith(b"<!doctype html") or line.startswith(b"<html"):
                    raise RuntimeError("Attempted to load a HTML document as RDF.")
                if line.startswith(b"<?xml") or line.startswith(b"<xml") or line.startswith(b"<rdf:"):
                    rdf_format = "xml"
                if (
                    line.startswith(b"@prefix ")
                    or line.startswith(b"PREFIX ")
                    or line.startswith(b"@base ")
                    or line.startswith(b"# baseURI:")
                ):
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
                if keyword == b"baseuri" or keyword == b"base":  # BASE is the SPARQL version of BaseURI
                    base_uri = wordval_str
                elif keyword == b"prefix":
                    uri_prefix = wordval_str
            try:
                _source.seek(0)
            except (AttributeError, UnsupportedOperation):
                raise RuntimeError("Seek failed while pre-parsing Turtle File.")
            except ValueError:
                raise RuntimeError("File closed while pre-parsing Turtle File.")

        # use base_uri if it is set, otherwise use identifier or _maybe_id
        use_base_uri = base_uri if base_uri else (identifier if identifier else _maybe_id)
        if isinstance(target_g, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            if identifier:
                dest_g = target_g.get_context(identifier)
                dest_g.base = use_base_uri
            else:
                dest_g = target_g.default_context
                dest_g.base = use_base_uri
            # parsing uses base_uri as the public_id, because it is used for relative URIs
            dest_g.parse(source=cast(IO[bytes], _source), format=rdf_format, publicID=use_base_uri)
        else:
            target_g.parse(source=cast(IO[bytes], _source), format=rdf_format, publicID=use_base_uri)
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
            _temp_target = rdflib.Graph(
                store=target_g.store,
                identifier=identifier,
                base=base_uri,
                namespace_manager=target_g.namespace_manager,
            )
            clone_graph(source, _temp_target)
        elif isinstance(target_g, rdflib.Graph) and isinstance(source, rdflib.Graph):
            clone_graph(source, target_g)
        else:
            raise RuntimeError("Cannot merge source graph into target graph.")

    if not source_is_graph:
        raise RuntimeError("Error opening graph from source.")

    if identifier:
        identifier_namespace = (
            identifier if (identifier.endswith('#') or identifier.endswith('/')) else identifier + "#"
        )
        if uri_prefix:
            if is_imported_graph and uri_prefix == '':
                # Don't reassign blank prefix, when importing subgraph
                pass
            else:
                has_named_prefix = target_g.store.namespace(uri_prefix)
                if not has_named_prefix:
                    target_g.namespace_manager.bind(uri_prefix, identifier_namespace)
        elif not is_imported_graph:
            existing_blank_prefix = target_g.store.namespace('')
            if not existing_blank_prefix:
                target_g.namespace_manager.bind('', identifier_namespace)
    if do_owl_imports:
        if isinstance(do_owl_imports, bool):
            do_owl_imports = 1 if do_owl_imports else 0
        elif isinstance(do_owl_imports, int):
            if do_owl_imports > MAX_OWL_IMPORT_DEPTH:
                return target_g
        else:
            do_owl_imports = 1

        if import_chain is None:
            import_chain = []
        return chain_load_owl_imports(identifier, target_g, import_chain, do_owl_imports, multigraph)
    return target_g


def chain_load_owl_imports(
    parent_id: Union[str, None],
    target_g: GraphLike,
    import_chain: List[Union[rdflib.URIRef, str]],
    load_iter: int,
    multigraph: bool,
) -> GraphLike:
    if parent_id and (parent_id.endswith('#') or parent_id.endswith('/')):
        root_id: Union[rdflib.URIRef, None] = rdflib.URIRef(parent_id[:-1])
    else:
        root_id = rdflib.URIRef(parent_id) if parent_id else None
    done_imports = 0

    def _load_from_imports_nodes(imports_nodes: List[Union[rdflib.URIRef, rdflib.BNode]]) -> int:
        nonlocal target_g, multigraph, import_chain, load_iter
        _done_imports = 0
        for _i in imports_nodes:
            import_with_identifier: Union[str, None] = None
            if isinstance(_i, rdflib.BNode):
                urls = list(target_g.objects(_i, SCHEMA.url))
                prioritized_urls = []  # Tuples of (priority, url_str)
                # Value of type variable "SupportsRichComparisonT" of "sorted" cannot be "Node"
                # Maybe we need to add "SupportsRichComparisonT" to Node in RDFLib?
                for url_i in sorted(urls):  # type: ignore[type-var]
                    url_str = str(url_i)
                    if url_str.startswith("file:"):
                        prioritized_urls.append((1, url_str))
                    else:
                        prioritized_urls.append((9, url_str))
                _prio, imp_str = sorted(prioritized_urls)[0]  # this causes the first (alphabetically) URL to be used
                use_identifiers = list(target_g.objects(_i, SCHEMA.identifier))
                if len(use_identifiers) > 0:
                    import_with_identifier = str(next(iter(use_identifiers)))
            else:
                imp_str = str(_i)
            if imp_str in import_chain:
                continue
            load_from_source(
                imp_str,
                g=target_g,
                identifier=import_with_identifier,
                multigraph=multigraph,
                do_owl_imports=load_iter + 1,
                import_chain=import_chain,
            )
            _done_imports += 1
        return _done_imports

    if isinstance(target_g, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        # Don't care about named graphs, search across the whole
        # thing at once.
        target_g.default_union = True

    if root_id is not None:
        owl_imports = list(target_g.objects(root_id, rdflib.OWL.imports))
        if len(owl_imports) > 0:
            import_chain.append(str(root_id))
            _done_imports = _load_from_imports_nodes(owl_imports)  # type: ignore[arg-type]
            if _done_imports < 1:
                import_chain.pop()
            else:
                done_imports += _done_imports
    if done_imports < 1 and parent_id is not None and root_id != parent_id:
        public_id_uri = rdflib.URIRef(parent_id)
        owl_imports = list(target_g.objects(public_id_uri, rdflib.OWL.imports))
        if len(owl_imports) > 0:
            import_chain.append(str(public_id_uri))
            _done_imports = _load_from_imports_nodes(owl_imports)  # type: ignore[arg-type]
            if _done_imports < 1:
                import_chain.pop()
            else:
                done_imports += _done_imports
    if done_imports < 1:
        ontologies = target_g.subjects(rdflib.RDF.type, rdflib.OWL.Ontology)
        for ont in ontologies:
            if ont == root_id or ont == parent_id:
                continue
            ont_str = str(ont)
            if ont_str in import_chain:
                continue
            owl_imports = list(target_g.objects(ont, rdflib.OWL.imports))
            if len(owl_imports) > 0:
                import_chain.append(ont_str)
                _done_imports = _load_from_imports_nodes(owl_imports)  # type: ignore[arg-type]
                if _done_imports < 1:
                    import_chain.pop()
                else:
                    done_imports += _done_imports
    return target_g
