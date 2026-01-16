# -*- coding: utf-8 -*-
#
import logging
import sys
from os import getenv, path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import rdflib
from rdflib import BNode, Literal, URIRef

from .consts import (
    RDF_type,
    SH_conforms,
    SH_result,
    SH_ValidationReport,
    env_truths,
)
from .errors import ReportableRuntimeError
from .extras import check_extra_installed
from .functions import apply_functions, gather_functions, unapply_functions
from .pytypes import GraphLike, SHACLExecutor
from .rdfutil import (
    add_baked_in,
    clone_blank_node,
    clone_graph,
    inoculate,
    inoculate_dataset,
    mix_datasets,
    mix_graphs,
)
from .rules import apply_rules, gather_rules
from .run_type import PySHACLRunType
from .shapes_graph import ShapesGraph
from .target import apply_target_types, gather_target_types

USE_FULL_MIXIN = getenv("PYSHACL_USE_FULL_MIXIN") in env_truths


class Validator(PySHACLRunType):
    def __init__(
        self,
        data_graph: GraphLike,
        *args,
        shacl_graph: Optional[GraphLike] = None,
        ont_graph: Optional[GraphLike] = None,
        options: Optional[Dict[str, Any]] = None,
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
        self._target_graph: Union[GraphLike, None] = None
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
        text_results = sorted(results, key=lambda r: r[0])
        for result in iter(text_results):
            _d, _bn, _tr = result
            v_text += _d
        for result in iter(results):
            _d, _bn, _tr = result
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

    @property
    def target_graph(self) -> Union[GraphLike, None]:
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
        return inoculate_dataset(
            self.data_graph,
            self.ont_graph,
            self.data_graph if self.inplace else None,
            URIRef("urn:pyshacl:inoculation"),
        )

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
        datagraph: Union[GraphLike, None] = self.target_graph
        if datagraph is not None:
            self._target_graph = datagraph
        else:
            has_cloned = False
            if self.ont_graph is not None:
                if self.inplace:
                    self.logger.debug("Adding ontology definitions to DataGraph")
                else:
                    self.logger.debug("Cloning DataGraph to temporary memory graph, to add ontology definitions.")
                # creates a copy of self.data_graph, doesn't modify it
                datagraph = self.mix_in_ontology()
                has_cloned = True
            else:
                datagraph = self.data_graph
            inference_option = self.options.get('inference', 'none')
            if self.inplace and self.debug:
                self.logger.debug("Skipping DataGraph clone because PySHACL is operating in inplace mode.")
            if inference_option and not self.pre_inferenced and str(inference_option) != "none":
                if self.options.get('sparql_mode', False):
                    raise ReportableRuntimeError("Cannot use any pre-inference option in SPARQL Remote Graph Mode.")
                if not has_cloned and not self.inplace:
                    self.logger.debug("Cloning DataGraph to temporary memory graph before pre-inferencing.")
                    datagraph = clone_graph(datagraph)
                    has_cloned = True
                self.logger.debug(f"Running pre-inferencing with option='{inference_option}'.")
                self._run_pre_inference(
                    datagraph, inference_option, URIRef("urn:pyshacl:inference"), logger=self.logger
                )
                self.pre_inferenced = True
            if not has_cloned and not self.inplace and self.options['advanced']:
                if self.options.get('sparql_mode', False):
                    raise ReportableRuntimeError("Cannot clone DataGraph in SPARQL Remote Graph Mode.")
                # We still need to clone in advanced mode, because of triple rules
                self.logger.debug("Forcing clone of DataGraph because advanced mode is enabled.")
                datagraph = clone_graph(datagraph)
                has_cloned = True
            if not has_cloned and not self.inplace:
                # No inferencing, no ont_graph, and no advanced mode, now implies inplace mode
                self.logger.debug("Running validation in-place, without modifying the DataGraph.")
                self.inplace = True
            self._target_graph = datagraph
        assert self._target_graph is not None
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
                        expanded_focus_node = self._target_graph.namespace_manager.expand_curie(f)
                    except ValueError:
                        expanded_focus_node = URIRef(f)
                    expanded_focus_nodes.append(expanded_focus_node)
            self.options["focus_nodes"] = expanded_focus_nodes
            specified_focus_nodes: Union[None, Sequence[URIRef]] = expanded_focus_nodes
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
            gather_from_shapes = None if not using_manually_specified_shapes else [s.node for s in shapes]
            advanced = {
                'functions': gather_functions(executor, self.shacl_graph),
                'rules': gather_rules(executor, self.shacl_graph, from_shapes=gather_from_shapes),
            }
            for s in shapes:
                s.set_advanced(True)
            apply_target_types(target_types)
        else:
            advanced = {}

        if specified_focus_nodes is not None and using_manually_specified_shapes:
            on_focus_nodes: Union[Sequence[URIRef], None] = specified_focus_nodes
        else:
            on_focus_nodes = None
        reports = []
        non_conformant = False
        if executor.abort_on_first and self.debug:
            self.logger.debug(
                "Abort on first error is enabled. Will exit at end of first Shape that fails validation."
            )

        if isinstance(self._target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            self._target_graph.default_union = True

        g = self._target_graph

        if self.debug:
            self.logger.debug(f"Validating DataGraph named {g.identifier}")
        if advanced:
            if advanced['functions']:
                apply_functions(executor, advanced['functions'], g)
            if advanced['rules']:
                if executor.sparql_mode:
                    self.logger.warning("Skipping SHACL Rules because operating in SPARQL Remote Graph Mode.")
                else:
                    apply_rules(executor, advanced['rules'], g, focus_nodes=on_focus_nodes)
        try:
            for s in shapes:
                _is_conform, _reports = s.validate(executor, g, focus=on_focus_nodes)
                non_conformant = non_conformant or (not _is_conform)
                reports.extend(_reports)
                if executor.abort_on_first and non_conformant:
                    break
        finally:
            if advanced and advanced['functions']:
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
    dash_file = path.join(HERE, "assets", "dash.pickle")
    add_baked_in("http://datashapes.org/dash", dash_file)
    add_baked_in("https://datashapes.org/dash", dash_file)
    add_baked_in("http://datashapes.org/dash.ttl", dash_file)
