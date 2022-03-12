# -*- coding: utf-8 -*-


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


class ShapeLoadError(ReportableRuntimeError):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\nFor reference, see {}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ShapeLoadError: {}".format(self.__str__())


class RuleLoadError(ReportableRuntimeError):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\nFor reference, see {}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "RuleLoadError: {}".format(self.__str__())


class ValidationFailure(ReportableRuntimeError):
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


class ValidationWarning(RuntimeWarning):
    def __init__(self, message, link):
        super(ValidationWarning, self).__init__()
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\nFor reference, see {}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "{}: {}".format(str(self.__class__), self.__str__())


class ShapeRecursionWarning(ValidationWarning):
    def __init__(self, evaluation_path):
        length = len(evaluation_path)
        r_string = "->".join(str(e) for e in evaluation_path)
        message = (
            "Warning, A Recursive Shape was detected executing a recursive validation sequence "
            "{} levels deep. Backing out.\n{}".format(length, r_string)
        )
        link = "https://www.w3.org/TR/shacl/#shapes-recursion"
        super(ShapeRecursionWarning, self).__init__(message, link)


class ConstraintLoadError(ReportableRuntimeError):
    def __init__(self, message, link):
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\nFor reference, see {}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ConstraintLoadError: {}".format(self.__str__())


class ConstraintLoadWarning(RuntimeWarning):
    def __init__(self, message, link):
        super(ConstraintLoadWarning, self).__init__()
        self.message = message
        self.link = link

    @property
    def args(self):
        return [self.message, self.link]

    def __str__(self):
        return "{}\nFor reference, see {}".format(str(self.message), str(self.link))

    def __repr__(self):
        return "ConstraintLoadWarning: {}".format(self.__str__())
