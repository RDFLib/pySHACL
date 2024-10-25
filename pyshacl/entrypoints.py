import logging
import os
import sys
from functools import wraps
from io import BufferedIOBase, TextIOBase
from sys import stderr
from typing import List, Optional, Tuple, Union

from rdflib import ConjunctiveGraph, Dataset, Graph, Literal, URIRef

from pyshacl.errors import ReportableRuntimeError, ValidationFailure
from pyshacl.pytypes import GraphLike

from .consts import SH, RDF_type
from .monkey import apply_patches, rdflib_bool_patch, rdflib_bool_unpatch
from .rdfutil import load_from_source
from .rule_expand_runner import RuleExpandRunner
from .validator import Validator, assign_baked_in
from .validator_conformance import check_dash_result


def validate(
    data_graph: Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes],
    *args,
    shacl_graph: Optional[Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes]] = None,
    ont_graph: Optional[Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes]] = None,
    advanced: Optional[bool] = False,
    inference: Optional[str] = None,
    inplace: Optional[bool] = False,
    abort_on_first: Optional[bool] = False,
    allow_infos: Optional[bool] = False,
    allow_warnings: Optional[bool] = False,
    max_validation_depth: Optional[int] = None,
    sparql_mode: Optional[bool] = False,
    focus_nodes: Optional[List[Union[str, URIRef]]] = None,
    use_shapes: Optional[List[Union[str, URIRef]]] = None,
    **kwargs,
):
    """
    :param data_graph: rdflib.Graph or file path or web url of the data to validate
    :type data_graph: rdflib.Graph | str | bytes
    :param args:
    :type args: list
    :param shacl_graph: rdflib.Graph or file path or web url of the SHACL Shapes graph to use to
    validate the data graph
    :type shacl_graph: rdflib.Graph | str | bytes
    :param ont_graph: rdflib.Graph or file path or web url of an extra ontology document to mix into the data graph
    :type ont_graph: rdflib.Graph | str | bytes
    :param advanced: Enable advanced SHACL features, default=False
    :type advanced: bool | None
    :param inference: One of "rdfs", "owlrl", "both", "none", or None
    :type inference: str | None
    :param inplace: If this is enabled, do not clone the datagraph, manipulate it in-place
    :type inplace: bool
    :param abort_on_first: Stop evaluating constraints after first violation is found
    :type abort_on_first: bool | None
    :param allow_infos: Shapes marked with severity of sh:Info will not cause result to be invalid.
    :type allow_infos: bool | None
    :param allow_warnings: Shapes marked with severity of sh:Warning or sh:Info will not cause result to be invalid.
    :type allow_warnings: bool | None
    :param max_validation_depth: The maximum number of SHACL shapes "deep" that the validator can go before reaching an "endpoint" constraint.
    :type max_validation_depth: int | None
    :param sparql_mode: Treat the DataGraph as a SPARQL endpoint, validate the graph at the SPARQL endpoint.
    :type sparql_mode: bool | None
    :param focus_nodes: A list of IRIs to validate only those nodes.
    :type focus_nodes: list | None
    :param use_shapes: A list of IRIs to use only those shapes from the SHACL ShapesGraph.
    :type use_shapes: list | None
    :param kwargs:
    :return:
    """

    do_debug = kwargs.get('debug', False)
    log = make_default_logger(name="pyshacl-validate", debug=do_debug)
    apply_patches()
    assign_baked_in()
    do_check_dash_result = kwargs.pop('check_dash_result', False)  # type: bool
    if kwargs.get('meta_shacl', False):
        to_meta_val = shacl_graph or data_graph
        conforms, v_r, v_t = meta_validate(to_meta_val, inference=inference, **kwargs)
        if not conforms:
            msg = f"SHACL File does not validate against the SHACL Shapes SHACL (MetaSHACL) file.\n{v_t}"
            log.error(msg)
            raise ReportableRuntimeError(msg)
    do_owl_imports = kwargs.pop('do_owl_imports', False)
    data_graph_format = kwargs.pop('data_graph_format', None)

    if isinstance(data_graph, (str, bytes, BufferedIOBase, TextIOBase)):
        # DataGraph is passed in as Text. It is not an rdflib.Graph
        # That means we load it into an ephemeral graph at runtime
        # that means we don't need to make a copy to prevent polluting it.
        ephemeral = True
    else:
        ephemeral = False
    use_js = kwargs.pop('js', None)
    if sparql_mode:
        if use_js:
            raise ReportableRuntimeError("Cannot use SHACL-JS in SPARQL Remote Graph Mode.")
        if inplace:
            raise ReportableRuntimeError("Cannot use inplace mode in SPARQL Remote Graph Mode.")
        if ont_graph is not None:
            raise ReportableRuntimeError("Cannot use SPARQL Remote Graph Mode with extra Ontology Graph inoculation.")
        if isinstance(data_graph, bytes):
            data_graph = data_graph.decode('utf-8')
        else:
            data_graph = data_graph
        ephemeral = False
        inplace = True
    if (
        sparql_mode
        and isinstance(data_graph, str)
        and (data_graph.lower().startswith("http:") or data_graph.lower().startswith("https:"))
    ):
        from rdflib.plugins.stores.sparqlstore import SPARQLStore

        query_endpoint: str = data_graph
        username = os.getenv("PYSHACL_SPARQL_USERNAME", "")
        method = os.getenv("PYSHACL_SPARQL_METHOD", "GET")
        auth: Optional[Tuple[str, str]]
        if username:
            password: str = os.getenv("PYSHACL_SPARQL_PASSWORD", "")
            auth = (username, password)
        else:
            auth = None
        store = SPARQLStore(query_endpoint=query_endpoint, auth=auth, method=method)
        loaded_dg = Dataset(store=store, default_union=True)
    else:
        # force no owl imports on data_graph
        loaded_dg = load_from_source(
            data_graph, rdf_format=data_graph_format, multigraph=True, do_owl_imports=False, logger=log
        )
    ont_graph_format = kwargs.pop('ont_graph_format', None)
    if ont_graph is not None:
        loaded_og = load_from_source(
            ont_graph, rdf_format=ont_graph_format, multigraph=True, do_owl_imports=do_owl_imports, logger=log
        )
    else:
        loaded_og = None
    shacl_graph_format = kwargs.pop('shacl_graph_format', None)
    if shacl_graph is not None:
        rdflib_bool_patch()
        loaded_sg = load_from_source(
            shacl_graph, rdf_format=shacl_graph_format, multigraph=True, do_owl_imports=do_owl_imports, logger=log
        )
        rdflib_bool_unpatch()
    else:
        loaded_sg = None
    iterate_rules = kwargs.pop('iterate_rules', False)
    if "abort_on_error" in kwargs:
        log.warning("Usage of abort_on_error is deprecated. Use abort_on_first instead.")
        ae = kwargs.pop("abort_on_error")
        abort_on_first = bool(abort_on_first) or bool(ae)
    validator_options_dict = {
        'debug': do_debug or False,
        'inference': inference,
        'inplace': inplace or ephemeral,
        'abort_on_first': abort_on_first,
        'allow_infos': allow_infos,
        'allow_warnings': allow_warnings,
        'advanced': advanced,
        'iterate_rules': iterate_rules,
        'use_js': use_js,
        'sparql_mode': sparql_mode,
        'logger': log,
        'focus_nodes': focus_nodes,
        'use_shapes': use_shapes,
    }
    if max_validation_depth is not None:
        validator_options_dict['max_validation_depth'] = max_validation_depth
    validator = None
    try:
        validator = Validator(
            loaded_dg,
            shacl_graph=loaded_sg,
            ont_graph=loaded_og,
            options=validator_options_dict,
        )
        conforms, report_graph, report_text = validator.run()
    except ValidationFailure as e:
        conforms = False
        report_graph = e
        report_text = "Validation Failure - {}".format(e.message)
    if do_check_dash_result and validator is not None:
        passes = check_dash_result(validator, report_graph, loaded_sg or loaded_dg)
        return passes, report_graph, report_text
    do_serialize_report_graph = kwargs.pop('serialize_report_graph', False)
    if do_serialize_report_graph and isinstance(report_graph, Graph):
        if not (isinstance(do_serialize_report_graph, str)):
            do_serialize_report_graph = 'turtle'
        report_graph = report_graph.serialize(None, encoding='utf-8', format=do_serialize_report_graph)
    return conforms, report_graph, report_text


