# -*- coding: utf-8 -*-
#
import itertools
import logging
import sys
from decimal import Decimal
from time import perf_counter
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Set, Type, Union

from rdflib import BNode, IdentifiedNode, Literal, URIRef

from .consts import (
    RDF_type,
    RDFS_Class,
    RDFS_subClassOf,
    SH_deactivated,
    SH_description,
    SH_Info,
    SH_jsFunctionName,
    SH_JSTarget,
    SH_JSTargetType,
    SH_message,
    SH_name,
    SH_order,
    SH_property,
    SH_resultSeverity,
    SH_select,
    SH_severity,
    SH_SPARQLTarget,
    SH_SPARQLTargetType,
    SH_target,
    SH_targetClass,
    SH_targetNode,
    SH_targetObjectsOf,
    SH_targetSubjectsOf,
    SH_Violation,
    SH_Warning,
)
from .errors import ConstraintLoadError, ConstraintLoadWarning, ReportableRuntimeError, ShapeLoadError
from .helper import get_query_helper_cls
from .helper.expression_helper import value_nodes_from_path
from .helper.path_helper import shacl_path_to_sparql_path
from .pytypes import GraphLike, RDFNode, SHACLExecutor

if TYPE_CHECKING:
    from pyshacl.constraints import ConstraintComponent
    from pyshacl.shapes_graph import ShapesGraph

module = sys.modules[__name__]


