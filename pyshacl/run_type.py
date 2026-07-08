import logging
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Optional

from .errors import ReportableRuntimeError

if TYPE_CHECKING:
    from rdflib.term import URIRef

    from .graph_abstraction import DataGraph


class PySHACLRunType(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def run(self):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def _run_pre_inference(
        cls,
        target_graph: 'DataGraph',
        inference_option: str,
        destination_graph_identifier: Optional['URIRef'] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Note, this is the OWL/RDFS pre-inference,
        it is not the Advanced Spec SHACL-Rule inferencing step.
        :param target_graph:
        :type target_graph: rdflib.Graph|rdflib.Dataset
        :param inference_option:
        :type inference_option: str
        :return:
        :rtype: NoneType
        """
        # Lazy import owlrl
        import owlrl
        from owlrl.graph_abstraction import DataGraph as OWLDataGraph

        from .inference import CustomRDFSOWLRLSemantics, CustomRDFSSemantics

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
                "Error during creation of OWL-RL Deductive Closure\n{}".format(str(e.args[0]))
            )
        if target_graph.is_oxigraph:
            ox_store = target_graph.impl
            owl_target = OWLDataGraph(ox_store)
        else:
            owl_target = target_graph.impl
        if target_graph.is_multigraph():
            target_graph.default_union = True
            if destination_graph_identifier is not None:
                if target_graph.is_oxigraph:
                    ox_store = target_graph.impl
                    owl_dest = OWLDataGraph(ox_store, locked_context=destination_graph_identifier)
                else:
                    rdf_graph = target_graph.impl.get_context(destination_graph_identifier)
                    owl_dest = rdf_graph
            else:
                owl_dest = target_graph.default_graph
        else:
            owl_dest = None
        try:
            inferencer.expand(owl_target, destination=owl_dest)
        except Exception as e:  # pragma: no cover
            raise
            logger.error("Error while running OWL-RL Deductive Closure")
            raise ReportableRuntimeError("Error while running OWL-RL Deductive Closure\n{}".format(str(e.args[0])))
