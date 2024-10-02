import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Union

import rdflib
from rdflib import BNode, Literal, URIRef
from rdflib.util import from_n3

from pyshacl.consts import (
    RDF_object,
    RDF_predicate,
    RDF_subject,
    RDF_type,
    RDFS_Resource,
    SH_conforms,
    SH_detail,
    SH_focusNode,
    SH_result,
    SH_resultMessage,
    SH_resultPath,
    SH_ValidationReport,
    SH_value,
)
from pyshacl.errors import ReportableRuntimeError, ValidationFailure
from pyshacl.functions import apply_functions, gather_functions
from pyshacl.pytypes import GraphLike, RDFNode
from pyshacl.rdfutil import compare_blank_node, compare_node, order_graph_literal, stringify_node

if TYPE_CHECKING:
    from pyshacl.validator import Validator


def clean_validation_reports(actual_graph, actual_report, expected_graph, expected_report):
    # remove rdfs-added stuff
    # remove resultMessage if expected_report does not include result_message
    # remove sh:detail if expected_report does not include details
    # expected_graph.remove((expected_report, RDF_type, RDFS_Resource))
    # actual_graph.remove((actual_report, RDF_type, RDFS_Resource))
    expected_graph.remove((None, RDF_type, RDFS_Resource))
    actual_graph.remove((None, RDF_type, RDFS_Resource))
    expected_results = list(expected_graph.objects(expected_report, SH_result))
    actual_results = list(actual_graph.objects(actual_report, SH_result))
    er_has_messages = None
    er_has_details = False
    for er in expected_results:
        expected_graph.remove((er, RDF_type, RDFS_Resource))
        er_has_messages = list(expected_graph.objects(er, SH_resultMessage))
        er_has_details = er_has_details or expected_graph.value(er, SH_detail) is not None
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
    if not er_has_details:
        # If no expected result had details, remove all details from actual
        for ar in actual_results:
            for detail in actual_graph.objects(ar, SH_detail):
                actual_graph -= actual_graph.cbd(detail)
                actual_graph.remove((ar, SH_detail, detail))
    return True


def compare_validation_reports(
    report_graph: GraphLike, expected_graph: GraphLike, expected_result, log: logging.Logger
):
    expected_conforms_i = expected_graph.objects(expected_result, SH_conforms)
    expected_conforms = set(expected_conforms_i)
    if len(expected_conforms) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expectedResult does not have an sh:conforms."
        )
    expected_conform = next(iter(expected_conforms))
    expected_result_nodes_i = expected_graph.objects(expected_result, SH_result)
    expected_result_nodes = list(expected_result_nodes_i)
    expected_result_node_count = len(expected_result_nodes)

    validation_reports = report_graph.subjects(RDF_type, SH_ValidationReport)
    validation_reports_set = set(validation_reports)
    if len(validation_reports_set) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the validation report, the report graph does not contain a ValidationReport"
        )
    validation_report = next(iter(validation_reports_set))
    clean_validation_reports(report_graph, validation_report, expected_graph, expected_result)
    eq = compare_blank_node(report_graph, validation_report, expected_graph, expected_result)
    if eq != 0:
        return False
    report_conforms_i = report_graph.objects(validation_report, SH_conforms)
    report_conforms = set(report_conforms_i)
    if len(report_conforms) < 1:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the validation report, the report graph does not have an sh:conforms."
        )
    report_conform = next(iter(report_conforms))

    if (
        isinstance(expected_conform, Literal)
        and isinstance(report_conform, Literal)
        and bool(expected_conform.value) != bool(report_conform.value)
    ):
        # TODO:coverage: write a test for this
        log.error("Expected Result Conforms value is different from Validation Report's Conforms value.")
        return False

    report_result_nodes_i = report_graph.objects(validation_report, SH_result)
    report_result_nodes = list(report_result_nodes_i)
    report_result_node_count = len(report_result_nodes)

    if expected_result_node_count != report_result_node_count:
        # TODO:coverage: write a test for this
        log.error(
            "Number of expected result's sh:result entries is different from Validation Report's sh:result entries.\n"
            "Expected {}, got {}.".format(expected_result_node_count, report_result_node_count)
        )
        return False

    expected_results_dict: Dict[Tuple[str, str, str], Any] = {}
    report_results_dict: Dict[Tuple[str, str, str], Any] = {}
    for result_nodes, result_graph, dest_dict in (
        (expected_result_nodes, expected_graph, expected_results_dict),
        (report_result_nodes, report_graph, report_results_dict),
    ):
        for result in result_nodes:
            result_focus_i = result_graph.objects(result, SH_focusNode)
            result_focus_list = list(result_focus_i)
            if len(result_focus_list) > 0:
                f_node = result_focus_list[0]
                if isinstance(f_node, Literal):
                    result_focus = str(f_node)
                elif isinstance(f_node, BNode):
                    # result_value = "_:" + str(v_node)
                    # Can't compare BNodes because they are
                    # different in the shapes graph than the data graph
                    result_focus = "BNode"
                else:
                    result_focus = stringify_node(result_graph, f_node)
            else:
                result_focus = ""
            result_value_i = result_graph.objects(result, SH_value)
            result_value_list = list(result_value_i)
            if len(result_value_list) > 0:
                v_node = result_value_list[0]
                if isinstance(v_node, Literal):
                    result_value = str(v_node)
                elif isinstance(v_node, BNode):
                    # result_value = "_:" + str(v_node)
                    # Can't compare BNodes because they are
                    # different in the shapes graph than the data graph
                    result_value = "BNode"
                else:
                    result_value = stringify_node(result_graph, v_node)
            else:
                result_value = ""
            result_path_i = result_graph.objects(result, SH_resultPath)
            result_path_list = list(result_path_i)
            if len(result_path_list) > 0:
                result_path = stringify_node(result_graph, result_path_list[0])
            else:
                result_path = ""
            dest_dict[(result_focus, result_value, result_path)] = result
    not_found_results = 0
    for expected_focus, expected_value, expected_path in expected_results_dict.keys():
        if (expected_focus, expected_value, expected_path) not in report_results_dict:
            log.error(
                "Expected result not found in Validation Report.\n"
                "Expected focus: {}, value: {}, path: {}.".format(expected_focus, expected_value, expected_path)
            )
            not_found_results += 1
    if not_found_results > 0:
        return False
    return True


