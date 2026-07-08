try:
    from pyoxigraph import (
        BlankNode as ox_BlankNode,
    )
    from pyoxigraph import (
        DefaultGraph as ox_DefaultGraph,
    )
    from pyoxigraph import (
        Literal as ox_Literal,
    )
    from pyoxigraph import (
        NamedNode as ox_NamedNode,
    )
    from pyoxigraph import (
        Quad as ox_Quad,
    )
    from pyoxigraph import (
        QueryBoolean as ox_QueryBoolean,
    )
    from pyoxigraph import (
        QuerySolutions as ox_QuerySolutions,
    )
    from pyoxigraph import (
        QueryTriples as ox_QueryTriples,
    )
    from pyoxigraph import (
        Store as ox_Store,
    )
    from pyoxigraph import (
        Triple as ox_Triple,
    )
    from pyoxigraph import (
        Variable as ox_Variable,
    )

    has_oxigraph = True
except ImportError:
    has_oxigraph = False
    ox_Store = None
    ox_DefaultGraph = None
    ox_Quad = None
    ox_Literal = None
    ox_BlankNode = None
    ox_NamedNode = None
    ox_QuerySolutions = None
    ox_Variable = None

import shutil
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, Mapping, Sequence, Tuple, Type, Union

from rdflib import Dataset as rdf_Dataset
from rdflib import Graph as rdf_Graph
from rdflib import IdentifiedNode
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID
from rdflib.namespace import RDF, NamespaceManager
from rdflib.plugins.sparql.operators import register_custom_function, unregister_custom_function
from rdflib.plugins.sparql.sparql import Query, Update
from rdflib.query import Processor, Result
from rdflib.store import VALID_STORE
from rdflib.store import Store as rdflib_Store
from rdflib.term import (
    BNode as rdf_BNode,
)
from rdflib.term import (
    IdentifiedNode as rdf_IdentifiedNode,
)
from rdflib.term import (
    Literal as rdf_Literal,
)
from rdflib.term import (
    URIRef as rdf_URIRef,
)
from rdflib.term import (
    Variable as rdf_Variable,
)

ALLOWED_BACKING_TYPES = Union[rdflib_Store, ox_Store]


class DataGraph(rdf_Dataset):
    is_oxigraph: bool
    impl: ALLOWED_BACKING_TYPES
    _default_union: bool

    def __new__(
        cls,
        store: ALLOWED_BACKING_TYPES,
        impl: Union[rdf_Dataset, rdf_Graph, None] = None,
        locked_context: Union[rdf_Graph, str, None] = None,
    ):
        use_oxigraph = has_oxigraph and isinstance(store, ox_Store)
        if cls is DataGraph:
            # Determine the correct subclass to use
            if use_oxigraph:
                cls = OxigraphDataGraph
            else:
                cls = RdfLibDataGraph
            self = cls.__new__(cls, store, locked_context)
            return self
        else:
            self = super().__new__(cls)
            self.is_oxigraph = use_oxigraph
            self._default_union = False
            return self

    @classmethod
    def is_multigraph(self) -> bool:
        return False

    @property
    def default_union(self) -> bool:
        return self._default_union

    @property
    def default_graph(self):
        raise NotImplementedError("Default graph is not supported for this graph type")

    @default_union.setter
    def default_union(self, value: bool):
        self._default_union = value
        if self.is_oxigraph:
            pass
        else:
            impl = getattr(self, 'impl', None)
            if impl and isinstance(impl, rdf_Dataset):
                impl.default_union = value

    @property
    def namespace_manager(self) -> NamespaceManager:
        raise NotImplementedError("Namespace manager is not supported for this graph type")

    def query(self, **kwargs):
        raise NotImplementedError("Query is not supported for this graph type")

    @classmethod
    def from_rdflib_dataset(cls, dataset: rdf_Dataset) -> "DataGraph":
        return cls(store=dataset.store, impl=dataset)

    @classmethod
    def from_rdflib_graph(cls, graph: rdf_Graph) -> "DataGraph":
        return cls(store=graph.store, impl=graph)

    @classmethod
    def from_rdflib(cls, source: Union[rdf_Dataset, rdf_Graph]) -> "DataGraph":
        if isinstance(source, rdf_Dataset):
            return cls.from_rdflib_dataset(source)
        elif isinstance(source, rdf_Graph):
            return cls.from_rdflib_graph(source)
        else:
            raise ValueError("Invalid rdflib source type")

    @classmethod
    def from_oxigraph_store(cls, store: ox_Store) -> "DataGraph":
        if not has_oxigraph:
            raise ValueError("pyoxigraph is not installed")
        return cls(store, impl=None)

    def register_custom_function(
        self,
        function_name: str | rdf_IdentifiedNode,
        rdflib_fn: Callable,
        oxigraph_fn: Callable,
        override: bool = False,
        raw: bool = False,
        is_aggregate: bool = False,
    ):
        raise NotImplementedError("register_custom_function is not supported for this graph type")

    def clone(self) -> "DataGraph":
        raise NotImplementedError("clone is not supported for this graph type")

    @property
    def identifier(self) -> str:
        return self.impl.identifier


