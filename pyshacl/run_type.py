import logging
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Optional

import rdflib

from pyshacl.errors import ReportableRuntimeError

if TYPE_CHECKING:
    from pyshacl.pytypes import GraphLike


class PySHACLRunType(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def run(self):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def _run_pre_inference(
        cls, target_graph: 'GraphLike', inference_option: str, logger: Optional[logging.Logger] = None
    ):
        """
        Note, this is the OWL/RDFS pre-inference,
        it is not the Advanced Spec SHACL-Rule inferencing step.
        :param target_graph:
        :type target_graph: rdflib.Graph|rdflib.ConjunctiveGraph|rdflib.Dataset
        :param inference_option:
        :type inference_option: str
        :return:
        :rtype: NoneType
        """
        # Lazy import owlrl
        import owlrl

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
        if isinstance(target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
            named_graphs = []
            for i in target_graph.store.contexts(None):
                if isinstance(i, rdflib.Graph):
                    named_graphs.append(i)
                else:
                    named_graphs.append(
                        rdflib.Graph(target_graph.store, i, namespace_manager=target_graph.namespace_manager)
                    )
        else:
            named_graphs = [target_graph]
        try:
            # I'd prefer to not have to infer every namged graph individually, but OWL-RL doesn't
            # support doing inference on a Dataset/ConjunctiveGraph yet. (New release will be soon?)
            for g in named_graphs:
                inferencer.expand(g)
        except Exception as e:  # pragma: no cover
            logger.error("Error while running OWL-RL Deductive Closure")
            raise ReportableRuntimeError("Error while running OWL-RL Deductive Closure\n{}".format(str(e.args[0])))
