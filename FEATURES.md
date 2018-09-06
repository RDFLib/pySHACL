# pySHACL Features Matrix


##[Core Constraint Components](https://www.w3.org/TR/shacl/#core-components)


###[Value Type Constraint Components](https://www.w3.org/TR/shacl/#core-components-value-type)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:class`  	    | `ClassConstraintComponent`        | [▶][ClassConstraintComponent]         | ![status-complete] 	|           |
| `sh:datatype`     | `DatatypeConstraintComponent`     | [▶][DatatypeConstraintComponent]      | ![status-complete]    |           |
| `sh:nodeKind`     | `NodeKindConstraintComponent`     | [▶][NodeKindConstraintComponent]      | ![status-complete]    |           |


###[Cardinality Constraint Components](https://www.w3.org/TR/shacl/#core-components-count)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:minCount`     | `MinCountConstraintComponent`     | [▶][MinCountConstraintComponent]      | ![status-complete] 	|           |
| `sh:maxCount`     | `MaxCountConstraintComponent`     | [▶][MaxCountConstraintComponent]      | ![status-complete] 	|           |


###[Value Range Constraint Components](https://www.w3.org/TR/shacl/#core-components-range)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	|
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	|
| `sh:minExclusive` | `MinExclusiveConstraintComponent` | [▶][MinExclusiveConstraintComponent]  | ![status-missing] 	|           |
| `sh:minInclusive` | `MinInclusiveConstraintComponent` | [▶][MinInclusiveConstraintComponent]  | ![status-missing] 	|           |
| `sh:maxExclusive` | `MaxExclusiveConstraintComponent` | [▶][MaxExclusiveConstraintComponent]  | ![status-missing] 	|           |
| `sh:maxInclusive` | `MaxInclusiveConstraintComponent` | [▶][MaxInclusiveConstraintComponent]  | ![status-missing] 	|           |


###[String-based Constraint Components](https://www.w3.org/TR/shacl/#core-components-string)
| Parameter         | Constraint                        |  Link 	                            |      Status      	    |  Comments	             |
|:----------        |:-------------                     |:------:	                            |:-------------:	    |:------	             |
| `sh:minLength`    | `MinLengthConstraintComponent`    | [▶][MinLengthConstraintComponent]     | ![status-missing] 	|                        |
| `sh:maxLength`    | `MaxLengthConstraintComponent`    | [▶][MaxLengthConstraintComponent]     | ![status-missing] 	|                        |
| `sh:pattern`      | `PatternConstraintComponent`      | [▶][PatternConstraintComponent]       | ![status-complete]  	| includes `sh:flags`    |
| `sh:languageIn`   | `LanguageInConstraintComponent`   | [▶][LanguageInConstraintComponent]    | ![status-missing] 	|                        |
| `sh:uniqueLang`   | `UniqueLangConstraintComponent`   | [▶][UniqueLangConstraintComponent]    | ![status-missing] 	|                        |


###[Property Pair Constraint Components](https://www.w3.org/TR/shacl/#core-components-property-pairs)
| Parameter               | Constraint                              |  Link 	                                |      Status      	    |  Comments	|
|:----------              |:-------------                           |:------:	                                |:-------------:	    |:------	|
| `sh:equals`             | `EqualsConstraintComponent`             | [▶][EqualsConstraintComponent]            | ![status-missing] 	|           |
| `sh:disjoint`           | `DisjointConstraintComponent`           | [▶][DisjointConstraintComponent]          | ![status-missing] 	|           |
| `sh:lessThan`           | `LessThanConstraintComponent`           | [▶][LessThanConstraintComponent]          | ![status-missing]  	|           |
| `sh:lessThanOrEquals`   | `LessThanOrEqualsConstraintComponent`   | [▶][LessThanOrEqualsConstraintComponent]  | ![status-missing] 	|           |


###[Logical Constraint Components](https://www.w3.org/TR/shacl/#core-components-logical)
| Parameter  | Constraint                 |  Link 	                      |      Status   	    |  Comments	|
|:---------- |:-------------              |:------:	                      |:-------------:	    |:------	|
| `sh:not`   | `NotConstraintComponent`   | [▶][NotConstraintComponent]   | ![status-missing] 	|           |
| `sh:and`   | `AndConstraintComponent`   | [▶][AndConstraintComponent]   | ![status-missing] 	|           |
| `sh:or`    | `OrConstraintComponent`    | [▶][OrConstraintComponent]    | ![status-missing] 	|           |
| `sh:xone`  | `XoneConstraintComponent`  | [▶][XoneConstraintComponent]  | ![status-missing] 	|           |


