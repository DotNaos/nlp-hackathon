from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from nlp_hackathon.submission import PROJECT_ROOT, build_submission


DEFAULT_GOLD = PROJECT_ROOT / "data" / "dev-test-set" / "dev_set.json"


def row_key(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def score_rows(predicted_rows: list[dict[str, Any]], gold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicted = {row_key(row) for row in predicted_rows}
    gold = {row_key(row) for row in gold_rows}
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    if not predicted and not gold:
        precision = recall = f1 = 1.0
    else:
        precision = safe_divide(true_positive, true_positive + false_positive)
        recall = safe_divide(true_positive, true_positive + false_negative)
        f1 = safe_divide(2 * precision * recall, precision + recall)

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": predicted == gold,
        "predicted_count": len(predicted),
        "gold_count": len(gold),
    }


def evaluate_submission(gold_questions: list[dict[str, Any]], submission: list[dict[str, Any]]) -> dict[str, Any]:
    submission_by_id = {str(item.get("id") or item.get("question_id")): item for item in submission}
    per_question: list[dict[str, Any]] = []

    for question in gold_questions:
        if "gold_result" not in question:
            continue

        question_id = question["id"]
        prediction = submission_by_id.get(question_id, {})
        score = score_rows(
            list(prediction.get("predicted_result", [])),
            list(question["gold_result"]),
        )
        per_question.append(
            {
                "id": question_id,
                "graph": question["graph"],
                "difficulty": question.get("difficulty", ""),
                "execution_success": bool(prediction.get("execution_success")),
                **score,
            }
        )

    total_tp = sum(item["true_positive"] for item in per_question)
    total_fp = sum(item["false_positive"] for item in per_question)
    total_fn = sum(item["false_negative"] for item in per_question)
    evaluated = len(per_question)
    if evaluated and total_tp == 0 and total_fp == 0 and total_fn == 0:
        micro_precision = micro_recall = micro_f1 = 1.0
    else:
        micro_precision = safe_divide(total_tp, total_tp + total_fp)
        micro_recall = safe_divide(total_tp, total_tp + total_fn)
        micro_f1 = safe_divide(2 * micro_precision * micro_recall, micro_precision + micro_recall)

    summary = {
        "evaluated_questions": evaluated,
        "exact_match_accuracy": safe_divide(
            sum(1 for item in per_question if item["exact_match"]),
            evaluated,
        ),
        "execution_success_rate": safe_divide(
            sum(1 for item in per_question if item["execution_success"]),
            evaluated,
        ),
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "macro_precision": safe_divide(sum(item["precision"] for item in per_question), evaluated),
        "macro_recall": safe_divide(sum(item["recall"] for item in per_question), evaluated),
        "macro_f1": safe_divide(sum(item["f1"] for item in per_question), evaluated),
        "total_true_positive": total_tp,
        "total_false_positive": total_fp,
        "total_false_negative": total_fn,
    }
    return {"summary": summary, "per_question": per_question}


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--submission", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gold = load_json(args.gold)
    submission = load_json(args.submission) if args.submission else build_submission(args.gold)
    report = evaluate_submission(gold, submission)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
