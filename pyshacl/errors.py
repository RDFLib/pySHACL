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
        return "ShapeLoadError: {}".format(self.__str__())