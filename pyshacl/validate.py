# -*- coding: utf-8 -*-
#
import logging
import os
import sys
from functools import wraps
from io import BufferedIOBase, TextIOBase
from os import getenv, path
from sys import stderr
from typing import Dict, List, Optional, Tuple, Union

import rdflib
from rdflib import BNode, Literal, URIRef

from .consts import (
    RDF_type,
    SH_conforms,
    SH_result,
    SH_ValidationReport,
    env_truths,
)
from .errors import ReportableRuntimeError, ValidationFailure
from .extras import check_extra_installed
from .functions import apply_functions, gather_functions, unapply_functions
from .monkey import apply_patches, rdflib_bool_patch, rdflib_bool_unpatch
from .pytypes import GraphLike, SHACLExecutor
from .rdfutil import (
    add_baked_in,
    clone_blank_node,
    clone_graph,
    inoculate,
    inoculate_dataset,
    load_from_source,
    mix_datasets,
    mix_graphs,
)
from .rules import apply_rules, gather_rules
from .shapes_graph import ShapesGraph
from .target import apply_target_types, gather_target_types
from .validator_conformance import check_dash_result

USE_FULL_MIXIN = getenv("PYSHACL_USE_FULL_MIXIN") in env_truths

log_handler = logging.StreamHandler(stderr)
log = logging.getLogger(__name__)
for h in log.handlers:
    log.removeHandler(h)  # pragma:no cover
log.addHandler(log_handler)
log.setLevel(logging.INFO)
log_handler.setLevel(logging.INFO)