class RdfLibDataGraph(DataGraph):
    locked_context: rdf_Graph | None
    is_multi_graph: bool
    _store: rdflib_Store
    impl: Union[rdf_Dataset, rdf_Graph]

    def __init__(
        self,
        store: rdflib_Store,
        impl: Union[rdf_Dataset, rdf_Graph, None] = None,
        locked_context: Union[rdf_Graph, str, None] = None,
    ):
        if impl is not None:
            if isinstance(impl, rdf_Dataset):
                _default_union = impl.default_union
                _is_multi_graph = True
            else:
                _default_union = False
                _is_multi_graph = False
            self.impl = impl
            self._store = store
            rdf_Dataset.__init__(self, default_union=_default_union)
            self.is_multi_graph = _is_multi_graph
        else:
            self._store = store
            self.impl = super(RdfLibDataGraph, self)
            rdf_Dataset.__init__(self, store=store, default_union=False)
            self.is_multi_graph = True
        if isinstance(locked_context, rdf_Graph):
            self.locked_context = locked_context
        elif isinstance(locked_context, str):
            if not self.is_multi_graph:
                self.locked_context = self.impl
            else:
                self.locked_context = self.impl.get_context(rdf_URIRef(locked_context))
        else:
            self.locked_context = None

    def clone(
        self, destination: Union[rdf_Dataset, rdf_Graph, None] = None, identifier: Union[str, None] = None
    ) -> "RdfLibDataGraph":
        if identifier is None:
            if self.is_multi_graph:
                identifier = self.default_graph.identifier
            else:
                identifier = self.impl.identifier
        # Lazy import to avoid circular import, where it can depend on graph_abstraction.py.
        from .rdfutil.clone import clone_graph

        new_impl = clone_graph(self.impl, destination, identifier)
        return RdfLibDataGraph(new_impl.store, new_impl, self.locked_context)

    @property
    def default_graph(self) -> rdf_Graph:
        if self.is_multi_graph:
            return self.impl.default_graph
        else:
            return self.impl

    @property
    def identifier(self) -> str:
        if isinstance(self.impl, rdf_Dataset):
            if self.locked_context:
                if isinstance(self.locked_context, rdf_Graph):
                    return self.locked_context.identifier
                else:
                    return str(self.locked_context)
            else:
                return "RDFLibDataset"
        elif isinstance(self.impl, rdf_Graph):
            return str(self.impl.identifier)
        else:
            return "RDFLibGraph"

    @property
    def namespace_manager(self) -> NamespaceManager:
        return self.impl.namespace_manager

    def is_multigraph(self) -> bool:
        return self.is_multi_graph

    @property
    def store(self) -> rdflib_Store:
        return self._store

    def register_custom_function(
        self,
        function_name: rdf_IdentifiedNode,
        rdflib_fn: Callable,
        oxigraph_fn: Union[Callable, None] = None,
        override: bool = False,
        raw: bool = False,
        is_aggregate: bool = False,
    ):
        register_custom_function(function_name, rdflib_fn, override, raw)

    def unregister_custom_function(
        self, function_name: rdf_IdentifiedNode, rdflib_fn: Callable, oxigraph_fn: Union[Callable, None] = None
    ):
        unregister_custom_function(function_name, rdflib_fn)

    def query(
        self,
        query_object: Union[str, Query],
        processor: Union[str, Processor] = "sparql",
        result: Union[str, Type[Result]] = "sparql",
        initNs: Union[Mapping[str, Any], None] = None,  # noqa: N803
        initBindings: Union[Mapping[str, IdentifiedNode], None] = None,  # noqa: N803
        use_store_provided: bool = True,
        **kwargs: Any,
    ) -> Result:
        return self.impl.query(query_object, processor, result, initNs, initBindings, use_store_provided, **kwargs)

    def add(
        self,
        triple: Tuple[
            Union[rdf_IdentifiedNode, rdf_Literal],
            rdf_IdentifiedNode,
            Union[rdf_Literal, rdf_IdentifiedNode],
        ],
    ):
        if self.locked_context is not None:
            if isinstance(self.impl, rdf_Dataset):
                return self.impl.add((triple[0], triple[1], triple[2], self.locked_context))
            else:
                return self.locked_context.add((triple[0], triple[1], triple[2]))
        else:
            return self.impl.add((triple[0], triple[1], triple[2]))

    def remove(
        self,
        triple: Tuple[
            Union[rdf_IdentifiedNode, rdf_Literal],
            rdf_IdentifiedNode,
            Union[rdf_Literal, rdf_IdentifiedNode],
        ],
    ):
        if self.locked_context is not None:
            if isinstance(self.impl, rdf_Dataset):
                return self.impl.remove((triple[0], triple[1], triple[2], self.locked_context))
            else:
                return self.locked_context.remove((triple[0], triple[1], triple[2]))
        else:
            return self.impl.remove((triple[0], triple[1], triple[2]))

    def triples(
        self,
        triple: Tuple[
            Union[rdf_IdentifiedNode, rdf_Literal, None],
            Union[rdf_IdentifiedNode, None],
            Union[rdf_IdentifiedNode, rdf_Literal, None],
        ],
    ) -> Generator[
        Tuple[
            Union[rdf_IdentifiedNode, rdf_Literal],
            rdf_IdentifiedNode,
            Union[rdf_IdentifiedNode, rdf_Literal],
        ],
        None,
        None,
    ]:
        if self.locked_context is not None:
            if isinstance(self.impl, rdf_Dataset):
                yield from self.impl.triples(triple, context=self.locked_context)
            else:
                yield from self.locked_context.triples(triple)
        else:
            yield from self.impl.triples(triple)

    def subject_objects(
        self, predicate: Union[rdf_IdentifiedNode, None], unique: bool = False
    ) -> Generator[tuple, None, None]:
        if self.locked_context is not None:
            yield from self.locked_context.subject_objects(predicate, unique=unique)
        else:
            yield from self.impl.subject_objects(predicate, unique=unique)

    def subject_predicates(
        self, object_: Union[rdf_IdentifiedNode, rdf_Literal, None], unique: bool = False
    ) -> Generator[Any, None, None]:
        if self.locked_context is not None:
            yield from self.locked_context.subject_predicates(object_, unique=unique)
        else:
            yield from self.impl.subject_predicates(object_, unique=unique)

    def predicate_objects(
        self, subject: Union[rdf_IdentifiedNode, rdf_Literal, None], unique: bool = False
    ) -> Generator[tuple, None, None]:
        if self.locked_context is not None:
            yield from self.locked_context.predicate_objects(subject, unique=unique)
        else:
            yield from self.impl.predicate_objects(subject, unique=unique)

    def subjects(
        self,
        predicate: rdf_IdentifiedNode,
        object_: Union[rdf_IdentifiedNode, rdf_Literal, Sequence[Union[rdf_IdentifiedNode, rdf_Literal]], None],
        unique: bool = False,
    ) -> Generator[rdf_IdentifiedNode, None, None]:
        if isinstance(object_, (list, tuple)):
            for o in object_:
                yield from self.subjects(predicate, o, unique=unique)
            return
        if self.locked_context is not None:
            yield from self.locked_context.subjects(predicate, object_, unique=unique)
        else:
            yield from self.impl.subjects(predicate, object_, unique=unique)

    def transitive_subjects(
        self,
        predicate: rdf_IdentifiedNode,
        object_: Union[rdf_IdentifiedNode, rdf_Literal, None],
        remember: Union[Dict[Union[rdf_IdentifiedNode, rdf_Literal], int], None] = None,
    ):
        if self.locked_context is not None:
            yield from self.locked_context.transitive_subjects(predicate, object_, remember=remember)
        else:
            yield from self.impl.transitive_subjects(predicate, object_, remember=remember)

    def transitive_objects(
        self,
        subject: Union[rdf_IdentifiedNode, rdf_Literal, None],
        predicate: Union[rdf_IdentifiedNode, None],
        remember: Union[Dict[Union[rdf_IdentifiedNode, rdf_Literal], int], None] = None,
    ):
        if self.locked_context is not None:
            yield from self.locked_context.transitive_objects(subject, predicate, remember=remember)
        else:
            yield from self.impl.transitive_objects(subject, predicate, remember=remember)

    def objects(
        self,
        subject: Union[rdf_IdentifiedNode, rdf_Literal, Sequence[Union[rdf_IdentifiedNode, rdf_Literal]], None],
        predicate: Union[rdf_IdentifiedNode, None],
        unique: bool = False,
    ) -> Generator[Union[rdf_IdentifiedNode, rdf_Literal], None, None]:
        if isinstance(subject, (list, tuple)):
            for s in subject:
                yield from self.objects(s, predicate, unique=unique)
            return
        if self.locked_context is not None:
            yield from self.locked_context.objects(subject, predicate, unique=unique)
        else:
            yield from self.impl.objects(subject, predicate, unique=unique)

    def with_locked_context(self, identifier: Union[rdf_URIRef, str]) -> "RdfLibDataGraph":
        if not isinstance(self.impl, rdf_Dataset):
            raise ValueError("Cannot create a locked context on a non-dataset graph")
        the_graph = self.impl.get_context(rdf_URIRef(identifier))
        return RdfLibDataGraph(the_graph.store, the_graph, the_graph)

    def get_context(self, identifier: Union[rdf_URIRef, str]) -> Any:
        if not isinstance(self.impl, rdf_Dataset):
            return self.impl  # Just return the graph itself
        return self.impl.get_context(rdf_URIRef(identifier))  # type: ignore

    def __contains__(
        self,
        triple: Tuple[
            Union[rdf_IdentifiedNode, rdf_Literal, None],
            Union[rdf_IdentifiedNode, None],
            Union[rdf_IdentifiedNode, rdf_Literal, None],
        ],
    ) -> bool:
        if self.locked_context is not None:
            if isinstance(self.impl, rdf_Dataset):
                quad = (triple[0], triple[1], triple[2], self.locked_context)
                return quad in self.impl
            else:
                return triple in self.locked_context
        else:
            return triple in self.impl

    def __len__(self) -> int:
        if self.locked_context is not None:
            return len(self.locked_context)
        else:
            return len(self.impl)

    def items(self, list_: rdf_IdentifiedNode) -> Generator[Union[rdf_IdentifiedNode, rdf_Literal], None, None]:
        """Generator over all items in the resource specified by list

        Args:
            list: An RDF collection.
        """
        if self.locked_context is not None:
            yield from self.locked_context.items(list_)
        else:
            yield from self.impl.items(list_)

    def bind(self, prefix: str, namespace: str, **kwargs) -> None:
        self.impl.bind(prefix, namespace, **kwargs)


