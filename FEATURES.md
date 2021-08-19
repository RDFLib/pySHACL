# pySHACL Features Matrix

## [Core Constraint Components](https://www.w3.org/TR/shacl/#core-components)


### [Value Type Constraint Components](https://www.w3.org/TR/shacl/#core-components-value-type)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:class`  	    | `ClassConstraintComponent`        | [▶][ClassConstraintComponent]         | ![status-complete] 	|           |
| `sh:datatype`     | `DatatypeConstraintComponent`     | [▶][DatatypeConstraintComponent]      | ![status-complete]    |           |
| `sh:nodeKind`     | `NodeKindConstraintComponent`     | [▶][NodeKindConstraintComponent]      | ![status-complete]    |           |


### [Cardinality Constraint Components](https://www.w3.org/TR/shacl/#core-components-count)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:minCount`     | `MinCountConstraintComponent`     | [▶][MinCountConstraintComponent]      | ![status-complete] 	|           |
| `sh:maxCount`     | `MaxCountConstraintComponent`     | [▶][MaxCountConstraintComponent]      | ![status-complete] 	|           |


### [Value Range Constraint Components](https://www.w3.org/TR/shacl/#core-components-range)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:minExclusive` | `MinExclusiveConstraintComponent` | [▶][MinExclusiveConstraintComponent]  | ![status-complete] 	|           |
| `sh:minInclusive` | `MinInclusiveConstraintComponent` | [▶][MinInclusiveConstraintComponent]  | ![status-complete] 	|           |
| `sh:maxExclusive` | `MaxExclusiveConstraintComponent` | [▶][MaxExclusiveConstraintComponent]  | ![status-complete] 	|           |
| `sh:maxInclusive` | `MaxInclusiveConstraintComponent` | [▶][MaxInclusiveConstraintComponent]  | ![status-complete] 	|           |


### [String-based Constraint Components](https://www.w3.org/TR/shacl/#core-components-string)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	             |
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	             |
| `sh:minLength`    | `MinLengthConstraintComponent`    | [▶][MinLengthConstraintComponent]     | ![status-complete] 	|                        |
| `sh:maxLength`    | `MaxLengthConstraintComponent`    | [▶][MaxLengthConstraintComponent]     | ![status-complete] 	|                        |
| `sh:pattern`      | `PatternConstraintComponent`      | [▶][PatternConstraintComponent]       | ![status-complete]  	| includes `sh:flags`    |
| `sh:languageIn`   | `LanguageInConstraintComponent`   | [▶][LanguageInConstraintComponent]    | ![status-complete] 	|                        |
| `sh:uniqueLang`   | `UniqueLangConstraintComponent`   | [▶][UniqueLangConstraintComponent]    | ![status-complete] 	|                        |


### [Property Pair Constraint Components](https://www.w3.org/TR/shacl/#core-components-property-pairs)
| Parameter               | Constraint                              |  Link 	                                |      Status      	    |  Comments	|
|:----------              |:-------------                           |:------:	                                |:-------------:	    |:------	|
| `sh:equals`             | `EqualsConstraintComponent`             | [▶][EqualsConstraintComponent]            | ![status-complete] 	|           |
| `sh:disjoint`           | `DisjointConstraintComponent`           | [▶][DisjointConstraintComponent]          | ![status-complete] 	|           |
| `sh:lessThan`           | `LessThanConstraintComponent`           | [▶][LessThanConstraintComponent]          | ![status-complete]  	|           |
| `sh:lessThanOrEquals`   | `LessThanOrEqualsConstraintComponent`   | [▶][LessThanOrEqualsConstraintComponent]  | ![status-complete] 	|           |


### [Logical Constraint Components](https://www.w3.org/TR/shacl/#core-components-logical)
| Parameter  | Constraint                 |  Link 	                      |      Status   	    |  Comments	|
|:---------- |:-------------              |:------:	                      |:-------------:	    |:------	|
| `sh:not`   | `NotConstraintComponent`   | [▶][NotConstraintComponent]   | ![status-complete] 	|           |
| `sh:and`   | `AndConstraintComponent`   | [▶][AndConstraintComponent]   | ![status-complete] 	|           |
| `sh:or`    | `OrConstraintComponent`    | [▶][OrConstraintComponent]    | ![status-complete] 	|           |
| `sh:xone`  | `XoneConstraintComponent`  | [▶][XoneConstraintComponent]  | ![status-complete] 	|           |


