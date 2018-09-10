# Changelog  
All notable changes to this project will be documented in this file.  

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Python PEP 440 Versioning](https://www.python.org/dev/peps/pep-0440/).  

## [Unreleased]  
- tbd

## [0.1.0a7.dev20180910]  
### Added  
- Added the ability to specify a rdf_format string (for the target graph and/or the shacl graph) on the main `validate` callable.  
- Added the ability to ingest and validate RDF n-triples .nt files (as the target graph, or the shacl graph)  
- Added the option to serialize the output ValidationReport graph  
- Added an example script to show a full working example of how to use the validator  

### Changed  
- Fixed the main validate function so that it actually returns the results to the caller


## [0.1.0a6.dev20180909]  
### Added
- Added a benchmark file, run it on your computer to see how fast you can do a validation.

### Changed
- Changed the default inferencing method to 'none' to make the validator both faster and more predictable
- Fixed the default_options function, it no longer incorrectly overwrites a passed in option.
- Removed the stray main.py file which served no purpose anymore.
- Bumped version number


## [0.1.0a5.dev20180907]  
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


## [0.1.0a4.dev20180906]  
### Added  
- Added 4 value-range constraint
  - MinExclusive, MinInclusive
  - MaxExclusive, MaxInclusive
- Added a misc constraint: InComponentConstraint
### Changed  
- Fixed some other edge cases so that more tests pass
- 52 tests now passing
- Bumped version number


## [0.1.0a3.dev20180906]  
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

[Unreleased]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a7.dev20180910...HEAD  
[0.1.0a7.dev20180910]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a6.dev20180909...v0.1.0a7.dev20180910
[0.1.0a6.dev20180909]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a5.dev20180907...v0.1.0a6.dev20180909
[0.1.0a5.dev20180907]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a4.dev20180906...v0.1.0a5.dev20180907
[0.1.0a4.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a3.dev20180906...v0.1.0a4.dev20180906 
[0.1.0a3.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a2.dev20180906...v0.1.0a3.dev20180906 
[0.1.0a2.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a1.dev20180904...v0.1.0a2.dev20180906  

