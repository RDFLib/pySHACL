# -*- coding: utf-8 -*-
#
from __future__ import annotations

import functools
import re
import typing
from typing import Dict, List, Sequence

from rdflib import XSD, Literal
from rdflib.plugins.sparql.sparql import SPARQLError

from ..consts import SH, RDFS_comment, SH_ask, SH_parameter, SH_select
from ..errors import ConstraintLoadError, ReportableRuntimeError
from ..graph_abstraction import has_oxigraph, to_ox, to_rdf
from ..helper import get_query_helper_cls
from ..parameter import SHACLParameter

if typing.TYPE_CHECKING:
    from pyoxigraph import (
        BlankNode,
        NamedNode,
        Triple,
    )
    from pyoxigraph import (
        Literal as OxLiteral,
    )

    from ..graph_abstraction import DataGraph, OxigraphDataGraph
    from ..pytypes import GraphLike
    from ..shapes_graph import ShapesGraph

if has_oxigraph:
    from pyoxigraph import Literal as ox_Literal
    from pyoxigraph import QueryBoolean as ox_QueryBoolean
    from pyoxigraph import QuerySolutions as ox_QuerySolutions


SH_returnType = SH.returnType
SH_optional = SH.optional

_SPARQL_VAR_TOKEN = re.compile(r"(\?|\$)([a-zA-Z_][\w]*)")


def _skip_sparql_string(query: str, start: int) -> int:
    """Advance past a SPARQL string literal opener at *start*."""
    quote = query[start]
    i = start + 1
    n = len(query)
    while i < n:
        if query[i] == "\\":
            i += 2
            continue
        if query[i] == quote:
            return i + 1
        i += 1
    return n


def _find_keyword_at_brace_depth_zero(query: str, keyword: str, start: int = 0) -> int | None:
    """Return the index of *keyword* only when it appears at SPARQL graph-pattern depth zero."""
    keyword_re = re.compile(rf"(?i)\b{re.escape(keyword)}\b")
    i = start
    n = len(query)
    brace_depth = 0
    while i < n:
        ch = query[i]
        if ch in ('"', "'"):
            i = _skip_sparql_string(query, i)
            continue
        if ch == "{":
            brace_depth += 1
            i += 1
            continue
        if ch == "}":
            brace_depth = max(0, brace_depth - 1)
            i += 1
            continue
        if brace_depth == 0:
            m = keyword_re.match(query, i)
            if m:
                return i
        i += 1
    return None


def _split_top_level_select_query(query: str) -> tuple[str, str, str] | None:
    """Split *query* into (prefix, select_clause, suffix).

    *prefix* is any prologue and text before the top-level ``SELECT``.
    *select_clause* is the projection between top-level ``SELECT`` and ``WHERE``.
    *suffix* begins with the top-level ``WHERE`` keyword, or is empty when absent.

    Only the outermost ``SELECT`` is considered; nested ``SELECT`` inside ``WHERE``
    graph patterns are left untouched.
    """
    select_kw = _find_keyword_at_brace_depth_zero(query, "SELECT", 0)
    if select_kw is None:
        return None
    select_match = re.match(r"(?i)\bSELECT\b", query[select_kw:])
    if select_match is None:
        return None
    select_clause_start = select_kw + select_match.end()
    where_kw = _find_keyword_at_brace_depth_zero(query, "WHERE", select_clause_start)
    if where_kw is not None:
        select_clause = query[select_clause_start:where_kw].strip()
        suffix = query[where_kw:]
    else:
        select_clause = query[select_clause_start:].strip()
        suffix = ""
    prefix = query[:select_kw]
    return prefix, select_clause, suffix


def _collect_bare_projected_var_names(select_clause: str) -> set[str]:
    """Return variable names projected at the top level of a SELECT clause.

    Variables that only appear inside parenthesized ``(expr AS ?var)`` expressions
    are not counted, because Oxigraph does not treat them as explicit projections
    for substitution purposes.
    """
    projected: set[str] = set()
    depth = 0
    i = 0
    n = len(select_clause)
    while i < n:
        ch = select_clause[i]
        if ch in ('"', "'"):
            i = _skip_sparql_string(select_clause, i)
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0:
            m = _SPARQL_VAR_TOKEN.match(select_clause, i)
            if m:
                projected.add(m.group(2))
                i = m.end()
                continue
        i += 1
    return projected


def _preferred_var_sigil(select_clause: str, name: str) -> str:
    """Pick ``$`` or ``?`` for a variable name, matching existing query style when possible."""
    if re.search(rf"\${re.escape(name)}\b", select_clause):
        return "$"
    if re.search(rf"\?{re.escape(name)}\b", select_clause):
        return "?"
    return "$"


def _append_top_level_select_projections(query: str, binding_names: Sequence[str]) -> str:
    """Append any missing top-level SELECT projections required by Oxigraph substitutions."""
    parts = _split_top_level_select_query(query)
    if parts is None:
        return query
    prefix, select_clause, suffix = parts
    bare_projected = _collect_bare_projected_var_names(select_clause)
    missing = [name for name in binding_names if name not in bare_projected]
    if not missing:
        return query
    extra = " ".join(f"{_preferred_var_sigil(select_clause, name)}{name}" for name in missing)
    new_select_clause = f"{select_clause} {extra}".strip()
    if suffix:
        return f"{prefix}SELECT {new_select_clause} {suffix}"
    return f"{prefix}SELECT {new_select_clause}"