### [Shape-based Constraint Components](https://www.w3.org/TR/shacl/#core-components-shape)
| Parameter                 | Constraint                                |  Link 	                                   |      Status      	  |  Comments                                     |
|:----------                |:-------------                             |:------:	                                   |:-------------:	      |:------	                                      |
| `sh:node`                 | `NodeConstraintComponent`                 | [▶][NodeConstraintComponent]                 | ![status-complete]   |                                               |
| `sh:property`             | `PropertyConstraintComponent`             | [▶][PropertyConstraintComponent]             | ![status-complete]   | See SHACL Property Paths feature table below  |
| `sh:qualifiedValueShape`  | `QualifiedValueShapeConstraintComponent`  | [▶][QualifiedValueShapeConstraintComponent]  | ![status-complete]   | includes `sh:qualifiedValueShapesDisjoint`    |
| `sh:qualifiedMinCount`    | `QualifiedMinCountConstraintComponent`    | [▶][QualifiedValueShapeConstraintComponent]  | ![status-complete]   |                                               |
| `sh:qualifiedMaxCount`    | `QualifiedMaxCountConstraintComponent`    | [▶][QualifiedValueShapeConstraintComponent]  | ![status-complete]   |                                               |


### [Other Constraint Components](https://www.w3.org/TR/shacl/#core-components-others)
| Parameter               | Constraint                    |  Link 	                          |      Status      	|  Comments	                 |
|:----------              |:-------------                 |:------:	                          |:-------------:	    |:------	                 |
| `sh:closed`             | `ClosedConstraintComponent`   | [▶][ClosedConstraintComponent]    | ![status-complete]	|                            |
| `sh:ignoredProperties`  | `ClosedConstraintComponent`   | [▶][ClosedConstraintComponent]    | ![status-complete] 	|                            |
| `sh:hasValue`           | `HasValueConstraintComponent` | [▶][HasValueConstraintComponent]  | ![status-complete] 	|                            |
| `sh:in`                 | `InConstraintComponent`       | [▶][InConstraintComponent]        | ![status-complete] 	|                            |

## [SPARQL Constraints](https://www.w3.org/TR/shacl/#sparql-constraints)

### [SPARQL Based Constraints](https://www.w3.org/TR/shacl/#sparql-constraints)
| Parameter               | Constraint                    |  Link 	                          |      Status      	|  Comments	                 |
|:----------              |:-------------                 |:------:	                          |:-------------:	    |:------	                 |
| `sh:sparql`             | `SPARQLConstraintComponent`   | [▶][SPARQLConstraintComponent]    | ![status-complete]	|                            |


### [SPARQL Based Constraint Components](https://www.w3.org/TR/shacl/#dfn-sparql-based-constraint-component)
| Parameter               | Constraint                    |  Link 	                          |      Status      	|  Comments	                 |
|:----------              |:-------------                 |:------:	                          |:-------------:	    |:------	                 |
| `sh:validator`          | `ConstraintComponent`         | [▶][ConstraintComponent]          | ![status-complete]	|                            |
| `sh:select`             | `SPARQLSelectValidator`       | [▶][SPARQLSelectValidator]        | ![status-complete]	|                            |
| `sh:ask`                | `SPARQLAskValidator`          | [▶][SPARQLAskValidator]           | ![status-complete]	|                            |


### [SHACL Property Paths](https://www.w3.org/TR/shacl/#property-paths)
| Path                |  Link 	                 |      Status      	|  Comments	|
|:----------          |:------:	                 |:-------------:	    |:------	|
| Predicate Path      | [▶][PredicatePath]       | ![status-complete] 	|           |
| Sequence Paths      | [▶][SequencePath]        | ![status-complete] 	|           |
| Alternative Paths   | [▶][AlternativePath]     | ![status-complete] 	|           |
| Inverse Paths       | [▶][InversePath]         | ![status-complete] 	|           |
| Zero-Or-More Paths  | [▶][ZeroOrMorePath]      | ![status-complete] 	|           |
| One-Or-More Paths   | [▶][OneOrMorePath]       | ![status-complete] 	|           |
| Zero-Or-One Paths   | [▶][ZeroOrOnePath]       | ![status-complete] 	|           |


### [Non-Validating Shape Characteristics](https://www.w3.org/TR/shacl/#nonValidation)
| Path                |  Link 	                 |      Status      	|  Comments	|
|:----------          |:------:	                 |:-------------:	    |:------	|
| `sh:name`           | [▶][ShapeName]           | ![status-complete]	|           |
| `sh:description`    | [▶][ShapeName]           | ![status-complete]	|           |
| `sh:order`          | [▶][ShapeOrder]          | ![status-missing] 	|           |
| `sh:group`          | [▶][ShapeGroup]          | ![status-missing] 	|           |
| `sh:defaultValue`   | [▶][ShapeDefaultValue]   | ![status-missing] 	|           |


