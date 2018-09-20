# -*- coding: utf-8 -*-

def rdflib_bool_patch():
    import rdflib
    from rdflib.term import _toPythonMapping, _XSD_PFX, URIRef
    rdflib.NORMALIZE_LITERALS = False
    _toPythonMapping[URIRef(_XSD_PFX + 'boolean')] = \
        lambda i: i.lower() == 'true'

def apply_patches():
    #applied = apply_patches.applied
    #if applied:
    #    return True
    rdflib_bool_patch()
    #apply_patches.applied = True
    return True
apply_patches.applied = False

