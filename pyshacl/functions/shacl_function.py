# -*- coding: utf-8 -*-
#
import typing

from typing import Dict, List

from rdflib import XSD, Literal, URIRef
from rdflib.plugins.sparql.operators import register_custom_function, unregister_custom_function
from rdflib.plugins.sparql.sparql import SPARQLError

from pyshacl.consts import SH, RDFS_comment, SH_ask, SH_description, SH_order, SH_parameter, SH_path, SH_select
from pyshacl.errors import ConstraintLoadError, ReportableRuntimeError
from pyshacl.sparql_query_helper import SPARQLQueryHelper


if typing.TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike
    from pyshacl.shapes_graph import ShapesGraph

SH_datatype = SH.term('datatype')
SH_returnType = SH.term('returnType')
SH_optional = SH.term('optional')


class SHACLFunctionParameter(object):
    __slots__ = ("node", "path", "datatype", "description", "order", "optional")

    def __init__(self, pa_node, fn):
        """
        :type fn: SHACLFunction

        """
        sg = fn.sg  # type: ShapesGraph
        self.node = pa_node
        paths = list(sg.objects(pa_node, SH_path))
        if len(paths) < 1:
            self.path = URIRef("http://")  # todo: is this a blank path?
        elif len(paths) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:path.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.path = paths[0]
        datatypes = list(sg.objects(pa_node, SH_datatype))
        if len(datatypes) < 1:
            self.datatype = None
        elif len(datatypes) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:datatype.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.datatype = datatypes[0]
        descs = list(sg.objects(pa_node, SH_description))
        if len(descs) < 1:
            self.description = None
        elif len(descs) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:description.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.description = descs[0]
        orders = list(sg.objects(pa_node, SH_order))
        if len(orders) < 1:
            self.order = None
        elif len(orders) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:order.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            # TODO: check order is a literal with type Int
            self.order = int(orders[0])
        optionals = list(sg.objects(pa_node, SH_optional))
        if len(optionals) < 1:
            self.optional = False
        elif len(optionals) > 1:
            raise ConstraintLoadError(
                "sh:parameter cannot have more than one value for sh:optional.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            # TODO: check optional is a literal with type Bool
            self.optional = bool(optionals[0])

    @property
    def localname(self):
        path = self.path
        if path.startswith("http:"):
            path = path[5:]
        elif path.startswith("https:"):
            path = path[6:]
        try:
            parts = [p for p in path.split("/") if len(p)]
        except (LookupError, ValueError):
            return ""
        if len(parts) < 1 or len(parts[-1]) < 1:
            return ""
        last_part = parts[-1]
        try:
            parts = last_part.split("#", 1)
            if len(parts) < 2:
                return parts[0]
            else:
                return parts[1]
        except (LookupError, ValueError):
            return last_part


class SHACLFunction(object):
    __slots__ = ("sg", "node", "comments", "parameters", "rtype")

    def __init__(self, fn_node, sg):
        """

        :param fn_node:
        :type fn_node: rdflib.Identifier
        :param sg:
        :type sg: ShapesGraph
        """
        super(SHACLFunction, self).__init__()
        self.node = fn_node
        self.sg = sg
        params = list(sg.objects(fn_node, SH_parameter))
        self.parameters = [SHACLFunctionParameter(p, self) for p in params]  # type: List[SHACLFunctionParameter]
        self.comments = set(sg.objects(fn_node, RDFS_comment))
        rtypes = list(sg.objects(fn_node, SH_returnType))
        if len(rtypes) < 1:
            self.rtype = None
        elif len(rtypes) > 1:
            raise ConstraintLoadError(
                "SHACLFunction cannot have more than one value for sh:returnType.",
                "https://www.w3.org/TR/shacl-af/#functions-example",
            )
        else:
            self.rtype = rtypes[0]

    # TODO: Maybe cache this? Its called a few times per loop
    def get_params_in_order(self):
        if len(self.parameters) < 1:
            return []
        orders = (p.order for p in self.parameters)
        if None not in orders:
            # sort by _order_ field
            params = sorted(self.parameters, key=lambda x: x.order)
        else:
            # sort by _localname_ of path
            params = sorted(self.parameters, key=lambda x: x.localname)
        return params

    def get_optional_map(self):
        params = self.get_params_in_order()
        return [True if p.optional else False for p in params]

    def apply(self, g):
        self.sg.add_shacl_function(self.node, self.execute, self.get_optional_map())

    def unapply(self, g):
        self.sg.remove_shacl_function(self.node, self.execute)

    def execute(self, g, *args):
        raise NotImplementedError(
            "SHACLFunction cannot be executed by itself. " "It needs to be a SPARQLFunction or something similar."
        )


class SPARQLFunction(SHACLFunction):
    __slots__ = ("select", "ask", "_qh")

    def __init__(self, fn_node, sg):
        super(SPARQLFunction, self).__init__(fn_node, sg)
        selects = list(self.sg.objects(self.node, SH_select))
        asks = list(self.sg.objects(self.node, SH_ask))
        num_selects = len(selects)
        num_asks = len(asks)
        if num_asks > 0 and num_selects > 0:
            raise ConstraintLoadError(
                "SPARQLFunction cannot have both sh:select and sh:ask.",
                "https://www.w3.org/TR/shacl-af/#SPARQLFunction",
            )
        elif num_asks < 1 and num_selects < 1:
            raise ConstraintLoadError(
                "SPARQLFunction must have one of either sh:select or sh:ask.",
                "https://www.w3.org/TR/shacl-af/#SPARQLFunction",
            )
        if num_selects > 1:
            raise ConstraintLoadError(
                "SPARQLFunction cannot have more than one value for sh:select.",
                "https://www.w3.org/TR/shacl-af/#SPARQLFunction",
            )
        if num_asks > 1:
            raise ConstraintLoadError(
                "SPARQLFunction cannot have more than one value for sh:ask.",
                "https://www.w3.org/TR/shacl-af/#SPARQLFunction",
            )
        if num_asks:
            self.ask = asks[0]
            if self.rtype and self.rtype != XSD.boolean:
                raise ConstraintLoadError(
                    "SPARQLFunction with sh:ask must have sh:returnType of xsd:boolean.",
                    "https://www.w3.org/TR/shacl-af/#SPARQLFunction",
                )
            else:
                self.rtype = XSD.boolean
        else:
            self.ask = None
        self.select = selects[0] if num_selects else None
        query_helper = SPARQLQueryHelper(self, self.node, None, deactivated=False)
        query_helper.collect_prefixes()
        self._qh = query_helper

    def execute(self, g, *args):
        params = self.get_params_in_order()
        if len(args) != len(params):
            raise ReportableRuntimeError("Got incorrect number of arguments for SHACLFunction {}.".format(self.node))
        init_bindings = {}
        for i, p in enumerate(params):
            arg = args[i]
            ln = p.localname
            if arg is None and p.optional is False:
                raise ReportableRuntimeError("Got NoneType for Non-optional argument {}.".format(ln))
            init_bindings[ln] = arg
        if self.ask:
            return self.execute_ask(g, init_bindings)
        else:
            return self.execute_select(g, init_bindings)

    def execute_select(self, g: 'GraphLike', init_bindings: Dict):
        s = self._qh.apply_prefixes(self.select)
        results = g.query(s, initBindings=init_bindings)
        if results.type != "SELECT":
            raise ReportableRuntimeError("Was expecting an SELECT response from the Select query.")
        rvars = len(results.vars)
        rbindings = len(results.bindings)
        if rvars < 1 or rbindings < 1:
            return []
        rvar = results.vars[0]
        result = results.bindings[0]
        return result[rvar]

    def execute_ask(self, g: 'GraphLike', init_bindings: Dict):
        a = self._qh.apply_prefixes(self.ask)
        results = g.query(a, initBindings=init_bindings)
        if results.type != "ASK":
            raise ReportableRuntimeError("Was expecting an ASK response from the Ask query.")
        return Literal(results.askAnswer)

    def execute_from_sparql(self, e, ctx):
        if not e.expr:
            raise SPARQLError("Nothing given to SPARQLFunction.")
        params = self.get_params_in_order()
        num_params = len(params)
        if len(e.expr) > num_params:
            raise SPARQLError("Too many parameters passed to SPARQLFunction.")
        elif len(e.expr) < num_params:
            raise SPARQLError("Too few parameters passed to SPARQLFunction.")
        new_binds = ctx.ctx.initBindings.copy()
        new_binds.update(ctx.ctx.bindings)
        g = ctx.ctx.graph
        for i, var in enumerate(e.expr):
            var_val = ctx[var]
            bind_name = params[i].localname
            new_binds[bind_name] = var_val
        if self.ask:
            return self.execute_ask(g, new_binds)
        else:
            return self.execute_select(g, new_binds)

    def apply(self, g):
        super(SPARQLFunction, self).apply(g)
        register_custom_function(self.node, self.execute_from_sparql, True, True)

    def unapply(self, g):
        super(SPARQLFunction, self).unapply(g)
        unregister_custom_function(self.node, self.execute_from_sparql)
