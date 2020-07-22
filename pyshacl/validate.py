# -*- coding: utf-8 -*-
#
import logging

from functools import wraps
from sys import stderr
from typing import List, Optional, Tuple, Union

import owlrl
import rdflib

from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil.clone import mix_datasets


if owlrl.json_ld_available:
    import rdflib_jsonld  # noqa: F401

from rdflib import BNode, Literal, URIRef

from pyshacl.consts import (
    RDF_object,
    RDF_predicate,
    RDF_subject,
    RDF_type,
    RDFS_Resource,
    SH_conforms,
    SH_result,
    SH_resultMessage,
    SH_ValidationReport,
)
from pyshacl.errors import ReportableRuntimeError, ValidationFailure
from pyshacl.inference import CustomRDFSOWLRLSemantics, CustomRDFSSemantics
from pyshacl.monkey import apply_patches, rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.rdfutil import (
    clone_graph,
    clone_node,
    compare_blank_node,
    load_from_source,
    mix_graphs,
    order_graph_literal,
)
from pyshacl.rules import apply_rules, gather_functions, gather_rules
from pyshacl.shapes_graph import ShapesGraph


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
        options_dict.setdefault('advanced', False)
        options_dict.setdefault('inference', 'none')
        options_dict.setdefault('abort_on_error', False)
        if 'logger' not in options_dict:
            options_dict['logger'] = logging.getLogger(__name__)

    @classmethod
    def _run_pre_inference(
        cls, target_graph: GraphLike, inference_option: str, logger: Optional[logging.Logger] = None
    ):
        """
        Note, this is the OWL/RDFS pre-inference,
        it is not the Advanced Spec SHACL-Rule inferencing step.
        :param target_graph:
        :param inference_option:
        :return:
        """
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
                "Error during creation of OWL-RL Deductive Closure\n" "{}".format(str(e.args[0]))
            )
        if isinstance(target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            named_graphs = [
                rdflib.Graph(target_graph.store, i, namespace_manager=target_graph.namespace_manager)
                if not isinstance(i, rdflib.Graph)
                else i
                for i in target_graph.store.contexts(None)
            ]
        else:
            named_graphs = [target_graph]
        try:
            for g in named_graphs:
                inferencer.expand(g)
        except Exception as e:  # pragma: no cover
            logger.error("Error while running OWL-RL Deductive Closure")
            raise ReportableRuntimeError("Error while running OWL-RL Deductive Closure\n" "{}".format(str(e.args[0])))

    @classmethod
    def create_validation_report(cls, conforms: bool, results: List[Tuple]):
        v_text = "Validation Report\nConforms: {}\n".format(str(conforms))
        result_len = len(results)
        if not conforms:
            assert result_len > 0, "A Non-Conformant Validation Report must have at least one result."
        if result_len > 0:
            v_text += "Results ({}):\n".format(str(result_len))
        vg = rdflib.Graph()
        # for p, n in sg.namespace_manager.namespaces():
        #     vg.namespace_manager.bind(p, n)
        vr = BNode()
        vg.add((vr, RDF_type, SH_ValidationReport))
        vg.add((vr, SH_conforms, Literal(conforms)))
        for result in iter(results):
            _d, _bn, _tr = result
            v_text += _d
            vg.add((vr, SH_result, _bn))
            for tr in iter(_tr):
                s, p, o = tr
                if isinstance(o, tuple):
                    source = o[0]
                    node = o[1]
                    o = clone_node(source, node, vg)
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
        self.pre_inferenced = kwargs.pop('pre_inferenced', False)
        if not isinstance(data_graph, rdflib.Graph):
            raise RuntimeError("data_graph must be a rdflib Graph object")
        self.data_graph = data_graph
        self._target_graph = None
        self.ont_graph = ont_graph
        self.data_graph_is_multigraph = isinstance(self.data_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph))
        if self.ont_graph is not None and isinstance(self.ont_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            self.ont_graph.default_union = True

        if shacl_graph is None:
            shacl_graph = clone_graph(data_graph, identifier='shacl')
        assert isinstance(shacl_graph, rdflib.Graph), "shacl_graph must be a rdflib Graph object"
        self.shacl_graph = ShapesGraph(shacl_graph, self.logger)

    @property
    def target_graph(self):
        return self._target_graph

    def mix_in_ontology(self):
        if not self.data_graph_is_multigraph:
            return mix_graphs(self.data_graph, self.ont_graph)
        return mix_datasets(self.data_graph, self.ont_graph)

    def run(self):
        if self.ont_graph is not None:
            # creates a copy of self.data_graph, doesn't modify it
            the_target_graph = self.mix_in_ontology()
        else:
            the_target_graph = self.data_graph
        inference_option = self.options.get('inference', 'none')
        if inference_option:
            if self.pre_inferenced:
                the_target_graph = self._target_graph
            elif str(inference_option) != "none":
                self._run_pre_inference(the_target_graph, inference_option, self.logger)
                self.pre_inferenced = True
        self._target_graph = the_target_graph

        shapes = self.shacl_graph.shapes  # This property getter triggers shapes harvest.
        if self.options['advanced']:
            advanced = {'functions': gather_functions(self.shacl_graph), 'rules': gather_rules(self.shacl_graph)}
            for s in shapes:
                s.set_advanced(True)
        else:
            advanced = {}
        if isinstance(the_target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            named_graphs = [
                rdflib.Graph(the_target_graph.store, i, namespace_manager=the_target_graph.namespace_manager)
                if not isinstance(i, rdflib.Graph)
                else i
                for i in the_target_graph.store.contexts(None)
            ]
        else:
            named_graphs = [the_target_graph]
        reports = []
        non_conformant = False
        for g in named_graphs:
            if advanced:
                # TODO: apply functions?
                apply_rules(advanced['rules'], g)
            for s in shapes:
                _is_conform, _reports = s.validate(g)
                non_conformant = non_conformant or (not _is_conform)
                reports.extend(_reports)
        v_report, v_text = self.create_validation_report(not non_conformant, reports)
        return (not non_conformant), v_report, v_text


def with_metashacl_shacl_graph_cache(f):
    # noinspection PyPep8Naming
    EMPTY = object()

    @wraps(f)
    def wrapped(*args, **kwargs):
        graph_cache = getattr(wrapped, "graph_cache", None)
        assert graph_cache is not None
        if graph_cache is EMPTY:
            import pickle
            import sys

            from os import path

            if getattr(sys, 'frozen', False):
                # runs in a pyinstaller bundle
                here_dir = sys._MEIPASS
                pickle_file = path.join(here_dir, "shacl-shacl.pickle")
            else:
                here_dir = path.dirname(__file__)
                pickle_file = path.join(here_dir, "shacl-shacl.pickle")
            with open(pickle_file, 'rb') as shacl_pickle:
                u = pickle.Unpickler(shacl_pickle, fix_imports=False)
                shacl_shacl_store = u.load()
            shacl_shacl_graph = rdflib.Graph(store=shacl_shacl_store, identifier="http://www.w3.org/ns/shacl-shacl")
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
    data_graph: Union[GraphLike, str, bytes],
    *args,
    shacl_graph: Optional[Union[GraphLike, str, bytes]] = None,
    ont_graph: Optional[Union[GraphLike, str, bytes]] = None,
    advanced: Optional[bool] = False,
    inference: Optional[str] = None,
    abort_on_error: Optional[bool] = False,
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
    :param abort_on_error:
    :type abort_on_error: bool | None
    :param kwargs:
    :return:
    """

    if kwargs.get('debug', False):
        log_handler.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
    apply_patches()
    do_check_dash_result = kwargs.pop('check_dash_result', False)  # type: bool
    do_check_sht_result = kwargs.pop('check_sht_result', False)  # type: bool
    if kwargs.get('meta_shacl', False):
        to_meta_val = shacl_graph or data_graph
        conforms, v_r, v_t = meta_validate(to_meta_val, inference=inference, **kwargs)
        if not conforms:
            msg = "Shacl File does not validate against the Shacl Shapes Shacl file.\n{}".format(v_t)
            log.error(msg)
            raise ReportableRuntimeError(msg)
    do_owl_imports = kwargs.pop('do_owl_imports', False)
    data_graph_format = kwargs.pop('data_graph_format', None)
    # force no owl imports on data_graph
    data_graph = load_from_source(data_graph, rdf_format=data_graph_format, multigraph=True, do_owl_imports=False)
    ont_graph_format = kwargs.pop('ont_graph_format', None)
    if ont_graph is not None:
        ont_graph = load_from_source(
            ont_graph, rdf_format=ont_graph_format, multigraph=True, do_owl_imports=do_owl_imports
        )
    shacl_graph_format = kwargs.pop('shacl_graph_format', None)
    if shacl_graph is not None:
        # SHACL spec requires rdf BOOL literals to operate in a very specific way
        rdflib_bool_patch()
        shacl_graph = load_from_source(
            shacl_graph, rdf_format=shacl_graph_format, multigraph=True, do_owl_imports=do_owl_imports
        )
        rdflib_bool_unpatch()
    try:
        validator = Validator(
            data_graph,
            shacl_graph=shacl_graph,
            ont_graph=ont_graph,
            options={'inference': inference, 'abort_on_error': abort_on_error, 'advanced': advanced, 'logger': log},
        )
        conforms, report_graph, report_text = validator.run()
    except ValidationFailure as e:
        conforms = False
        report_graph = e
        report_text = "Validation Failure - {}".format(e.message)
    if do_check_dash_result:
        passes = check_dash_result(validator.target_graph, report_graph, shacl_graph or data_graph)
        return passes, report_graph, report_text
    if do_check_sht_result:
        (sht_graph, sht_result_node) = kwargs.pop('sht_validate', (False, None))
        if not sht_result_node:
            raise RuntimeError("Cannot check SHT result if SHT graph and result node are not given.")
        passes = check_sht_result(report_graph, sht_graph or shacl_graph or data_graph, sht_result_node)
        return passes, report_graph, report_text
    do_serialize_report_graph = kwargs.pop('serialize_report_graph', False)
    if do_serialize_report_graph and isinstance(report_graph, rdflib.Graph):
        if not (isinstance(do_serialize_report_graph, str)):
            do_serialize_report_graph = 'turtle'
        report_graph = report_graph.serialize(None, encoding='utf-8', format=do_serialize_report_graph)
    return conforms, report_graph, report_text


def clean_validation_reports(actual_graph, actual_report, expected_graph, expected_report):
    # remove rdfs-added stuff
    # remove resultMessage if expected_report does not include result_message
    # expected_graph.remove((expected_report, RDF_type, RDFS_Resource))
    # actual_graph.remove((actual_report, RDF_type, RDFS_Resource))
    expected_graph.remove((None, RDF_type, RDFS_Resource))
    actual_graph.remove((None, RDF_type, RDFS_Resource))
    expected_results = list(expected_graph.objects(expected_report, SH_result))
    actual_results = list(actual_graph.objects(actual_report, SH_result))
    er_has_messages = None
    for er in expected_results:
        expected_graph.remove((er, RDF_type, RDFS_Resource))
        er_has_messages = list(expected_graph.objects(er, SH_resultMessage))
        # sourceShapes = list(expected_graph.objects(er, SH_sourceShape))
        # for s in sourceShapes:
        #     expected_graph.remove((s, RDF_type, RDFS_Resource))
        # resultPaths = list(expected_graph.objects(er, SH_resultPath))
        # for r in resultPaths:
        #     expected_graph.remove((r, RDF_type, RDFS_Resource))
        # sourceConstraints = list(expected_graph.objects(er, SH_sourceConstraint))
        # for s in sourceConstraints:
        #     expected_graph.remove((s, RDF_type, RDFS_Resource))
    if er_has_messages and len(er_has_messages) > 0:
        # keep messages in actual
        pass
    else:
        for ar in actual_results:
            actual_graph.remove((ar, SH_resultMessage, None))
    return True


def compare_validation_reports(report_graph, expected_graph, expected_result):
    expected_conforms = expected_graph.objects(expected_result, SH_conforms)
    expected_conforms = set(expected_conforms)
    if len(expected_conforms) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expectedResult does not have an sh:conforms."
        )
    expected_conforms = next(iter(expected_conforms))
    expected_result_nodes = expected_graph.objects(expected_result, SH_result)
    expected_result_nodes = set(expected_result_nodes)
    expected_result_node_count = len(expected_result_nodes)

    validation_reports = report_graph.subjects(RDF_type, SH_ValidationReport)
    validation_reports = set(validation_reports)
    if len(validation_reports) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the validation report, the report graph does not contain a ValidationReport"
        )
    validation_report = next(iter(validation_reports))
    clean_validation_reports(report_graph, validation_report, expected_graph, expected_result)
    eq = compare_blank_node(report_graph, validation_report, expected_graph, expected_result)
    if eq != 0:
        return False
    report_conforms = report_graph.objects(validation_report, SH_conforms)
    report_conforms = set(report_conforms)
    if len(report_conforms) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the validation report, the report graph does not have an sh:conforms."
        )
    report_conforms = next(iter(report_conforms))

    if bool(expected_conforms.value) != bool(report_conforms.value):
        # TODO:coverage: write a test for this
        log.error("Expected Result Conforms value is different from Validation Report's Conforms value.")
        return False

    report_result_nodes = report_graph.objects(validation_report, SH_result)
    report_result_nodes = set(report_result_nodes)
    report_result_node_count = len(report_result_nodes)

    if expected_result_node_count != report_result_node_count:
        # TODO:coverage: write a test for this
        log.error(
            "Number of expected result's sh:result entries is different from Validation Report's sh:result entries.\n"
            "Expected {}, got {}.".format(expected_result_node_count, report_result_node_count)
        )
        return False
    return True


def compare_inferencing_reports(data_graph: GraphLike, expected_graph: GraphLike, expected_result: GraphLike):
    expected_object = set(expected_graph.objects(expected_result, RDF_object))
    if len(expected_object) < 1:
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expectedResult does not have an rdf:object."
        )
    expected_object = next(iter(expected_object))
    expected_subject = set(expected_graph.objects(expected_result, RDF_subject))
    if len(expected_subject) < 1:
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expectedResult does not have an rdf:subject."
        )
    expected_subject = next(iter(expected_subject))
    expected_predicate = set(expected_graph.objects(expected_result, RDF_predicate))
    if len(expected_predicate) < 1:
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expectedResult does not have an rdf:predicate."
        )
    expected_predicate = next(iter(expected_predicate))
    if isinstance(expected_object, Literal):
        found_objs = set(data_graph.objects(expected_subject, expected_predicate))
        if len(found_objs) < 1:
            return False
        found = False
        for o in found_objs:
            if isinstance(o, Literal):
                found = 0 == order_graph_literal(expected_graph, expected_object, data_graph, o)
        return found

    elif isinstance(expected_object, BNode):
        found_objs = set(data_graph.objects(expected_subject, expected_predicate))
        if len(found_objs) < 1:
            return False
        found = False
        for o in found_objs:
            if isinstance(o, BNode):
                found = 0 == compare_blank_node(expected_graph, expected_object, data_graph, o)
        return found
    else:
        found_triples = set(data_graph.triples((expected_subject, expected_predicate, expected_object)))
        if len(found_triples) < 1:
            return False
    return True


def check_dash_result(data_graph: GraphLike, report_graph: GraphLike, expected_result_graph: GraphLike):
    DASH = rdflib.namespace.Namespace('http://datashapes.org/dash#')
    DASH_GraphValidationTestCase = DASH.term('GraphValidationTestCase')
    DASH_InferencingTestCase = DASH.term('InferencingTestCase')
    DASH_expectedResult = DASH.term('expectedResult')

    gv_test_cases = expected_result_graph.subjects(RDF_type, DASH_GraphValidationTestCase)
    gv_test_cases = set(gv_test_cases)
    inf_test_cases = expected_result_graph.subjects(RDF_type, DASH_InferencingTestCase)
    inf_test_cases = set(inf_test_cases)

    if len(gv_test_cases) > 0:
        test_case = next(iter(gv_test_cases))
        expected_results = expected_result_graph.objects(test_case, DASH_expectedResult)
        expected_results = set(expected_results)
        if len(expected_results) < 1:  # pragma: no cover
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given GraphValidationTestCase does not have an expectedResult."
            )
        expected_result = next(iter(expected_results))
        gv_res = compare_validation_reports(report_graph, expected_result_graph, expected_result)
    else:
        gv_res = True
    if len(inf_test_cases) > 0:
        test_case = next(iter(inf_test_cases))
        expected_results = expected_result_graph.objects(test_case, DASH_expectedResult)
        expected_results = set(expected_results)
        if len(expected_results) < 1:  # pragma: no cover
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given InferencingTestCase does not have an expectedResult."
            )
        expected_result = next(iter(expected_results))
        inf_res = compare_inferencing_reports(data_graph, expected_result_graph, expected_result)
    else:
        inf_res = True
    if gv_res is None and inf_res is None:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expected result graph does not have a GraphValidationTestCase or InferencingTestCase."
        )
    return gv_res and inf_res


def check_sht_result(report_graph: GraphLike, sht_graph: GraphLike, sht_result_node: Union[URIRef, BNode]):
    SHT = rdflib.namespace.Namespace('http://www.w3.org/ns/shacl-test#')
    types = set(sht_graph.objects(sht_result_node, RDF_type))
    expected_failure = sht_result_node == SHT.Failure
    if expected_failure and isinstance(report_graph, ValidationFailure):
        return True
    elif isinstance(report_graph, ValidationFailure):
        # TODO:coverage: write a test for this
        log.error("Validation Report indicates a Validation Failure, but the SHT entry does not expect a failure.")
        return False
    elif expected_failure:
        # TODO:coverage: write a test for this
        log.error(
            "SHT expects a Validation Failure, but the Validation Report does not indicate a Validation Failure."
        )
        return False
    if SH_ValidationReport not in types:
        raise ReportableRuntimeError("SHT expected result must have type sh:ValidationReport")
    return compare_validation_reports(report_graph, sht_graph, sht_result_node)
