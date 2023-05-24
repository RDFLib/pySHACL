# -*- coding: utf-8 -*-
from rdflib.namespace import XSD, Namespace

RDF_PFX = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
OWL_PFX = 'http://www.w3.org/2002/07/owl#'
SH_PFX = 'http://www.w3.org/ns/shacl#'
RDF = Namespace(RDF_PFX)
RDFS = Namespace(RDFS_PFX)
OWL = Namespace(OWL_PFX)
SH = Namespace(SH_PFX)

XSD_WHOLE_INTEGERS = (
    XSD.integer,
    XSD.int,
    XSD.long,
    XSD.negativeInteger,
    XSD.nonNegativeInteger,
    XSD.nonPositiveInteger,
    XSD.positiveInteger,
    XSD.short,
    XSD.unsignedByte,
    XSD.unsignedInt,
    XSD.unsignedLong,
    XSD.unsignedShort,
)

# Classes
RDF_Property = RDF.Property
RDF_List = RDF.List
RDFS_Resource = RDFS.Resource
RDFS_Class = RDFS.Class
OWL_Ontology = OWL.Ontology
OWL_Class = OWL.Class
OWL_DatatypeProperty = OWL.DatatypeProperty
SH_NodeShape = SH.NodeShape
SH_PropertyShape = SH.PropertyShape
SH_ValidationResult = SH.ValidationResult
SH_ValidationReport = SH.ValidationReport
SH_Violation = SH.Violation
SH_Info = SH.Info
SH_Warning = SH.Warning
SH_IRI = SH.IRI
SH_BlankNode = SH.BlankNode
SH_Literal = SH.Literal
SH_BlankNodeOrIRI = SH.BlankNodeOrIRI
SH_BlankNodeORLiteral = SH.BlankNodeOrLiteral
SH_IRIOrLiteral = SH.IRIOrLiteral
SH_ConstraintComponent = SH.ConstraintComponent
SH_PropertyConstraintComponent = SH.PropertyConstraintComponent
SH_NodeConstraintComponent = SH.NodeConstraintComponent
SH_SHACLFunction = SH.SHACLFunction
SH_SPARQLFunction = SH.SPARQLFunction
SH_SPARQLRule = SH.SPARQLRule
SH_TripleRule = SH.TripleRule
SH_SPARQLTarget = SH.SPARQLTarget
SH_SPARQLTargetType = SH.SPARQLTargetType
SH_JSTarget = SH.JSTarget
SH_JSTargetType = SH.JSTargetType
SH_JSFunction = SH.JSFunction

# predicates
RDF_type = RDF.type
RDF_first = RDF.first
RDF_rest = RDF.rest
RDF_object = RDF.object
RDF_predicate = RDF.predicate
RDF_subject = RDF.subject
RDFS_subClassOf = RDFS.subClassOf
RDFS_comment = RDFS.comment
SH_path = SH.path
SH_deactivated = SH.deactivated
SH_message = SH.message
SH_name = SH.name
SH_description = SH.description
SH_property = SH.property
SH_node = SH.node
SH_target = SH.target  # from advanced spec
SH_targetClass = SH.targetClass
SH_targetNode = SH.targetNode
SH_targetObjectsOf = SH.targetObjectsOf
SH_targetSubjectsOf = SH.targetSubjectsOf
SH_focusNode = SH.focusNode
SH_resultSeverity = SH.resultSeverity
SH_resultPath = SH.resultPath
SH_resultMessage = SH.resultMessage
SH_sourceConstraint = SH.sourceConstraint
SH_sourceConstraintComponent = SH.sourceConstraintComponent
SH_sourceShape = SH.sourceShape
SH_severity = SH.severity
SH_value = SH.value
SH_conforms = SH.conforms
SH_result = SH.result
SH_inversePath = SH.inversePath
SH_alternativePath = SH.alternativePath
SH_zeroOrMorePath = SH.zeroOrMorePath
SH_oneOrMorePath = SH.oneOrMorePath
SH_zeroOrOnePath = SH.zeroOrOnePath
SH_prefixes = SH.prefixes
SH_prefix = SH.prefix
SH_namespace = SH.namespace
SH_rule = SH.rule
SH_condition = SH.condition
SH_order = SH.order
SH_construct = SH.construct
SH_subject = SH.subject
SH_predicate = SH.predicate
SH_object = SH.object
SH_parameter = SH.parameter
SH_ask = SH.ask
SH_select = SH.select
SH_this = SH.this
SH_filterShape = SH.filterShape
SH_nodes = SH.nodes
SH_union = SH.union
SH_intersection = SH.intersection
SH_datatype = SH.datatype
SH_nodeKind = SH.nodeKind
SH_optional = SH.optional
SH_js = SH.js
SH_jsFunctionName = SH.jsFunctionName
SH_jsLibrary = SH.jsLibrary
SH_detail = SH.detail

# For env var truth comparisons
env_truths = ("t", "T", "y", "Y", "1", "True", "true", "TRUE", "yes", "YES", 1, True)