# SHACL Advanced Features [spec](https://www.w3.org/TR/shacl-af/)

### [Custom Targets](https://www.w3.org/TR/shacl-af/#targets)
| Parameter             |  Link 	               |      Status      	|  Comments	|
|:----------            |:------:	               |:-------------:	    |:------	|
| `sh:target`           | [▶][AFSPARQLTarget]      | ![status-complete]	|           |
| `sh:SPARQLTarget`     | [▶][AFSPARQLTarget]      | ![status-complete]	|           |
| `sh:SPARQLTargetType` | [▶][AFSPARQLTargetType]  | ![status-complete]	|           |


### [Annotation Properties](https://www.w3.org/TR/shacl-af/#sparql-constraints-annotations)
| Parameter               |  Link 	             |      Status      	|  Comments	|
|:----------              |:------:	             |:-------------:	    |:------	|
| `sh:annotationProperty` | [▶][AFAnnotation]    | ![status-missing]	|           |
| `sh:annotationVarName`  | [▶][AFAnnotation]    | ![status-missing]	|           |
| `sh:annotationValue`    | [▶][AFAnnotation]    | ![status-missing] 	|           |

### [SHACL Functions](https://www.w3.org/TR/shacl-af/#functions)
| Parameter               |  Link 	              |      Status      	|  Comments	|
|:----------              |:------:	              |:-------------:	    |:------:	|
| `sh:SHACLFunction`      | [▶][AFSPARQLFunction] | ![status-complete]	| fully implemented        |
| `sh:SPARQLFunction`     | [▶][AFSPARQLFunction] | ![status-complete]	| implemented using RDFLib |

### [Node Expressions](https://www.w3.org/TR/shacl-af/#node-expressions)
| Path                |  Link 	                 |      Status      	|  Comments	 |
|:----------          |:------:	                 |:-------------:	    |:---------: |
| `sh:this`           | [▶][AFExpressionFocus]   | ![status-complete]	|            |
| Constant Term       | [▶][AFExpConstantTerm]   | ![status-complete]	|            |
| `sh:filterShape`    | [▶][AFExpFilterShape]    | ![status-complete] 	| not tested |
| SHACL Function      | [▶][AFExpFunction]       | ![status-complete] 	|            |
| `sh:path`           | [▶][AFExpPath]           | ![status-complete] 	|            |
| `sh:intersection`   | [▶][AFExpIntersection]   | ![status-complete] 	| not tested |
| `sh:union`          | [▶][AFExpUnion]          | ![status-complete] 	| not tested |

### [Expression Constraints][AFExpression]
| Path                               |  Link 	              |      Status      	|  Comments	|
|:----------                         |:------:	              |:-------------:	    |:------:   |
| `sh:ExpressionConstraintComponent` | [▶][AFExpression]      | ![status-complete] 	|           |

### [SHACL Rules](https://www.w3.org/TR/shacl-af/#rules)
| Parameter               |  Link 	              |      Status      	|  Comments	|
|:----------              |:------:	              |:-------------:	    |:------:   |
| `sh:condition`          | [▶][AFCondition]      | ![status-complete]	|           |
| `sh:order`              | [▶][AFOrder]          | ![status-complete]	|           |
| `sh:deactivated`        | [▶][AFDeactivated]    | ![status-complete]	|           |
| `sh:entailment`         | [▶][AFEntailment]     | ![status-missing]	|           |
| `sh:TripleRule`         | [▶][AFTripleRule]     | ![status-complete]	|           |
| `sh:SPARQLRule`         | [▶][AFSPARQLRule]     | ![status-complete]	|           |

# SHACL-JS [spec](https://www.w3.org/TR/shacl-js/)

The SHACL-JS features are implemented behind a Python "extras" feature.
To enable it, you must install PySHACL using PIP with the extras included like `pyshacl[js]`

### [Javascript-based Constraints](https://www.w3.org/TR/shacl-js/#js-constraints)
| Parameter             |  Link 	                	|      Status       	|  Comments	|
|:----------            |:------:	                	|:-----------------:	|:------	|
| `sh:js`               | [▶][JSConstraintValidation]	| ![status-complete]	|           |

