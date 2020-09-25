import typing
from typing import List, Dict
from rdflib import Literal
if typing.TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph
from pyshacl.constraints import ConstraintComponent
from pyshacl.consts import SH
from pyshacl.errors import ConstraintLoadError
from pyshacl.rdfutil import stringify_node
from pyshacl.pytypes import GraphLike
from .context import SHACLJSContext


SH_js = SH.term('js')
SH_jsFunctionName = SH.term('jsFunctionName')
SH_jsLibrary = SH.term('jsLibrary')
SH_jsLibraryURL = SH.term('jsLibraryURL')
SH_JSConstraintComponent = SH.term('JSConstraintComponent')


class JSExecutable(object):
    __slots__ = ("sg","node","fn_name","libraries")


    def __init__(self, sg: 'ShapesGraph', node):
        self.node = node
        self.sg = sg
        fn_names = set(sg.objects(node, SH_jsFunctionName))
        if len(fn_names) < 1:
            raise ConstraintLoadError(
                "At least one sh:jsFunctionName must be present on a JS Executable.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        elif len(fn_names) > 1:
            raise ConstraintLoadError(
                "At most one sh:jsFunctionName can be present on a JS Executable.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        fn_name = next(iter(fn_names))
        if not isinstance(fn_name, Literal):
            raise ConstraintLoadError(
                "sh:jsFunctionName must be an RDF Literal with type xsd:string.",
                "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
            )
        else:
            fn_name = str(fn_name)
        self.fn_name = fn_name
        library_defs = sg.objects(node, SH_jsLibrary)
        seen_library_defs = []
        libraries = {}
        for libn in library_defs:
            if libn in seen_library_defs:
                continue
            if isinstance(libn, Literal):
                raise ConstraintLoadError(
                    "sh:jsLibrary must not have a value that is a Literal.",
                    "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                )
            seen_library_defs.append(libn)
            jsLibraryURLs = list(sg.objects(libn, SH_jsLibraryURL))
            if len(jsLibraryURLs) > 0:
                libraries[libn] = libraries.get(libn, [])
            for u in jsLibraryURLs:
                if not isinstance(u, Literal):
                    raise ConstraintLoadError(
                        "sh:jsLibraryURL must have a value that is a Literal.",
                        "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                    )
                libraries[libn].append(str(u))
            library_defs2 = sg.objects(libn, SH_jsLibrary)
            for libn2 in library_defs2:
                if libn2 in seen_library_defs:
                    continue
                if isinstance(libn2, Literal):
                    raise ConstraintLoadError(
                        "sh:jsLibrary must not have a value that is a Literal.",
                        "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                    )
                seen_library_defs.append(libn2)
                jsLibraryURLs2 = list(sg.objects(libn2, SH_jsLibraryURL))
                if len(jsLibraryURLs2) > 0:
                    libraries[libn2] = libraries.get(libn2, [])
                for u2 in jsLibraryURLs2:
                    if not isinstance(u2, Literal):
                        raise ConstraintLoadError(
                            "sh:jsLibraryURL must have a value that is a Literal.",
                            "https://www.w3.org/TR/shacl-js/#dfn-javascript-executables",
                        )
                    libraries[libn2].append(str(u2))
        self.libraries = libraries

    def execute(self, datagraph, *args, **kwargs):
        ctx = SHACLJSContext(self.sg, datagraph, **kwargs)
        for lib_node, lib_urls in self.libraries.items():
            for lib_url in lib_urls:
                ctx.load_js_library(lib_url)
        return ctx.run_js_function(self.fn_name, args)

class JSConstraintComponent(ConstraintComponent):
    """
    sh:minCount specifies the minimum number of value nodes that satisfy the condition. If the minimum cardinality value is 0 then this constraint is always satisfied and so may be omitted.
    Link:
    https://www.w3.org/TR/shacl/#MinCountConstraintComponent
    Textual Definition:
    If the number of value nodes is less than $minCount, there is a validation result.
    """

    def __init__(self, shape):
        super(JSConstraintComponent, self).__init__(shape)
        js_decls = list(self.shape.objects(SH_js))
        if len(js_decls) < 1:
            raise ConstraintLoadError(
                "JSConstraintComponent must have at least one sh:js predicate.",
                "https://www.w3.org/TR/shacl-js/#js-constraints",
            )
        self.js_exes = [JSExecutable(shape.sg, j) for j in js_decls]

    @classmethod
    def constraint_parameters(cls):
        return [SH_js]

    @classmethod
    def constraint_name(cls):
        return "JSConstraintComponent"

    @classmethod
    def shacl_constraint_class(cls):
        return SH_JSConstraintComponent

    def make_generic_messages(self, datagraph: GraphLike, focus_node, value_node) -> List[Literal]:
        return [Literal("Javascript Function generated constraint validation reports.")]

    def evaluate(self, data_graph: GraphLike, focus_value_nodes: Dict, _evaluation_path: List):
        """
        :type data_graph: rdflib.Graph
        :type focus_value_nodes: dict
        :type _evaluation_path: list
        """
        reports = []
        non_conformant = False
        for c in self.js_exes:
            _n, _r = self._evaluate_js_exe(data_graph, focus_value_nodes, c)
            non_conformant = non_conformant or _n
            reports.extend(_r)
        return (not non_conformant), reports

    def _evaluate_js_exe(self, data_graph, f_v_dict, js_exe):
        reports = []
        non_conformant = False
        for f, value_nodes in f_v_dict.items():
            for v in value_nodes:
                failed = False
                try:
                    res = js_exe.execute(data_graph, f, v)
                    if isinstance(res, bool) and not res:
                        failed = True
                        reports.append(self.make_v_result(data_graph, f, value_node=v))
                    elif isinstance(res, str):
                        failed = True
                        reports.append(self.make_v_result(data_graph, f, value_node=v, extra_messages=[res]))
                    elif isinstance(res, dict):
                        failed = True
                        val = res.get('value', None)
                        if val is None:
                            val = v
                        path = res.get('path', None)
                        msgs = []
                        message = res.get('message', None)
                        if message is not None:
                            msgs.append(message)
                        reports.append(self.make_v_result(data_graph, f, value_node=val, result_path=path, extra_messages=msgs))
                    elif isinstance(res, list):
                        for r in res:
                            failed = True
                            if isinstance(r, bool) and not r:
                                reports.append(self.make_v_result(data_graph, f, value_node=v))
                            elif isinstance(r, str):
                                reports.append(self.make_v_result(data_graph, f, value_node=v, extra_messages=[r]))
                            elif isinstance(r, dict):
                                val = r.get('value', None)
                                if val is None:
                                    val = v
                                path = r.get('path', None)
                                msgs = []
                                message = r.get('message', None)
                                if message is not None:
                                    msgs.append(message)
                                reports.append(self.make_v_result(data_graph, f, value_node=val, result_path=path,
                                                                  extra_messages=msgs))
                except Exception as e:
                    raise
                if failed:
                    non_conformant = True
        return non_conformant, reports
