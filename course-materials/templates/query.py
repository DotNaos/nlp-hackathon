from rdflib import Graph

g = Graph()
g.parse("05-hackathon/knowledge-graphs/recipes_100.ttl", format="turtle")

query = """
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name ?time
WHERE {
  ?r a schema:Recipe ;
     schema:name ?name ;
     ex:totalTimeMinutes ?time .
  FILTER(?time <= 30)
}
ORDER BY ?time ?name
"""

for row in g.query(query):
    print(row.name)