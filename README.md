# pySHACL
A Python validator for SHACL.  

This is a pure Python module which allows for the validation of [RDF](https://www.w3.org/2001/sw/wiki/RDF) graphs against Shapes Constraint Language ([SHACL](https://www.w3.org/TR/shacl/)) graphs. This module uses the [rdflib](https://github.com/RDFLib/rdflib) Python library for working with RDF and is dependent on the [OWL-RL](https://github.com/RDFLib/OWL-RL) Python module for [OWL2 RL Profile](https://www.w3.org/TR/owl2-overview/#ref-owl-2-profiles)-based expansion of data graphs. 

This module is developed to adhere to the SHACL Recommendation:  
> Holger Knublauch; Dimitris Kontokostas. *Shapes Constraint Language (SHACL)*. 20 July 2017. W3C Recommendation. URL: <https://www.w3.org/TR/shacl/> ED: <https://w3c.github.io/data-shapes/shacl/>

## Installation
Install with PIP (Using the Python3 pip installer `pip3`)  
```bash
$ pip3 install pyshacl
```

Or in a python virtualenv _(these example commandline instructions are for a Linux/Unix based OS)_  
```bash
$ python3 -m virtualenv --python=python3 --no-site-packages shaclvenv
$ source ./shaclvenv/bin/activate
$ pip3 install pyshacl
```
To exit the virtual enviornment:  
```bash
$ deactivate
```

## Command Line Use
For command line use:  
_(these example commandline instructions are for a Linux/Unix based OS)_  
```bash
pyshacl -s /path/to/shapesGraph.ttl -m -i rdfs -f human /path/to/dataGraph.ttl
```
Where
 - `-s` is an (optional) path to the shapes graph to use  
 - `-i` is the pre-inferencing option  
 - `-f` is the ValidationReport output format (`human` = human-readable validation report)  
 - `-m` enable the meta-shacl feature  

System exit codes are:  
`0` = DataGraph is Conformant  
`1` = DataGraph is Non-Conformant  
`2` = The validator encountered a RuntimeError (check stderr output for details)  
`3` = Not-Implemented; The validator encountered a SHACL feature that is not yet implemented.  

Full CLI Usage options:
```bash
pyshacl [-h] [-s [SHACL]] [-i {none,rdfs,owlrl,both}] [-m] [-a] [-d]
               [-f {human,turtle,xml,json-ld,nt}] [-o [OUTPUT]]
               DataGraph

positional arguments:
  DataGraph             The file containing the Target Data Graph.

optional arguments:
  -h, --help            show this help message and exit
  -s [SHACL], --shacl [SHACL]
                        [Optional] The file containing the SHACL Shapes Graph.
  -i {none,rdfs,owlrl,both}, --inference {none,rdfs,owlrl,both}
                        [Optional] Choose a type of inferencing to run against
                        the Data Graph before validating.
  -m, --metashacl       [Optional] Validate the SHACL Shapes graph against the
                        shacl-shacl Shapes Graph before before validating the
                        Data Graph.
  -a, --abort           [Optional] Abort on first error.
  -d, --debug           [Optional] Output additional runtime messages.
  -f {human,turtle,xml,json-ld,nt}, --format {human,turtle,xml,json-ld,nt}
                        [Optional] Choose an output format. Default is
                        "human".
  -o [OUTPUT], --output [OUTPUT]
                        [Optional] Send output to a file (defaults to stdout).
```

## Python Module Use
For basic use of this module, you can just call the `validate` function of the `pyshacl` module like this:

```
from pyshacl import validate
r = validate(target_graph, shacl_graph, inference='rdfs', abort_on_error=False, meta_shacl=False, debug=False)
conforms, results_graph, results_text = r
```
where:  
* `target_graph` is an rdflib `Graph` object, the graph to be validated
* `shacl_graph` is an rdflib `Graph` object, the graph containing the SHACL shapes to validate with, or None if the SHACL shapes are included in the target_graph.
* `inference` is a Python string value to indicate whether or not to perform OWL inferencing expansion of the `target_graph` before validation. 
Options are 'rdfs', 'owlrl', 'both', or 'none'. The default is 'none'.
* `abort_on_error` (optional) a Python `bool` value to indicate whether or not the program should abort after encountering a validation error or to continue. Default is to continue.
* `meta_shacl` (optional) a Python `bool` value to indicate whether or not the program should enable the Meta-SHACL feature. Default is False.
* `debug` (optional) a Python `bool` value to indicate whether or not the program should emit debugging output text. Default is False.

on return:  
* a three-component `tuple` containing:
  * `conforms` a `bool`, indicating whether or not the `target_graph` conforms to the `shacl_graph`
  * `results_graph` an rdflib `Graph` object built according to the SHACL specification's [Validation Report](https://www.w3.org/TR/shacl/#validation-report) semantics
  * `results_text` python string representing a verbose textual representation of the [Validation Report](https://www.w3.org/TR/shacl/#validation-report) 
  

PySHACL is a Python3 library. For best compatibility use Python v3.5 or greater. This library _**does not work**_ on Python 2.7.x or below.


## Features  
A features matrix is kept in the [FEATURES file](https://github.com/RDFLib/pySHACL/blob/master/FEATURES.md).  


## Changelog  
A comprehensive changelog is kept in the [CHANGELOG file](https://github.com/RDFLib/pySHACL/blob/master/CHANGELOG.md).  


## Benchmarks  
This project includes a script to measure the difference in performance of validating the same source graph that has been inferenced using each of the four different inferencing options. Run it on your computer to see how fast the validator operates for you.


## License  
This repository is licensed under Apache License, Version 2.0. See the [LICENSE deed](https://github.com/RDFLib/pySHACL/blob/master/LICENSE.txt) for details.


## Contributors
See the [CONTRIBUTORS file](https://github.com/RDFLib/pySHACL/blob/master/CONTRIBUTORS.md).  


## Contacts  
Project Lead:  
**Nicholas Car**  
*Senior Experimental Scientist*  
CSIRO Land & Water, Environmental Informatics Group  
Brisbane, Qld, Australia  
<nicholas.car@csiro.au>  
<http://orcid.org/0000-0002-8742-7730>  

Lead Developer:  
**Ashley Sommer**  
*Software Engineer*  
CSIRO Land & Water, Environmental Informatics Group  
Brisbane, Qld, Australia  
<Ashley.Sommer@csiro.au>  
