from __future__ import annotations

import json
from pathlib import Path

from nlp_hackathon.submission import GRAPH_FILES, build_submission, load_graph, run_query


ROOT = Path(__file__).resolve().parents[1]
DEV_SET = ROOT / "data" / "dev-test-set" / "dev_set.json"
PUBLIC_SET = ROOT / "data" / "dev-test-set" / "test_set_public.json"


EXPECTED_PUBLIC_COUNTS = {
    "test_super_01": 10,
    "test_super_02": 14,
    "test_super_03": 71,
    "test_super_04": 28,
    "test_super_05": 19,
    "test_super_06": 40,
    "test_super_07": 3,
    "test_super_08": 8,
    "test_super_09": 10,
    "test_super_10": 4,
    "test_super_11": 21,
    "test_super_12": 1,
    "test_super_13": 2,
    "test_super_14": 2,
    "test_super_15": 0,
    "test_recipe_01": 35,
    "test_recipe_02": 65,
    "test_recipe_03": 15,
    "test_recipe_04": 15,
    "test_recipe_05": 31,
    "test_recipe_06": 5,
    "test_recipe_07": 10,
    "test_recipe_08": 51,
    "test_recipe_09": 8,
    "test_recipe_10": 16,
    "test_recipe_11": 7,
    "test_recipe_12": 56,
    "test_recipe_13": 5,
    "test_recipe_14": 15,
    "test_recipe_15": 20,
}


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def sorted_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True))


def test_graph_files_parse_with_expected_sizes() -> None:
    expected_sizes = {
        "superhero_universe": 2223,
        "recipes_100": 2534,
    }

    for graph_name, graph_path in GRAPH_FILES.items():
        assert graph_path.exists()
        graph = load_graph(graph_name)
        assert len(graph) == expected_sizes[graph_name]


def test_reference_queries_match_all_dev_gold_results() -> None:
    questions = load_json(DEV_SET)

    for question in questions:
        graph = load_graph(question["graph"])
        rows = run_query(graph, question["reference_sparql"])
        assert sorted_rows(rows) == sorted_rows(question["gold_result"]), question["id"]


def test_generated_queries_solve_all_dev_gold_results() -> None:
    questions = load_json(DEV_SET)
    submission = build_submission(DEV_SET)

    assert len(submission) == 20
    for question, result in zip(questions, submission, strict=True):
        assert result["execution_success"] is True, question["id"]
        assert result["generated_sparql"].strip(), question["id"]
        assert sorted_rows(result["predicted_result"]) == sorted_rows(question["gold_result"]), question["id"]


def test_public_submission_executes_every_question_with_expected_counts() -> None:
    submission = build_submission(PUBLIC_SET)

    assert len(submission) == 30
    assert {entry["id"] for entry in submission} == set(EXPECTED_PUBLIC_COUNTS)
    assert {entry["question_id"] for entry in submission} == set(EXPECTED_PUBLIC_COUNTS)
    for entry in submission:
        assert entry["id"] == entry["question_id"]
        assert entry["execution_success"] is True, entry["question_id"]
        assert entry["generated_sparql"].strip(), entry["question_id"]
        assert len(entry["predicted_result"]) == EXPECTED_PUBLIC_COUNTS[entry["question_id"]]


def test_public_submission_has_expected_semantic_spot_checks() -> None:
    by_id = {entry["question_id"]: entry for entry in build_submission(PUBLIC_SET)}

    antiheroes = {row["name"] for row in by_id["test_super_01"]["predicted_result"]}
    assert antiheroes == {
        "Blade",
        "Catwoman",
        "Deadpool",
        "Ghost Rider",
        "Harley Quinn",
        "John Constantine",
        "Moon Knight",
        "Punisher",
        "Venom",
        "Winter Soldier",
    }

    role_counts = {row["role"]: row["count"] for row in by_id["test_super_10"]["predicted_result"]}
    assert role_counts == {
        "Antihero": 10,
        "Civilian": 9,
        "Superhero": 61,
        "Villain": 41,
    }

    cuisine_counts = {row["cuisineName"]: row["count"] for row in by_id["test_recipe_10"]["predicted_result"]}
    assert cuisine_counts["Japanese"] == 15
    assert cuisine_counts["American"] == 10
    assert cuisine_counts["Italian"] == 5

    hot_cuisines = {row["cuisineName"] for row in by_id["test_recipe_11"]["predicted_result"]}
    assert hot_cuisines == {
        "British",
        "Chinese",
        "Indian",
        "Japanese",
        "Middle Eastern",
        "Spanish",
        "Thai",
    }
