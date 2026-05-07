from __future__ import annotations

from nlp_hackathon.llm_pipeline import SYSTEM_MESSAGE, build_prompt, extract_sparql


def test_build_prompt_contains_question_schema_and_output_contract() -> None:
    prompt = build_prompt(
        {
            "id": "test_super_01",
            "graph": "superhero_universe",
            "difficulty": "easy",
            "question_de": "Nenne alle Antiheld:innen.",
        }
    )

    assert "Question id: test_super_01" in prompt
    assert "Target graph: superhero_universe" in prompt
    assert "German question: Nenne alle Antiheld:innen." in prompt
    assert "PREFIX ex: <http://example.org/>" in prompt
    assert "ex:Antihero" in prompt
    assert "Output exactly one SPARQL query" in prompt
    assert "Return only one executable SPARQL query" in SYSTEM_MESSAGE


def test_extract_sparql_from_fenced_response() -> None:
    response = """Here is the query:

```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x a ex:Antihero ;
     schema:name ?name .
}
ORDER BY ?name
```
"""

    query = extract_sparql(response)

    assert query.startswith("PREFIX ex:")
    assert query.endswith("ORDER BY ?name")
    assert "```" not in query


def test_extract_sparql_from_plain_response_with_extra_text() -> None:
    response = """PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x a ex:Antihero ;
     schema:name ?name .
}
ORDER BY ?name

Explanation: this selects antiheroes."""

    query = extract_sparql(response)

    assert "Explanation" not in query
    assert "SELECT ?name" in query