class Validator(object):
    @classmethod
    def _load_default_options(cls, options_dict: dict):
        options_dict.setdefault('debug', False)
        options_dict.setdefault('advanced', False)
        options_dict.setdefault('inference', 'none')
        options_dict.setdefault('inplace', False)
        options_dict.setdefault('use_js', False)
        options_dict.setdefault('iterate_rules', False)
        options_dict.setdefault('abort_on_first', False)
        options_dict.setdefault('allow_infos', False)
        options_dict.setdefault('allow_warnings', False)
        options_dict.setdefault('sparql_mode', False)
        options_dict.setdefault('max_validation_depth', 15)
        options_dict.setdefault('focus_nodes', None)
        options_dict.setdefault('use_shapes', None)
        if 'logger' not in options_dict:
            options_dict['logger'] = logging.getLogger(__name__)
            if options_dict['debug']:
                options_dict['logger'].setLevel(logging.DEBUG)

    @classmethod
    def _run_pre_inference(
        cls, target_graph: GraphLike, inference_option: str, logger: Optional[logging.Logger] = None
    ):
        """
        Note, this is the OWL/RDFS pre-inference,
        it is not the Advanced Spec SHACL-Rule inferencing step.
        :param target_graph:
        :type target_graph: rdflib.Graph|rdflib.ConjunctiveGraph|rdflib.Dataset
        :param inference_option:
        :type inference_option: str
        :return:
        :rtype: NoneType
        """
        # Lazy import owlrl
        import owlrl

        from .inference import CustomRDFSOWLRLSemantics, CustomRDFSSemantics

        if logger is None:
            logger = logging.getLogger(__name__)
        try:
            if inference_option == 'rdfs':
                inferencer = owlrl.DeductiveClosure(CustomRDFSSemantics)
            elif inference_option == 'owlrl':
                inferencer = owlrl.DeductiveClosure(owlrl.OWLRL_Semantics)
            elif inference_option == 'both' or inference_option == 'all' or inference_option == 'rdfsowlrl':
                inferencer = owlrl.DeductiveClosure(CustomRDFSOWLRLSemantics)
            else:
                raise ReportableRuntimeError("Don't know how to do '{}' type inferencing.".format(inference_option))
        except Exception as e:  # pragma: no cover
            logger.error("Error during creation of OWL-RL Deductive Closure")
            if isinstance(e, ReportableRuntimeError):
                raise e
            raise ReportableRuntimeError(
                "Error during creation of OWL-RL Deductive Closure\n{}".format(str(e.args[0]))
            )
        if isinstance(target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            named_graphs = []
            for i in target_graph.store.contexts(None):
                if isinstance(i, rdflib.Graph):
                    named_graphs.append(i)
                else:
                    named_graphs.append(
                        rdflib.Graph(target_graph.store, i, namespace_manager=target_graph.namespace_manager)
                    )
        else:
            named_graphs = [target_graph]
        try:
            for g in named_graphs:
                inferencer.expand(g)
        except Exception as e:  # pragma: no cover
            logger.error("Error while running OWL-RL Deductive Closure")
            raise ReportableRuntimeError("Error while running OWL-RL Deductive Closure\n{}".format(str(e.args[0])))

    @classmethod
    def create_validation_report(cls, sg, conforms: bool, results: List[Tuple]):
        v_text = "Validation Report\nConforms: {}\n".format(str(conforms))
        result_len = len(results)
        if not conforms and result_len < 1:
            raise RuntimeError("A Non-Conformant Validation Report must have at least one result.")
        if result_len > 0:
            v_text += "Results ({}):\n".format(str(result_len))
        vg = rdflib.Graph(bind_namespaces='core')
        for p, n in sg.graph.namespace_manager.namespaces():
            vg.namespace_manager.bind(p, n)
        vr = BNode()
        vg.add((vr, RDF_type, SH_ValidationReport))
        vg.add((vr, SH_conforms, Literal(conforms)))
        cloned_nodes: Dict[Tuple[GraphLike, str], Union[BNode, URIRef]] = {}
        for result in iter(results):
            _d, _bn, _tr = result
            v_text += _d
            vg.add((vr, SH_result, _bn))
            for tr in iter(_tr):
                s, p, o = tr
                if isinstance(o, tuple):
                    source = o[0]
                    node = o[1]
                    if isinstance(node, Literal):
                        o = node  # No need to clone a literal from the data graph
                    else:
                        _id = str(node)
                        if (source, _id) in cloned_nodes:
                            o = cloned_nodes[(source, _id)]
                        elif isinstance(node, BNode):
                            cloned_nodes[(source, _id)] = o = clone_blank_node(source, node, vg, keepid=True)
                        else:
                            cloned_nodes[(source, _id)] = o = URIRef(_id)
                vg.add((s, p, o))
        return vg, v_text

    def __init__(
        self,
        data_graph: GraphLike,
        *args,
        shacl_graph: Optional[GraphLike] = None,
        ont_graph: Optional[GraphLike] = None,
        options: Optional[dict] = None,
        **kwargs,
    ):
        options = options or {}
        self._load_default_options(options)
        self.options = options  # type: dict
        self.logger = options['logger']  # type: logging.Logger
        self.debug = options['debug']
        self.pre_inferenced = kwargs.pop('pre_inferenced', False)
        self.inplace = options['inplace']
        if not isinstance(data_graph, rdflib.Graph):
            raise RuntimeError("data_graph must be a rdflib Graph object")
        self.data_graph = data_graph  # type: GraphLike
        self._target_graph = None
        self.ont_graph = ont_graph  # type: Optional[GraphLike]
        self.data_graph_is_multigraph = isinstance(self.data_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph))
        if self.ont_graph is not None and isinstance(self.ont_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            self.ont_graph.default_union = True
        if self.ont_graph is not None and options['sparql_mode']:
            raise ReportableRuntimeError("Cannot use SPARQL Remote Graph Mode with extra Ontology Graph inoculation.")
        if shacl_graph is None:
            if options['sparql_mode']:
                raise ReportableRuntimeError(
                    "SHACL Shapes Graph must be a separate local graph or file when in SPARQL Remote Graph Mode."
                )
            shacl_graph = clone_graph(data_graph, identifier='shacl')
        assert isinstance(shacl_graph, rdflib.Graph), "shacl_graph must be a rdflib Graph object"
        self.shacl_graph = ShapesGraph(shacl_graph, self.debug, self.logger)  # type: ShapesGraph

        if options['use_js']:
            if options['sparql_mode']:
                raise ReportableRuntimeError("Cannot use SHACL-JS in SPARQL Remote Graph Mode.")
            is_js_installed = check_extra_installed('js')
            if is_js_installed:
                self.shacl_graph.enable_js()

    @property
    def target_graph(self):
        return self._target_graph

    def mix_in_ontology(self):
        if USE_FULL_MIXIN:
            if not self.data_graph_is_multigraph:
                return mix_graphs(self.data_graph, self.ont_graph, "inplace" if self.inplace else None)
            return mix_datasets(self.data_graph, self.ont_graph, "inplace" if self.inplace else None)
        if not self.data_graph_is_multigraph:
            if self.inplace:
                to_graph = self.data_graph
            else:
                to_graph = clone_graph(self.data_graph, identifier=self.data_graph.identifier)
            return inoculate(to_graph, self.ont_graph)
        return inoculate_dataset(self.data_graph, self.ont_graph, self.data_graph if self.inplace else None)

    def make_executor(self) -> SHACLExecutor:
        return SHACLExecutor(
            validator=self,
            advanced_mode=bool(self.options.get('advanced', False)),
            abort_on_first=bool(self.options.get("abort_on_first", False)),
            allow_infos=bool(self.options.get("allow_infos", False)),
            allow_warnings=bool(self.options.get("allow_warnings", False)),
            iterate_rules=bool(self.options.get("iterate_rules", False)),
            sparql_mode=bool(self.options.get("sparql_mode", False)),
            max_validation_depth=self.options.get("max_validation_depth", 15),
            focus_nodes=self.options.get("focus_nodes", None),
            debug=self.debug,
        )

    def run(self):
        if self.target_graph is not None:
            the_target_graph = self.target_graph
        else:
            has_cloned = False
            if self.ont_graph is not None:
                if self.inplace:
                    self.logger.debug("Adding ontology definitions to DataGraph")
                else:
                    self.logger.debug("Cloning DataGraph to temporary memory graph, to add ontology definitions.")
                # creates a copy of self.data_graph, doesn't modify it
                the_target_graph = self.mix_in_ontology()
                has_cloned = True
            else:
                the_target_graph = self.data_graph
            inference_option = self.options.get('inference', 'none')
            if self.inplace and self.debug:
                self.logger.debug("Skipping DataGraph clone because PySHACL is operating in inplace mode.")
            if inference_option and not self.pre_inferenced and str(inference_option) != "none":
                if self.options.get('sparql_mode', False):
                    raise ReportableRuntimeError("Cannot use any pre-inference option in SPARQL Remote Graph Mode.")
                if not has_cloned and not self.inplace:
                    self.logger.debug("Cloning DataGraph to temporary memory graph before pre-inferencing.")
                    the_target_graph = clone_graph(the_target_graph)
                    has_cloned = True
                self.logger.debug(f"Running pre-inferencing with option='{inference_option}'.")
                self._run_pre_inference(the_target_graph, inference_option, logger=self.logger)
                self.pre_inferenced = True
            if not has_cloned and not self.inplace and self.options['advanced']:
                if self.options.get('sparql_mode', False):
                    raise ReportableRuntimeError("Cannot clone DataGraph in SPARQL Remote Graph Mode.")
                # We still need to clone in advanced mode, because of triple rules
                self.logger.debug("Forcing clone of DataGraph because advanced mode is enabled.")
                the_target_graph = clone_graph(the_target_graph)
                has_cloned = True
            if not has_cloned and not self.inplace:
                # No inferencing, no ont_graph, and no advanced mode, now implies inplace mode
                self.logger.debug("Running validation in-place, without modifying the DataGraph.")
                self.inplace = True
            self._target_graph = the_target_graph
        if self.options.get("use_shapes", None) is not None and len(self.options["use_shapes"]) > 0:
            using_manually_specified_shapes = True
            expanded_use_shapes = []
            for s in self.options["use_shapes"]:
                s_lower = s.lower()
                if (
                    s_lower.startswith("http:")
                    or s_lower.startswith("https:")
                    or s_lower.startswith("urn:")
                    or s_lower.startswith("file:")
                ):
                    expanded_use_shapes.append(URIRef(s))
                else:
                    try:
                        expanded_use_shape = self.shacl_graph.graph.namespace_manager.expand_curie(s)
                    except ValueError:
                        expanded_use_shape = URIRef(s)
                    expanded_use_shapes.append(expanded_use_shape)
            shapes = self.shacl_graph.shapes_from_uris(expanded_use_shapes)
        else:
            using_manually_specified_shapes = False
            shapes = self.shacl_graph.shapes  # This property getter triggers shapes harvest.
        option_focus_nodes = self.options.get("focus_nodes", None)
        if option_focus_nodes is not None and len(option_focus_nodes) > 0:
            # Expand any CURIEs in the focus_nodes list
            expanded_focus_nodes: List[URIRef] = []
            for f in option_focus_nodes:
                f_lower = f.lower()
                if (
                    f_lower.startswith("http:")
                    or f_lower.startswith("https:")
                    or f_lower.startswith("urn:")
                    or f_lower.startswith("file:")
                ):
                    expanded_focus_nodes.append(URIRef(f))
                else:
                    try:
                        expanded_focus_node = self.target_graph.namespace_manager.expand_curie(f)
                    except ValueError:
                        expanded_focus_node = URIRef(f)
                    expanded_focus_nodes.append(expanded_focus_node)
            self.options["focus_nodes"] = expanded_focus_nodes
            specified_focus_nodes: Union[None, List[URIRef]] = expanded_focus_nodes
        else:
            specified_focus_nodes = None
        executor = self.make_executor()

        # Special hack, if we are using manually specified shapes, and have
        # manually specified focus nodes, then we need to disable the
        # focus_nodes in the executor, because we apply the specified focus
        # nodes directly to the specified shapes.
        if using_manually_specified_shapes and specified_focus_nodes is not None:
            executor.focus_nodes = None

        if executor.advanced_mode:
            self.logger.debug("Activating SHACL-AF Features.")
            target_types = gather_target_types(self.shacl_graph)
            advanced = {
                'functions': gather_functions(executor, self.shacl_graph),
                'rules': gather_rules(executor, self.shacl_graph),
            }
            for s in shapes:
                s.set_advanced(True)
            apply_target_types(target_types)
        else:
            advanced = {}
        if isinstance(the_target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            named_graphs = [
                (
                    rdflib.Graph(the_target_graph.store, i, namespace_manager=the_target_graph.namespace_manager)
                    if not isinstance(i, rdflib.Graph)
                    else i
                )
                for i in the_target_graph.store.contexts(None)
            ]
        else:
            named_graphs = [the_target_graph]
        reports = []

        non_conformant = False
        aborted = False
        if executor.abort_on_first and self.debug:
            self.logger.debug(
                "Abort on first error is enabled. Will exit at end of first Shape that fails validation."
            )
        if self.debug:
            self.logger.debug(f"Will run validation on {len(named_graphs)} named graph/s.")
        for g in named_graphs:
            if self.debug:
                self.logger.debug(f"Validating DataGraph named {g.identifier}")
            if advanced:
                if advanced['functions']:
                    apply_functions(executor, advanced['functions'], g)
                if advanced['rules']:
                    if executor.sparql_mode:
                        self.logger.warning("Skipping SHACL Rules because operating in SPARQL Remote Graph Mode.")
                    else:
                        apply_rules(executor, advanced['rules'], g)
            try:
                for s in shapes:
                    if using_manually_specified_shapes and specified_focus_nodes is not None:
                        _is_conform, _reports = s.validate(executor, g, focus=specified_focus_nodes)
                    else:
                        _is_conform, _reports = s.validate(executor, g)
                    non_conformant = non_conformant or (not _is_conform)
                    reports.extend(_reports)
                    if executor.abort_on_first and non_conformant:
                        aborted = True
                        break
                if aborted:
                    break
            finally:
                if advanced:
                    unapply_functions(advanced['functions'], g)
        v_report, v_text = self.create_validation_report(self.shacl_graph, not non_conformant, reports)
        return (not non_conformant), v_report, v_text


def assign_baked_in():
    if getattr(sys, 'frozen', False):
        # runs in a pyinstaller bundle
        HERE = sys._MEIPASS
    else:
        HERE = path.dirname(__file__)
    shacl_file = path.join(HERE, "assets", "shacl.pickle")
    add_baked_in("http://www.w3.org/ns/shacl", shacl_file)
    add_baked_in("https://www.w3.org/ns/shacl", shacl_file)
    add_baked_in("http://www.w3.org/ns/shacl.ttl", shacl_file)
    shacl_shacl_file = path.join(HERE, "assets", "shacl-shacl.pickle")
    add_baked_in("http://www.w3.org/ns/shacl-shacl", shacl_shacl_file)
    add_baked_in("https://www.w3.org/ns/shacl-shacl", shacl_shacl_file)
    add_baked_in("http://www.w3.org/ns/shacl-shacl.ttl", shacl_shacl_file)
    schema_file = path.join(HERE, "assets", "schema.pickle")
    add_baked_in("http://datashapes.org/schema", schema_file)
    add_baked_in("https://datashapes.org/schema", schema_file)
    add_baked_in("http://datashapes.org/schema.ttl", schema_file)


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
                here_dir = path.dirname(__file__)
            pickle_file = path.join(here_dir, "assets", "shacl-shacl.pickle")
            with open(pickle_file, 'rb') as shacl_pickle:
                u = pickle.Unpickler(shacl_pickle, fix_imports=False)
                shacl_shacl_store, identifier = u.load()
            shacl_shacl_graph = rdflib.Graph(store=shacl_shacl_store, identifier=identifier)
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
    :param kwargs:
    :return:
    """

    do_debug = kwargs.get('debug', False)
    if do_debug:
        log_handler.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
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
        loaded_dg = rdflib.Dataset(store=store, default_union=True)
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
    if do_serialize_report_graph and isinstance(report_graph, rdflib.Graph):
        if not (isinstance(do_serialize_report_graph, str)):
            do_serialize_report_graph = 'turtle'
        report_graph = report_graph.serialize(None, encoding='utf-8', format=do_serialize_report_graph)
    return conforms, report_graph, report_text