if has_oxigraph:

    class OxigraphDataGraph(DataGraph):
        # This acts as kind of a cross between a rdflib.Graph, and rdflib.Dataset and rdflib.Store
        # It can be used in palce of an rdflib.Graph and rdflib.Dataset
        # But it can also be used as a Store, in the case of Graph(store=self)

        impl: ox_Store
        locked_context: Union[ox_NamedNode, None]
        custom_functions: Dict[ox_NamedNode, Any]
        custom_aggregate_functions: Dict[ox_NamedNode, Any]
        _store: 'OxigraphStore'
        _default_graph: rdf_Graph
        _namespace_manager: NamespaceManager

        def __init__(
            self,
            ox_store: ox_Store,
            impl: Union[rdf_Dataset, None] = None,
            locked_context: Union[rdf_Graph, str, None] = None,
        ):
            self.impl = ox_store
            # This is the RDFLib Proxy Store over the Oxigraph Rust Store
            self._store = OxigraphStore(store=ox_store)
            rdf_Dataset.__init__(self, store=self._store)

            self._default_union = False
            if isinstance(locked_context, rdf_Graph):
                self.locked_context = ox_NamedNode(locked_context.identifier)
            elif isinstance(locked_context, str):
                self.locked_context = ox_NamedNode(locked_context)
            else:
                self.locked_context = None
            self._default_graph = rdf_Graph(store=self._store, identifier=DATASET_DEFAULT_GRAPH_ID)
            self._namespace_manager = NamespaceManager(self._default_graph, bind_namespaces="core")
            self.custom_functions = {}
            self.custom_aggregate_functions = {}

        @property
        def identifier(self) -> str:
            return "OxigraphStore"

        @property
        def namespace_manager(self) -> NamespaceManager:
            return self._namespace_manager

        @classmethod
        def is_multigraph(cls) -> bool:
            return True

        @property
        def store(self) -> Any:
            return self._store

        def graphs(self, triple: Union[ox_Triple, None] = None) -> Generator[rdf_Graph, None, None]:
            if triple is not None:
                raise NotImplementedError("Graphs() on an Oxigraph store are not supported when specifying a triple")
            yield self._default_graph
            yield from (from_ox_graph_name(g, self._store) for g in self.impl.named_graphs())

        @property
        def default_graph(self) -> rdf_Graph:
            # Not sure how to lock the Oxigraph backing Store to only show the default graph
            return self._default_graph

        def clone(self, destination: Union[ox_Store, None] = None) -> "OxigraphDataGraph":
            new_ox_store = clone_oxigraph_store(self.impl, destination)
            new_dg = OxigraphDataGraph(new_ox_store, None, self.locked_context)
            new_dg.custom_functions = self.custom_functions.copy()
            new_dg.custom_aggregate_functions = self.custom_aggregate_functions.copy()
            return new_dg

        def register_custom_function(
            self,
            function_name: rdf_IdentifiedNode,
            rdflib_fn: Callable,
            oxigraph_fn: Union[Callable, None] = None,
            override: bool = False,
            raw: bool = False,
            is_aggregate: bool = False,
        ):
            if oxigraph_fn is None:
                return
            ox_node = to_ox(function_name)
            if is_aggregate:
                if ox_node in self.custom_aggregate_functions:
                    if override:
                        self.custom_aggregate_functions[ox_node] = oxigraph_fn
                    else:
                        pass
                else:
                    self.custom_aggregate_functions[ox_node] = oxigraph_fn
            else:
                if ox_node in self.custom_functions:
                    if override:
                        self.custom_functions[ox_node] = oxigraph_fn
                    else:
                        pass
                else:
                    self.custom_functions[ox_node] = oxigraph_fn

        def unregister_custom_function(
            self, function_name: rdf_IdentifiedNode, rdflib_fn: Callable, oxigraph_fn: Union[Callable, None] = None
        ):
            ox_node = to_ox(function_name)
            if ox_node in self.custom_aggregate_functions:
                del self.custom_aggregate_functions[ox_node]
            if ox_node in self.custom_functions:
                del self.custom_functions[ox_node]

        def query_oxigraph(
            self,
            query_object: str,
            initNs: Union[Mapping[str, Any], None] = None,  # noqa: N803
            initBindings: Union[Mapping[str, Any], None] = None,  # noqa: N803
            **kwargs: Any,
        ) -> Union[ox_QueryBoolean, ox_QuerySolutions, ox_QueryTriples]:
            """Run a SPARQL query and return native pyoxigraph results (no rdflib conversion)."""
            query_graph = kwargs.get("query_graph", None)
            ns_map = {**self.store._namespace_for_prefix}
            if initNs is not None:
                for ns, uri in initNs.items():
                    ns_map[ns] = uri

            if initBindings is not None:
                variable_subs = {ox_Variable(var_uri): term for var_uri, term in initBindings.items()}
            else:
                variable_subs = None

            return self.impl.query(
                query_object,
                base_iri=None,
                prefixes=ns_map,
                use_default_graph_as_union=self._default_union or query_graph == "__UNION__",
                default_graph=None,
                named_graphs=None,
                substitutions=variable_subs,
                custom_functions=self.custom_functions,
                custom_aggregate_functions=self.custom_aggregate_functions,
            )

        def query(
            self,
            query_object: Union[str, Query],
            processor: Union[str, Processor] = "sparql",
            result: Union[str, Type[Result]] = "sparql",
            initNs: Union[Mapping[str, Any], None] = None,  # noqa: N803
            initBindings: Union[Mapping[str, IdentifiedNode], None] = None,  # noqa: N803
            use_store_provided: bool = True,
            **kwargs: Any,
        ) -> Result:
            if not isinstance(query_object, str):
                raise ValueError("Query on an Oxigraph store must be a string")
            ox_bindings = None
            if initBindings is not None:
                ox_bindings = {var_uri: to_ox(term) for var_uri, term in initBindings.items()}
            query_result = self.query_oxigraph(query_object, initNs=initNs, initBindings=ox_bindings, **kwargs)
            if isinstance(query_result, ox_QueryBoolean):
                out = Result("ASK")
                out.askAnswer = bool(query_result)
            elif isinstance(query_result, ox_QuerySolutions):
                out = Result("SELECT")
                out.vars = [rdf_Variable(v.value) for v in query_result.variables]
                out.bindings = ({v: to_rdf(val) for v, val in zip(out.vars, solution)} for solution in query_result)
            elif isinstance(query_result, ox_QueryTriples):
                out = Result("CONSTRUCT")
                out.graph = rdf_Graph()
                out.graph += ((to_rdf(t[0]), to_rdf(t[1]), to_rdf(t[2])) for t in query_result)
            else:
                raise ValueError(f"Unexpected query result: {query_result}")
            return out

        def add(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal],
                rdf_IdentifiedNode,
                Union[rdf_Literal, rdf_IdentifiedNode],
            ],
            context: Union[rdf_Graph, None] = None,
            quoted: bool = False,
        ):
            if quoted:
                raise NotImplementedError("Oxigraph store is not formula-aware")
            if isinstance(triple[1], rdf_BNode) or isinstance(triple[1], rdf_Literal):
                # Oxigraph does not support BNode or Literal in the predicate position
                # Cannot add the triple
                warnings.warn(
                    "PySHACL rules tried to add a triple with a BNode or Literal in the predicate position",
                )
                return
            if isinstance(triple[0], rdf_Literal):
                # Oxigraph does not support Literal in the subject position
                # Cannot add the triple
                warnings.warn(
                    "PySHACL rules tried to add a triple with a Literal in the subject position",
                )
                return
            ox_s, ox_p, ox_o = convert_triple_to_oxigraph(triple)

            if self.locked_context is not None:
                ox_g = self.locked_context
            elif context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    ox_g = ox_DefaultGraph()
                else:
                    ox_g = to_ox(context.identifier)
            else:
                ox_g = ox_DefaultGraph()
            return self.impl.add(ox_Quad(ox_s, ox_p, ox_o, ox_g))

        def remove(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal],
                rdf_IdentifiedNode,
                Union[rdf_Literal, rdf_IdentifiedNode],
            ],
            context: Union[rdf_Graph, None] = None,
        ):
            ox_triple = convert_triple_to_oxigraph(triple)
            if isinstance(ox_triple[1], ox_BlankNode) or isinstance(ox_triple[1], ox_Literal):
                # Oxigraph does not support BNode or Literal in the predicate position
                # Cannot remove the triple
                warnings.warn(
                    "PySHACL rules tried to remove a triple with a BNode or Literal in the predicate position. This is not supported by Oxigraph.",
                )
                return
            if isinstance(ox_triple[0], ox_Literal):
                # Oxigraph does not support Literal in the subject position
                # Cannot remove the triple
                warnings.warn(
                    "PySHACL rules tried to remove a triple with a Literal in the subject position. This is not supported by Oxigraph.",
                )
                return
            if self.locked_context is not None:
                to_remove = list(
                    self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], self.locked_context)
                )
            elif context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    ox_g = ox_DefaultGraph()
                else:
                    ox_g = to_ox(context.identifier)
                to_remove = list(self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], ox_g))
            elif self._default_union:
                to_remove = list(self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], None))
            else:
                to_remove = list(
                    self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], ox_DefaultGraph())
                )
            for q in to_remove:
                self.impl.remove(q)

        def triples(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal, None],
                Union[rdf_IdentifiedNode, None],
                Union[rdf_IdentifiedNode, rdf_Literal, None],
            ],
        ) -> Generator[
            Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal],
                rdf_IdentifiedNode,
                Union[rdf_IdentifiedNode, rdf_Literal],
            ],
            None,
            None,
        ]:
            ox_triple = convert_triple_to_oxigraph(triple)
            if isinstance(ox_triple[1], ox_BlankNode) or isinstance(ox_triple[1], ox_Literal):
                # Oxigraph does not support BNode or Literal in the predicate position
                # Cannot yield any results
                return
            if isinstance(ox_triple[0], ox_Literal):
                # Oxigraph does not support Literal in the subject position
                # Cannot yield any results
                return
            if self.locked_context is not None:
                for q in self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], self.locked_context):
                    yield convert_quad_to_rdflib(q)[:3]
            elif self._default_union:
                for q in self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], None):
                    yield convert_quad_to_rdflib(q)[:3]
            else:
                default_graph = ox_DefaultGraph()
                for q in self.impl.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], default_graph):
                    yield convert_quad_to_rdflib(q)[:3]

        def subject_objects(
            self, predicate: Union[rdf_IdentifiedNode, None], unique: bool = False
        ) -> Generator[
            Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal],
                Union[rdf_IdentifiedNode, rdf_Literal],
            ],
            None,
            None,
        ]:
            if isinstance(predicate, rdf_BNode) or isinstance(predicate, rdf_Literal):
                # Oxigraph does not support BNode or Literal in the predicate position
                # Cannot yield any results
                return
            _p = to_ox(predicate)
            if self.locked_context is not None:
                for q in self.impl.quads_for_pattern(None, _p, None, self.locked_context):
                    s, _, o, _ = convert_quad_to_rdflib(q)
                    yield s, o
            elif self._default_union:
                for q in self.impl.quads_for_pattern(None, _p, None, None):
                    s, _, o, _ = convert_quad_to_rdflib(q)
                    yield s, o
            else:
                for q in self.impl.quads_for_pattern(None, _p, None, ox_DefaultGraph()):
                    s, _, o, _ = convert_quad_to_rdflib(q)
                    yield s, o

        def subject_predicates(
            self, object_: Union[rdf_IdentifiedNode, rdf_Literal, None], unique: bool = False
        ) -> Generator[Tuple[Union[rdf_IdentifiedNode, rdf_Literal], rdf_IdentifiedNode], None, None]:
            _o = to_ox(object_)
            if self.locked_context is not None:
                for q in self.impl.quads_for_pattern(None, None, _o, self.locked_context):
                    s, p, _, _ = convert_quad_to_rdflib(q)
                    yield s, p
            elif self._default_union:
                for q in self.impl.quads_for_pattern(None, None, _o, None):
                    s, p, _, _ = convert_quad_to_rdflib(q)
                    yield s, p
            else:
                for q in self.impl.quads_for_pattern(None, None, _o, ox_DefaultGraph()):
                    s, p, _, _ = convert_quad_to_rdflib(q)
                    yield s, p

        def predicate_objects(
            self, subject: Union[rdf_IdentifiedNode, rdf_Literal, None], unique: bool = False
        ) -> Generator[Tuple[rdf_IdentifiedNode, Union[rdf_IdentifiedNode, rdf_Literal]], None, None]:
            _s = to_ox(subject)
            if self.locked_context is not None:
                for q in self.impl.quads_for_pattern(_s, None, None, self.locked_context):
                    _, p, o, _ = convert_quad_to_rdflib(q)
                    yield p, o
            elif self._default_union:
                for q in self.impl.quads_for_pattern(_s, None, None, None):
                    _, p, o, _ = convert_quad_to_rdflib(q)
                    yield p, o
            else:
                for q in self.impl.quads_for_pattern(_s, None, None, ox_DefaultGraph()):
                    _, p, o, _ = convert_quad_to_rdflib(q)
                    yield p, o

        def subjects(
            self,
            predicate: rdf_IdentifiedNode,
            object_: Union[rdf_IdentifiedNode, rdf_Literal, Sequence[Union[rdf_IdentifiedNode, rdf_Literal]], None],
            unique: bool = False,
        ) -> Generator[Union[rdf_IdentifiedNode, rdf_Literal], None, None]:
            if isinstance(object_, (list, tuple)):
                for o in object_:
                    yield from self.subjects(predicate, o, unique=unique)
                return
            _p = to_ox(predicate)
            _o = to_ox(object_)
            if self.locked_context is not None:
                for s, _, _, _ in self.impl.quads_for_pattern(None, _p, _o, self.locked_context):
                    yield to_rdf(s)
            elif self._default_union:
                for s, _, _, _ in self.impl.quads_for_pattern(None, _p, _o, None):
                    yield to_rdf(s)
            else:
                for s, _, _, _ in self.impl.quads_for_pattern(None, _p, _o, ox_DefaultGraph()):
                    yield to_rdf(s)

        def transitive_subjects(
            self,
            predicate: rdf_IdentifiedNode,
            object_: Union[rdf_IdentifiedNode, rdf_Literal, None],
            remember: Union[Dict[Union[rdf_IdentifiedNode, rdf_Literal], int], None] = None,
        ):
            if remember is None:
                remember = {}
            if object_ in remember:
                return
            remember[object_] = 1
            yield object_
            for subject in self.subjects(predicate, object_):
                yield from self.transitive_subjects(predicate, subject, remember)

        def objects(
            self,
            subject: Union[rdf_IdentifiedNode, rdf_Literal, Sequence[Union[rdf_IdentifiedNode, rdf_Literal]], None],
            predicate: Union[rdf_IdentifiedNode, None],
            unique: bool = False,
        ) -> Generator[Union[rdf_IdentifiedNode, rdf_Literal], None, None]:
            if isinstance(subject, (list, tuple)):
                for s in subject:
                    yield from self.objects(s, predicate, unique=unique)
                return
            _s = to_ox(subject)
            _p = to_ox(predicate)
            if self.locked_context is not None:
                for _, _, o, _ in self.impl.quads_for_pattern(_s, _p, None, self.locked_context):
                    yield to_rdf(o)
            elif self._default_union:
                for _, _, o, _ in self.impl.quads_for_pattern(_s, _p, None, None):
                    yield to_rdf(o)
            else:
                for _, _, o, _ in self.impl.quads_for_pattern(_s, _p, None, ox_DefaultGraph()):
                    yield to_rdf(o)

        def transitive_objects(
            self,
            subject: Union[rdf_IdentifiedNode, rdf_Literal, None],
            predicate: Union[rdf_IdentifiedNode, None],
            remember: Union[Dict[Union[rdf_IdentifiedNode, rdf_Literal], int], None] = None,
        ):
            if remember is None:
                remember = {}
            if subject in remember:
                return
            remember[subject] = 1
            yield subject
            for object_ in self.objects(subject, predicate):
                yield from self.transitive_objects(object_, predicate, remember)

        def with_locked_context(self, identifier: Union[rdf_URIRef, str]) -> "OxigraphDataGraph":
            return OxigraphDataGraph(self.impl, None, str(identifier))

        def get_context(self, identifier: Union[rdf_URIRef, str]) -> Any:
            return rdf_Graph(store=self._store, identifier=rdf_URIRef(identifier))

        def __contains__(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal, None],
                Union[rdf_IdentifiedNode, None],
                Union[rdf_IdentifiedNode, rdf_Literal, None],
            ],
        ) -> bool:
            if triple[0] is not None and isinstance(triple[0], rdf_Literal):
                # Oxigraph does not support Literal in the subject position
                # It cannot exist in the oxigraph store
                return False
            triple_ = convert_triple_to_oxigraph(triple)
            if self.locked_context is not None:
                quad = ox_Quad(triple_[0], triple_[1], triple_[2], self.locked_context)
            elif self._default_union:
                quad = ox_Quad(triple_[0], triple_[1], triple_[2], None)
            else:
                quad = ox_Quad(triple_[0], triple_[1], triple_[2], ox_DefaultGraph())
            return quad in self.impl

        def __len__(self, context: Union[rdf_Graph, None] = None) -> int:
            default_graph_as_union = context is None or context == "__UNION__" or self._default_union
            if context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    default_graph = ox_DefaultGraph()
                else:
                    default_graph = to_ox(context.identifier)
            else:
                default_graph = None
            return int(
                next(
                    self.impl.query(
                        "SELECT (COUNT(DISTINCT TRIPLE(?s, ?p, ?o)) AS ?c) WHERE { ?s ?p ?o }",
                        **(
                            {"use_default_graph_as_union": True}
                            if default_graph_as_union
                            else {"default_graph": default_graph}  # type: ignore[dict-item]
                        ),
                    ),
                )[0].value,
            )

        def items(self, list_: rdf_IdentifiedNode) -> Generator[Union[rdf_IdentifiedNode, rdf_Literal], None, None]:
            """Generator over all items in the resource specified by list

            Args:
                list: An RDF collection.
            """
            if isinstance(list_, rdf_URIRef):
                next_list = ox_NamedNode(str(list_))
            elif isinstance(list_, rdf_BNode):
                next_list = ox_BlankNode(str(list_))
            else:
                raise ValueError("List must be a URIRef, or BNode")
            chain = set[ox_NamedNode]([next_list])
            FIRST = ox_NamedNode(RDF.first)
            REST = ox_NamedNode(RDF.rest)
            while next_list:
                if self.locked_context:
                    firsts = list(self.impl.quads_for_pattern(next_list, FIRST, None, self.locked_context))
                else:
                    firsts = list(self.impl.quads_for_pattern(next_list, FIRST, None, None))
                if len(firsts) == 0:
                    item = None
                else:
                    item = firsts[0][2]
                if item is not None:
                    yield to_rdf(item)
                if self.locked_context:
                    rests = list(self.impl.quads_for_pattern(next_list, REST, None, self.locked_context))
                else:
                    rests = list(self.impl.quads_for_pattern(next_list, REST, None, None))
                if len(rests) == 0:
                    next_list = None
                else:
                    next_list = rests[0][2]
                if next_list in chain:
                    raise ValueError("List contains a recursive rdf:rest reference")
                chain.add(next_list)

    class OxigraphStore(rdflib_Store):
        # OxigraphStore is borrowed from the OxRDFLib poroject
        # https://github.com/oxigraph/oxrdflib/blob/main/src/oxrdflib/store.py

        context_aware: bool = True
        formula_aware: bool = False
        transaction_aware: bool = False
        graph_aware: bool = True

        def __init__(
            self,
            configuration: Union[str, None] = None,
            identifier: Union[rdf_URIRef, None] = None,
            *,
            store: Union[ox_Store, None] = None,
        ) -> None:
            self._store = store
            self._prefix_for_namespace: Dict[rdf_URIRef, str] = {}
            self._namespace_for_prefix: Dict[str, rdf_URIRef] = {}
            super().__init__(configuration, identifier)

        def open(self, configuration: str, create: bool = False) -> Union[int, None]:
            path = Path(configuration)
            if self._store is not None:
                raise ValueError("The open function should be called before any RDF operation")
            if create and path.exists():
                raise ValueError(f"The directory {configuration} already exist")
            self._store = ox_Store(configuration)
            return VALID_STORE

        def close(self, commit_pending_transaction: bool = False) -> None:  # noqa: ARG002
            del self._store

        def destroy(self, configuration: str) -> None:
            shutil.rmtree(configuration)

        def gc(self) -> None:
            pass

        @property
        def _inner(self) -> ox_Store:
            if self._store is None:
                self._store = ox_Store()
            return self._store

        def add(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal], rdf_IdentifiedNode, Union[rdf_Literal, rdf_IdentifiedNode]
            ],
            context: Union[rdf_Graph, None] = None,
            quoted: bool = False,
        ) -> None:
            if quoted:
                raise ValueError("Oxigraph stores are not formula aware")
            ox_triple = convert_triple_to_oxigraph(triple)
            if context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    ox_context = ox_DefaultGraph()
                else:
                    ox_context = to_ox(context.identifier)
            else:
                ox_context = ox_DefaultGraph()
            self._inner.add(ox_Quad(ox_triple[0], ox_triple[1], ox_triple[2], ox_context))
            super().add(triple, context, quoted)

        def addN(self, quads: Iterable[tuple]) -> None:  # noqa: N802
            raise NotImplementedError("addN is not supported by Oxigraph store")

        def remove(
            self,
            triple: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal, None],
                Union[rdf_IdentifiedNode, None],
                Union[rdf_IdentifiedNode, rdf_Literal, None],
            ],
            context: Union[rdf_Graph, None] = None,
        ) -> None:
            ox_triple = convert_triple_to_oxigraph(triple)
            if context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    ox_context = ox_DefaultGraph()
                else:
                    ox_context = to_ox(context.identifier)
            else:
                ox_context = None
            for q in self._inner.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], ox_context):
                self._inner.remove(q)
            super().remove(triple, context)

        def triples(
            self,
            triple_pattern: Tuple[
                Union[rdf_IdentifiedNode, rdf_Literal, None],
                Union[rdf_IdentifiedNode, None],
                Union[rdf_IdentifiedNode, rdf_Literal, None],
            ],
            context: Union[rdf_Graph, None] = None,
        ) -> Generator[
            Tuple[
                Tuple[
                    Union[rdf_IdentifiedNode, rdf_Literal], rdf_IdentifiedNode, Union[rdf_Literal, rdf_IdentifiedNode]
                ],
                Generator[Union[rdf_Graph, None], None, None],
            ],
            None,
            None,
        ]:
            try:
                ox_triple = convert_triple_to_oxigraph(triple_pattern)
                if context is not None:
                    if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                        ox_context = ox_DefaultGraph()
                    else:
                        ox_context = to_ox(context.identifier)
                else:
                    ox_context = None
                for q in self._inner.quads_for_pattern(ox_triple[0], ox_triple[1], ox_triple[2], ox_context):
                    yield (
                        (to_rdf(q[0]), to_rdf(q[1]), to_rdf(q[2])),
                        iter(
                            (from_ox_graph_name(q[3], self),),
                        ),
                    )
            except (TypeError, ValueError):
                return iter(())  # We just don't return anything

        def __len__(self, context: Union[rdf_Graph, None] = None) -> int:
            default_graph_as_union = context is None or context == "__UNION__"
            if context is not None:
                if context.identifier == DATASET_DEFAULT_GRAPH_ID:
                    default_graph = ox_DefaultGraph()
                else:
                    default_graph = to_ox(context.identifier)
            else:
                default_graph = None
            return int(
                next(
                    self._inner.query(
                        "SELECT (COUNT(DISTINCT TRIPLE(?s, ?p, ?o)) AS ?c) WHERE { ?s ?p ?o }",
                        **(
                            {"use_default_graph_as_union": True}
                            if default_graph_as_union
                            else {"default_graph": default_graph}  # type: ignore[dict-item]
                        ),
                    ),
                )[0].value,
            )

        def contexts(self, triple: Union[ox_Triple, None] = None) -> Generator[rdf_Graph, None, None]:
            if triple is None:
                return (from_ox_graph_name(g, self) for g in self._inner.named_graphs())
            raise NotImplementedError("Graphs() on an Oxigraph store are not supported when specifying a triple")

        def query(
            self,
            query: Union[Query, str],
            initNs: Mapping[str, Any],  # noqa: N803
            initBindings: Mapping[str, rdf_IdentifiedNode],  # noqa: N803
            queryGraph: str,  # noqa: N803
            **kwargs: object,
        ) -> "Result":
            if isinstance(query, Query):
                raise NotImplementedError("The already parsed Queries are not supported by Oxigraph store")
            for kwarg in kwargs:
                raise NotImplementedError(f"The parameter {kwarg} is not supported by Oxigraph store")

            query_graph = kwargs.get("query_graph", None)
            ns_map = {**self._prefix_for_namespace}
            if initNs:
                for ns, uri in initNs.items():
                    ns_map[ns] = uri

            if initBindings:
                variable_subs = {}
                for var_uri, term in initBindings.items():
                    variable_subs[ox_Variable(var_uri)] = to_ox(term)
            else:
                variable_subs = None

            result: Union[
                ox_QueryBoolean, Generator[ox_QuerySolutions, None, None], Generator[ox_QueryTriples, None, None]
            ] = self._inner.query(
                query,
                base_iri=None,
                prefixes=ns_map,
                use_default_graph_as_union=query_graph == "__UNION__",
                default_graph=to_ox(queryGraph) if isinstance(queryGraph, rdf_IdentifiedNode) else None,
                named_graphs=None,
                substitutions=variable_subs,
                # custom_functions = self.custom_functions,
                # custom_aggregate_functions = self.custom_aggregate_functions,
            )
            if isinstance(result, ox_QueryBoolean):
                out = Result("ASK")
                out.askAnswer = bool(result)
            elif isinstance(result, ox_QuerySolutions):
                out = Result("SELECT")
                out.vars = [rdf_Variable(v.value) for v in result.variables]
                out.bindings = ({v: to_rdf(val) for v, val in zip(out.vars, solution)} for solution in result)
            elif isinstance(result, ox_QueryTriples):
                out = Result("CONSTRUCT")
                out.graph = rdf_Graph()
                out.graph += ((to_rdf(t[0]), to_rdf(t[1]), to_rdf(t[2])) for t in result)
            else:
                raise ValueError(f"Unexpected query result: {result}")
            return out

        def update(
            self,
            update: Union[Update, str],
            initNs: Mapping[str, Any],  # noqa: N803
            initBindings: Mapping[str, rdf_IdentifiedNode],  # noqa: N803
            queryGraph: str,  # noqa: N803
            **kwargs: object,
        ) -> None:
            if initBindings:
                raise NotImplementedError("initBindings are not supported by Oxigraph store in update mode")
            if queryGraph != DATASET_DEFAULT_GRAPH_ID:
                raise NotImplementedError(f"Only {DATASET_DEFAULT_GRAPH_ID} is supported by native Oxigraph store")
            if isinstance(update, Update):
                raise NotImplementedError("The already parsed Updates are not supported by Oxigraph store")
            for kwarg in kwargs:
                raise NotImplementedError(f"The parameter {kwarg} is not supported by Oxigraph store")
            self._inner.update(update, prefixes=dict(self._namespace_for_prefix, **initNs))

        def commit(self) -> None:
            # TODO: implement
            pass

        def rollback(self) -> None:
            # TODO: implement
            pass

        def add_graph(self, graph: rdf_Graph) -> None:
            self._inner.add_graph(to_ox(graph))

        def remove_graph(self, graph: rdf_Graph) -> None:
            self._inner.remove_graph(to_ox(graph))

        def bind(self, prefix: str, namespace: rdf_URIRef, override: bool = True) -> None:
            if not override and (prefix in self._namespace_for_prefix or namespace in self._prefix_for_namespace):
                return  # nothing to do
            self._delete_from_prefix(prefix)
            self._delete_from_namespace(namespace)
            self._namespace_for_prefix[prefix] = namespace
            self._prefix_for_namespace[namespace] = prefix

        def _delete_from_prefix(self, prefix: str) -> None:
            if prefix not in self._namespace_for_prefix:
                return
            namespace = self._namespace_for_prefix[prefix]
            del self._namespace_for_prefix[prefix]
            self._delete_from_namespace(namespace)

        def _delete_from_namespace(self, namespace: str) -> None:
            if namespace not in self._prefix_for_namespace:
                return
            prefix = self._prefix_for_namespace[namespace]
            del self._prefix_for_namespace[namespace]
            self._delete_from_prefix(prefix)

        def prefix(self, namespace: rdf_URIRef) -> Union[str, None]:
            return self._prefix_for_namespace.get(namespace)

        def namespace(self, prefix: str) -> Union[rdf_URIRef, None]:
            return self._namespace_for_prefix.get(prefix)

        def namespaces(self) -> Generator[Tuple[str, rdf_URIRef], None, None]:
            yield from self._namespace_for_prefix.items()

