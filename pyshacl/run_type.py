from abc import ABC, ABCMeta, abstractmethod


class PySHACLRunType(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def run(self):
        raise NotImplementedError()  # pragma: no cover