def compare_inferencing_reports(data_graph: GraphLike, expected_graph: GraphLike, expected_results: Union[List, Set]):
    all_good = True
    for expected_result in expected_results:
        expected_objects = set(expected_graph.objects(expected_result, RDF_object))
        if len(expected_objects) < 1:
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given expectedResult does not have an rdf:object."
            )
        expected_object = next(iter(expected_objects))
        expected_subjects = set(expected_graph.objects(expected_result, RDF_subject))
        if len(expected_subjects) < 1:
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given expectedResult does not have an rdf:subject."
            )
        expected_subject = next(iter(expected_subjects))
        expected_predicates = set(expected_graph.objects(expected_result, RDF_predicate))
        if len(expected_predicates) < 1:
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given expectedResult does not have an rdf:predicate."
            )
        expected_predicate = next(iter(expected_predicates))
        if isinstance(expected_object, Literal):
            found_objs = set(data_graph.objects(expected_subject, expected_predicate))
            if len(found_objs) < 1:
                all_good = False
                print("Found no sub/pred matching {} {}".format(expected_subject, expected_predicate))
                continue
            found = False
            for o in found_objs:
                if isinstance(o, Literal):
                    found = 0 == order_graph_literal(expected_graph, expected_object, data_graph, o)
                    if found:
                        break
            if not found:
                print(
                    "Found no sub/pred/obj matching {} {} {}".format(
                        expected_subject, expected_predicate, expected_object
                    )
                )
            all_good = all_good and found
            continue

        elif isinstance(expected_object, BNode):
            found_objs = set(data_graph.objects(expected_subject, expected_predicate))
            if len(found_objs) < 1:
                all_good = False
                print("Found no sub/pred matching {} {}".format(expected_subject, expected_predicate))
                continue
            found = False
            for o in found_objs:
                if isinstance(o, BNode):
                    found = 0 == compare_blank_node(expected_graph, expected_object, data_graph, o)
                    if found:
                        break
            if not found:
                print(
                    "Found no sub/pred/obj matching {} {} {}".format(
                        expected_subject, expected_predicate, expected_object
                    )
                )
            all_good = all_good and found
            continue
        else:
            found_triples = set(data_graph.triples((expected_subject, expected_predicate, expected_object)))
            if len(found_triples) < 1:
                all_good = False

    return all_good