else:

    class OxigraphDataGraph(DataGraph):
        def __init__(self, **kwargs) -> None:
            raise NotImplementedError("pyoxigraph is not installed")

    class OxigraphStore(rdflib_Store):
        def __init__(self, **kwargs) -> None:
            raise NotImplementedError("pyoxigraph is not installed")


def to_ox(term: Union[rdf_IdentifiedNode, rdf_Literal, None]) -> Union[ox_NamedNode, ox_BlankNode, ox_Literal, None]:
    if term is None:
        return None
    elif term == DATASET_DEFAULT_GRAPH_ID:
        return ox_DefaultGraph()
    elif isinstance(term, rdf_BNode):
        return ox_BlankNode(str(term))
    elif isinstance(term, rdf_Literal):
        if term.language is not None:
            return ox_Literal(str(term), language=term.language)
        data_type = term.datatype
        if data_type is not None:
            data_type = ox_NamedNode(str(data_type))
        return ox_Literal(str(term), datatype=data_type)
    elif isinstance(term, rdf_Graph):
        return to_ox(term.identifier)
    else:
        return ox_NamedNode(str(term))


def to_rdf(
    term: Union[ox_NamedNode, ox_BlankNode, ox_Literal, ox_DefaultGraph, None],
) -> Union[rdf_IdentifiedNode, rdf_Literal, None]:
    if term is None:
        return None
    elif isinstance(term, ox_DefaultGraph):
        return DATASET_DEFAULT_GRAPH_ID
    elif isinstance(term, ox_BlankNode):
        return rdf_BNode(term.value)
    elif isinstance(term, ox_Literal):
        if term.language is not None:
            return rdf_Literal(term.value, lang=term.language)
        data_type = term.datatype
        if data_type is not None:
            data_type = rdf_URIRef(data_type.value)
        return rdf_Literal(term.value, datatype=data_type)
    else:
        return rdf_URIRef(term.value)


