import pyshacl
from rdflib import Graph

qb_shacl = '''\
# baseURI: http://topbraid.org/datacube
# imports: http://datashapes.org/dash
# imports: http://purl.org/linked-data/cube
# imports: http://www.w3.org/2004/02/skos/core

@prefix dash: <http://datashapes.org/dash#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix qb: <http://purl.org/linked-data/cube#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://topbraid.org/datacube>
  rdf:type owl:Ontology ;
  rdfs:comment "Implements the integrity constraints defined by section 11.1 of the Data Cube specification. Most of the constraints work in standard SHACL-SPARQL, but two constraints require a SHACL function (from SHACL Advanced Features) to recursively walk a dynamically computed property path. An alternative implementation of these constraints could be produced without a helper function based on SHACL-JS." ;
  rdfs:label "SHACL shapes for RDF Data Cube Vocabulary" ;
  rdfs:seeAlso <https://www.w3.org/TR/vocab-data-cube/#wf-rules> ;
  owl:imports <http://datashapes.org/dash> ;
  owl:imports <http://purl.org/linked-data/cube> ;
  owl:imports <http://www.w3.org/2004/02/skos/core> ;
  owl:versionInfo "Created with TopBraid Composer. This is currently completely untested." ;
  sh:declare [
      rdf:type sh:PrefixDeclaration ;
      sh:namespace "http://purl.org/linked-data/cube#"^^xsd:anyURI ;
      sh:prefix "qb" ;
    ] ;
.

qb:ObservationShape
  rdf:type sh:NodeShape ;
  rdfs:label "Observation shape" ;
  sh:property [
      sh:path qb:dataSet ;
      rdfs:comment "IC-1. Unique DataSet" ;
      sh:maxCount 1 ;
      sh:message "Every qb:Observation has exactly one associated qb:DataSet." ;
      sh:minCount 1 ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-11. All dimensions required" ;
      sh:message "Every qb:Observation has a value for each dimension declared in its associated qb:DataStructureDefinition." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	$this qb:dataSet/qb:structure/qb:component/qb:componentProperty ?dim .
    ?dim a qb:DimensionProperty;
    FILTER NOT EXISTS { $this ?dim [] }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-12. No duplicate observations" ;
      sh:message "No two qb:Observations in the same qb:DataSet may have the same value for all dimensions." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	{
		# For each pair of observations test if all the dimension values are the same
		SELECT $this (MIN(?equal) AS ?allEqual)
		WHERE {
			$this qb:dataSet ?dataset .
			?obs2 qb:dataSet ?dataset .
			FILTER ($this != ?obs2)
			?dataset qb:structure/qb:component/qb:componentProperty ?dim .
			?dim a qb:DimensionProperty .
			$this ?dim ?value1 .
			?obs2 ?dim ?value2 .
			BIND( ?value1 = ?value2 AS ?equal)
		}
		GROUP BY $this ?obs2
	}
	FILTER( ?allEqual )
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-13. Required attributes" ;
      sh:message "Every qb:Observation has a value for each declared attribute that is marked as required." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	$this qb:dataSet/qb:structure/qb:component ?component .
	?component qb:componentRequired true ;
		qb:componentProperty ?attr .
	FILTER NOT EXISTS { $this ?attr [] }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-14. All measures present" ;
      sh:message "In a qb:DataSet which does not use a Measure dimension then each individual qb:Observation must have a value for every declared measure." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	# Observation in a non-measureType cube
	$this qb:dataSet/qb:structure ?dsd .
	FILTER NOT EXISTS { ?dsd qb:component/qb:componentProperty qb:measureType }
	# verify every measure is present
	?dsd qb:component/qb:componentProperty ?measure .
	?measure a qb:MeasureProperty;
	FILTER NOT EXISTS { $this ?measure [] }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-15. Measure dimension consistent" ;
      sh:message "In a qb:DataSet which uses a Measure dimension then each qb:Observation must have a value for the measure corresponding to its given qb:measureType." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	# Observation in a measureType-cube
	$this qb:dataSet/qb:structure ?dsd ;
		qb:measureType ?measure .
	?dsd qb:component/qb:componentProperty qb:measureType .
	# Must have value for its measureType
	FILTER NOT EXISTS { $this ?measure [] }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-16. Single measure on measure dimension observation" ;
      sh:message """In a qb:DataSet which uses a Measure dimension then each qb:Observation must only have a value for one measure (by IC-15 this will be the measure corresponding to its qb:measureType).
""" ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	# Observation with measureType
	$this qb:dataSet/qb:structure ?dsd ;
		qb:measureType ?measure ;
		?omeasure [] .
	# Any measure on the observation
	?dsd qb:component/qb:componentProperty qb:measureType ;
		qb:component/qb:componentProperty ?omeasure .
	?omeasure a qb:MeasureProperty .
	# Must be the same as the measureType
	FILTER (?omeasure != ?measure)
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-17. All measures present in measures dimension cube" ;
      sh:message "In a qb:DataSet which uses a Measure dimension then if there is a Observation for some combination of non-measure dimensions then there must be other Observations with the same non-measure dimension values for each of the declared measures." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	{
		# Count number of other measures found at each point
		SELECT $this ?numMeasures (COUNT(?obs2) AS ?count)
		WHERE {
			{
				# Find the DSDs and check how many measures they have
				SELECT $this ?dsd (COUNT(?m) AS ?numMeasures)
				WHERE {
					?dsd qb:component/qb:componentProperty ?m.
					?m a qb:MeasureProperty .
				}
				GROUP BY ?dsd
			}
			# Observation in measureType cube
			$this qb:dataSet/qb:structure ?dsd;
				qb:dataSet ?dataset ;
				qb:measureType ?m1 .

			# Other observation at same dimension value
			?obs2 qb:dataSet ?dataset ;
				qb:measureType ?m2 .
			FILTER NOT EXISTS {
				?dsd qb:component/qb:componentProperty ?dim .
				FILTER (?dim != qb:measureType)
				?dim a qb:DimensionProperty .
				$this ?dim ?v1 .
				?obs2 ?dim ?v2.
				FILTER (?v1 != ?v2)
			}
		}
		GROUP BY $this ?numMeasures
		HAVING (?count != ?numMeasures)
	}
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-18. Consistent data set links" ;
      sh:message "If a qb:DataSet D has a qb:slice S, and S has an qb:observation O, then the qb:dataSet corresponding to O must be D." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	?slice qb:observation $this .
	?dataset qb:slice ?slice .
    FILTER NOT EXISTS { $this qb:dataSet ?dataset . }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-19. a) Codes from code list" ;
      owl:versionInfo "See section IC-19 in the Data Cubes spec on pre-conditions that need to be met prior to the execution of this constraints. Parts of them are covered by the rules at skos:memberListShape." ;
      sh:message "If a dimension property has a qb:codeList, then the value of the dimension property on every qb:Observation must be in the code list." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
    $this qb:dataSet/qb:structure/qb:component/qb:componentProperty ?dim .
    ?dim a qb:DimensionProperty ;
        qb:codeList ?list .
    ?list a skos:ConceptScheme .
    $this ?dim ?v .
    FILTER NOT EXISTS { ?v a skos:Concept ; skos:inScheme ?list }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-19. b) Codes from code list" ;
      owl:versionInfo "See section IC-19 in the Data Cubes spec on pre-conditions that need to be met prior to the execution of this constraints. Parts of them are covered by the rules at skos:memberListShape." ;
      sh:message "If a dimension property has a qb:codeList, then the value of the dimension property on every qb:Observation must be in the code list." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
    $this qb:dataSet/qb:structure/qb:component/qb:componentProperty ?dim .
    ?dim a qb:DimensionProperty ;
        qb:codeList ?list .
    ?list a skos:Collection .
    $this ?dim ?v .
    FILTER NOT EXISTS { ?v a skos:Concept ; skos:member+ ?v }
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-20. Codes from hierarchy" ;
      sh:message "If a dimension property has a qb:HierarchicalCodeList with a non-blank qb:parentChildProperty then the value of that dimension property on every qb:Observation must be reachable from a root of the hierarchy using zero or more hops along the qb:parentChildProperty links." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	$this qb:dataSet/qb:structure/qb:component/qb:componentProperty ?dim .
	?dim a qb:DimensionProperty ;
		qb:codeList ?list .
	?list a qb:HierarchicalCodeList .
	$this ?dim ?v .
	?hierarchy a qb:HierarchicalCodeList ;
		qb:parentChildProperty ?p .
	FILTER ( isIRI(?p) ) .
	FILTER NOT EXISTS {
		?list qb:hierarchyRoot ?root .
		FILTER qb:hasZeroOrMore(?root, ?p, ?v) .
	}
}""" ;
    ] ;
  sh:sparql [
      rdfs:comment "IC-21. Codes from hierarchy (inverse)" ;
      sh:message "If a dimension property has a qb:HierarchicalCodeList with an inverse qb:parentChildProperty then the value of that dimension property on every qb:Observation must be reachable from a root of the hierarchy using zero or more hops along the inverse qb:parentChildProperty links." ;
      sh:prefixes <http://topbraid.org/datacube> ;
      sh:select """SELECT $this
WHERE {
	$this qb:dataSet/qb:structure/qb:component/qb:componentProperty ?dim .
	?dim a qb:DimensionProperty ;
		qb:codeList ?list .
	?list a qb:HierarchicalCodeList .
	$this ?dim ?v .
	?hierarchy a qb:HierarchicalCodeList;
		qb:parentChildProperty ?pcp .
	FILTER( isBlank(?pcp) )
	?pcp  owl:inverseOf ?p .
	FILTER( isIRI(?p) )
	FILTER NOT EXISTS {
		?list qb:hierarchyRoot ?root .
		FILTER qb:hasZeroOrMore(?root, ?p, ?v) .
	}
}""" ;
    ] ;
  sh:targetClass qb:Observation ;
.
'''

qb_data = '''\
# baseURI: http://topbraid.org/datacube_example
# imports: http://purl.org/linked-data/cube

@prefix qb: <http://purl.org/linked-data/cube#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <http://topbraid.org/datacube_example#> .

ex:ds1 a qb:DataSet .

ex:obs1 a qb:Observation ;
  qb:dataSet ex:ds1 ;
.

'''

def test_102():
    g_shacl = Graph().parse(data=qb_shacl, format="turtle")
    g_data = Graph().parse(data=qb_data, format="turtle")

    conforms, a, b = pyshacl.validate(g_data, shacl_graph=g_shacl, debug=True)
    print(a)
    assert conforms

if __name__ == "__main__":
    test_102()
