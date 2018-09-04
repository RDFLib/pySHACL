
"""
https://www.w3.org/TR/shacl/#core-components-value-type
"""
import abc
import pyshacl.consts

class ConstraintComponent(object, metaclass=abc.ABCMeta):

    def __init__(self, shape):
        self.shape = shape

    @classmethod
    @abc.abstractmethod
    def constraint_parameters(cls):
        return NotImplementedError()

    @abc.abstractmethod
    def evaluate(self, target_graph, value_nodes):
        return NotImplementedError()