class SHACLFunction(object):
    __slots__ = ("sg", "node", "comments", "parameters", "rtype")

    def __init__(self, fn_node, sg: 'ShapesGraph'):
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
        self.parameters: List[SHACLParameter] = [SHACLParameter(sg, p) for p in params]
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
        orders = (p.param_order for p in self.parameters)
        if None not in orders:
            # sort by _param_order_ field
            params = sorted(self.parameters, key=lambda x: x.param_order)
        else:
            # sort by _localname_ of path
            params = sorted(self.parameters, key=lambda x: x.localname)
        return params

    def get_optional_map(self):
        params = self.get_params_in_order()
        return [True if p.optional else False for p in params]

    def objects(self, predicate=None):
        return self.sg.graph.objects(self.node, predicate)

    def apply(self, g):
        self.sg.add_shacl_function(self.node, self.execute, self.get_optional_map())

    def unapply(self, g):
        self.sg.remove_shacl_function(self.node, self.execute)

    def execute(self, g, *args):
        raise NotImplementedError(
            "SHACLFunction cannot be executed by itself. It needs to be a SPARQLFunction or something similar."
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
        # deliberately not passing in Parameters to queryHelper here, because we can't bind them to this function
        # (this function is not a Shape, and Function Params don't get bound to it)
        SPARQLQueryHelper = get_query_helper_cls()
        query_helper = SPARQLQueryHelper(self, self.node, None, None, deactivated=False)
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
        if getattr(g, "is_oxigraph", False):
            ox_bindings = {k: to_ox(v) for k, v in init_bindings.items()}
            if self.ask:
                return Literal(bool(self.execute_ask_oxigraph(g, ox_bindings)))
            ox_result = self.execute_select_oxigraph(g, ox_bindings)
            return to_rdf(ox_result) if ox_result is not None else None
        if self.ask:
            return self.execute_ask(g, init_bindings)
        return self.execute_select(g, init_bindings)

    def _ensure_oxigraph_select_bindings(self, select: str, binding_names: Sequence[str]) -> str:
        """Oxigraph requires substituted variables to appear as bare SELECT projections."""
        return _append_top_level_select_projections(select.strip(), binding_names)

    def execute_select(self, g: 'GraphLike', init_bindings: Dict):
        s = self._qh.apply_prefixes(self.select)
        results = g.query(s, initBindings=init_bindings)
        if results.type != "SELECT" or results.vars is None:
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

    def execute_select_oxigraph(
        self,
        g: 'OxigraphDataGraph',
        init_bindings: Dict[str, NamedNode | BlankNode | OxLiteral | Triple],
    ):
        s = self._qh.apply_prefixes(self.select)
        s = self._ensure_oxigraph_select_bindings(s, list(init_bindings.keys()))
        results = g.query_oxigraph(s, initBindings=init_bindings)
        if not isinstance(results, ox_QuerySolutions):
            raise ReportableRuntimeError("Was expecting a SELECT response from the Select query.")
        if len(results.variables) < 1:
            return None
        try:
            solution = next(iter(results))
        except StopIteration:
            return None
        return solution[0]

    def execute_ask_oxigraph(
        self,
        g: 'OxigraphDataGraph',
        init_bindings: Dict[str, NamedNode | BlankNode | OxLiteral | Triple],
    ):
        a = self._qh.apply_prefixes(self.ask)
        results = g.query_oxigraph(a, initBindings=init_bindings)
        if not isinstance(results, ox_QueryBoolean):
            raise ReportableRuntimeError("Was expecting an ASK response from the Ask query.")
        return ox_Literal(bool(results))

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

    def execute_from_sparql_oxigraph(
        self,
        g: 'DataGraph',
        *args: NamedNode | BlankNode | OxLiteral | Triple,
    ):
        """Oxigraph custom-function callback: evaluated argument terms in, one RDF term out.

        PyOxigraph invokes this with one positional argument per SPARQL function argument
        (pyoxigraph NamedNode, BlankNode, Literal, or Triple). The DataGraph is not provided
        by Oxigraph; apply() binds it with functools.partial().
        """
        if not g.is_oxigraph:
            raise ReportableRuntimeError("execute_from_sparql_oxigraph requires an Oxigraph-backed DataGraph.")
        params = self.get_params_in_order()
        num_params = len(params)
        num_args = len(args)
        if num_args > num_params:
            raise ValueError("Too many parameters passed to SPARQLFunction {}.".format(self.node))
        if num_args < num_params:
            raise ValueError("Too few parameters passed to SPARQLFunction {}.".format(self.node))
        init_bindings: Dict[str, NamedNode | BlankNode | OxLiteral | Triple] = {}
        for i, p in enumerate(params):
            ox_arg = args[i]
            ln = p.localname
            if ox_arg is None and p.optional is False:
                raise ReportableRuntimeError("Got NoneType for Non-optional argument {}.".format(ln))
            init_bindings[ln] = ox_arg
        if self.ask:
            return self.execute_ask_oxigraph(g, init_bindings)
        return self.execute_select_oxigraph(g, init_bindings)

    def apply(self, g: 'DataGraph'):
        super(SPARQLFunction, self).apply(g)
        if has_oxigraph:
            g.register_custom_function(
                self.node,
                self.execute_from_sparql,
                functools.partial(self.execute_from_sparql_oxigraph, g),
                True,
                True,
            )
        else:
            g.register_custom_function(self.node, self.execute_from_sparql, None, True, True)

    def unapply(self, g: 'DataGraph'):
        super(SPARQLFunction, self).unapply(g)
        if has_oxigraph:
            g.unregister_custom_function(self.node, self.execute_from_sparql, self.execute_from_sparql_oxigraph)
        else:
            g.unregister_custom_function(self.node, self.execute_from_sparql, None)
