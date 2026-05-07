from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rdflib import Graph

# Passe die Dateinamen bei Bedarf an
TEST_SET_FILE = "dev-test-set/test_set_public.json"
GRAPH_FILES = {
    "superhero_universe": "knowledge-graphs/superhero_universe.ttl",
    "recipes_100": "knowledge-graphs/recipes_100.ttl",
}


def load_graph(graph_name: str) -> Graph:
    path = GRAPH_FILES[graph_name]
    g = Graph()
    g.parse(path, format="turtle")
    return g


def run_query(graph: Graph, query: str) -> list[dict[str, Any]]:
    results = graph.query(query)
    var_names = [str(v) for v in results.vars]
    rows: list[dict[str, Any]] = []

    for row in results:
        row_dict: dict[str, Any] = {}
        for var_name, cell in zip(var_names, row):
            value = cell.toPython() if hasattr(cell, "toPython") else str(cell)
            if not isinstance(value, (str, int, float, bool)):
                value = str(value)
            row_dict[var_name] = value
        rows.append(row_dict)

    rows.sort(key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
    return rows


def build_prompt(question_obj: dict[str, Any]) -> str:
    # Hier kann eigener Ontologie-Kontext, Few-shot Prompting etc. ergänzt werden.
    return f"Erzeuge eine SPARQL-Query für die Frage: {question_obj['question_de']}"


def generate_sparql(question_obj: dict[str, Any]) -> str:
    """
    Diese Funktion müssen die Studierenden anpassen.
    Hier kann ein LLM aufgerufen oder eine eigene Pipeline verwendet werden.
    """
    # Platzhalter:
    # Beispiel: Query für test_super_01
    if question_obj["id"] == "test_super_01":
        return """PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x a ex:Antihero ;
     schema:name ?name .
}
ORDER BY ?name"""
    return ""


def solve_question(question_obj: dict[str, Any]) -> dict[str, Any]:
    graph_name = question_obj["graph"]
    graph = load_graph(graph_name)

    sparql = generate_sparql(question_obj)

    if not sparql.strip():
        return {
            "id": question_obj["id"],
            "graph": question_obj["graph"],
            "difficulty": question_obj.get("difficulty", ""),
            "question_de": question_obj["question_de"],
            "generated_sparql": "",
            "execution_success": False,
            "predicted_result": []
        }

    try:
        predicted_result = run_query(graph, sparql)
        execution_success = True
    except Exception:
        predicted_result = []
        execution_success = False

    return {
        "id": question_obj["id"],
        "graph": question_obj["graph"],
        "difficulty": question_obj.get("difficulty", ""),
        "question_de": question_obj["question_de"],
        "generated_sparql": sparql,
        "execution_success": execution_success,
        "predicted_result": predicted_result
    }


def main() -> None:
    test_set = json.loads(Path(TEST_SET_FILE).read_text(encoding="utf-8"))
    submissions = []

    for question_obj in test_set:
        result = solve_question(question_obj)
        submissions.append(result)

    out_path = Path("submission.json")
    out_path.write_text(json.dumps(submissions, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created {out_path.resolve()}")


if __name__ == "__main__":
    main()
