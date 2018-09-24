# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraints
"""
import re
import rdflib
from rdflib import RDF, XSD

from pyshacl.constraints.constraint_component import ConstraintComponent
from pyshacl.consts import SH, SH_message, SH_deactivated, SH_inversePath, SH_alternativePath, SH_zeroOrMorePath, \
    SH_oneOrMorePath, SH_zeroOrOnePath, SH_prefixes, SH_prefix, SH_namespace
from pyshacl.errors import ConstraintLoadError, ValidationFailure, ReportableRuntimeError

SH_sparql = SH.term('sparql')
SH_select = SH.term('select')
SH_declare = SH.term('declare')

SH_SPARQLConstraintComponent = SH.term('SPARQLConstraintComponent')


class SPARQLQueryHelper(object):
    bind_this_regex = re.compile(r"([\s{}()])[\$\?]this", flags=re.M)
    bind_value_regex = re.compile(r"([\s{}()])[\$\?]value", flags=re.M)
    bind_path_regex = re.compile(r"([\s{}()])[\$\?]PATH", flags=re.M)
    bind_sg_regex = re.compile(r"([\s{}()])[\$\?]shapesGraph", flags=re.M)
    bind_cs_regex = re.compile(r"([\s{}()])[\$\?]currentShape", flags=re.M)
    has_minus_regex = re.compile(r"[^\?\$]MINUS[\s\{]", flags=re.M | re.I)
    has_values_regex = re.compile(r"[^\?\$]VALUES[\s\{]", flags=re.M | re.I)
    has_service_regex = re.compile(r"[^\?\$]SERVICE[\s\<]", flags=re.M | re.I)
    has_nested_select_regex = re.compile(r"SELECT[\s\(\)\$\?\a-z]*\{[^\}]*SELECT\s+((?:(?:[\?\$]\w+\s+)|(?:\*\s+))+)", flags=re.M | re.I)
    has_as_var_regex = re.compile(r"[^\w]+AS[\s]+[\$\?](\w+)", flags=re.M | re.I)


    def __init__(self, shape, node, select_text, messages=None, deactivated=False):
        self.shape = shape
        self.node = node
        self.select_text = select_text
        self.messages = messages
        self.deactivated = deactivated
        self.prefixes = {}

    def collect_prefixes(self):
        sg = self.shape.sg.graph
        prefixes_vals = set(sg.objects(self.node, SH_prefixes))
        if len(prefixes_vals) < 1:
            return
        for prefixes_val in iter(prefixes_vals):
            find_declares = set(sg.objects(prefixes_val, SH_declare))
            for dec in iter(find_declares):
                if isinstance(dec, rdflib.Literal):
                    raise ConstraintLoadError(
                        "sh:declare value must be either a URIRef or a BNode.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes")
                prefix_vals = set(sg.objects(dec, SH_prefix))
                if len(prefix_vals) < 1 or len(prefix_vals) > 1:
                    raise ConstraintLoadError(
                        "sh:declare must have exactly one sh:prefix predicate.",
                         "https://www.w3.org/TR/shacl/#sparql-prefixes")
                prefix = next(iter(prefix_vals))
                if not (isinstance(prefix, rdflib.Literal) and
                        isinstance(prefix.value, str)):
                    raise ConstraintLoadError(
                        "sh:prefix value must be an RDF Literal with type xsd:string.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes")
                prefix = str(prefix.value)
                namespace_vals = set(sg.objects(dec, SH_namespace))
                if len(namespace_vals) < 1 or len(namespace_vals) > 1:
                    raise ConstraintLoadError(
                        "sh:declare must have exactly one sh:namespace predicate.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes")
                namespace = next(iter(namespace_vals))
                if not (isinstance(namespace, rdflib.Literal) and
                        namespace.datatype == XSD.anyURI):
                    raise ConstraintLoadError(
                        "sh:namespace value must be an RDF Literal with type xsd:anyURI.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes")
                namespace = rdflib.URIRef(str(namespace.value))
                self.prefixes[prefix] = namespace

    def apply_prefixes(self, sparql):
        prefix_string = ""
        for p, ns in self.prefixes.items():
            prefix_string += "PREFIX {}: <{}>\n".format(
                str(p), str(ns)
            )
        return "{}\n{}".format(prefix_string, sparql)

    def _shacl_path_to_sparql_path(self, path_val, recursion=0):
        """

        :param path_val:
        :type path_val: rdflib.term.Node
        :param recursion:
        :type recursion: int
        :returns: string
        :rtype: str
        """
        sg = self.shape.sg
        # Link: https://www.w3.org/TR/shacl/#property-paths
        if isinstance(path_val, rdflib.URIRef):
            string_uri = str(path_val)
            for p, ns in self.prefixes.items():
                if string_uri.startswith(ns):
                    string_uri = ':'.join([p, string_uri.replace(ns, '')])
                    return string_uri
            return "<{}>".format(string_uri)
        elif isinstance(path_val, rdflib.Literal):
            raise ReportableRuntimeError(
                "Values of a property path cannot be a Literal.")
        # At this point, path_val _must_ be a BNode
        # TODO, the path_val BNode must be value of exactly one sh:path subject in the SG.
        if recursion >= 10:
            raise ReportableRuntimeError("Path traversal depth is too much!")
        sequence_list = set(sg.objects(path_val, RDF.first))
        if len(sequence_list) > 0:
            all_collected = []
            for s in sg.items(sequence_list):
                seq1_string = self._shacl_path_to_sparql_path(
                              s, recursion=recursion + 1)
                all_collected.append(seq1_string)
            if len(all_collected) < 2:
                raise ReportableRuntimeError(
                    "List of SHACL sequence paths "
                    "must have alt least two path items.")
            return "/".join(all_collected)

        find_inverse = set(sg.objects(path_val, SH_inversePath))
        if len(find_inverse) > 0:
            inverse_path = next(iter(find_inverse))
            inverse_path_string = self._shacl_path_to_sparql_path(
                                  inverse_path, recursion=recursion + 1)
            return "^{}".format(inverse_path_string)

        find_alternatives = set(sg.objects(path_val, SH_alternativePath))
        if len(find_alternatives) > 0:
            alternatives_list = next(iter(find_alternatives))
            all_collected = []
            for a in sg.items(alternatives_list):
                alt1_string = self._shacl_path_to_sparql_path(
                              a, recursion=recursion + 1)
                all_collected.append(alt1_string)
            if len(all_collected) < 2:
                raise ReportableRuntimeError(
                    "List of SHACL alternate paths "
                    "must have alt least two path items.")
            return "|".join(all_collected)

        find_zero_or_more = set(sg.objects(path_val, SH_zeroOrMorePath))
        if len(find_zero_or_more) > 0:
            zero_or_more_path = next(iter(find_zero_or_more))
            zom_path_string = self._shacl_path_to_sparql_path(
                              zero_or_more_path, recursion=recursion + 1)
            return "{}*".format(zom_path_string)

        find_zero_or_one = set(sg.objects(path_val, SH_zeroOrOnePath))
        if len(find_zero_or_one) > 0:
            zero_or_one_path = next(iter(find_zero_or_one))
            zoo_path_string = self._shacl_path_to_sparql_path(
                              zero_or_one_path, recursion=recursion + 1)
            return "{}?".format(zoo_path_string)

        find_one_or_more = set(sg.objects(path_val, SH_oneOrMorePath))
        if len(find_one_or_more) > 0:
            one_or_more_path = next(iter(find_one_or_more))
            oom_path_string = self._shacl_path_to_sparql_path(
                              one_or_more_path, recursion=recursion + 1)
            return "{}+".format(oom_path_string)

        raise NotImplementedError(
            "That path method to get value nodes of property shapes is not yet implemented.")

    @classmethod
    def _node_to_sparql_text(cls, node):
        if isinstance(node, rdflib.Literal):
            if isinstance(node.value, str):
                node_text = "\"{}\"".format(node.value)
            else:
                node_text = str(node.value)
            if node.language:
                node_text = "{}@{}".format(
                    node_text, str(node.language))
            elif node.datatype:
                node_text = "{}^^{}".format(
                    node_text, cls._node_to_sparql_text(node.datatype))
            return node_text
        elif isinstance(node, rdflib.URIRef):
            return "<{}>".format(str(node))
        elif isinstance(node, rdflib.BNode):
            # I think this works to convert a BNode to its internal id.
            return str(node)
        elif isinstance(node, str):
            return node
        raise NotImplementedError("Cannot turn that kind of node into text.")

    def check_invalid_sparql(self, sparql_text, valuenode=None, extravars=None):
        has_minus = self.has_minus_regex.search(sparql_text)
        if has_minus:
            raise ValidationFailure("A SPARQL Constraint must not contain a MINUS clause.")
        has_values = self.has_values_regex.search(sparql_text)
        if has_values:
            raise ValidationFailure("A SPARQL Constraint must not contain a VALUES clause.")
        has_service = self.has_service_regex.search(sparql_text)
        if has_service:
            raise ValidationFailure("A SPARQL Constraint must not contain a federated query (SERVICE).")
        potentially_prebound_variables = {'this', 'shapesGraph', 'currentShape'}
        if valuenode is not None:
            potentially_prebound_variables.add('value')
        if extravars is not None and len(extravars) > 0:
            potentially_prebound_variables.update(extravars)
        has_nested_select = self.has_nested_select_regex.search(sparql_text)
        if has_nested_select:
            var_string = has_nested_select.group(1)
            vars = var_string.split()
            if len(vars) == 0:
                raise ValidationFailure("Ill-formed nested SELECT statement found.")
            stripped_vars = [v.lstrip('$?').rstrip() for v in vars]
            if len(stripped_vars) == 1 and stripped_vars[0] == "*":
                raise ValidationFailure(
                    "Using 'SELECT *' in a nested SELECT query does not select potentially pre-bound variables.\n"
                    "See https://github.com/w3c/data-shapes/issues/84.")
            for p in potentially_prebound_variables:
                if p not in stripped_vars:
                    # these are optional:
                    if p == "shapesGraph" or p == "currentShape":
                        continue
                    raise ValidationFailure("All potentially pre-bound variables must be selected from a nested SELECT query.\n"
                                            "Potentially pre-bound variables for this query are: {}.".format(", ".join(potentially_prebound_variables)))
        has_as_var = self.has_as_var_regex.search(sparql_text)
        if has_as_var:
            var_name = has_as_var.group(1)
            if var_name in potentially_prebound_variables:
                raise ValidationFailure(
                    "Cannot use AS to re-bind potentially pre-bound variables such as {}".format(var_name))
        return True

    def pre_bind_variables(self, thisnode, valuenode=None, extravars=None):
        new_query_text = ""+self.select_text
        valid = self.check_invalid_sparql(new_query_text, valuenode=valuenode, extravars=extravars)
        init_bindings = {}
        found_this = self.bind_this_regex.search(new_query_text)
        if found_this:
            init_bindings['this'] = thisnode

        if valuenode:
            found_value = self.bind_value_regex.search(new_query_text)
            if found_value:
                init_bindings['value'] = valuenode

        found_cs = self.bind_cs_regex.search(new_query_text)
        if found_cs:
            init_bindings['currentShape'] = self.shape.node
        path = self.shape.path()
        if path:
            path_string = self._shacl_path_to_sparql_path(path)
            new_query_text = self.bind_path_regex.sub(
                             "\g<1>{}".format(path_string),
                             new_query_text)
        else:
            found_path = self.bind_path_regex.search(new_query_text)
            if found_path:
                raise ReportableRuntimeError(
                    "SPARQL Constraint text has $PATH in it, "
                    "but no path is known on this Shape.")
        #TODO: work out how to get shapesGraph binding from shape.sg
        #shapes_graph = self.shape.sg
        shapes_graph = False
        if shapes_graph:
            found_sg = self.bind_sg_regex.search(new_query_text)
            if found_sg:
                init_bindings['shapesGraph'] = shapes_graph
        else:
            found_sg = self.bind_sg_regex.search(new_query_text)
            if found_sg:
                raise NotImplementedError(
                    "SPARQL Constraint text has $shapesGraph in it, "
                    "but Shapes Graph is not currently supported.")

        return init_bindings, new_query_text


class SPARQLBasedConstraint(ConstraintComponent):
    """
    SHACL-SPARQL supports a constraint component that can be used to express restrictions based on a SPARQL SELECT query.
    Link:
    https://www.w3.org/TR/shacl/#sparql-constraints
    """

    def __init__(self, shape):
        super(SPARQLBasedConstraint, self).__init__(shape)
        sg = self.shape.sg.graph
        sparql_node_list = set(self.shape.objects(SH_sparql))
        if len(sparql_node_list) < 1:
            raise ConstraintLoadError(
                "SPARQLConstraintComponent must have at least one sh:sparql predicate.",
                "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
        sparql_constraints = set()
        for s in iter(sparql_node_list):
            select_node_list = set(sg.objects(s, SH_select))
            if len(select_node_list) < 1:
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must have "
                    "at least one sh:select predicate.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
            elif len(select_node_list) > 1:
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must have "
                    "at most one sh:select predicate.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
            select_node = next(iter(select_node_list))
            if not (isinstance(select_node, rdflib.Literal) and
                    isinstance(select_node.value, str)):
                raise ConstraintLoadError(
                    "SPARQLConstraintComponent value for sh:select must be "
                    "a Literal with type xsd:string.",
                    "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
            query_helper = SPARQLQueryHelper(self.shape, s, select_node.value)
            message_node_list = set(sg.objects(s, SH_message))
            if len(message_node_list) > 0:
                message = next(iter(message_node_list))
                if not (isinstance(message, rdflib.Literal) and
                        isinstance(message.value, str)):
                    raise ConstraintLoadError(
                        "SPARQLConstraintComponent value for sh:message must be "
                        "a Literal with type xsd:string.",
                        "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
                query_helper.messages = message_node_list
            deactivated_node_list = set(sg.objects(s, SH_deactivated))
            if len(deactivated_node_list) > 0:
                deactivated = next(iter(deactivated_node_list))
                if not (isinstance(deactivated, rdflib.Literal) and
                        isinstance(deactivated.value, bool)):
                    raise ConstraintLoadError(
                        "SPARQLConstraintComponent value for sh:deactivated must be "
                        "a Literal with type xsd:boolean.",
                        "https://www.w3.org/TR/shacl/#SPARQLConstraintComponent")
                query_helper.deactivated = deactivated.value
            query_helper.collect_prefixes()
            sparql_constraints.add(query_helper)
        self.sparql_constraints = sparql_constraints


    @classmethod
    def constraint_parameters(cls):
        return [SH_sparql]

    @classmethod
    def constraint_name(cls):
        return "SPARQLConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_SPARQLConstraintComponent

    def evaluate(self, target_graph, focus_value_nodes):
        """

        :type focus_value_nodes: dict
        :type target_graph: rdflib.Graph
        """
        reports = []
        non_conformant = False

        for query_helper in self.sparql_constraints:
            if query_helper.deactivated:
                continue
            _nc, _r = self._evaluate_sparql_constraint(
                query_helper, target_graph, focus_value_nodes)
            non_conformant = non_conformant or _nc
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_sparql_constraint(self, sparql_constraint,
                                    target_graph, f_v_dict):
        reports = []
        non_conformant = False
        extra_messages = sparql_constraint.messages or None
        rept_kwargs = {
            'source_constraint': sparql_constraint.node,
            'extra_messages': extra_messages
        }
        for f, value_nodes in f_v_dict.items():
            # we don't use value_nodes in the sparql constraint
            # All queries are done on the corresponding focus node.
            init_binds, sparql_text = sparql_constraint.pre_bind_variables(f)
            sparql_text = sparql_constraint.apply_prefixes(sparql_text)

            try:
                violating_vals = self._validate_sparql_query(
                    sparql_text, init_binds, target_graph)

            except ValidationFailure as e:
                raise e
            if not self.shape.is_property_shape:
                result_val = f
            else:
                result_val = None
            for v in violating_vals:
                non_conformant = True
                if isinstance(v, bool) and v is True:
                    rept = self.make_v_result(
                        f, value_node=result_val, **rept_kwargs)
                elif isinstance(v, tuple):
                    t, p, v = v
                    if v is None:
                        v = result_val
                    rept = self.make_v_result(
                        t or f, value_node=v, result_path=p,
                        **rept_kwargs)
                else:
                    rept = self.make_v_result(
                        f, value_node=v,
                        **rept_kwargs)
                reports.append(rept)
        return non_conformant, reports

    def _validate_sparql_query(self, query, init_binds, target_graph):
        results = target_graph.query(query, initBindings=init_binds)
        if not results or len(results.bindings) < 1:
            return []
        violations = set()
        for r in results:
            try:
                p = r['path']
            except KeyError:
                p = None
            try:
                v = r['value']
            except KeyError:
                v = None
                pass
            try:
                t = r['this']
            except KeyError:
                t = None
            if p or v or t:
                violations.add((t, p, v))
            else:
                try:
                    f = r['failure']
                    violations.add(True)
                except KeyError:
                    pass
        return violations