### [Javascript-based Constraints-Components](https://www.w3.org/TR/shacl-js/#js-components)
| Parameter             |  Link 	                	|      Status       	|  Comments	|
|:----------            |:------:	                	|:-----------------:	|:------	|
| `sh:validator`        | [▶][JSConstraintComponentValidation]	| ![status-complete]	|           |
| `sh:JSValidator`      | [▶][JSConstraintComponentValidation]	| ![status-complete]	|           |

### [Javascript-based SHACL Functions](https://www.w3.org/TR/shacl-js/#js-functions)
| Parameter             |  Link 	                	|      Status       	|  Comments	|
|:----------            |:------:	                	|:-----------------:	|:------	|
| `sh:JSFunction`       | [▶][JSFunctionsSyntax]    	| ![status-complete]	|           |
| `sh:parameter`        | [▶][JSFunctionsSyntax]    	| ![status-complete]	|           |

### [Javascript-based SHACL Rules](https://www.w3.org/TR/shacl-js/#rules)
| Parameter             |  Link 	                	|      Status       	|  Comments	|
|:----------            |:------:	                	|:-----------------:	|:------	|
| `sh:JSRule`           | [▶][JSRulesExecution]     	| ![status-complete]	|           |

### [Javascript-based Custom Targets](https://www.w3.org/TR/shacl-js/#targets)
| Parameter             |  Link 	                	|      Status       	|  Comments	|
|:----------            |:------:	                	|:-----------------:	|:------	|
| `sh:JSTarget`         | [▶][JSTarget]             	| ![status-complete]	|           |
| `sh:JSTargetType`     | [▶][JSTargetType]         	| ![status-complete]	|           |


# Implementation Notes

## SHACL Test Suite Failures:
```
- core/property/datatype-ill-formed.ttl : Waiting on RDFLib support for determining ill-formed Literals https://github.com/RDFLib/rdflib/issues/848
- sparql/pre-binding/shapesGraph-001.ttl : Prebinding to $shapesGraph is currently unsupported. This will be supported in the future.
```

[status-complete]: https://img.shields.io/badge/status-complete-green.svg?longCache=true&style=popout
[status-partial]: https://img.shields.io/badge/status-partial-yellow.svg?longCache=true&style=popout
[status-missing]: https://img.shields.io/badge/status-missing-orange.svg?longCache=true&style=popout
[link-icon]: https://assets-cdn.github.com/images/icons/emoji/unicode/1f517.png

[ClassConstraintComponent]: https://www.w3.org/TR/shacl/#ClassConstraintComponent
[DatatypeConstraintComponent]: https://www.w3.org/TR/shacl/#DatatypeConstraintComponent
[NodeKindConstraintComponent]: https://www.w3.org/TR/shacl/#NodeKindConstraintComponent
[MinCountConstraintComponent]: https://www.w3.org/TR/shacl/#MinCountConstraintComponent
[MaxCountConstraintComponent]: https://www.w3.org/TR/shacl/#MaxCountConstraintComponent
[MinExclusiveConstraintComponent]: https://www.w3.org/TR/shacl/#MinExclusiveConstraintComponent
[MinInclusiveConstraintComponent]: https://www.w3.org/TR/shacl/#MinInclusiveConstraintComponent
[MaxExclusiveConstraintComponent]: https://www.w3.org/TR/shacl/#MaxExclusiveConstraintComponent
[MaxInclusiveConstraintComponent]: https://www.w3.org/TR/shacl/#MaxInclusiveConstraintComponent
[MinLengthConstraintComponent]: https://www.w3.org/TR/shacl/#MinLengthConstraintComponent
[MaxLengthConstraintComponent]: https://www.w3.org/TR/shacl/#MaxLengthConstraintComponent
[PatternConstraintComponent]: https://www.w3.org/TR/shacl/#PatternConstraintComponent
[LanguageInConstraintComponent]: https://www.w3.org/TR/shacl/#LanguageInConstraintComponent
[UniqueLangConstraintComponent]: https://www.w3.org/TR/shacl/#UniqueLangConstraintComponent
[EqualsConstraintComponent]: https://www.w3.org/TR/shacl/#EqualsConstraintComponent
[DisjointConstraintComponent]: https://www.w3.org/TR/shacl/#DisjointConstraintComponent
[LessThanConstraintComponent]: https://www.w3.org/TR/shacl/#LessThanConstraintComponent
[LessThanOrEqualsConstraintComponent]: https://www.w3.org/TR/shacl/#LessThanOrEqualsConstraintComponent
[NotConstraintComponent]: https://www.w3.org/TR/shacl/#NotConstraintComponent
[AndConstraintComponent]: https://www.w3.org/TR/shacl/#AndConstraintComponent
[OrConstraintComponent]: https://www.w3.org/TR/shacl/#OrConstraintComponent
[XoneConstraintComponent]: https://www.w3.org/TR/shacl/#XoneConstraintComponent
[NodeConstraintComponent]: https://www.w3.org/TR/shacl/#NodeConstraintComponent
[PropertyConstraintComponent]: https://www.w3.org/TR/shacl/#PropertyConstraintComponent
[QualifiedValueShapeConstraintComponent]: https://www.w3.org/TR/shacl/#QualifiedValueShapeConstraintComponent
[ClosedConstraintComponent]: https://www.w3.org/TR/shacl/#ClosedConstraintComponent
[HasValueConstraintComponent]: https://www.w3.org/TR/shacl/#HasValueConstraintComponent
[InConstraintComponent]: https://www.w3.org/TR/shacl/#InConstraintComponent