def convert_quad_to_rdflib(quad: ox_Quad):
    s, p, o, g = quad
    if s is None:
        out_s = None
    elif isinstance(s, ox_BlankNode):
        out_s = rdf_BNode(s.value)
    elif isinstance(s, ox_Literal):
        # Technically a subject can never be a Literal
        # in Oxigraph, but this is here for completeness
        if s.language is not None:
            out_s = rdf_Literal(s.value, lang=s.language)
        else:
            data_type = s.datatype
            if data_type is not None:
                data_type = rdf_URIRef(data_type.value)
            out_s = rdf_Literal(s.value, datatype=data_type)
    else:
        out_s = rdf_URIRef(s.value)
    if p is None:
        out_p = None
    elif isinstance(p, ox_BlankNode):
        out_p = rdf_BNode(p.value)
    else:
        out_p = rdf_URIRef(p.value)
    if o is None:
        out_o = None
    elif isinstance(o, ox_Literal):
        if o.language is not None:
            out_o = rdf_Literal(o.value, lang=o.language)
        else:
            data_type = o.datatype
            if data_type is not None:
                data_type = rdf_URIRef(data_type.value)
            out_o = rdf_Literal(o.value, datatype=data_type)
    elif isinstance(o, ox_BlankNode):
        out_o = rdf_BNode(o.value)
    else:
        out_o = rdf_URIRef(o.value)
    if g is None:
        out_g = None
    elif isinstance(g, ox_DefaultGraph):
        out_g = None
    else:
        out_g = rdf_URIRef(g.value)
    return out_s, out_p, out_o, out_g


