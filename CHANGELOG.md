# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Python PEP 440 Versioning](https://www.python.org/dev/peps/pep-0440/).

## [Unreleased]
- Nothing yet...

## [0.24.1] - 2023-11-23
## Note - The 0.24.x series is the last to support Python 3.7
### RDFLib v7.0.0 and some other dependencies already don't support 3.7, so PySHACL will drop it from 0.25+
### Fixed
- Shape can have multiple values for `sh:not`. Fixes #217

## [0.24.0] - 2023-11-08
## Note - The 0.24.x series is the last to support Python 3.7
### RDFLib v7.0.0 and some other dependencies already don't support 3.7, so PySHACL will drop it from 0.25+
### Added
- Compatibility with RDFLib v7.0.0 - Closes #197
### Fixed
- `sh:qualifiedMinValue` on `sh:qualifiedValueShape` now works again, even if there are no value nodes found
  on the path of the parent `PropertyShape`. Fixes #213 Thank you @ajnelson-nist for finding and reporting this.
- Fixes in rdfuitl (clone dataset, mixin dataset, and innoculate dataset) to support the case where all the DS's
  triples are in the default-context-uri graph.
### Changed
- In accordance with corresponding changes in RDFLib v7.0.0, PySHACL will now always use the default-context-uri graph
  when parsing a grpah into a Dataset or a ConjunctiveGraph
- Switched from deprecated `pkg_resources` to `importlib.metadata` for compatibility with Python 3.11 and 3.12.
  - This changes the way `pyshacl[extras]` are detected at runtime. If this adversely affects you, let us know.
- Bumped PrettyTable dependency to a much newer version, to fix distro packaging conflicts and other issues.
- Fixed more internal typing issues, particularly with newer versions of MyPy and Python 3.11+

## [0.23.0] - 2023-05-23
### Added
- Added Python 3.11 support (use it, internal benchmarking shows its 25-30% faster than Python 3.8)
- `sh:node` NodeConstraint now includes details of its child validation results, that were normally not included in the validation report.
  - exposed via the `sh:detail` property on the NodeConstraint validation report

### Changed
- Added compatibility with Python 3.11, this requires:
  - RDFLib v6.3 or greater (recommended v6.3.2)
  - PyDuktape v0.4.3 for python 3.11 support
  - Poetry v1.5.0 (or poetry-core v1.6.0)
- Graph Namespace manager now only registers 'core' namespaces, this avoids having inconsistencies and incompatibilities with your own namespaces.
- Replaced Flake8 and isort with Ruff
- Updated to latest Black version for formatting

### Fixed
- Extend ontology inoculation to include triples where NamedIndividual URI is object.
- Re-black all files, re-sort with new Ruff isort, fix some Mypy typing inconsistencies


## [0.22.2] - 2023-04-27

### In this release:

### Fixed
- Inoculating the datagraph using an extra ontology graph now copies over any missing namespace prefixes from the ontology graph to the datagraph.
  - This is to match old ontology-graph-mixin behaviour that had this side-effect.
  - Added a test to ensure this behaviour is not broken again.
- Stringifying nodes in `QualifiedValueShape` default message was using wrong stringification operation.

## [0.22.1] - 2023-04-26

### In this release:

### Fixed
- Clone full contents of an `OWL:NamedIndividual` from the ontology graph to the datagraph, during the inoculation procedure.
  - This fixes the case where an NamedIndividual in an OWL ontology had properties that were required in the datagraph at runtime to ensure successful validation
- Avoid hitting the recursion limit when stringifying a blank node, when OWL inferencing has inserted owl:sameAs the same blank node as is being serialized.
- Avoid hitting the recursion limit when cloning a graph with a blank node, when OWL inferencing has inserted owl:sameAs the same blank node as is being cloned.

### Added
- Added a default message for `QualifiedValueShape` constraint component. It never had one before.

### Changed
- Lots more debug messaging. Debugging is now _much_ more verbose.
  - This gives more insight into how PySHACL runs, what it is doing, and how long each step takes.
  - All constraint evaluations will now output their results, regardless of whether are conformant or non-conformant or if they are used in the final conformance report.
  - You will probably want debug turned off unless you are tracking down the source of a problem or performance issue.


## [0.22.0] - 2023-04-18

### In this release:

### Changed
- Big change to how ontology mix-in mechanism works
- Feature is now called datagraph inoculation
- Inoculation copies _only_ RDFS and OWL axioms (classes, properties and relationships) from the extra-ontology file into the datagraph
  - This mitigates a class of errors that cause the validator to perform validation on Nodes that should not be in the datagraph
  - Such as cases where the Shapes graph and Extra-ontology graph are the same graph, but having SHACL Shapes and constraints in the datagraph is undesired.
- Details around automatically cloning the datagraph before modification (inoculation) remain unchanged.
- If you preferred the old behaviour, where the _whole_ extra-ontology file was mixed-in to the datafile, please file a Github issue outlining your need for that.


## [0.21.0] - 2023-03-31

### In this release:

### Added
- New HTTP Server functionality
  - run PySHACL as a persistent service, exposing an OpenAPI3.0-compatible REST interface
- Detection of filename when downloading web attachments is added
- Better detection of invalid integer values for sh:minLength and sh:maxLength string constraints.

### Fixed
- Opening a http link that has chunked encoding, or content-disposition attachment will now work correctly.


## [0.20.0] - 2022-09-08

### In this release:

### Fixed
- Ill-typed/Ill-formed literals now fail the DataType test, as expected
  - Requires RDFLib v6.2.0+
  - Fixes #140 (and possibly fixes #151)
  - Unskipped one of the remaining skipped shacl-test-suite SHT tests (`datatype-ill-formed_ttl.ttl`) 
