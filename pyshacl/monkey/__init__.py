# -*- coding: utf-8 -*-

from distutils.version import LooseVersion
import rdflib

RDFLIB_VERSION = LooseVersion(rdflib.__version__)
RDFLIB_421 = LooseVersion("4.2.1")
RDFLIB_500 = LooseVersion("5.0.0")

def rdflib_bool_patch():
    from rdflib.term import _toPythonMapping, _XSD_PFX, URIRef
    rdflib.NORMALIZE_LITERALS = False
    _toPythonMapping[URIRef(_XSD_PFX + 'boolean')] = \
        lambda i: i.lower() == 'true'

def rdflib_term_ge_le_patch():
    def __le__(term, other):
        r = term.__lt__(other)
        if r:
            return r
        try:
            return term.eq(other)
        except TypeError:
            return NotImplemented

    def __ge__(term, other):
        try:
            return term.__gt__(other) or term.eq(other)
        except TypeError:
            return NotImplemented
    setattr(rdflib.term.Literal, "__ge__", __ge__)
    setattr(rdflib.term.Literal, "__le__", __le__)

def apply_patches():
    #applied = apply_patches.applied
    #if applied:
    #    return True
    if RDFLIB_500 > RDFLIB_VERSION:
        rdflib_bool_patch()
    if RDFLIB_421 >= RDFLIB_VERSION:
        rdflib_term_ge_le_patch()
    #apply_patches.applied = True
    return True
apply_patches.applied = False

