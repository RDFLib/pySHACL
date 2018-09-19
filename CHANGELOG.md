# Changelog  
All notable changes to this project will be documented in this file.  

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Python PEP 440 Versioning](https://www.python.org/dev/peps/pep-0440/).  

## [0.9.1] - 2018-09-19  
### Added  
- A second testing framework is in place  
  - this one tests against the [data-shapes-test-suite](https://w3c.github.io/data-shapes/data-shapes-test-suite).  

### Changed  
- Changed the layout and structure of the tests folder  
- Fixed a bug in the XOne constraint, discovered indicated by the new tests
- 199 of 212 tests are now passing.  


## [0.9.0] - 2018-09-19  
### Added
- Sparql Based Constraint Components  
- Sparql Constraint Component Validators  
  - AskConstraintValidator  
  - SelectConstraintValidator  
- New meta-shacl mode!  
  -  You can now validate your SHACL Shapes Graph against the built-in SHACL-SHACL Shapes graph, as an added step before validating the Data Graph.
- Updated README with Command-Line tool instructions
- Updated README with Meta-SHACL instructions
- Added new sections to the FEATURES matrix

### Changed
- Internally, a SHACL Shapes graph is now represented as a python object with type `SHACLGraph`, rather than simply an `rdflib.Graph`.
  - This allows more SHACL-specific functionality and properties that are of the SHACL graph itself.
- Updated FEATURES matrix
- Bumped version to show magnitude of progress
- 92 tests now pass


## [0.8.3] - 2018-09-17  
### Added
- Another example, this one with separate SHACL and Target files.

### Changed  
- Fixed an issue where the content of a separate SHACL graph was ignored by the validator  
- Fixed a crash caused by the result generator receiving a value node that was a string but not an RDF literal.
- Refactored constraint file layouts, in preparation for the new SPARQL constraint component functionality
- Bumped version number


## [0.8.2] - 2018-09-16  
### Added   
- Added a CONTRIBUTORS file  
- Minor fixes for PyPI upload compatibility  


## [0.8.1] - 2018-09-14  
### Added  
- Basic SPARQL Query functionality.
- SPARQL Prefix support capability

### Changed  
- Changed make_v_report function name to make_v_result, because it actually makes individual validation results, not reports.
- Changed one of the SPARQL prefix tests to better test the SPARQL uri shortening functionality
- Bumped version number
- 88 Tests now passing


## [0.8.0] - 2018-09-12  
### Added  
- Added the CLI script. pySHACL can now be easily run from the command-line.
- Added the ability for the `validate` function to work on already-open file descriptors for target data file, and for shacl file.

### Changed  
- Main `validation` function now outputs a three-item-tuple: `(conformance: bool, validation_report_graph: rdflib.Graph, validation_report_text: str)`
- Level for seeing runtime output is now DEBUG
- Changed the way a single logging interface is used across the whole application
- Bumped version number way up to show project maturity


## [0.1.0b1.dev20180912] - 2018-09-12  
### Added  
- The SHACL Core functionality is Feature-Complete!
- Added languageIn and uniqueLang constraint components!
- Added the rest of the SHACL Property Path functionality
- Added a new error type, ReportableRuntimeError, which is a RuntimeError which is desgned to pass information back to the user (via commandline, or web interface).

### Changed  
- Changed most RuntimeErrors to ReportableRuntimeErrors
- Adding the new property path rules required refactoring the way shapes generate their targets. It is much more complicated now.
- Updated Features Matrix
- Bumped Version, changed Alpha to Beta
- All 84 Core tests now passing!


## [0.1.0a10.dev20180911] - 2018-09-11  
### Added  
- Added 3 more new constraint components!
  - sh:qualifiedValueShape - QualifiedValueShapeConstraintComponent
  - sh:qualifiedMinCount - QualifiedMinCountConstraintComponent
  - sh:qualifiedMaxCount - QualifiedMaxCountConstraintComponent

### Changed  
- the make_v_result function can now take an argument to overwrite the target failing component with a custom value.
  - this is required to allow QualifiedValueShapeConstraintComponent to output the correct type of failure
- Bumped version number
- 73 tests now passing!


## [0.1.0a9.dev20180911] - 2018-09-11  
### Added  
- Added 5 more new constraint components!
  - sh:equals - EqualsConstraintComponenet
  - sh:disjoint - DisjointConstraintComponent
  - sh:lessThan - LessThanConstraintComponent
  - sh:lessThanOrEqual - LessThanOrEqualConstraintComponent
  - sh:hasValue - HasValueConstraintComponent
### Changed  
- Bumped version number
- 70 tests now passing!


## [0.1.0a8.dev20180910] - 2018-09-10  
### Changed  
- Bug: Fixed setup.py to also install the pyshacl submodules
- Bug: Use the correct parse parameters when parsing plain-text RDF as a graph input source


## [0.1.0a7.dev20180910] - 2018-09-10   
### Added  
- Added the ability to specify a rdf_format string (for the target graph and/or the shacl graph) on the main `validate` callable.  
- Added the ability to ingest and validate RDF n-triples .nt files (as the target graph, or the shacl graph)  
- Added the option to serialize the output ValidationReport graph  
- Added an example script to show a full working example of how to use the validator  

### Changed  
- Bug: Fixed the main validate function so that it actually returns the results to the caller


## [0.1.0a6.dev20180909] - 2018-09-09  
### Added
- Added a benchmark file, run it on your computer to see how fast you can do a validation.

### Changed
- Changed the default inferencing method to 'none' to make the validator both faster and more predictable
- Bug: Fixed the default_options function, it no longer incorrectly overwrites a passed in option.
- Removed the stray main.py file which served no purpose anymore.
- Bumped version number


## [0.1.0a5.dev20180907] - 2018-09-07  
### Added  
- Added new ConstraintComponent:  
  - Closed Constraint  
- Added a new custom RDFS semantic closure for the OWL-RL reasoner.  
- Added new properties to Shape objects as per the SHACL spec:  
  - `sh:deactivated` to turn off a shape  
  - `sh:name` to name/title a shape when represented in a form  
  - `sh:description` to describe a shape when represented in a form  
  - `sh:message` a shape's message to include in the shape report output  
- Added new Shape Target types:  
  - `sh:targetSubjectsOf` and `sh:targetObjectsOf`  
- Added the Shape's message to the message output of the ValidationReport  
- Added a link to a correctly rendered view of the FEATURES table  

### Changed  
- Changed the default pre-inferencing type. Now only do RDFS by default, not RDFS+OWLRL  
  - The SHACL validator run approx 10-15x faster when the target graph is inferenced using RDFS rather than RDFS+OWLRL.  
  - And all the the tests still pass, so OWL-RL inferencing is not required for normal SHACL validation.  
- Changed the RDFS Semantic closure for inferencing to our new custom one which ignores the 'hidden' rules.  
- 61 tests now passing  
- Updated FEATURES list.  
- Bumped version number  


## [0.1.0a4.dev20180906] - 2018-09-06  
### Added  
- Added 4 value-range constraint
  - MinExclusive, MinInclusive
  - MaxExclusive, MaxInclusive
- Added a misc constraint: InComponentConstraint
### Changed  
- Fixed some other edge cases so that more tests pass
- 52 tests now passing
- Bumped version number


## [0.1.0a3.dev20180906] - 2018-09-06  
### Added  
- Added string-based min-length and max-length constraints  
- Added logic-shape constraints (not, or, and, xone)  
- Fixed the or-datatype.test.ttl file, which would never pass due to the nature of how RDFLib parses boolean literals.  
### Changed  
- Fixed a bug in the string-based pattern-match constraint  
- Changed the variable naming convention to more closely match the SHACL spec  
  - Renamed `fails`, `failures`, `f`, etc to "Reports", because failures in SHACL are a different thing, reports are their correct name.  
- Fixed some minor issues to get more tests passing  
- 40 Tests now passing


## [0.1.0a2.dev20180906] - 2018-09-06  
### Added  
- Added full pattern matching ConstraintComponent, with working flags.  
- Result reporting and report generation is implemented  
- Two types of shapes are now implemented (NodeShapes and PropertyShapes)  
- Implicit class targeting on target-less is implemented  
- Basic path traversal on PropertyShapes is implemented  
- Seven key types of ConstraintComponents are added and working  
### Changed  
- Fixed bug in datatype matcher that would cause some tests to fail.  
- Switched to running all tests in the directory, rather than running individual tests.  
- Fixed textual report output to format Literals better (to see how they are wrong).  
- Bug fixes since previous version  
- 10+ tests are passing.  


## 0.1.0a1.dev20180904 - 2018-09-04  
### Added  

- Initial version, limited functionality  

[Unreleased]: https://github.com/RDFLib/pySHACL/compare/v0.9.1...HEAD 
[0.9.1]: https://github.com/RDFLib/pySHACL/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/RDFLib/pySHACL/compare/v0.8.3...v0.9.0
[0.8.3]: https://github.com/RDFLib/pySHACL/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/RDFLib/pySHACL/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/RDFLib/pySHACL/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/RDFLib/pySHACL/compare/v0.1.0b1.dev20180912...v0.8.0
[0.1.0b1.dev20180912]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a10.dev20180911...v0.1.0b1.dev20180912
[0.1.0a10.dev20180911]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a9.dev20180911...v0.1.0a10.dev20180911
[0.1.0a9.dev20180911]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a8.dev20180910...v0.1.0a9.dev20180911
[0.1.0a8.dev20180910]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a7.dev20180910...v0.1.0a8.dev20180910
[0.1.0a7.dev20180910]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a6.dev20180909...v0.1.0a7.dev20180910
[0.1.0a6.dev20180909]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a5.dev20180907...v0.1.0a6.dev20180909
[0.1.0a5.dev20180907]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a4.dev20180906...v0.1.0a5.dev20180907
[0.1.0a4.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a3.dev20180906...v0.1.0a4.dev20180906 
[0.1.0a3.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a2.dev20180906...v0.1.0a3.dev20180906 
[0.1.0a2.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a1.dev20180904...v0.1.0a2.dev20180906  

