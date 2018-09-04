# -*- coding: utf-8 -*-
import rdflib

from rdflib.namespace import Namespace
from rdflib import RDFS, RDF, OWL

SH = Namespace('http://www.w3.org/ns/shacl#')

# Classes
SH_NodeShape = SH.term('NodeShape')
SH_PropertyShape = SH.term('PropertyShape')


# predicates
RDF_type = RDF.term('type')
RDFS_subClassOf = RDFS.term('subClassOf')
SH_path = SH.term('path')
SH_property = SH.term('property')
SH_targetClass = SH.term('targetClass')
SH_targetNode = SH.term('targetNode')
SH_targetObjectsOf = SH.term('targetObjectsOf')
SH_targetSubjectsOf = SH.term('targetSubjectsOf')