class Shape(object):
    __slots__ = (
        'logger',
        'sg',
        'node',
        '_p',
        '_path',
        '_advanced',
        '_deactivated',
        '_severity',
        '_messages',
        '_names',
        '_descriptions',
    )

    def __init__(
        self,
        sg: 'ShapesGraph',
        node: Union[URIRef, BNode],
        p=False,
        path: Optional[Union[URIRef, BNode]] = None,
        logger=None,
    ):
        """
        Shape
        :type sg: ShapesGraph
        :type node: URIRef | BNode
        :type p: bool
        :type path: URIRef | BNode | None
        :type logger: logging.Logger
        """
        self.logger = logger or logging.getLogger(__name__)
        self.sg = sg
        self.node = node
        self._p = p
        self._path = path
        self._advanced = False

        deactivated_vals = set(self.objects(SH_deactivated))
        if len(deactivated_vals) > 1:
            # TODO:coverage: we don't have any tests for invalid shapes
            raise ShapeLoadError(
                "A SHACL Shape cannot have more than one sh:deactivated predicate.",
                "https://www.w3.org/TR/shacl/#deactivated",
            )
        elif len(deactivated_vals) < 1:
            self._deactivated = False  # type: bool
        else:
            d = next(iter(deactivated_vals))
            if not isinstance(d, Literal):
                # TODO:coverage: we don't have any tests for invalid shapes
                raise ShapeLoadError(
                    "The value of sh:deactivated predicate on a SHACL Shape must be a Literal.",
                    "https://www.w3.org/TR/shacl/#deactivated",
                )
            self._deactivated = bool(d.value)
        severity = set(self.objects(SH_severity))
        if len(severity):
            self._severity = next(iter(severity))  # type: Union[URIRef, BNode, Literal]
        else:
            self._severity = SH_Violation
        messages = set(self.objects(SH_message))
        if len(messages):
            self._messages = messages  # type: Set
        else:
            self._messages = set()
        names = set(self.objects(SH_name))
        if len(names):
            self._names = names  # type: Set
        else:
            self._names = set()
        descriptions = set(self.objects(SH_description))
        if len(descriptions):
            self._descriptions = descriptions  # type: Set
        else:
            self._descriptions = set()

    def set_advanced(self, val):
        self._advanced = bool(val)

    def get_other_shape(self, shape_node):
        if self.sg.is_filtered_out_shape(shape_node):
            return None
        try:
            return self.sg.lookup_shape_from_node(shape_node)
        except (KeyError, AttributeError):
            # TODO:coverage: we never hit this during a successful test run
            return None

    @property
    def is_property_shape(self):
        return bool(self._p)

    def property_shapes(self):
        # TODO:coverage: this is never used?
        return self.sg.graph.objects(self.node, SH_property)

    @property
    def deactivated(self):
        return self._deactivated

    @property
    def severity(self):
        return self._severity

    @property
    def message(self):
        if self._messages is None:
            return
        for m in self._messages:
            yield m

    @property
    def name(self):
        if self._names is None:
            return
        for n in self._names:
            yield n

    def __str__(self):
        try:
            name = next(iter(self.name))
        except Exception:
            name = str(self.node)
        if self.is_property_shape:
            kind = "PropertyShape"
        else:
            kind = "NodeShape"
        return "<{} {}>".format(kind, name)

    def __repr__(self):
        if self.is_property_shape:
            p = "True"
        else:
            p = "False"
        names = list(self.name)
        if len(names):
            return "<Shape {} p={} node={}>".format(",".join(names), p, str(self.node))
        else:
            return "<Shape p={} node={}>".format(p, str(self.node))
        # return super(Shape, self).__repr__()

    @property
    def description(self):
        # TODO:coverage: this is never used?
        if self._descriptions is None:
            return
        for d in self._descriptions:
            yield d

    def objects(self, predicate=None):
        return self.sg.graph.objects(self.node, predicate)

    @property
    def order(self):
        order_nodes = list(self.objects(SH_order))
        if len(order_nodes) < 1:
            return Decimal("0.0")
        if len(order_nodes) > 1:
            raise ShapeLoadError(
                "A SHACL Shape can have only one sh:order property.", "https://www.w3.org/TR/shacl-af/#rules-order"
            )
        order_node = next(iter(order_nodes))
        if not isinstance(order_node, Literal):
            raise ShapeLoadError(
                "A SHACL Shape must be a numeric literal.", "https://www.w3.org/TR/shacl-af/#rules-order"
            )
        if isinstance(order_node.value, Decimal):
            order = order_node.value
        elif isinstance(order_node.value, int):
            order = Decimal(order_node.value)
        elif isinstance(order_node.value, float):
            order = Decimal(str(order_node.value))
        else:
            raise ShapeLoadError(
                "A SHACL Shape must be a numeric literal.", "https://www.w3.org/TR/shacl-af/#rules-order"
            )
        return order

    def target_nodes(self):
        return self.sg.graph.objects(self.node, SH_targetNode)

    def target_classes(self):
        return self.sg.graph.objects(self.node, SH_targetClass)

    def implicit_class_targets(self):
        types = list(self.sg.graph.objects(self.node, RDF_type))
        subclasses = list(self.sg.graph.subjects(RDFS_subClassOf, RDFS_Class))
        subclasses.append(RDFS_Class)
        for t in types:
            if t in subclasses:
                return [self.node]
        return []

    def target_objects_of(self):
        return self.sg.graph.objects(self.node, SH_targetObjectsOf)

    def target_subjects_of(self):
        return self.sg.graph.objects(self.node, SH_targetSubjectsOf)

    def path(self):
        if not self.is_property_shape:
            return None
        if self._path is not None:
            return self._path
        raise RuntimeError("property shape has no _path!")  # pragma: no cover

    def target(self):
        target_nodes = self.target_nodes()
        target_classes = self.target_classes()
        implicit_targets = self.implicit_class_targets()
        target_objects_of = self.target_objects_of()
        target_subjects_of = self.target_subjects_of()
        return (target_nodes, target_classes, implicit_targets, target_objects_of, target_subjects_of)

    def advanced_target(self):
        custom_targets = set(self.sg.objects(self.node, SH_target))
        result_set = dict()
        if self.sg.js_enabled:
            use_JSTarget: Union[bool, Type] = True
        else:
            use_JSTarget = False

        for c in custom_targets:
            ct = dict()
            selects = list(self.sg.objects(c, SH_select))
            has_select = len(selects) > 0
            fn_names = list(self.sg.objects(c, SH_jsFunctionName))
            has_fnname = len(fn_names) > 0
            is_types = set(self.sg.objects(c, RDF_type))
            if has_select or (SH_SPARQLTarget in is_types):
                ct['type'] = SH_SPARQLTarget
                SPARQLQueryHelper = get_query_helper_cls()
                qh = SPARQLQueryHelper(self, c, selects[0], deactivated=self._deactivated)
                qh.collect_prefixes()
                ct['qh'] = qh
            elif has_fnname or (SH_JSTarget in is_types):
                if use_JSTarget:
                    JST = getattr(module, "JSTarget", None)
                    if not JST:
                        # Lazy-import JS-Target to prevent RDFLib import error
                        from pyshacl.extras.js.target import JSTarget as JST

                        setattr(module, "JSTarget", JST)
                    ct['type'] = SH_JSTarget
                    ct['targeter'] = JST(self.sg, c)
                else:
                    #  Found JSTarget, but JS is not enabled in PySHACL. Ignore this target.
                    pass
            else:
                found_tt = None
                for t in is_types:
                    try:
                        found_tt = self.sg.get_shacl_target_type(t)
                        break
                    except LookupError:
                        continue
                if not found_tt:
                    msg = "None of these types match a TargetType: {}".format(" ".join(is_types))
                    raise ShapeLoadError(msg, "https://www.w3.org/TR/shacl-af/#SPARQLTargetType")
                bound_tt = found_tt.bind(self, c)
                ct['type'] = bound_tt.shacl_constraint_class()
                if ct['type'] == SH_SPARQLTargetType:
                    ct['qt'] = bound_tt
                elif ct['type'] == SH_JSTargetType:
                    ct['targeter'] = bound_tt
            result_set[c] = ct
        return result_set

    def focus_nodes(self, data_graph, debug=False):
        """
        The set of focus nodes for a shape may be identified as follows:

        specified in a shape using target declarations
        specified in any constraint that references a shape in parameters of shape-expecting constraint parameters (e.g. sh:node)
        specified as explicit input to the SHACL processor for validating a specific RDF term against a shape
        :return:
        """
        t1 = 0.0
        if debug:
            t1 = perf_counter()
        (target_nodes, target_classes, implicit_classes, target_objects_of, target_subjects_of) = self.target()
        if self._advanced:
            advanced_targets = self.advanced_target()
        else:
            advanced_targets = False
        found_node_targets = set()
        # Just add _all_ target_nodes to the set,
        # they don't need to actually exist in the graph
        found_node_targets.update(iter(target_nodes))
        target_classes = set(target_classes)
        target_classes.update(set(implicit_classes))
        found_target_instances = set()
        for tc in target_classes:
            s = data_graph.subjects(RDF_type, tc)
            found_target_instances.update(s)
            subc = data_graph.transitive_subjects(RDFS_subClassOf, tc)
            for subclass in iter(subc):
                if subclass == tc:
                    continue
                s1 = data_graph.subjects(RDF_type, subclass)
                found_target_instances.update(s1)
        found_node_targets.update(found_target_instances)
        found_target_subject_of = set()
        for s_of in target_subjects_of:
            subs = {s for s, o in data_graph.subject_objects(s_of)}
            found_target_subject_of.update(subs)
        found_node_targets.update(found_target_subject_of)
        found_target_object_of = set()
        for o_of in target_objects_of:
            objs = {o for s, o in data_graph.subject_objects(o_of)}
            found_target_object_of.update(objs)
        found_node_targets.update(found_target_object_of)
        if advanced_targets:
            for at_node, at in advanced_targets.items():
                if at['type'] == SH_SPARQLTarget:
                    qh = at['qh']
                    select = qh.apply_prefixes(qh.select_text)
                    results = data_graph.query(select, initBindings=None)
                    if not results or len(results.bindings) < 1:
                        continue
                    for r in results:
                        t = r['this']
                        found_node_targets.add(t)
                elif at['type'] in (SH_JSTarget, SH_JSTargetType):
                    results = at['targeter'].find_targets(data_graph)
                    for r in results:
                        found_node_targets.add(r)
                else:
                    results = at['qt'].find_targets(data_graph)
                    if not results or len(results.bindings) < 1:
                        continue
                    for r in results:
                        t = r['this']
                        found_node_targets.add(t)
        if debug:
            t2 = perf_counter()
            elapsed = t2 - t1
            self.logger.debug(f"Milliseconds to find focus nodes: {elapsed * 1000.0:.3f}ms")
        return found_node_targets

    @classmethod
    def make_focus_nodes_sparql_values(
        cls, target_classes_s: Set, implicit_classes_s: Set, target_objects_of_s: Set, target_subjects_of_s: Set
    ):
        init_bindings = {}
        values_keys = []
        values_vals = []
        if len(target_classes_s) > 1:
            values_keys.append("$targetClass")
            values_vals.append(list(target_classes_s))
        else:
            init_bindings["targetClass"] = next(iter(target_classes_s)) if len(target_classes_s) > 0 else "UNDEF"
        if len(implicit_classes_s) > 1:
            values_keys.append("$implicitClass")
            values_vals.append(list(implicit_classes_s))
        else:
            init_bindings["implicitClass"] = next(iter(implicit_classes_s)) if len(implicit_classes_s) > 0 else "UNDEF"
        if len(target_subjects_of_s) > 1:
            values_keys.append("$targetSubjectsOf")
            values_vals.append(list(target_subjects_of_s))
        else:
            init_bindings["targetSubjectsOf"] = (
                next(iter(target_subjects_of_s)) if len(target_subjects_of_s) > 0 else "UNDEF"
            )
        if len(target_objects_of_s) > 1:
            values_keys.append("$targetObjectsOf")
            values_vals.append(list(target_objects_of_s))
        else:
            init_bindings["targetObjectsOf"] = (
                next(iter(target_objects_of_s)) if len(target_objects_of_s) > 0 else "UNDEF"
            )
        if len(values_keys) < 1:
            return "", init_bindings
        else:
            values_clause = f"VALUES ({' '.join(values_keys)}) {{\n"
            product = itertools.product(*values_vals)
            for p in product:
                values_clause += f"\t( {' '.join(p_x.n3() for p_x in p)} )\n"
            values_clause += "}"
            return values_clause, init_bindings

    def focus_nodes_sparql(self, data_graph, debug=False):
        """
        The set of focus nodes for a shape may be identified as follows:

        specified in a shape using target declarations
        specified in any constraint that references a shape in parameters of shape-expecting constraint parameters (e.g. sh:node)
        specified as explicit input to the SHACL processor for validating a specific RDF term against a shape
        :return:
        """
        t1 = 0.0
        if debug:
            t1 = perf_counter()
        (target_nodes, target_classes, implicit_classes, target_objects_of, target_subjects_of) = self.target()
        if self._advanced:
            advanced_targets = self.advanced_target()
        else:
            advanced_targets = False
        found_node_targets = set()
        target_nodes = set(target_nodes)
        target_classes = set(target_classes)
        implicit_classes = set(implicit_classes)
        target_objects_of = set(target_objects_of)
        target_subjects_of = set(target_subjects_of)
        if all(
            (
                advanced_targets is False,
                len(target_nodes) < 1,
                len(target_classes) < 1,
                len(implicit_classes) < 1,
                len(target_objects_of) < 1,
                len(target_subjects_of) < 1,
            )
        ):
            return found_node_targets

        found_node_targets.update(target_nodes)
        if (
            advanced_targets is False
            and len(target_classes) < 1
            and len(implicit_classes) < 1
            and len(target_objects_of) < 1
            and len(target_subjects_of) < 1
        ):
            return found_node_targets
        if (
            len(target_classes) > 0
            or len(implicit_classes) > 0
            or len(target_objects_of) > 0
            or len(target_subjects_of) > 0
        ):
            focus_query = """\
            SELECT ?targetClass_F ?targetSubjectsOf_F ?targetObjectsOf_F WHERE {
                {VALUES_CLAUSE}
                OPTIONAL { {
                ?targetClass_F rdf:type/rdfs:subClassOf* $targetClass .
                } UNION {
                ?targetClass_F rdf:type/rdfs:subClassOf* $implicitClass .
                }. }
                OPTIONAL { ?targetSubjectsOf_F $targetSubjectsOf ?anyA . }
                OPTIONAL {?anyB $targetObjectsOf ?targetObjectsOf_F . }
            }
            """
            values_clause, init_bindings = self.make_focus_nodes_sparql_values(
                target_classes, implicit_classes, target_objects_of, target_subjects_of
            )
            new_query = focus_query.replace("{VALUES_CLAUSE}", values_clause)
            try:
                resp = data_graph.query(new_query, initBindings=init_bindings)
            except Exception as e:
                print(new_query)
                raise e
            if len(resp) > 0:
                for result_set in resp:
                    target_class_f, target_subjects_of_f, target_objects_of_f = result_set
                    if target_class_f is not None and target_class_f != "UNDEF":
                        found_node_targets.add(target_class_f)
                    if target_subjects_of_f is not None and target_subjects_of_f != "UNDEF":
                        found_node_targets.add(target_subjects_of_f)
                    if target_objects_of_f is not None and target_objects_of_f != "UNDEF":
                        found_node_targets.add(target_objects_of_f)
        if advanced_targets:
            for at_node, at in advanced_targets.items():
                if at['type'] == SH_SPARQLTarget:
                    qh = at['qh']
                    select = qh.apply_prefixes(qh.select_text)
                    results = data_graph.query(select, initBindings=None)
                    if not results or len(results.bindings) < 1:
                        continue
                    for r in results:
                        t = r['this']
                        found_node_targets.add(t)
                elif at['type'] in (SH_JSTarget, SH_JSTargetType):
                    raise ReportableRuntimeError(
                        "SHACL Advanced Targets with JSTargets are not yet implemented in SPARQL Remote Graph Mode."
                    )
                else:
                    results = at['qt'].find_targets(data_graph)
                    if not results or len(results.bindings) < 1:
                        continue
                    for r in results:
                        t = r['this']
                        found_node_targets.add(t)
        if debug:
            t2 = perf_counter()
            elapsed = t2 - t1
            self.logger.debug(f"Milliseconds to find focus nodes: {elapsed * 1000.0:.3f}ms")
        return found_node_targets

    def value_nodes(self, target_graph, focus, sparql_mode: bool = False, debug: bool = False):
        """
        For each focus node, you can get a set of value nodes.
        For a Node Shape, each focus node has just one value node,
            which is just the focus_node
        :param target_graph:
        :param focus:
        :param sparql_mode:
        :type sparql_mode: bool
        :param debug:
        :type debug: bool
        :return:
        """
        t1 = 0.0
        if debug:
            t1 = perf_counter()
        if not isinstance(focus, (tuple, list, set)):
            focus = [focus]
        if not self.is_property_shape:
            if debug:
                t2 = perf_counter()
                elapsed = t2 - t1
                self.logger.debug(f"Milliseconds to find value nodes for focus nodes: {elapsed * 1000.0:.3f}ms")
            return {f: set((f,)) for f in focus}
        path_val = self.path()

        focus_dict: Dict[RDFNode, Set[RDFNode]] = {}
        if sparql_mode:
            # Shortcut for simple URI path, path rewriting and everything else
            if isinstance(path_val, URIRef):
                sparql_path = path_val.n3(namespace_manager=target_graph.namespace_manager)
            else:
                prefixes = dict(target_graph.namespace_manager.namespaces())
                sparql_path = shacl_path_to_sparql_path(self.sg, path_val, prefixes=prefixes)
            values_query = f"SELECT {' '.join(f'?v{i}' for i, _ in enumerate(focus))} WHERE {{\n"
            init_bindings = {}
            for i, f in enumerate(focus):
                focus_dict[f] = set()
                values_query += f"OPTIONAL {{ \t$f{i} {sparql_path} ?v{i} . }}\n"
                init_bindings[f"f{i}"] = f
            values_query += "}"
            try:
                results = target_graph.query(values_query, initBindings=init_bindings)
            except Exception as e:
                print(e)
                raise
            if len(results) > 0:
                for r in results:
                    for i, f in enumerate(focus):
                        row_focus_result = r[i]
                        if row_focus_result is None or row_focus_result == "UNDEF":
                            continue
                        focus_dict[f].add(row_focus_result)
            else:
                pass
        else:
            for f in focus:
                focus_dict[f] = value_nodes_from_path(self.sg, f, path_val, target_graph)
        if debug:
            t2 = perf_counter()
            elapsed = t2 - t1
            self.logger.debug(f"Milliseconds to find value nodes for focus nodes: {elapsed * 1000.0:.3f}ms")
        return focus_dict

    def find_custom_constraints(self):
        applicable_custom_constraints = set()
        for c in self.sg.custom_constraints:
            mandatory = (p for p in c.parameters if not p.optional)
            found_all_mandatory = True
            for mandatory_param in mandatory:
                path = mandatory_param.path()
                assert isinstance(path, URIRef)
                found_vals = set(self.sg.objects(self.node, path))
                # found_vals = value_nodes_from_path(self.node, mandatory_param.path(), self.sg.graph)
                found_all_mandatory = found_all_mandatory and bool(len(found_vals) > 0)
            if found_all_mandatory:
                applicable_custom_constraints.add(c)
        return applicable_custom_constraints

    def validate(
        self,
        executor: SHACLExecutor,
        target_graph: GraphLike,
        focus: Optional[
            Union[
                Sequence[RDFNode],
                RDFNode,
            ]
        ] = None,
        _evaluation_path: Optional[List] = None,
    ):
        if self.deactivated:
            if executor.debug:
                self.logger.debug(f"Skipping shape because it is deactivated: {str(self)}")
            return True, []
        focus_list: Sequence[RDFNode]
        if focus is not None:
            lh_shape = False
            rh_shape = True
            self.logger.debug(f"Running evaluation of Shape {str(self)}")
            # Passed in Focus node _can_ be a Literal, happens in PropertyShapes
            # when the path resolves to a literal or set of Literals
            if isinstance(focus, (IdentifiedNode, Literal)):
                focus_list = [focus]
            else:
                focus_list = list(focus)
            self.logger.debug(f"Shape was passed {len(focus_list)} Focus Node/s to evaluate.")
        else:
            lh_shape = True
            rh_shape = False
            self.logger.debug(f"Checking if Shape {str(self)} defines its own targets.")
            self.logger.debug("Identifying targets to find focus nodes.")
            if executor.sparql_mode:
                focus_set = self.focus_nodes_sparql(target_graph, debug=executor.debug)
            else:
                focus_set = self.focus_nodes(target_graph, debug=executor.debug)
            focus_list = list(focus_set)
            self.logger.debug(f"Found {len(focus_list)} Focus Nodes to evaluate.")

        if len(focus_list) < 1:
            # It's possible for shapes to have _no_ focus nodes
            # (they are called in other ways)
            if executor.debug:
                self.logger.debug(f"Skipping shape {str(self)} because it found no focus nodes.")
            return True, []
        else:
            self.logger.debug(f"Running evaluation of Shape {str(self)}")

        if executor.focus_nodes is not None and len(executor.focus_nodes) > 0:
            filtered_focus_nodes: List[Union[URIRef]] = []
            for _fo in focus_list:  # type: RDFNode
                if isinstance(_fo, URIRef) and _fo in executor.focus_nodes:
                    filtered_focus_nodes.append(_fo)
            len_orig_focus = len(focus_list)
            len_filtered_focus = len(filtered_focus_nodes)
            if len_filtered_focus < 1:
                self.logger.debug(f"Skipping shape {str(self)} because specified focus nodes are not targeted.")
                return True, []
            elif len_filtered_focus != len_orig_focus:
                self.logger.debug(
                    f"Filtered focus nodes based on focus_nodes option. Only {len_filtered_focus} of {len_orig_focus} focus nodes remain."
                )
            focus_list = filtered_focus_nodes
        t1 = ct1 = 0.0  # prevent warnings about use-before-assign
        collect_stats = bool(executor.debug)

        if _evaluation_path is None:
            _evaluation_path = []
        else:
            validation_depth = len(_evaluation_path) // 2

            if validation_depth >= executor.max_validation_depth:
                # depth of 14 (_evaluation_length=28) is the depth required to
                # successfully do the meta-shacl test on shacl.ttl
                path_str = " -> ".join((str(e) for e in _evaluation_path))
                raise ReportableRuntimeError("Validation path too deep!\n{}".format(path_str))
        if collect_stats:
            t1 = perf_counter()
        # Lazy import here to avoid an import loop
        CONSTRAINT_PARAMETERS, PARAMETER_MAP = getattr(module, 'CONSTRAINT_PARAMS', (None, None))
        if not CONSTRAINT_PARAMETERS or not PARAMETER_MAP:
            from .constraints import ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP

            setattr(module, 'CONSTRAINT_PARAMS', (ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP))
            CONSTRAINT_PARAMETERS = ALL_CONSTRAINT_PARAMETERS
            PARAMETER_MAP = CONSTRAINT_PARAMETERS_MAP
        if self.sg.js_enabled or self._advanced:
            search_parameters = CONSTRAINT_PARAMETERS.copy()
            constraint_map = PARAMETER_MAP.copy()
            if self._advanced:
                from pyshacl.constraints.advanced import ExpressionConstraint, SH_expression

                search_parameters.append(SH_expression)
                constraint_map[SH_expression] = ExpressionConstraint
            if self.sg.js_enabled:
                from pyshacl.extras.js.constraint import JSConstraint, SH_js

                search_parameters.append(SH_js)
                constraint_map[SH_js] = JSConstraint
        else:
            search_parameters = CONSTRAINT_PARAMETERS
            constraint_map = PARAMETER_MAP
        parameters = (p for p, v in self.sg.predicate_objects(self.node) if p in search_parameters)
        reports = []
        focus_value_nodes = self.value_nodes(
            target_graph, focus_list, sparql_mode=executor.sparql_mode, debug=executor.debug
        )
        filter_reports: bool = False
        allow_conform: bool = False
        allowed_severities: Set[URIRef] = set()
        if executor.allow_infos:
            allowed_severities.add(SH_Info)
        if executor.allow_warnings:
            allowed_severities.add(SH_Info)
            allowed_severities.add(SH_Warning)
        if executor.allow_infos or executor.allow_warnings:
            if self.severity in allowed_severities:
                allow_conform = True
            else:
                filter_reports = True

        non_conformant = False
        done_constraints = set()
        run_count = 0
        _evaluation_path.append(self)
        if executor.debug:
            path_str = " -> ".join((str(e) for e in _evaluation_path))
            self.logger.debug(f"Current shape evaluation path: {path_str}")
        constraint_components = [constraint_map[p] for p in iter(parameters)]
        constraint_component: Type['ConstraintComponent']
        for constraint_component in constraint_components:
            if constraint_component in done_constraints:
                continue
            try:
                # if executor.debug:
                #     self.logger.debug(f"Constructing Constraint Component: {repr(constraint_component)}")
                c = constraint_component(self)
            except ConstraintLoadWarning as w:
                self.logger.warning(repr(w))
                continue
            except ConstraintLoadError as e:
                self.logger.error(repr(e))
                raise e
            _e_p_copy = _evaluation_path[:]
            _e_p_copy.append(c)
            if executor.debug:
                self.logger.debug(f"Checking conformance for constraint: {str(c)}")
            if collect_stats:
                ct1 = perf_counter()
            if executor.debug:
                path_str = " -> ".join((str(e) for e in _e_p_copy))
                self.logger.debug(f"Current constraint evaluation path: {path_str}")
            _is_conform, _reports = c.evaluate(executor, target_graph, focus_value_nodes, _e_p_copy)
            if executor.debug:
                if collect_stats:
                    ct2 = perf_counter()
                    elapsed = ct2 - ct1
                    self.logger.debug(f"Milliseconds to check constraint {str(c)}: {elapsed * 1000.0:.3f}ms")
                if _is_conform:
                    self.logger.debug(f"DataGraph conforms to constraint {c}.")
                elif allow_conform:
                    self.logger.debug(f"Focus nodes do _not_ conform to constraint {c} but given severity is allowed.")
                else:
                    self.logger.debug(f"Focus nodes do _not_ conform to constraint {c}.")
                    if lh_shape or (not rh_shape):
                        for v_str, v_node, v_parts in _reports:
                            self.logger.debug(v_str)

            if _is_conform or allow_conform:
                ...
            elif filter_reports:
                all_allow = True
                for v_str, v_node, v_parts in _reports:
                    severity_bits = list(filter(lambda p: p[0] == v_node and p[1] == SH_resultSeverity, v_parts))
                    if severity_bits:
                        all_allow = all_allow and (severity_bits[0][2] in allowed_severities)
                non_conformant = non_conformant or (not all_allow)
            else:
                non_conformant = non_conformant or (not _is_conform)
            reports.extend(_reports)
            run_count += 1
            done_constraints.add(constraint_component)
            if non_conformant and executor.abort_on_first:
                break
        applicable_custom_constraints = self.find_custom_constraints()
        for a in applicable_custom_constraints:
            if non_conformant and executor.abort_on_first:
                break
            _e_p_copy2 = _evaluation_path[:]
            validator = a.make_validator_for_shape(self)
            _e_p_copy2.append(validator)
            _is_conform, _r = validator.evaluate(executor, target_graph, focus_value_nodes, _e_p_copy2)
            non_conformant = non_conformant or (not _is_conform)
            reports.extend(_r)
            run_count += 1
        if collect_stats:
            t2 = perf_counter()
            elapsed = t2 - t1
            self.logger.debug(f"Milliseconds to evaluate shape {str(self)}: {elapsed * 1000.0:.3f}ms")
        # print(_evaluation_path, "Passes" if not non_conformant else "Fails")
        return (not non_conformant), reports