def check_dash_result(
    validator: 'Validator',
    report_graph: GraphLike,
    expected_result_graph: GraphLike,
    log: Union[logging.Logger, None] = None,
):
    DASH = rdflib.namespace.Namespace('http://datashapes.org/dash#')
    DASH_GraphValidationTestCase = DASH.GraphValidationTestCase
    DASH_InferencingTestCase = DASH.InferencingTestCase
    DASH_FunctionTestCase = DASH.FunctionTestCase
    DASH_expectedResult = DASH.expectedResult
    DASH_expression = DASH.expression
    was_default_union = None
    if log is None:
        log = logging.getLogger(__name__)
    if isinstance(expected_result_graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
        was_default_union = expected_result_graph.default_union
        expected_result_graph.default_union = True  # Force default-union to make all of this a bit easier
    gv_test_cases = expected_result_graph.subjects(RDF_type, DASH_GraphValidationTestCase)
    gv_test_cases_set = set(gv_test_cases)
    inf_test_cases = expected_result_graph.subjects(RDF_type, DASH_InferencingTestCase)
    inf_test_cases_set = set(inf_test_cases)
    fn_test_cases = expected_result_graph.subjects(RDF_type, DASH_FunctionTestCase)
    fn_test_cases_set = set(fn_test_cases)
    if len(gv_test_cases_set) > 0:
        test_case = next(iter(gv_test_cases_set))
        expected_results = expected_result_graph.objects(test_case, DASH_expectedResult)
        expected_results_set = set(expected_results)
        if len(expected_results_set) < 1:  # pragma: no cover
            raise ReportableRuntimeError(
                "Cannot check the expected result, the given GraphValidationTestCase does not have an expectedResult."
            )
        expected_result = next(iter(expected_results_set))
        gv_res: Union[bool, None] = compare_validation_reports(
            report_graph, expected_result_graph, expected_result, log
        )
    else:
        gv_res = None
    if len(inf_test_cases_set) > 0:
        data_graph = validator.target_graph
        if isinstance(data_graph, (rdflib.ConjunctiveGraph, rdflib.Dataset)):
            named_graphs = list(data_graph.contexts())
        else:
            named_graphs = [data_graph]
        inf_res: Union[bool, None] = True
        for test_case in inf_test_cases_set:
            expected_results = expected_result_graph.objects(test_case, DASH_expectedResult)
            expected_results_set = set(expected_results)
            if len(expected_results_set) < 1:  # pragma: no cover
                raise ReportableRuntimeError(
                    "Cannot check the expected result, the given InferencingTestCase does not have an expectedResult."
                )
            found = False
            for g in named_graphs:
                found = found or compare_inferencing_reports(g, expected_result_graph, expected_results_set)
            inf_res = inf_res and found
    else:
        inf_res = None
    if len(fn_test_cases_set) > 0:
        executor = validator.make_executor()
        data_graph = validator.target_graph
        fns = gather_functions(executor, validator.shacl_graph)
        apply_functions(executor, fns, data_graph)
        fn_res: Union[bool, None] = True
        for test_case in fn_test_cases_set:
            expected_results_set = set(expected_result_graph.objects(test_case, DASH_expectedResult))
            if len(expected_results_set) < 1:  # pragma: no cover
                raise ReportableRuntimeError(
                    "Cannot check the expected result, the given FunctionTestCase does not have an expectedResult."
                )
            expected_result = next(iter(expected_results_set))
            expressions = set(expected_result_graph.objects(test_case, DASH_expression))
            if len(expressions) < 1:
                raise ReportableRuntimeError(
                    "Cannot check the expected result, the given FunctionTestCase does not have an expression."
                )
            expression_node = next(iter(expressions))
            expression = str(expression_node).strip()
            parts = [e.strip() for e in expression.split("(", 1)]
            eargs: List[Optional[Union[str, RDFNode]]]
            if len(parts) < 1:
                expression = parts[0]
                eargs = []
            else:
                expression, sargs = parts
                sargs = sargs.rstrip(")")
                if len(sargs) < 1:
                    eargs_str_list: List[str] = []
                else:
                    eargs_str_list = [a.strip() for a in sargs.split(',')]
                eargs = []
                for e in eargs_str_list:
                    eargs.append(from_n3(e, None, expected_result_graph.store, expected_result_graph.namespace_manager))  # type: ignore[arg-type]
            find_uri = from_n3(expression, None, expected_result_graph.store, expected_result_graph.namespace_manager)  # type: ignore[arg-type]
            if find_uri is None or not isinstance(find_uri, (str, URIRef, Literal, BNode)):
                raise ReportableRuntimeError("Cannot execute function {}.\nBad declaration format.".format(find_uri))
            try:
                fn, options = validator.shacl_graph.get_shacl_function(find_uri)
            except KeyError:
                raise ReportableRuntimeError(
                    "Cannot execute function {}.\nCannot find it in the ShapesGraph object.".format(find_uri)
                )
            result = fn(data_graph, *eargs)
            fn_res = fn_res and 0 == compare_node(expected_result_graph, expected_result, data_graph, result)

    else:
        fn_res = None
    if was_default_union is not None:
        expected_result_graph.default_union = was_default_union
    if gv_res is None and inf_res is None and fn_res is None:  # pragma: no cover
        raise ReportableRuntimeError(
            "Cannot check the expected result, the given expected result graph does not have a GraphValidationTestCase or InferencingTestCase."
        )
    return (gv_res or gv_res is None) and (inf_res or inf_res is None) and (fn_res or fn_res is None)


def check_sht_result(
    report_graph: GraphLike,
    sht_graph: GraphLike,
    sht_result_node: Union[URIRef, BNode],
    log: Union[logging.Logger, None] = None,
):
    SHT = rdflib.namespace.Namespace('http://www.w3.org/ns/shacl-test#')
    types = set(sht_graph.objects(sht_result_node, RDF_type))
    expected_failure = sht_result_node == SHT.Failure
    if log is None:
        log = logging.getLogger(__name__)
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
    return compare_validation_reports(report_graph, sht_graph, sht_result_node, log)