def from_ox_graph_name(
    graph_name: Union[ox_NamedNode, ox_BlankNode, ox_DefaultGraph],
    store: rdflib_Store,
) -> rdf_Graph:
    if isinstance(graph_name, ox_NamedNode):
        return rdf_Graph(identifier=rdf_URIRef(graph_name.value), store=store)
    if isinstance(graph_name, ox_BlankNode):
        return rdf_Graph(identifier=rdf_BNode(graph_name.value), store=store)
    if isinstance(graph_name, ox_DefaultGraph):
        return rdf_Graph(identifier=DATASET_DEFAULT_GRAPH_ID, store=store)
    raise ValueError(f"Unexpected Oxigraph graph name: {graph_name!r}")


def convert_triple_to_oxigraph(
    triple: Tuple[
        Union[rdf_IdentifiedNode, rdf_Literal, None],
        Union[rdf_IdentifiedNode, None],
        Union[rdf_Literal, rdf_IdentifiedNode, None],
    ],
):
    in_s, in_p, in_o = triple

    if in_s is None:
        out_s = None
    elif isinstance(in_s, rdf_BNode):
        out_s = ox_BlankNode(str(in_s))
    elif isinstance(in_s, rdf_Literal):
        if in_s.language is not None:
            out_s = ox_Literal(str(in_s), language=in_s.language)
        else:
            data_type = in_s.datatype
            if data_type is not None:
                data_type = ox_NamedNode(str(data_type))
            out_s = ox_Literal(str(in_s), datatype=data_type)
    else:
        out_s = ox_NamedNode(str(in_s))
    if in_p is None:
        out_p = None
    elif isinstance(in_p, rdf_BNode):
        out_p = ox_BlankNode(str(in_p))
    else:
        out_p = ox_NamedNode(str(in_p))
    if in_o is None:
        out_o = None
    elif isinstance(in_o, rdf_BNode):
        out_o = ox_BlankNode(str(in_o))
    elif isinstance(in_o, rdf_Literal):
        if in_o.language is not None:
            out_o = ox_Literal(str(in_o), language=in_o.language)
        else:
            data_type = in_o.datatype
            if data_type is not None:
                data_type = ox_NamedNode(str(data_type))
            out_o = ox_Literal(str(in_o), datatype=data_type)
    else:
        out_o = ox_NamedNode(str(in_o))
    return out_s, out_p, out_o


def clone_oxigraph_store(store1: Union[ox_Store], store2: Union[ox_Store, None] = None) -> ox_Store:
    if store2 is None:
        store2 = ox_Store()
    for graph in store1.named_graphs():
        store2.add_graph(graph)
    for q in store1.quads_for_pattern(None, None, None, None):
        store2.add(q)
    return store2
