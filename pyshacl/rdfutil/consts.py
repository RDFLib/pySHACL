# -*- coding: utf-8 -*-
#
from typing import Union

from rdflib import RDF, RDFS, ConjunctiveGraph, Dataset, Graph, Namespace
from rdflib.namespace import OWL
from rdflib.term import Node

RDFS_Resource = RDFS.Resource
RDF_first = RDF.first
SH = Namespace('http://www.w3.org/ns/shacl#')

ConjunctiveLike = Union[ConjunctiveGraph, Dataset]
GraphLike = Union[ConjunctiveLike, Graph]
RDFNode = Node

OWL_properties = [
    OWL.allValuesFrom,
    OWL.annotatedProperty,
    OWL.annotatedSource,
    OWL.annotatedTarget,
    OWL.assertionProperty,
    OWL.cardinality,
    OWL.complementOf,
    OWL.datatypeComplementOf,
    OWL.differentFrom,
    OWL.disjointUnionOf,
    OWL.disjointWith,
    OWL.distinctMembers,
    OWL.equivalentClass,
    OWL.equivalentProperty,
    OWL.hasKey,
    OWL.hasSelf,
    OWL.hasValue,
    OWL.intersectionOf,
    OWL.inverseOf,
    OWL.maxCardinality,
    OWL.maxQualifiedCardinality,
    OWL.members,
    OWL.minCardinality,
    OWL.minQualifiedCardinality,
    OWL.onClass,
    OWL.onDataRange,
    OWL.onDatatype,
    OWL.onProperties,
    OWL.onProperty,
    OWL.oneOf,
    OWL.propertyChainAxiom,
    OWL.propertyDisjointWith,
    OWL.qualifiedCardinality,
    OWL.sameAs,
    OWL.someValuesFrom,
    OWL.sourceIndividual,
    OWL.targetIndividual,
    OWL.targetValue,
    OWL.unionOf,
    OWL.withRestrictions,
    OWL.backwardCompatibleWith,
    OWL.deprecated,
    OWL.incompatibleWith,
    OWL.priorVersion,
    OWL.versionInfo,
    OWL.bottomDataProperty,
    OWL.topDataProperty,
    OWL.bottomObjectProperty,
    OWL.topObjectProperty,
    OWL.imports,
    OWL.versionIRI,
]
OWL_classes = [
    OWL.AllDifferent,
    OWL.AllDisjointClasses,
    OWL.AllDisjointProperties,
    OWL.Annotation,
    OWL.AnnotationProperty,
    OWL.AsymmetricProperty,
    OWL.Axiom,
    OWL.Class,
    OWL.DataRange,
    OWL.DatatypeProperty,
    OWL.DeprecatedClass,
    OWL.DeprecatedProperty,
    OWL.FunctionalProperty,
    OWL.InverseFunctionalProperty,
    OWL.IrreflexiveProperty,
    OWL.NamedIndividual,
    OWL.NegativePropertyAssertion,
    OWL.ObjectProperty,
    OWL.Ontology,
    OWL.OntologyProperty,
    OWL.ReflexiveProperty,
    OWL.Restriction,
    OWL.SymmetricProperty,
    OWL.TransitiveProperty,
]
RDFS_properties = [
    RDFS.comment,
    RDFS.domain,
    RDFS.isDefinedBy,
    RDFS.label,
    RDFS.member,
    RDFS.range,
    RDFS.seeAlso,
    RDFS.subClassOf,
    RDFS.subPropertyOf,
]
RDFS_classes = [
    RDFS.Class,
    RDFS.Container,
    RDFS.ContainerMembershipProperty,
    RDFS.Datatype,
    RDFS.Literal,
    RDFS.Resource,
]