- Fixed detection of recursion to be more lenient of deliberately recursive (but not infinitely recursive) shapes.
  - Fixes #154
- MetaShacl works again now with RDFLib >= v6.2.0
  - Fixes #153
- Fixed typing issues affecting interoperability of new version of RDFLib and PySHACL.

### Changed

- RDFLib v6.2.0 or greater is now _required_ to run PySHACL
  - This new version of RDFLib implements the ill-typed Literals feature, that helps with `sh:datatype` constraint validation.
  - Removing support for older versions of RDFLib allows PySHACL to implement new features, and have less unnecessary code
- Bumped to using new Poetry v1.2.0 (or newest poetry-core v1.1.0)
  - Changed pytest-cov and coverage tests to be optional dependencies for dev
- Bumped version of Black to 22.8.0, and re-blacked all files
- Removed old monkey patches, no longer needed for the latest version of RDFLib
- Removed bundled "Memory2" store, now using the default "Memory" from RDFLib
  - Regenerated bundled pickled triplestores, to use Memory instead of Memory2
- Updated official dockerfile with newest version of PySHACL and RDFLib
  - Published to dockerhub at [ashleysommer/pyshacl](https://hub.docker.com/repository/docker/ashleysommer/pyshacl)
  - `docker pull docker.io/ashleysommer/pyshacl:latest`


## [0.19.1] - 2022-06-30

### In this release:

### Fixed
- CLI Output Table formatting crashed when report graph did not contain a resultMessage
  - Fixes #145
- Executing advanced-mode triples rules can sometimes skip the graph clone step, and incorrectly emits new triples directly into the input data-graph
  - Discovered when investigating #148

### Changed
- Executing advanced triples rules no longer incorrectly emits new triples directly into the input data-graph
  - This _may_ been seen as a breaking change, if your workflow relied on this incorrect behaviour.
  - If you _really_ the rules engine to emit new triples into your input data graph, use the `inplace` validator option.
- Updated built-in `schema.ttl` file to newer version that doesn't have UTF-8 encoding issues

### Added
- Official Dockerfile is now included in the repository
  - Thanks @KonradHoeffner; Fixes #135
  - Published to dockerhub at [ashleysommer/pyshacl](https://hub.docker.com/repository/docker/ashleysommer/pyshacl)
  - `docker pull docker.io/ashleysommer/pyshacl:latest`

## [0.19.0] - 2022-03-22

### In this release:

### Fixed
- Fixed a long-standing oversight where ShapeLoadErrors and ConstraintLoadErrors were not reported correctly when running PySHACL in CLI mode.
  - Sorry about that. Thanks lots of people for reporting this over the last year. I wish I fixed it sooner.
- Fixed a long-standing bug where using `$PATH` in a sh:sparql query on a PropertyShape would not work correctly.
  - Fixes #124, Thanks @Martijn-Y-ai
- Fixed a long-standing bug, that allows PySHACL to more reliably determine if graph source is a file path, or a graph string.
  - Fixes #132, Thanks @Zezombye
- Fixed an issue where `sh:pattern` could not be applied to a Literal that was not an `xsd:string` or URI.
  - Fixes #133, Thanks @nicholascar
- Fixed the outdated/incorrect error reported when a PropertyShape's `sh:path` value gets an unknown path type.
  - Fixes #129, Thanks @edmondchuc  

### Added
- New `--allow-infos` option in CLI mode and Python Module mode.
  - This is like `--allow-warnings` except it only allows violations with severity of `sh:Info`.
  - (`--allow-warnings` continues to allow both `sh:Warning` and `sh:Info` as it used to.)
  - Fixes #126, Thanks @ajnelson-nist
- SPARQL-based Constraints can now substitute arbitrary bound SPARQL variables into their sh:message
  - Fixes #120

### Changed
- `--allow-infos` and `--allow-warnings` can now also be enabled with `--allow-info` and `--allow-warning` respectively.
- Removed Snyk check on CI/CD pipeline, because there is an RDFLib issue blocking Snyk on PySHACL from passing.

## [0.18.1] - 2022-01-22

### Added
- Added the ability to pipe in SHACL file or ONT file via stdin on Linux or MacOS

### Fixed
- Fixed an issue where the filetype detection routine in the RDF loader would fail to reset the file back to the start.

## [0.18.0] - 2022-01-13

### Added
- Added Python 3.10 support (when using RDFLib v6.1.1 or greater)
- Added more type hinting, to conform to the new type hinting added by RDFLib 6.1.1

### Changed
- Subtle correction in the way `sh:prefixs` works with `sh:declare` on the given named ontology.
- Bumped some min versions of libraries, to gain compatibility with Python 3.10

### Fixed
- Fixed test for issue #76
- Fixed #76 again (after fixed test)

## [0.17.3] - 2021-12-13

### Fixed
- Don't crash when a SHACL function is registered more than once (eg, if a function is both SPARQLFunction and JSFunction), fixes \#108, thanks Gabe Fierro
- Fixed typo in CLI help output, thanks Alex Nelson
- Don't print env vars when importing JS module, thanks MPolitze
- Fix typo preventing OWL-RL >=6.0 to be used with pySHACL, Fixes #111

### Added
- Add Snyk checks to CI/CD pipeline

## [0.17.2] - 2021-10-25

### Fixed
- SPARQL queries with words "values", "minus", or "service" in its comments no longer incorrectly throw an exception.

### Changed
- Switched from Travis to Drone for CI testing

### Added
- New Table output type for commandline tool. Thanks @nicholascar


## [0.17.1] - 2021-10-11

### Fixed
- Handle transitive subclasses when evaluating sh:targetClass - @gtfierro
  - Fixes #96
- Improve detection of RDF/XML files when loading unknown content
  - Fixes #98
- Imported type stubs and resolved ALL MyPy issues! (this was a big effort)
- Logic fixes in the dataset loader (thanks to inconsistencies exposed by MyPy)

### Changed
- Add special cases to sh:dataclass constraint, when the given shape uses rdfs:Literal or rdfs:Dataclass as the dataclass to match on
  - Fixes #71

### Added
- Add datashapes.org/schema as a built-in graph
  - Fixes #98
- Added ability to pass a TextIO or TextIOWrapper object into the dataset loader

## [0.17.0.post1] - 2021-09-15

## Notice
This version of PySHACL **requires RDFLib 6.0.0_**. 
As a direct result of that, this version of PySHACL **also requires Python v3.7**.

### Changed
- Lazy-load OWL-RL module to avoid owl-rl import warnings when not required


## [0.17.0] - 2021-09-13

## Notice
This version of PySHACL **requires RDFLib 6.0.0_**. 
As a direct result of that, this version of PySHACL **also requires Python v3.7**.

### Changed
- Upped RDFLib min version to 6.0.0 in order to get built-in json-ld
- Upped OWL-RL to min version 5.2.3 in order to remove json-ld dependency
- Made min python version v3.7
- Change black config to use python 3.7 compat code
- Re-black and isort all source files


## [0.16.2] - 2021-09-13

## Notice
This is the **last version of PySHACL to support RDFLib 5.0.0**, subsequent releases of PySHACL will depend on RDFLib v6.0.0.
As a direct result of that, this is also the **last version of PySHACL to support Python v3.6**.

### Changed
- Pinned JSON-ld dep to <6.0 to avoid the tombstone release (so not to force rdflib 6.0)
- Updated minimum Black version to 21.8b0 to fix a black bug
- Re-black and isort all source files

### Fixed
- Fixed detection of import error when loading json-ld module in RDF loader
- Fixed Black bug with new version of black


## [0.16.1] - 2021-08-20

### Added
- [ExpressionConstraintComponent](https://www.w3.org/TR/shacl-af/#ExpressionConstraintComponent) is implemented!
  - Use your previously defined SHACL Functions to express complex constraints
  - Added DASH-tests for ExpressionConstraintComponent
  - Added advanced tests for ExpressionConstraintComponent, SHACLRules, and SHACLFunctions.
- New Advanced features example, showcasing ExpressionConstraint and others features

### Changed
- Allow sh:message to be attached to an expression block, without breaking its functionality
- A SHACL Function within a SHACL Expression now must be a list-valued property.
- Refactored node-expression and path-expression methods to be common and reusable code
- Re-black and isort all source files


## [0.16.0] - 2021-08-19

### Changed
- `sh:class` Constraint now applies transitively.
  - This means it will follow `rdfs:subClassOf` relationships right to the top of the hierarchy.
  - Be careful with this, could lead to recursion or infinite loops!
  - This requires a big version number bump because it's technically a breaking change.
  - Fixes #87, thanks `@gtfierro`

## [0.15.0] - 2021-07-20

### Fixed
- Compatibility with RDFLib 6.0.0
  - Don't use `.term()` (PR #84)
  - Use Namespaces in a way that works on both RDFLib 5 and 6.

### Changed
- Do not patch rdflib with Memory2 store on RDFLib 6.0.0+


## [0.14.5] - 2021-07-07

### Added
- Allow-Warnings is finally available. (Closes #64)
  - Setting this option puts PySHACL into a non-standard operation mode, where Shapes marked with severity of sh:Warning or sh:Info will not cause result to be invalid.
  - Despite the name, it allows both sh:Info and sh:Warning.
  - Try it with `allow_warnings=True` on `validate()` or `-w` in the CLI tool.

### Fixed
- Fixed Abort Mode. (Fixes #75)
  - This optional mode allows the validator to exit early, on the first time your data fails to validate against a Constraint.
  - Name changed from `abort_on_error` to `abort_on_first`
  - Try it out with `abort_on_first=True` on `validate()` or `--abort` in the CLI tool.


## [0.14.4] - 2021-05-26

### Added
- Added an iterate_rules option, that causes SHACL Rules to run repeatedly until reaching a steady state. (Closes #76)
  - Works with SPARQLRules, TripleRules, and JSRules.
- Variables {$this}, {$path}, and {$value} will be populated in the sh:message of a SPARQL Constraint. (Closes #30)


## [0.14.3] - 2021-02-20

### Changed
- Relaxed the Max Evaluation Depth from 28 to 30, we were seeing some real-world cases where meta-shacl was failing on large Shapes Graphs at 28 levels deep.
- sh:namespace values can now be xsd:anyURI or xsd:string or "literal string", but now cannot be <URI nodes>.
- sh:order can now support xsd:decimal values and xsd:integer values, and can be interchanged at will.


## [0.14.2] - 2021-01-02

### Added
- Potential speedups when executing validation by lazy-loading large modules which may never be required in a normal validation run.

### Fixed
- Black and Flake8 issues outstanding from 0.14.1 release.
- Workaround a RDFLib bug trying to import `requests` when requests is not required to be installed.
  - This bug will still be observed if you use SPARQLConstraints, SPARQLFunction or JSFunction features, but it can be worked around by simply installing `requests` in your python environment.


## [0.14.1] - 2020-12-23

### Added
- Inplace Mode, for when cloning your datagraph is undesirable
  - Normally pyshacl will create an in-memory copy of your datagraph before modifying it (when using ontology mixin, or inferencing features)
  - This might be unwanted if your datagraph is very large or remote and cloning it into memory is not a good option
  - Enabling inplace mode will bypass this clone step, and apply modification operations directly on your data_graph (use with caution!)
  - Enable with `inplace=True` kwarg on `validate()`.
  - Inplace mode is not yet available via the CLI application, and perhaps doesn't even make sense to have it available there.

### Fixed
- Inferencing will no longer incorrectly place expanded triples into your original data_graph, unless you enable 'inplace'
- SHACL-JS loader will no longer fail if the `regex` module is not installed (it will fall back to using builtin `re`)
- SHACL-Rule DASH-tests will now pass when the SHACL-rule is applied on multigraph (Dataset or ConjunctiveGraph)


## [0.14.0] - 2020-10-14

### Added
- SHACL-JS Support!
- Implements all of the features in the SHACL-JS SHACL Extension specification: https://www.w3.org/TR/shacl-js/
- Includes:
  - JS Constraints
  - JS ConstraintComponents
  - JS SHACL Functions
  - JS SHACL Rules
  - JS Target
  - JS TargetType
- To install it, make sure you do `pip3 install pyshacl[js]` to get the correct extra packages.

### Changed
- Added JS flag to the CLI tool to enable SHACL-JS features
- Updated README and FEATURES matrix


## [0.13.3] - 2020-09-11

### Fixed
- Fixed a long standing issue where our fancy loader would try to `seek()` on a file, after the file
  was closed by the JSON-LD parser
  - (thanks @nicholsn for reporting it)
- Fixed https://github.com/RDFLib/pySHACL/issues/62


## [0.13.2] - 2020-09-10

### Added
- Added the ability for PySHACL to use baked in graphs instead of fetching them from a HTTP endpoint when a known graph
  is imported using owl:imports
  - This allows for time savings on graph-load and saves a HTTP request
  - Also allows us to embed fixed errata versions of files in place of release-time ones online

### Fixed
- With new features, comes new bugs
- With the ability to now load SPARQLFunctions, this removes the barrier for loading Schema.org SHACL in advanced mode
- But when doing so revealed more issues. They are now fixed:
- Fixed SPARQLConstraintComponent getting confused when `shacl.ttl` was loaded into your Shapes file using owl:imports
- Fixed https://github.com/RDFLib/pySHACL/issues/61

### Changed
- Refactored `SPARQLConstraintComponent` code, to allow for other custom constraint components in the future
  - This prevented SPARQLConstraintComponent getting confused when `shacl.ttl` was loaded into the Shapes file
  using owl:imports


## [0.13.1] - 2020-09-07

### Added
- SPARQLTargetType
  - New SPARQL-based Target Type feature
  - The Paramaterisable form of SPARQLTarget from the SHACL Advanced Features spec
  - https://www.w3.org/TR/shacl-af/#SPARQLTargetType
- Added a test for SPARQLTargetType - Theres none in the SHT suite, or the DASH suite.

### Changed
- Refactored `sh:parameter` code in SPARQL-based Constraint Components, SHACLFunctions, and SPARQL-Based Target Types
  - They all now share a common SHACLParameter helper class, reducing code duplication
- Refactored `SPARQLQueryHelper`
  - `SPARQLQueryHelper` internal class is now more helpful
  - `query_helper` can now extract param bindings into param-value pairs for parameterised queries
  - Reduces more code duplication


## [0.13.0] - 2020-09-04

### Added
- New SHACL Advanced Spec Features!
- All NodeExpressions can now be used in SHACL Rules
  - Focus Node (sh:this)
  - FilterShape (sh:filterShape)
  - Function Expressions (any sh:SHACLFunction and args)
  - Path Expressions (use sh:path in a NodeExpression)
  - Intersection Expressions (sh:intersection)
  - Union Expressions (sh:union)
- SHACLFunctions (including SPARQLFunction)
  - Both SHACLFunction and SPARQLFunction are now fully implemented including unit tests and edge cases
  - SHACLFunctions are bound to PySHACL and can be used in SHACL Rules and NodeExpressions
  - SPARQLFunctions are bound to the RDFLib SPARQL Engine, so they can be used in other SPARQL queries
  - Read the manual for more info: https://www.w3.org/TR/shacl-af/#functions

### Fixed
- Short versions of uris were sometimes not used in the Validation Report when they should've been
- Checking results of some tests was being skipped! Lucky this wasn't letting through any SHACL errors.
- Fixed error message when using sh:ignoredProperties on a node that isn't sh:closed issue #58


## [0.12.2] - 2020-08-12

### Fixed
- In a validation report graph, when FocusNode and ValueNode are the same node, and are a blank node, when they get
copied into the validation report graph they will have the same bnode id as each other.
- Optimised the algorithm for copying different kinds of rdf nodes into the validation graph.

### Changed
- When the FocusNode and ValueNode are copied into the validation graph from the data graph, they will try to keep the
same bnode id they had before, if possible.


## [0.12.1.post2] - 2020-07-23

### Fixed
- A couple of autogenerated sh:message strings were trying to serialize from dataGraph rather than shapeGraph


## [0.12.1.post1] - 2020-07-22

### Fixed
- A couple of autogenerated sh:message strings were missing their focusNode element in v0.12.1


## [0.12.1] - 2020-07-22

### Added
- All SHACL Core constraints now have their own autogenerated sh:message.
  - This is used as a fallback when your Shape does not provide its own sh:message
  - See the new sh:resultMessage entries in the Validation Report output
  - These are hopefully more human-readable than the other fields of the Validation Report results

- Added a copy of the implementation of the new 'Memory2' rdflib triplestore backend.
  - This when using Python 3.6 or above, this is faster than the default 'IOMemory' store by:
    - 10.3% when benchmarking validation with no inferencing
    - 17% when benchmarking validation with rdfs inferencing
    - 19.5% when benchmarking validation with rdfs+owlrl inferencing

### Changed
- PySHACL is now categorised as **Production/Stable**.
  - This marks a level of maturity in PySHACL we are happy to no longer consider a beta
  - A v1.0.0 might be coming soon, but its just a version number, doesn't mean anything special
- Changed default rdflib triplestore backend to 'Memory2' as above.
- Tiny optimisations in the way sh:message items are added to a validation report graph.

### Fixed
- Regression since v0.11.0, sh:value and sh:focusNode from the datagraph were not included in the validation report
  graph if the datagraph was of type rdflib.ConjunctiveGraph or rdflib.Dataset.


## [0.12.0] - 2020-07-10

### Removed
- Python 3.5 support is removed. PySHACL now requires Python 3.6 or above.
  - Routine tests are run using Python 3.6.11, 3.7.8, and 3.8.2.
  - Python 3.9 might work but is not yet supported.

### Added
- Python 3.6-compatible type hinting is added throughout the codebase
- MyPy library is used to run type checking during testing process
- Flake8 linting is added to enforce PEP8
- isort is added to enforce imports linting
- Black is added to keep formatting consistent across releases

### Changed
- PySHACL is no longer a setuptools-based project with a `setup.py` and `requirements.txt` file.
- PySHACL is now a PEP518 & PEP517 project, it uses `pyproject.toml` and `poetry` to manage
dependencies, build and install.
- For best compatibility when installing from PyPI with `pip`, upgrade to pip v18.1.0 or above.
  - If you're on Ubuntu 16.04 or 18.04, you will need to run `sudo pip3 install --upgrade pip`
- Editor Line Length for PySHACL code is now set to 119 as opposed to 79 chars.



## [0.11.6.post1] - 2020-07-09

### Added
- New feature to CLI tool
  - `-V` shows the PySHACL version
- Run module directly
  - You can get access to the same CLI tool if you install the module and run it using `python3 -m pyshacl`
  - See `python3 -m pyshacl --help` for more details

### Deprecated
#### Announcement
- **This is the final version with Python v3.5 support**
  - Versions 0.12.0 and above will have newer package management and dependency management, and will
  require Python v3.6+.


## [0.11.6] - 2020-07-09

### Fixed
- Fixed a bug present since `v0.11.0`. If the data graph has multiple named graphs, and an extra ontology mixin source
used and that also has multiple named graphs, then only the first graph in the mixins source was added to the datagraph.
  - Now all named graphs from the mixin source are mixed into all named graphs of the datagraph, as originally intended.
  - Fixed one unit test which had been intermittently failing
- Cleaned up the behaviour around performing patch to Boolean Literal parsing on rdflib 5.0.0


## [0.11.5] - 2020-03-28

### Fixed
- Preparatory changes for the incoming rdflib 5.0.0 release
- Changed to a new more predictable literal comparison routine for minInclusive, minExclusive,
    maxInclusive, and maxExclusive. This removes the need for one monkey-patch in rdflib 4.2.2 and works around
    the `TOTAL_ORDER_CASTERS` special cases in rdflib `5.0.0`.


## [0.11.4] - 2020-01-31

### Fixed
- Fixed Issue [#040](https://github.com/RDFLib/pySHACL/issues/40)
- Fixed badly-formatted dates in the changelog

### Added
- Added ability for pySHACL to track and monitor its evaluation path during validation
  - This allows for the validator to detect two different scenarios:
    - A recursive shape has triggered an infinitely-recursive validation, back out
    - Evaluation Path too deep (error generated, prevents python recursion depth errors)
- Added a test for Issue #40


## [0.11.3.post1] - 2019-11-02

### Fixed
- Fixed Issue [#036](https://github.com/RDFLib/pySHACL/issues/36)

### Added
- Added test for [#036](https://github.com/RDFLib/pySHACL/issues/36)

### Changed
- Nodes defined as TargetNode by a SHACL Shape no longer is required to be present in the DataGraph.


## [0.11.3] - 2019-10-21

### Fixed
- Fixed Issue [#032](https://github.com/RDFLib/pySHACL/issues/32)
- Stringification of Focus Node, and Value Node in the results text string now works correctly
  - This is an old bug, that has been around since the first versions of pySHACL
  - Manifests when the DataGraph is a different graph than the ShapesGraph
  - Recent change from using Graphs by default to using Datasets by default helped to expose this bug
  - Thanks to @jameshowison for reporting the bug

### Changed
- Stringification of a blank node now operates on a rdflib.Graph only, rather than a Dataset.
  - Added mechanism to extract the correct named graph from a dataset when stringifying a blank node.
- Added a workaround for a json-ld loader bug where the namespace_manager for named graphs within a conjunctive graph
  is set to the parent conjunctive graph.
  - This necessary workaround was exposed only after changing the blank node stringification above.
  (Fixing one bug exposed another bug!)


## [0.11.2] - 2019-10-17

### Changed
- Bumped min OWL-RL version to 5.2.1 to bring in some new bugfixes
- Corrected some tiny typos in readme


## [0.11.1.post1] - 2019-10-11

### Fixed
- Fixed an inferencing bug introduced in v0.11.0 (present in v0.11.0 and v0.11.1)
  - OWL or RDFS or BOTH inferencing wasn't being applied correctly because RDF data is now loaded in as a Dataset
  rather than a Graph.
### Changed
- Fixed the "extras" tests to take advantage of RDFS inferencing to better expose this kind of bug in the future.


## [0.11.1] - 2019-09-16

### Changed
- Implemented change in behaviour to resolve issue #029
  - A SHACL Shapes file will now get populated with some basic subClassOf relationships before
  the shapes are executed. This allows you to use owl:Class rather than rdfs:Class if you
  want to for implicit shapes.


## [0.11.0] - 2019-09-06

### Added
- Ability to load files with embedded named graphs (like in json-ld or trig)
  - Shape constraints are validated against every named graph in the dataset.
- Added a new SHACL Advanced Features feature, the Custom Target feature using sh:target
  - Only works with `sh:SPARQLTarget` custom targets for now
- New internal utilities in rdfutil module, for cloning a dataset and mixing datasets (as well as graphs)
- New test for issue #029

### Changed
- Big changes internally:
  - All loaded files are loaded into a Dataset, rather than a graph
  - All graph operations are now Dataset operations
  - Shapes are applied on every named graph on the dataset


## [0.10.0] - 2019-08-08

### Added
- New features from SHACL Advanced Features spec:
  - SHACL Triple Rules
  - SHACL SPARQL Rules
- New option in the cli application to enable advanced features with `--advanced`.
  - Changed the `-a` shortcut to mean `--advanced` rather than `--abort`.
- New tests for the advanced features

### Changed
- Changed usage of setup.py scripts, to proper cli entrypoints. [#23](https://github.com/RDFLib/pySHACL/pull/23)
  - This should not affect end user usability of the pyshacl script.
- Updated README.md to reflect changes including Advanced Features, and cli `--advanced` arg.
- Updated feature matrix to add section for SHACL Advanced Features.
- Fix owl:imports typo [#27](https://github.com/RDFLib/pySHACL/pull/27)


## [0.9.11] - 2019-05-01

### Changed
- When using the pySHACL `Validator` class directly, the `target_graph` property will now be correctly updated to always
  refer to the fully expanded graph if inferencing is enabled, and will be the mixed graph if the ontology-mixin option
  is enabled.
- Fixed a bug in the commandline tool when the validator throws a ValidationError, the `validator()` helper would catch
  and format the error, so the commandline tool would output the wrong text and return the wrong exit code.


## [0.9.10.post2] - 2019-03-28

### Added
- New ability for the RDF source loader to directly load a bytes string (for example, from a HTTP request body)
  - To use, just put the bytes dump as the source parameter to the rdf load function


## [0.9.10.post1] - 2019-03-11

### Changed
- More refinements to the RDF Source loader. Fixes some minor bugs.
- Moved some of the SHACL-specific RDF Utility functions (into the RDF Source loader) into a submodule.
  - This will one day be pulled out into its own RDF Utilities python module.
- Listed some additional Trove Classifiers in the setup.py file.


## [0.9.10] - 2019-03-07

### Added
- Added the ability to for the graph loader to load multiple source files into a single graph.
- This gives the ability follow `owl:imports` statements. We currently go (base+3) levels of imports deep maximum.
- Added `--imports` switch to the cmdline script, that turns on the owl:imports feature.
- Added the ability for the web rdf retriever to inspect the HTTP headers for 'Content-Type' for the RDF format
- Added documentation to the readme about `--imports` option.
- Add more coverage tests. Bumped coverage to 86%.

### Changed
- More potential Windows fixes
- Fixed a bug where the graph_id and base_uri was calculated incorrectly in some cases.
- Fix an issue when extracting base uri and prefix from comments in turtle when it was formatted in Windows line endings.
- Hitting a HTTP error when importing a subgraph is no longer an issue, we just ignore that import statement.


## [0.9.9.post1] - 2019-02-28

### Changed
- Fixed an issue with loading RDF files on Windows
- Fixed an issue running the test suite on Windows
- Main pyshacl module now exports the Validator class by default


## [0.9.9] - 2019-01-09
- This is a big release, building up to the major 1.0 release.
- Expect some issues, there will be 0.9.9.postX releases with just bug fixes between now and 1.0

### Added
- Major new feature. Added the ability to pass in an extra ontology document which gets parsed and mixed with the
data graph before pre-inferencing. This helps in the cases where the target data graph contains a data snippet which
can only be fully expanded with the help of an external ontology document containing RDFS and OWL axioms.
  - Use `ont_graph=path_to_graph` in the python module or
  - Use `-e` or `--ont-graph` on the command line utility to take advantage of this feature.
- SHACL graph or ONT graph can now be a Web URL, rather than a file path.
  - This works from the module validator entrypoint or the commandline tool.
- Added built in tests for issue#14 and for the commandline tool.
- Added new details to the README about the above new features.
- Added coverage statistics to the README.
- Started adding some hopefully-informative debugging output messages when debug mode is turned on. More to come.

### Changed
- Pre-inferencing can now only ever be run once per Validator instance, this is an attempt to prevent running
pre-inferencing multiple times unnecessarily.
- Internal shapes lookup cache is now stored in the `SHACLGraph` instance, rather than in a global static class
variable on the `Shape` class
- Fixed some bugs in the examples code, thanks @johannesloetzsch!
- Lots of code coverage specific changes, and comments where we can improve coverage.


## [0.9.8.post1] - 2018-12-05
### Changed
- Fixed a bug where files passed in to the command-line utility would get closed after being parsed, but sometimes
they would need to be reopened again, like in the case of doing metashacl. The fix detects when this is the case and
just leaves the files open. Now it is up to the command-line client to close the files.

## [0.9.8] - 2018-11-30
### Changed
- Fixed a bug in 0.9.7 where some references to the RDFClosure module were still in use in the code.
  - So v0.9.7 only worked if you had installed 0.9.6 and upgraded to 0.9.7. New installs didn't work.
  - All references to RDFClosure are now changed to owlrl.
- Bumped required owlrl version to the new 5.2 release, which is faster (doesn't use LiteralProxy anymore).

## [0.9.7] - 2018-11-23
### Added
- A new tests directory for testing reported github issues, and ensuring they pass even in future versions of this tool
### Changed
- RDFClosure is now named `owlrl`, and is now published on PyPI.
  - Use the new package name
  - Use the version from pypi
  - No longer need dependency_links when installing
  - Resume issuing binary builds
  - Remove dependency_links instructions from readme.md


## [0.9.6] - 2018-11-18
### Added
- CLI tool got two new options, `--shacl_file_format` (`-sf`) and `--data_file_format` (`-df`), for when the auto file format detection doesn't work for you.
### Changed
- The `validate` entrypoint, renamed `target_graph` to `data_graph`, and `target_graph_format` to `data_graph_format`
  - Updated example files to match
- Fixed a bug in sh:closed rule. It was incorrectly checking the rule against the shacl shapes graph, instead of the target graph


## [0.9.5] - 2018-09-25
### Added
- Added the missed 'proposed' test in the SHT conformance suite

### Changed
- EARL namespace https->http
- No longer publishing Binary Wheels for now, this is to force pip to run setup.py when installing the module, in order to process dependency links.


## [0.9.4.post1] - 2018-09-24
### Added
- Post-Release fixed a setup.py issue where it was not installing all of the required pySHACL modules.
  - This has actually been a severe bug since 0.8.3, sorry!


## [0.9.4] - 2018-09-24
### Added
- Additional required check that all potentially pre-bound variables are SELECTED from a nested SELECT statement in a SPARQL subquery.
- Better Literal less-than-or-equal and greater-than-or-equal comparison
  - fixes date-time comparisons with timezones, and other small issues
- Formal EARL validation report generator
- Submitted EARL validation report

### Changed
- Graph cleaner now works in a much more agressive manner, to remove all rdfs:Resource added triples
- Fixed SPARQL-based Constraint Component validator now outputs a default sh:value item if it is validating with a sourceShape that is a SHACL NodeShape
- Fixed a tiny bug in the list-compare subsection of the blank-node deep-compare utility
- Changed OWL-RL dependency from @py3 to @master, because master branch is now on Py3.
- One test from the SHT test suite was changed by Holger, so it passes now.
- Two timezone-based datetime comparison tests now pass


## [0.9.3] - 2018-09-22
### Added
- A new deep-compare feature to check actual validation-result blank-nodes against expected validation-result blank nodes
- Added a validation-report graph cleaner, to remove all unwanted triples from a validation report graph.
- A new RDF Node deep-clone feature to properly clone nodes into the Validation Report graph, rather than copying them.

### Changed
- Removed old test suite directory accidentally left in
- Fixed some bugs identified by the new expected-result deep-compare feature
- Changed incorrectly named constraint components (mislead by typo in the SHACL spec)
  - PropertyShapeComponent -> PropertyConstraintComponent
  - NodeShapeComponent -> NodeConstraintComponent
- Fixed some bugs identified by the [data-shapes-test-suite](https://w3c.github.io/data-shapes/data-shapes-test-suite)
- Bumped version number


## [0.9.2] - 2018-09-20
### Added
- A feature to patch RDFLib Literal conversion functions, to fix some RDFLib bugs
- A new exception ConstrainLoadWarning, for when a constraint is invalid but we want to ignore it
- Additional rules are now applied to the SPARQL queries in SPARQL-based constraints, as per the SHACL spec
- Currently failing [data-shapes-test-suite](https://w3c.github.io/data-shapes/data-shapes-test-suite) documented in the FEATURES file

### Changed
- Fixed some bugs identified by the [data-shapes-test-suite](https://w3c.github.io/data-shapes/data-shapes-test-suite)
- Bumped version number
- 206 of 212 tests are now passing


## [0.9.1] - 2018-09-19
### Added
- A second testing framework is in place
  - this one tests against the [data-shapes-test-suite](https://w3c.github.io/data-shapes/data-shapes-test-suite).

### Changed
- Changed the layout and structure of the tests folder
- Fixed a bug in the XOne constraint, discovered indicated by the new tests
- 199 of 212 tests are now passing


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


## [0.1.0a4.dev20180906] - 2018-09-04
### Added

- Initial version, limited functionality

[Unreleased]: https://github.com/RDFLib/pySHACL/compare/v0.24.1...HEAD
[0.24.1]: https://github.com/RDFLib/pySHACL/compare/v0.24.0...v0.24.1
[0.24.0]: https://github.com/RDFLib/pySHACL/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/RDFLib/pySHACL/compare/v0.22.2...v0.23.0
[0.22.2]: https://github.com/RDFLib/pySHACL/compare/v0.22.1...v0.22.2
[0.22.1]: https://github.com/RDFLib/pySHACL/compare/v0.22.0...v0.22.1
[0.22.0]: https://github.com/RDFLib/pySHACL/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/RDFLib/pySHACL/compare/v0.20.0...v0.21.0
[0.20.0]: https://github.com/RDFLib/pySHACL/compare/v0.19.1...v0.20.0
[0.19.1]: https://github.com/RDFLib/pySHACL/compare/v0.19.0...v0.19.1
[0.19.0]: https://github.com/RDFLib/pySHACL/compare/v0.18.1...v0.19.0
[0.18.1]: https://github.com/RDFLib/pySHACL/compare/v0.18.0...v0.18.1
[0.18.0]: https://github.com/RDFLib/pySHACL/compare/v0.17.3...v0.18.0
[0.17.3]: https://github.com/RDFLib/pySHACL/compare/v0.17.2...v0.17.3
[0.17.2]: https://github.com/RDFLib/pySHACL/compare/v0.17.1...v0.17.2
[0.17.1]: https://github.com/RDFLib/pySHACL/compare/v0.17.0.post1...v0.17.1
[0.17.0.post1]: https://github.com/RDFLib/pySHACL/compare/v0.17.0...v0.17.0.post1
[0.17.0]: https://github.com/RDFLib/pySHACL/compare/v0.16.2...v0.17.0
[0.16.2]: https://github.com/RDFLib/pySHACL/compare/v0.16.1...v0.16.2
[0.16.1]: https://github.com/RDFLib/pySHACL/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/RDFLib/pySHACL/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/RDFLib/pySHACL/compare/v0.14.5...v0.15.0
[0.14.5]: https://github.com/RDFLib/pySHACL/compare/v0.14.4...v0.14.5
[0.14.4]: https://github.com/RDFLib/pySHACL/compare/v0.14.3...v0.14.4
[0.14.3]: https://github.com/RDFLib/pySHACL/compare/v0.14.2...v0.14.3
[0.14.2]: https://github.com/RDFLib/pySHACL/compare/v0.14.1...v0.14.2
[0.14.1]: https://github.com/RDFLib/pySHACL/compare/v0.14.0...v0.14.1
[0.14.0]: https://github.com/RDFLib/pySHACL/compare/v0.13.3...v0.14.0
[0.13.3]: https://github.com/RDFLib/pySHACL/compare/v0.13.2...v0.13.3
[0.13.2]: https://github.com/RDFLib/pySHACL/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/RDFLib/pySHACL/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/RDFLib/pySHACL/compare/v0.12.2...v0.13.0
[0.12.2]: https://github.com/RDFLib/pySHACL/compare/v0.12.1.post2...v0.12.2
[0.12.1.post2]: https://github.com/RDFLib/pySHACL/compare/v0.12.1.post1...v0.12.1.post2
[0.12.1.post1]: https://github.com/RDFLib/pySHACL/compare/v0.12.1...v0.12.1.post1
[0.12.1]: https://github.com/RDFLib/pySHACL/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/RDFLib/pySHACL/compare/v0.11.6.post1...v0.12.0
[0.11.6.post1]: https://github.com/RDFLib/pySHACL/compare/v0.11.6...v0.11.6.post1
[0.11.6]: https://github.com/RDFLib/pySHACL/compare/v0.11.5...v0.11.6
[0.11.5]: https://github.com/RDFLib/pySHACL/compare/v0.11.4...v0.11.5
[0.11.4]: https://github.com/RDFLib/pySHACL/compare/v0.11.3.post1...v0.11.4
[0.11.3.post1]: https://github.com/RDFLib/pySHACL/compare/v0.11.3...v0.11.3.post1
[0.11.3]: https://github.com/RDFLib/pySHACL/compare/v0.11.2...v0.11.3
[0.11.2]: https://github.com/RDFLib/pySHACL/compare/v0.11.1.post1...v0.11.2
[0.11.1.post1]: https://github.com/RDFLib/pySHACL/compare/v0.11.1...v0.11.1.post1
[0.11.1]: https://github.com/RDFLib/pySHACL/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/RDFLib/pySHACL/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/RDFLib/pySHACL/compare/v0.9.11...v0.10.0
[0.9.11]: https://github.com/RDFLib/pySHACL/compare/v0.9.10.post2...v0.9.11
[0.9.10.post2]: https://github.com/RDFLib/pySHACL/compare/v0.9.10.post1...v0.9.10.post2
[0.9.10.post1]: https://github.com/RDFLib/pySHACL/compare/v0.9.10...v0.9.10.post1
[0.9.10]: https://github.com/RDFLib/pySHACL/compare/v0.9.9.post1...v0.9.10
[0.9.9.post1]: https://github.com/RDFLib/pySHACL/compare/v0.9.9...v0.9.9.post1
[0.9.9]: https://github.com/RDFLib/pySHACL/compare/v0.9.8.post1...v0.9.9
[0.9.8.post1]: https://github.com/RDFLib/pySHACL/compare/v0.9.8...v0.9.8.post1
[0.9.8]: https://github.com/RDFLib/pySHACL/compare/v0.9.7...v0.9.8
[0.9.7]: https://github.com/RDFLib/pySHACL/compare/v0.9.6...v0.9.7
[0.9.6]: https://github.com/RDFLib/pySHACL/compare/v0.9.5...v0.9.6
[0.9.5]: https://github.com/RDFLib/pySHACL/compare/v0.9.4.post1...v0.9.5
[0.9.4.post1]: https://github.com/RDFLib/pySHACL/compare/v0.9.4...v0.9.4.post1
[0.9.4]: https://github.com/RDFLib/pySHACL/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/RDFLib/pySHACL/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/RDFLib/pySHACL/compare/v0.9.1...v0.9.2
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
