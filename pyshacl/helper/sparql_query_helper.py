# -*- coding: utf-8 -*-
"""
https://www.w3.org/TR/shacl/#sparql-constraints
"""
import re

import rdflib
from rdflib import XSD

from ..consts import (
    OWL_PFX,
    RDF_PFX,
    RDFS_PFX,
    SH,
    OWL_Ontology,
    RDF_type,
    SH_alternativePath,
    SH_inversePath,
    SH_namespace,
    SH_oneOrMorePath,
    SH_prefix,
    SH_prefixes,
    SH_zeroOrMorePath,
    SH_zeroOrOnePath,
)
from ..errors import ConstraintLoadError, ReportableRuntimeError, ValidationFailure

SH_declare = SH.declare
invalid_parameter_names = {'this', 'shapesGraph', 'currentShape', 'path', 'PATH', 'value'}


class SPARQLQueryHelper(object):
    bind_this_regex = re.compile(r"([\s{}()])[\$\?]this", flags=re.M)
    bind_value_regex = re.compile(r"([\s{}()])[\$\?]value", flags=re.M)
    bind_path_regex = re.compile(r"([\s{}()])[\$\?]PATH", flags=re.M)
    bind_sg_regex = re.compile(r"([\s{}()])[\$\?]shapesGraph", flags=re.M)
    bind_cs_regex = re.compile(r"([\s{}()])[\$\?]currentShape", flags=re.M)
    has_minus_regex = re.compile(r"^(?:[^#]*|M)(?!#)#?[^\?\$\#]M?INUS[\s\{]", flags=re.M | re.I)
    has_values_regex = re.compile(r"^(?:[^#]*|V)(?!#)#?[^\?\$\#]V?ALUES[\s\{]", flags=re.M | re.I)
    has_service_regex = re.compile(r"^(?:[^#]*|S)(?!#)#?[^\?\$\#]S?ERVICE[\s\<]", flags=re.M | re.I)
    has_nested_select_regex = re.compile(
        r"SELECT[\s\(\)\$\?\a-z]*\{[^\}]*SELECT\s+((?:(?:[\?\$]\w+\s+)|(?:\*\s+))+)", flags=re.M | re.I
    )
    has_as_var_regex = re.compile(r"[^\w]+AS[\s]+[\$\?](\w+)", flags=re.M | re.I)
    find_msg_subs = re.compile(r"({[\$\?]([^{}]+)})", flags=re.M)

    def __init__(self, shape, node, select_text, parameters=None, messages=None, deactivated=False):
        self._shape = None
        self.node = node
        self.select_text = select_text
        self.unbound_messages = messages or set()
        self.deactivated = deactivated
        self.parameters = [] if parameters is None else parameters
        self.param_bind_map = {}
        self.bound_messages = set()
        self.prefixes = {
            'rdf': RDF_PFX,
            'rdfs': RDFS_PFX,
            'owl': OWL_PFX,
        }
        if shape:
            self.shape = shape

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, newshape):
        self._shape = newshape
        if len(self.parameters) > 0:
            self.bind_params()
            self.bind_messages()

    @property
    def messages(self):
        if len(self.bound_messages) < 1:
            return self.unbound_messages
        return self.bound_messages

    def bind_params(self):
        bind_map = {}
        shape = self.shape
        for p in self.parameters:
            name = p.localname
            if name in invalid_parameter_names:
                # TODO:coverage: No test for this case
                raise ReportableRuntimeError("Parameter name {} cannot be used.".format(name))
            shape_params = set(shape.objects(p.path()))
            if len(shape_params) < 1:
                if not p.optional:
                    # TODO:coverage: No test for this case
                    raise ReportableRuntimeError("Shape does not have mandatory parameter {}.".format(str(p.path())))
                continue
            # TODO: Can shapes have more than one value for the predicate?
            # Just use one for now.
            # TODO: Check for sh:class and sh:nodeKind on the found param value
            bind_map[name] = next(iter(shape_params))
        self.param_bind_map = bind_map

    def bind_messages(self, param_map=None):
        # must call bind_params _before_ bind_messages
        if param_map is None:
            param_map = self.param_bind_map
        var_replacers = {}
        bound_messages = set()
        for m in self.unbound_messages:
            m_val = str(m.value)
            finds = self.find_msg_subs.findall(m_val)
            if len(finds) < 1:
                bound_messages.add(m)
                continue
            for f in finds:
                variable = f[1]
                if variable not in param_map.keys():
                    continue
                try:
                    replacer = var_replacers[variable]
                except KeyError:
                    replacer = re.compile(r"{[\$\?]" + variable + r"}", flags=re.M)
                    var_replacers[variable] = replacer
                m_val = replacer.sub(str(param_map[variable]), m_val, 1)
            bound_messages.add(rdflib.Literal(m_val, lang=m.language, datatype=m.datatype))
        self.bound_messages = bound_messages

    def collect_prefixes(self):
        sg = self.shape.sg.graph
        prefixes_vals = set(sg.objects(self.node, SH_prefixes))
        if len(prefixes_vals) < 1:
            return
        named_graph = sg.identifier
        if named_graph:
            ng_declares = set(sg.objects(named_graph, SH_declare))
        else:
            ng_declares = set()
        onts = set(sg.subjects(RDF_type, OWL_Ontology))
        ont_declares = set()
        for o in onts:
            ont_declares.update(set(sg.objects(o, SH_declare)))
        global_declares = ng_declares.union(ont_declares)

        for prefixes_val in iter(prefixes_vals):
            pfx_declares = set(sg.objects(prefixes_val, SH_declare))
            if pfx_declares and prefixes_val in onts:
                all_declares = pfx_declares.union(ng_declares)
            else:
                all_declares = global_declares.union(pfx_declares)
            for dec in iter(all_declares):
                if isinstance(dec, rdflib.Literal):
                    raise ConstraintLoadError(
                        "sh:declare value must be either a URIRef or a BNode.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes",
                    )
                prefix_vals = set(sg.objects(dec, SH_prefix))
                if len(prefix_vals) < 1 or len(prefix_vals) > 1:
                    raise ConstraintLoadError(
                        "sh:declare must have exactly one sh:prefix predicate.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes",
                    )
                prefix = next(iter(prefix_vals))
                if not (isinstance(prefix, rdflib.Literal) and isinstance(prefix.value, str)):
                    raise ConstraintLoadError(
                        "sh:prefix value must be an RDF Literal with type xsd:string.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes",
                    )
                prefix = str(prefix.value)
                namespace_vals = set(sg.objects(dec, SH_namespace))
                if len(namespace_vals) < 1 or len(namespace_vals) > 1:
                    raise ConstraintLoadError(
                        "sh:declare must have exactly one sh:namespace predicate.",
                        "https://www.w3.org/TR/shacl/#sparql-prefixes",
                    )
                namespace = next(iter(namespace_vals))  # type: rdflib.Literal
                if not (isinstance(namespace, rdflib.Literal) and namespace.datatype == XSD.anyURI):
                    if prefix == "sh" and isinstance(namespace.value, str):
                        # Known bug in shacl.ttl https://github.com/w3c/data-shapes/issues/125
                        pass
                    elif (
                        namespace.datatype == XSD.string
                        or namespace.language is not None
                        or isinstance(namespace.value, str)
                    ):
                        # Its now possible for namespace to be xsd:string or string literal
                        pass
                    else:
                        raise ConstraintLoadError(
                            "sh:namespace value must be an RDF Literal with type xsd:anyURI.\nLiteral: {} type={}".format(
                                namespace.value, namespace.datatype or namespace.language
                            ),
                            "https://www.w3.org/TR/shacl/#sparql-prefixes",
                        )
                namespace = rdflib.URIRef(str(namespace.value))
                self.prefixes[prefix] = namespace

    def apply_prefixes(self, sparql):
        prefix_string = ""
        for p, ns in self.prefixes.items():
            prefix_string += "PREFIX {}: <{}>\n".format(str(p), str(ns))
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
            raise ReportableRuntimeError("Values of a property path cannot be a Literal.")
        # At this point, path_val _must_ be a BNode
        # TODO, the path_val BNode must be value of exactly one sh:path subject in the SG.
        if recursion >= 10:
            raise ReportableRuntimeError("Path traversal depth is too much!")
        sequence_list = list(sg.graph.items(path_val))
        if len(sequence_list) > 0:
            all_collected = []
            for s in sequence_list:
                seq1_string = self._shacl_path_to_sparql_path(s, recursion=recursion + 1)
                all_collected.append(seq1_string)
            if len(all_collected) < 2:
                raise ReportableRuntimeError("List of SHACL sequence paths must have alt least two path items.")
            return "/".join(all_collected)

        find_inverse = set(sg.objects(path_val, SH_inversePath))
        if len(find_inverse) > 0:
            inverse_path = next(iter(find_inverse))
            inverse_path_string = self._shacl_path_to_sparql_path(inverse_path, recursion=recursion + 1)
            return "^{}".format(inverse_path_string)

        find_alternatives = set(sg.objects(path_val, SH_alternativePath))
        if len(find_alternatives) > 0:
            alternatives_list = next(iter(find_alternatives))
            all_collected = []
            for a in sg.graph.items(alternatives_list):
                alt1_string = self._shacl_path_to_sparql_path(a, recursion=recursion + 1)
                all_collected.append(alt1_string)
            if len(all_collected) < 2:
                raise ReportableRuntimeError("List of SHACL alternate paths must have alt least two path items.")
            return "|".join(all_collected)

        find_zero_or_more = set(sg.objects(path_val, SH_zeroOrMorePath))
        if len(find_zero_or_more) > 0:
            zero_or_more_path = next(iter(find_zero_or_more))
            zom_path_string = self._shacl_path_to_sparql_path(zero_or_more_path, recursion=recursion + 1)
            return "{}*".format(zom_path_string)

        find_zero_or_one = set(sg.objects(path_val, SH_zeroOrOnePath))
        if len(find_zero_or_one) > 0:
            zero_or_one_path = next(iter(find_zero_or_one))
            zoo_path_string = self._shacl_path_to_sparql_path(zero_or_one_path, recursion=recursion + 1)
            return "{}?".format(zoo_path_string)

        find_one_or_more = set(sg.objects(path_val, SH_oneOrMorePath))
        if len(find_one_or_more) > 0:
            one_or_more_path = next(iter(find_one_or_more))
            oom_path_string = self._shacl_path_to_sparql_path(one_or_more_path, recursion=recursion + 1)
            return "{}+".format(oom_path_string)

        raise NotImplementedError("That path method to get value nodes of property shapes is not yet implemented.")

    @classmethod
    def _node_to_sparql_text(cls, node):
        if isinstance(node, rdflib.Literal):
            if isinstance(node.value, str):
                node_text = "\"{}\"".format(node.value)
            else:
                node_text = str(node.value)
            if node.language:
                node_text = "{}@{}".format(node_text, str(node.language))
            elif node.datatype:
                node_text = "{}^^{}".format(node_text, cls._node_to_sparql_text(node.datatype))
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
                    "See https://github.com/w3c/data-shapes/issues/84."
                )
            for p in potentially_prebound_variables:
                if p not in stripped_vars:
                    # these are optional:
                    if p == "shapesGraph" or p == "currentShape":
                        continue
                    elif p == "this":
                        raise ValidationFailure(
                            "All potentially pre-bound variables must be selected from a nested SELECT query.\n"
                            "Don't forget to include variable `$this` in your SELECT arguments."
                        )
                    else:
                        raise ValidationFailure(
                            "All potentially pre-bound variables must be selected from a nested SELECT query.\n"
                            "Potentially pre-bound variables for this query are: {}.".format(
                                ", ".join(potentially_prebound_variables)
                            )
                        )
        has_as_var = self.has_as_var_regex.search(sparql_text)
        if has_as_var:
            var_name = has_as_var.group(1)
            if var_name in potentially_prebound_variables:
                raise ValidationFailure(
                    "Cannot use AS to re-bind potentially pre-bound variables such as {}".format(var_name)
                )
        return True

    def pre_bind_variables(self, thisnode, valuenode=None, extravars=None):
        new_query_text = "" + self.select_text
        _ = self.check_invalid_sparql(new_query_text, valuenode=valuenode, extravars=extravars)
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
            new_query_text = self.bind_path_regex.sub(r"\g<1>{}".format(path_string), new_query_text)
        else:
            found_path = self.bind_path_regex.search(new_query_text)
            if found_path:
                raise ReportableRuntimeError(
                    "SPARQL Constraint text has $PATH in it, but no path is known on this Shape."
                )
        # TODO: work out how to get shapesGraph binding from shape.sg
        #  shapes_graph = self.shape.sg
        shapes_graph = False
        if shapes_graph:
            found_sg = self.bind_sg_regex.search(new_query_text)
            if found_sg:
                init_bindings['shapesGraph'] = shapes_graph
        else:
            found_sg = self.bind_sg_regex.search(new_query_text)
            if found_sg:
                raise NotImplementedError(
                    "SPARQL Constraint text has $shapesGraph in it, but Shapes Graph is not currently supported."
                )

        return init_bindings, new_query_text
