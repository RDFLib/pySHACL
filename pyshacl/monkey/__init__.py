# -*- coding: utf-8 -*-

import rdflib

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
    rdflib_bool_patch()
    rdflib_term_ge_le_patch()
    #apply_patches.applied = True
    return True
apply_patches.applied = False

