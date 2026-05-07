from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rdflib import Graph

from nlp_hackathon.query_generation import generate_sparql


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "dev-test-set" / "test_set_public.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "submission.json"
GRAPH_FILES = {
    "superhero_universe": PROJECT_ROOT
    / "data"
    / "knowledge-graphs"
    / "superhero_universe.ttl",
    "recipes_100": PROJECT_ROOT / "data" / "knowledge-graphs" / "recipes_100.ttl",
}


def load_graph(graph_name: str) -> Graph:
    graph_path = GRAPH_FILES[graph_name]
    graph = Graph()
    graph.parse(graph_path, format="turtle")
    return graph


def run_query(graph: Graph, query: str) -> list[dict[str, Any]]:
    results = graph.query(query)
    var_names = [str(var) for var in results.vars]
    rows: list[dict[str, Any]] = []

    for row in results:
        row_dict: dict[str, Any] = {}
        for var_name, cell in zip(var_names, row, strict=True):
            value = cell.toPython() if hasattr(cell, "toPython") else str(cell)
            if not isinstance(value, str | int | float | bool):
                value = str(value)
            row_dict[var_name] = value
        rows.append(row_dict)

    rows.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    return rows


def solve_question(question: dict[str, Any], *, use_reference: bool) -> dict[str, Any]:
    question_id = question["id"]
    sparql = question.get("reference_sparql", "") if use_reference else generate_sparql(question)

    execution_success = False
    predicted_result: list[dict[str, Any]] = []
    if sparql.strip():
        try:
            graph = load_graph(question["graph"])
            predicted_result = run_query(graph, sparql)
            execution_success = True
        except Exception:
            predicted_result = []
            execution_success = False

    return {
        "id": question_id,
        "question_id": question_id,
        "graph": question["graph"],
        "difficulty": question.get("difficulty", ""),
        "question_de": question["question_de"],
        "generated_sparql": sparql,
        "execution_success": execution_success,
        "predicted_result": predicted_result,
    }


def build_submission(
    input_path: Path,
    *,
    use_reference: bool = False,
) -> list[dict[str, Any]]:
    questions = json.loads(input_path.read_text(encoding="utf-8"))
    return [solve_question(question, use_reference=use_reference) for question in questions]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--use-reference",
        action="store_true",
        help="Use reference_sparql from the dev set for local verification only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    submission = build_submission(args.input, use_reference=args.use_reference)
    args.output.write_text(
        json.dumps(submission, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Created {args.output.resolve()} with {len(submission)} entries")


if __name__ == "__main__":
    main()