def with_metashacl_shacl_graph_cache(f):
    # noinspection PyPep8Naming
    EMPTY = object()

    @wraps(f)
    def wrapped(*args, **kwargs):
        graph_cache = getattr(wrapped, "graph_cache", None)
        assert graph_cache is not None
        if graph_cache is EMPTY:
            import pickle

            if getattr(sys, 'frozen', False):
                # runs in a pyinstaller bundle
                here_dir = sys._MEIPASS
            else:
                here_dir = os.path.dirname(__file__)
            pickle_file = os.path.join(here_dir, "assets", "shacl-shacl.pickle")
            with open(pickle_file, 'rb') as shacl_pickle:
                u = pickle.Unpickler(shacl_pickle, fix_imports=False)
                shacl_shacl_store, identifier = u.load()
            shacl_shacl_graph = Graph(store=shacl_shacl_store, identifier=identifier)
            setattr(wrapped, "graph_cache", shacl_shacl_graph)
        return f(*args, **kwargs)

    setattr(wrapped, "graph_cache", EMPTY)
    return wrapped


@with_metashacl_shacl_graph_cache
def meta_validate(shacl_graph: Union[GraphLike, str], inference: Optional[str] = 'rdfs', **kwargs):
    shacl_shacl_graph = meta_validate.graph_cache
    shacl_graph = load_from_source(shacl_graph, rdf_format=kwargs.pop('shacl_graph_format', None), multigraph=True)
    _ = kwargs.pop('meta_shacl', None)
    return validate(shacl_graph, shacl_graph=shacl_shacl_graph, inference=inference, **kwargs)


