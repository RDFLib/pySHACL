# -*- coding: utf-8 -*-


class ShapeLoadError(RuntimeError):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\n{}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ShapeLoadError: {}".format(self.__str__())


class ValidationFailure(RuntimeError):
    """
    https://www.w3.org/TR/shacl/#failures
    Validation and conformance checking can result in a failure. For example, a particular SHACL processor might allow recursive shapes but report a failure if it detects a loop within the data. Failures can also be reported due to resource exhaustion. Failures are signalled through implementation-specific channels.
    """
    def __init__(self, message):
        self.message = message

    @property
    def args(self):
        return [self.message]

    def __str__(self):
        return str(self.message)

    def __repr__(self):
        return "ValidationFailure: {}".format(self.__str__())


class ConstraintLoadError(RuntimeError):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\n{}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ConstraintLoadError: {}".format(self.__str__())

class ConstraintLoadWarning(RuntimeWarning):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\n{}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ConstraintLoadWarning: {}".format(self.__str__())


class ReportableRuntimeError(RuntimeError):
    def __init__(self, message):
        self.message = message

    @property
    def args(self):
        return [self.message]

    def __str__(self):
        return str(self.message)

    def __repr__(self):
        return "ReportableRuntimeError: {}".format(self.__str__())

