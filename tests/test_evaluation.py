from __future__ import annotations

from nlp_hackathon.evaluation import evaluate_submission, score_rows


def test_score_rows_treats_matching_empty_sets_as_perfect() -> None:
    score = score_rows([], [])

    assert score["exact_match"] is True
    assert score["precision"] == 1.0
    assert score["recall"] == 1.0
    assert score["f1"] == 1.0


def test_score_rows_counts_false_positive_and_false_negative() -> None:
    score = score_rows(
        [{"name": "Batman"}, {"name": "Robin"}],
        [{"name": "Batman"}, {"name": "Superman"}],
    )

    assert score["true_positive"] == 1
    assert score["false_positive"] == 1
    assert score["false_negative"] == 1
    assert score["precision"] == 0.5
    assert score["recall"] == 0.5
    assert score["f1"] == 0.5
    assert score["exact_match"] is False


def test_evaluate_submission_summary_uses_exact_match_accuracy() -> None:
    report = evaluate_submission(
        [
            {"id": "q1", "graph": "g", "gold_result": [{"name": "Batman"}]},
            {"id": "q2", "graph": "g", "gold_result": []},
        ],
        [
            {"id": "q1", "execution_success": True, "predicted_result": [{"name": "Batman"}]},
            {"id": "q2", "execution_success": True, "predicted_result": []},
        ],
    )

    assert report["summary"]["exact_match_accuracy"] == 1.0
    assert report["summary"]["micro_precision"] == 1.0
    assert report["summary"]["micro_recall"] == 1.0
    assert report["summary"]["micro_f1"] == 1.0
    assert report["summary"]["macro_f1"] == 1.0