def make_default_logger(
    name: Union[str, None] = None, debug: bool = False, clear_handlers: bool = True
) -> logging.Logger:
    log_handler = logging.StreamHandler(stderr)
    log = logging.getLogger(name)
    if clear_handlers:
        for h in log.handlers:
            log.removeHandler(h)  # pragma:no cover
    log.addHandler(log_handler)
    log.setLevel(logging.INFO if not debug else logging.DEBUG)
    log_handler.setLevel(logging.INFO if not debug else logging.DEBUG)
    return log


def shacl_rules(
    data_graph: Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes],
    *args,
    shacl_graph: Optional[Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes]] = None,
    ont_graph: Optional[Union[GraphLike, BufferedIOBase, TextIOBase, str, bytes]] = None,
    inference: Optional[str] = None,
    inplace: Optional[bool] = False,
    focus_nodes: Optional[List[Union[str, URIRef]]] = None,
    use_shapes: Optional[List[Union[str, URIRef]]] = None,
    **kwargs,
) -> Union[str, GraphLike]:
    """
    :param data_graph: rdflib.Graph or file path or web url of the data to validate
    :type data_graph: rdflib.Graph | str | bytes
    :param args:
    :type args: list
    :param shacl_graph: rdflib.Graph or file path or web url of the SHACL Shapes graph to use to
    validate the data graph
    :type shacl_graph: rdflib.Graph | str | bytes
    :param ont_graph: rdflib.Graph or file path or web url of an extra ontology document to mix into the data graph
    :type ont_graph: rdflib.Graph | str | bytes
    :param inference: One of "rdfs", "owlrl", "both", "none", or None
    :type inference: str | None
    :param inplace: If this is enabled, do not clone the datagraph, manipulate it in-place
    :type inplace: bool
    :param focus_nodes: A list of IRIs to validate only those nodes.
    :type focus_nodes: list | None
    :param use_shapes: A list of IRIs to use only those shapes from the SHACL ShapesGraph.
    :type use_shapes: list | None
    :param kwargs:
    :return:
    """

    do_debug = kwargs.get('debug', False)
    log = make_default_logger(name="pyshacl-rules", debug=do_debug)
    apply_patches()
    assign_baked_in()
    do_owl_imports = kwargs.pop('do_owl_imports', False)
    data_graph_format = kwargs.pop('data_graph_format', None)
    if kwargs.get('sparql_mode', None):
        raise ReportableRuntimeError("The SHACL Rules expander cannot be used in SPARQL Remote Graph Mode.")
    if isinstance(data_graph, (str, bytes, BufferedIOBase, TextIOBase)):
        # DataGraph is passed in as Text. It is not a rdflib.Graph
        # That means we load it into an ephemeral graph at runtime
        # that means we don't need to make a copy to prevent polluting it.
        ephemeral = True
    else:
        ephemeral = False
    use_js = kwargs.pop('js', None)
    # force no owl imports on data_graph
    loaded_dg = load_from_source(
        data_graph, rdf_format=data_graph_format, multigraph=True, do_owl_imports=False, logger=log
    )
    ont_graph_format = kwargs.pop('ont_graph_format', None)
    if ont_graph is not None:
        loaded_og = load_from_source(
            ont_graph, rdf_format=ont_graph_format, multigraph=True, do_owl_imports=do_owl_imports, logger=log
        )
    else:
        loaded_og = None
    shacl_graph_format = kwargs.pop('shacl_graph_format', None)
    if shacl_graph is not None:
        rdflib_bool_patch()
        loaded_sg = load_from_source(
            shacl_graph, rdf_format=shacl_graph_format, multigraph=True, do_owl_imports=do_owl_imports, logger=log
        )
        rdflib_bool_unpatch()
    else:
        loaded_sg = None
    iterate_rules = kwargs.pop('iterate_rules', False)
    runner_options_dict = {
        'debug': do_debug or False,
        'inference': inference,
        'inplace': inplace or ephemeral,
        'iterate_rules': iterate_rules,
        'use_js': use_js,
        'logger': log,
        'focus_nodes': focus_nodes,
        'use_shapes': use_shapes,
    }
    serialize_expanded_graph = kwargs.get('serialize_expanded_graph', None)
    try:
        runner = RuleExpandRunner(
            loaded_dg,
            shacl_graph=loaded_sg,
            ont_graph=loaded_og,
            options=runner_options_dict,
        )
        expanded_graph = runner.run()
    except ValidationFailure as e:
        error = "SHACL Rules Expansion Failure - {}".format(e.message)
        if serialize_expanded_graph:
            return error
        else:
            g = Graph()
            g.add((URIRef("<urn:rdflib:pyshacl:shacl-rules-error>"), RDF_type, SH.ValidationFailure))
            g.add((URIRef("<urn:rdflib:pyshacl:shacl-rules-error>"), SH.message, Literal(error)))
            return g
    if serialize_expanded_graph:
        guess_format = "trig" if isinstance(expanded_graph, (Dataset, ConjunctiveGraph)) else "turtle"
        serialize_format = kwargs.get('serialize_expanded_graph_format', guess_format)
        return expanded_graph.serialize(format=serialize_format)
    return expanded_graph