###[Shape-based Constraint Components](https://www.w3.org/TR/shacl/#core-components-shape)
| Parameter                 | Constraint                                |  Link 	                                   |      Status      	  |  Comments                                     |
|:----------                |:-------------                             |:------:	                                   |:-------------:	      |:------	                                      |
| `sh:node`                 | `NodeConstraintComponent`                 | [▶][NodeConstraintComponent]                 | ![status-complete]   |                                               |
| `sh:property`             | `PropertyConstraintComponent`             | [▶][PropertyConstraintComponent]             | ![status-partial] 	  | See SHACL Property Paths feature table below  |
| `sh:qualifiedValueShape`  | `QualifiedValueShapeConstraintComponent`  | [▶][QualifiedValueShapeConstraintComponent]  | ![status-missing] 	  |                                               |


###[Other Constraint Components](https://www.w3.org/TR/shacl/#core-components-others)
| Parameter               | Constraint                    |  Link 	                          |      Status      	|  Comments	                 |
|:----------              |:-------------                 |:------:	                          |:-------------:	    |:------	                 |
| `sh:closed`             | `ClosedConstraintComponent`   | [▶][ClosedConstraintComponent]    | ![status-missing] 	| Will be hard to implement  |
| `sh:ignoredProperties`  | `ClosedConstraintComponent`   | [▶][ClosedConstraintComponent]    | ![status-missing] 	|                            |
| `sh:hasValue`           | `HasValueConstraintComponent` | [▶][HasValueConstraintComponent]  | ![status-missing] 	|                            |
| `sh:in`                 | `InConstraintComponent`       | [▶][InConstraintComponent]        | ![status-missing] 	|                            |


##[SHACL Property Paths](https://www.w3.org/TR/shacl/#property-paths)
| Path                |  Link 	                 |      Status      	|  Comments	|
|:----------          |:------:	                 |:-------------:	    |:------	|
| Predicate Path      | [▶][PredicatePath]       | ![status-complete] 	|           |
| Sequence Paths      | [▶][SequencePath]        | ![status-missing] 	|           |
| Alternative Paths   | [▶][AlternativePath]     | ![status-missing] 	|           |
| Inverse Paths       | [▶][InversePath]         | ![status-complete] 	|           |
| Zero-Or-More Paths  | [▶][ZeroOrMorePath]      | ![status-missing] 	|           |
| One-Or-More Paths   | [▶][OneOrMorePath]       | ![status-missing] 	|           |
| Zero-Or-One Paths   | [▶][ZeroOrOnePath]       | ![status-missing] 	|           |


##[Non-Validating Shape Characteristics](https://www.w3.org/TR/shacl/#nonValidation)
| Path                |  Link 	                 |      Status      	|  Comments	|
|:----------          |:------:	                 |:-------------:	    |:------	|
| `sh:name`           | [▶][ShapeName]           | ![status-missing] 	|           |
| `sh:description`    | [▶][ShapeName]           | ![status-missing] 	|           |
| `sh:order`          | [▶][ShapeOrder]          | ![status-missing] 	|           |
| `sh:group`          | [▶][ShapeGroup]          | ![status-missing] 	|           |
| `sh:defaultValue`   | [▶][ShapeDefaultValue]   | ![status-missing] 	|           |


[status-complete]: https://img.shields.io/badge/status-complete-green.svg?longCache=true&style=popout
[status-partial]: https://img.shields.io/badge/status-partial-yellow.svg?longCache=true&style=popout
[status-missing]: https://img.shields.io/badge/status-missing-orange.svg?longCache=true&style=popout
[link-icon]: https://assets-cdn.github.com/images/icons/emoji/unicode/1f517.png

[ClassConstraintComponent]: https://www.w3.org/TR/shacl/#ClassConstraintComponent
[DatatypeConstraintComponent]: https://www.w3.org/TR/shacl/#DatatypeConstraintComponent
[NodeKindConstraintComponent]: https://www.w3.org/TR/shacl/#NodeKindConstraintComponent
[MinCountConstraintComponent]: https://www.w3.org/TR/shacl/#MinCountConstraintComponent
[MinCountConstraintComponent]: https://www.w3.org/TR/shacl/#MaxCountConstraintComponent
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