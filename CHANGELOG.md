# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Python PEP 440 Versioning](https://www.python.org/dev/peps/pep-0440/).

## [Unreleased]
### Added
- Added string-based min-length and max-length constraints
### Changed
- Fixed a bug in the string-based pattern-match constraint
- 30 Tests now passing

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

[Unreleased]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a2.dev20180906...HEAD
[0.1.0a2.dev20180906]: https://github.com/RDFLib/pySHACL/compare/v0.1.0a1.dev20180904...v0.1.0a2.dev20180906

