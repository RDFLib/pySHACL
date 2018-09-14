# pySHACL
A Python validator for SHACL.  

This is a pure Python module which allows for the validation of [RDF](https://www.w3.org/2001/sw/wiki/RDF) graphs against Shapes Constraint Language ([SHACL](https://www.w3.org/TR/shacl/)) graphs. This module uses the [rdflib](https://github.com/RDFLib/rdflib) Python library for working with RDF and is dependent on the [OWL-RL](https://github.com/RDFLib/OWL-RL) Python module for [OWL2 RL Profile](https://www.w3.org/TR/owl2-overview/#ref-owl-2-profiles)-based expansion of data graphs. 

This module is developed to adhere to the SHACL Recommendation:  
> Holger Knublauch; Dimitris Kontokostas. *Shapes Constraint Language (SHACL)*. 20 July 2017. W3C Recommendation. URL: <https://www.w3.org/TR/shacl/> ED: <https://w3c.github.io/data-shapes/shacl/>

## Use
For basic use, of this module, you can just call the `validate` function of the `pyshacl` module like this:

```
from pyshacl import validate
validate(target_graph, shacl_graph, inference='rdfs', abort_on_error=False)
```
where:  
* `target_graph` is an rdflib `Graph` object, the graph to be validated
* `shacl_graph` is an rdflib `Graph` object, the graph containing the SHACL shapes to validate with, or None if the SHACL shapes are included in the target_graph.
* `inference` is a Python string value to indicate whether or not to perform OWL inferencing expansion of the `target_graph` before validation. 
Options are 'rdfs', 'owlrl', 'both', or 'none'. The default is 'none'.
* `abort_on_error` is a Python `bool` value to indicate whether or not the program should abort after encountering a validation error or to continue. Default is to continue.
on return:  
* a `tuple` containing:
  * `conforms` a `bool`, indicating whether or not the `target_graph` conforms to the `shacl_graph`
  * `results_graph` an rdflib `Graph` object built according to the SHACL specification's [Validation Report](https://www.w3.org/TR/shacl/#validation-report) semantics
  

## Features  
A features matrix is kept in the [FEATURES file](FEATURES.md).  


## Changelog  
A comprehensive changelog is kept in the [CHANGELOG file](CHANGELOG.md).  


## Benchmarks  
This project includes a script to measure the difference in performance of validatating the same source graph that has been inferenced using each of the four different inferencing options. Run it on your computer to see how fast the validator operates for you.  


## License  
This repository is licensed under Apache License, Version 2.0. See the [LICENSE deed](LICENSE.txt) for details.  


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