[SPARQLConstraintComponent]: https://www.w3.org/TR/shacl/#dfn-sparql-based-constraints
[ConstraintComponent]: https://www.w3.org/TR/shacl/#dfn-sparql-based-constraint-component
[SPARQLAskValidator]: https://www.w3.org/TR/shacl/#SPARQLAskValidator
[SPARQLSelectValidator]: https://www.w3.org/TR/shacl/#SPARQLSelectValidator

[PredicatePath]: https://www.w3.org/TR/shacl/#property-path-predicate
[SequencePath]: https://www.w3.org/TR/shacl/#property-path-sequence
[AlternativePath]: https://www.w3.org/TR/shacl/#property-path-alternative
[InversePath]: https://www.w3.org/TR/shacl/#property-path-inverse
[ZeroOrMorePath]: https://www.w3.org/TR/shacl/#property-path-zero-or-more
[OneOrMorePath]: https://www.w3.org/TR/shacl/#property-path-one-or-more
[ZeroOrOnePath]: https://www.w3.org/TR/shacl/#property-path-zero-or-one

[ShapeName]: https://www.w3.org/TR/shacl/#name
[ShapeOrder]: https://www.w3.org/TR/shacl/#order
[ShapeGroup]: https://www.w3.org/TR/shacl/#group
[ShapeDefaultValue]: https://www.w3.org/TR/shacl/#defaultValue

[AFSPARQLTarget]: https://www.w3.org/TR/shacl-af/#SPARQLTarget
[AFSPARQLTargetType]: https://www.w3.org/TR/shacl-af/#SPARQLTargetType
[AFAnnotation]: https://www.w3.org/TR/shacl-af/#sparql-constraints-annotations
[AFSPARQLFunction]: https://www.w3.org/TR/shacl-af/#SPARQLFunction
[AFExpressionFocus]: https://www.w3.org/TR/shacl-af/#node-expressions-focus
[AFExpConstantTerm]: https://www.w3.org/TR/shacl-af/#node-expressions-constant
[AFExpFilterShape]: https://www.w3.org/TR/shacl-af/#node-expressions-filter-shape
[AFExpFunction]: https://www.w3.org/TR/shacl-af/#node-expressions-function
[AFExpPath]: https://www.w3.org/TR/shacl-af/#node-expressions-path
[AFExpIntersection]: https://www.w3.org/TR/shacl-af/#intersection
[AFExpUnion]: https://www.w3.org/TR/shacl-af/#union

[AFExpression]: https://www.w3.org/TR/shacl-af/#ExpressionConstraintComponent
[AFCondition]: https://www.w3.org/TR/shacl-af/#condition
[AFOrder]: https://www.w3.org/TR/shacl-af/#rules-order
[AFDeactivated]: https://www.w3.org/TR/shacl-af/#deactivated
[AFEntailment]: https://www.w3.org/TR/shacl-af/#Rules
[AFTripleRule]: https://www.w3.org/TR/shacl-af/#TripleRule
[AFSPARQLRule]: https://www.w3.org/TR/shacl-af/#SPARQLRule

[JSConstraintValidation]: https://www.w3.org/TR/shacl-js/#js-constraints-validation
[JSConstraintComponentValidation]: https://www.w3.org/TR/shacl-js/#validation-of-javascript-based-constraint-components
[JSFunctionsSyntax]: https://www.w3.org/TR/shacl-js/#syntax-and-semantics-of-javascript-based-functions
[JSRulesExecution]: https://www.w3.org/TR/shacl-js/#rules-execution
[JSTarget]: https://www.w3.org/TR/shacl-js/#JSTarget
[JSTargetType]: https://www.w3.org/TR/shacl-js/#JSTargetType
