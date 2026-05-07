from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


GOLD_FILE = "dev-test-set/test_set.json"
SUBMISSIONS_DIR = "submissions"
REPORTS_DIR = "reports"
LEADERBOARD_JSON = "leaderboard.json"
LEADERBOARD_CSV = "leaderboard.csv"
LEADERBOARD_HTML = "leaderboard.html"


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple((k, canonicalize(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(sorted(canonicalize(v) for v in value))
    return value


def result_set_from_list(rows: list[Any]) -> set[Any]:
    return {canonicalize(row) for row in rows}


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute_scores(predicted_result: list[Any], gold_result: list[Any], execution_success: bool) -> dict[str, float | bool]:
    if not execution_success:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "exact_match": False,
        }

    pred_set = result_set_from_list(predicted_result)
    gold_set = result_set_from_list(gold_result)

    tp = len(pred_set & gold_set)
    precision = safe_div(tp, len(pred_set))
    recall = safe_div(tp, len(gold_set))

    if len(pred_set) == 0 and len(gold_set) == 0:
        f1 = 1.0
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    exact_match = pred_set == gold_set

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": exact_match,
    }


def evaluate_submission(gold: list[dict[str, Any]], submission: list[dict[str, Any]], submission_name: str) -> dict[str, Any]:
    gold_by_id = {item["id"]: item for item in gold}
    submission_by_id = {item["id"]: item for item in submission}

    question_reports = []
    execution_success_count = 0
    exact_match_count = 0
    sum_precision = 0.0
    sum_recall = 0.0
    sum_f1 = 0.0

    f1_by_graph: dict[str, list[float]] = {}
    f1_by_difficulty: dict[str, list[float]] = {}

    for qid, gold_item in gold_by_id.items():
        sub_item = submission_by_id.get(qid)

        if sub_item is None:
            sub_item = {
                "id": qid,
                "graph": gold_item["graph"],
                "difficulty": gold_item.get("difficulty", ""),
                "question_de": gold_item["question_de"],
                "generated_sparql": "",
                "execution_success": False,
                "predicted_result": [],
            }

        predicted_result = sub_item.get("predicted_result", [])
        gold_result = gold_item.get("gold_result", [])
        execution_success = bool(sub_item.get("execution_success", False))
        scores = compute_scores(predicted_result, gold_result, execution_success)
        execution_success_count += int(execution_success)
        exact_match_count += int(bool(scores["exact_match"]))

        sum_precision += float(scores["precision"])
        sum_recall += float(scores["recall"])
        sum_f1 += float(scores["f1"])

        graph = gold_item["graph"]
        difficulty = gold_item.get("difficulty", "")

        f1_by_graph.setdefault(graph, []).append(float(scores["f1"]))
        f1_by_difficulty.setdefault(difficulty, []).append(float(scores["f1"]))

        question_reports.append({
            "id": qid,
            "graph": graph,
            "difficulty": difficulty,
            "question_de": gold_item["question_de"],
            "execution_success": execution_success,
            "precision": scores["precision"],
            "recall": scores["recall"],
            "f1": scores["f1"],
            "exact_match": scores["exact_match"],
            "gold_result_size": len(gold_result),
            "predicted_result_size": len(predicted_result),
            "generated_sparql": sub_item.get("generated_sparql", ""),
            "predicted_result": predicted_result,
            "gold_result": gold_result,
        })

    n = len(gold_by_id)
    summary = {
        "submission_name": submission_name,
        "num_questions": n,
        "execution_rate": safe_div(execution_success_count, n),
        "exact_match_rate": safe_div(exact_match_count, n),
        "macro_precision": safe_div(sum_precision, n),
        "macro_recall": safe_div(sum_recall, n),
        "macro_f1": safe_div(sum_f1, n),
        "f1_by_graph": {k: safe_div(sum(v), len(v)) for k, v in f1_by_graph.items()},
        "f1_by_difficulty": {k: safe_div(sum(v), len(v)) for k, v in f1_by_difficulty.items()},
    }

    return {
        "summary": summary,
        "questions": question_reports,
    }


def sort_key(report: dict[str, Any]) -> tuple[float, float, float, str]:
    summary = report["summary"]
    hard_f1 = summary.get("f1_by_difficulty", {}).get("hard", 0.0)
    return (
        float(summary["macro_f1"]),
        float(summary["execution_rate"]),
        float(hard_f1),
        summary["submission_name"],
    )


def winner_key(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(row["macro_f1"]),
        float(row["execution_rate"]),
        float(row["f1_by_difficulty"].get("hard", 0.0)),
    )


def write_csv(leaderboard: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "rank",
        "submission_name",
        "macro_f1",
        "execution_rate",
        "exact_match_rate",
        "macro_precision",
        "macro_recall",
        "f1_superhero_universe",
        "f1_recipes_100",
        "f1_easy",
        "f1_medium",
        "f1_hard",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in leaderboard:
            writer.writerow({
                "rank": row["rank"],
                "submission_name": row["submission_name"],
                "macro_f1": row["macro_f1"],
                "execution_rate": row["execution_rate"],
                "exact_match_rate": row["exact_match_rate"],
                "macro_precision": row["macro_precision"],
                "macro_recall": row["macro_recall"],
                "f1_superhero_universe": row["f1_by_graph"].get("superhero_universe", 0.0),
                "f1_recipes_100": row["f1_by_graph"].get("recipes_100", 0.0),
                "f1_easy": row["f1_by_difficulty"].get("easy", 0.0),
                "f1_medium": row["f1_by_difficulty"].get("medium", 0.0),
                "f1_hard": row["f1_by_difficulty"].get("hard", 0.0),
            })


def fmt(x: float) -> str:
    return f"{x:.4f}"


def html_escape_json(obj: Any) -> str:
    return html.escape(json.dumps(obj, ensure_ascii=False, indent=2))


def build_html(out: dict[str, Any]) -> str:
    winners = out["winners"]
    leaderboard = out["leaderboard"]
    detailed_reports = out["detailed_reports"]

    winner_items = "".join(
        f"<li><strong>{html.escape(w['submission_name'])}</strong> — "
        f"Macro F1 {fmt(w['macro_f1'])}, "
        f"Execution Rate {fmt(w['execution_rate'])}, "
        f"F1 Hard {fmt(w['f1_by_difficulty'].get('hard', 0.0))}</li>"
        for w in winners
    )

    leaderboard_rows = []
    for row in leaderboard:
        leaderboard_rows.append(
            f"<tr>"
            f"<td>{row['rank']}</td>"
            f"<td>{html.escape(row['submission_name'])}</td>"
            f"<td>{fmt(row['macro_f1'])}</td>"
            f"<td>{fmt(row['execution_rate'])}</td>"
            f"<td>{fmt(row['exact_match_rate'])}</td>"
            f"<td>{fmt(row['macro_precision'])}</td>"
            f"<td>{fmt(row['macro_recall'])}</td>"
            f"<td>{fmt(row['f1_by_graph'].get('superhero_universe', 0.0))}</td>"
            f"<td>{fmt(row['f1_by_graph'].get('recipes_100', 0.0))}</td>"
            f"<td>{fmt(row['f1_by_difficulty'].get('hard', 0.0))}</td>"
            f"</tr>"
        )

    deep_dives = []
    for report in detailed_reports:
        summary = report["summary"]
        rows = []
        for q in report["questions"]:
            details_id = f"{summary['submission_name']}_{q['id']}".replace(".", "_").replace(" ", "_")
            rows.append(
                f"<tr>"
                f"<td>{html.escape(q['id'])}</td>"
                f"<td>{html.escape(q['graph'])}</td>"
                f"<td>{html.escape(q['difficulty'])}</td>"
                f"<td>{'✅' if q['execution_success'] else '❌'}</td>"
                f"<td>{fmt(q['precision'])}</td>"
                f"<td>{fmt(q['recall'])}</td>"
                f"<td>{fmt(q['f1'])}</td>"
                f"<td>{'✅' if q['exact_match'] else '❌'}</td>"
                f"<td>{q['gold_result_size']}</td>"
                f"<td>{q['predicted_result_size']}</td>"
                f"<td><button onclick=\"toggleDetails('{details_id}')\">Details</button></td>"
                f"</tr>"
                f"<tr id='{details_id}' class='hidden details-row'>"
                f"<td colspan='11'>"
                f"<div class='details-grid'>"
                f"<div><h4>Frage</h4><p>{html.escape(q['question_de'])}</p></div>"
                f"<div><h4>Generated SPARQL</h4><pre>{html.escape(q['generated_sparql'])}</pre></div>"
                f"<div><h4>Predicted Result</h4><pre>{html_escape_json(q['predicted_result'])}</pre></div>"
                f"<div><h4>Gold Result</h4><pre>{html_escape_json(q['gold_result'])}</pre></div>"
                f"</div>"
                f"</td></tr>"
            )

        deep_dives.append(
            f"<section class='card'>"
            f"<h2>{html.escape(summary['submission_name'])}</h2>"
            f"<div class='summary-grid'>"
            f"<div><span>Macro F1</span><strong>{fmt(summary['macro_f1'])}</strong></div>"
            f"<div><span>Execution Rate</span><strong>{fmt(summary['execution_rate'])}</strong></div>"
            f"<div><span>Exact Match Rate</span><strong>{fmt(summary['exact_match_rate'])}</strong></div>"
            f"<div><span>Macro Precision</span><strong>{fmt(summary['macro_precision'])}</strong></div>"
            f"<div><span>Macro Recall</span><strong>{fmt(summary['macro_recall'])}</strong></div>"
            f"<div><span>F1 Hard</span><strong>{fmt(summary['f1_by_difficulty'].get('hard', 0.0))}</strong></div>"
            f"</div>"
            f"<p><strong>F1 by Graph:</strong> superhero_universe={fmt(summary['f1_by_graph'].get('superhero_universe', 0.0))}, "
            f"recipes_100={fmt(summary['f1_by_graph'].get('recipes_100', 0.0))}</p>"
            f"<p><strong>F1 by Difficulty:</strong> easy={fmt(summary['f1_by_difficulty'].get('easy', 0.0))}, "
            f"medium={fmt(summary['f1_by_difficulty'].get('medium', 0.0))}, "
            f"hard={fmt(summary['f1_by_difficulty'].get('hard', 0.0))}</p>"
            f"<table><thead><tr>"
            f"<th>ID</th><th>Graph</th><th>Difficulty</th><th>Exec</th><th>P</th><th>R</th><th>F1</th><th>EM</th><th>Gold</th><th>Pred</th><th>Deep Dive</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
            f"</section>"
        )

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Text-to-SPARQL Leaderboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
h1, h2, h3, h4 {{ margin-bottom: 0.3rem; }}
p {{ line-height: 1.45; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; margin: 20px 0; }}
.summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 12px 0 16px 0; }}
.summary-grid div {{ background: #f6f6f6; border-radius: 8px; padding: 10px; }}
.summary-grid span {{ display: block; font-size: 12px; color: #555; margin-bottom: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; text-align: left; }}
th {{ background: #f2f2f2; position: sticky; top: 0; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #fafafa; border: 1px solid #eee; padding: 10px; border-radius: 6px; max-height: 260px; overflow: auto; }}
.muted {{ color: #666; }}
.details-row td {{ background: #fcfcfc; }}
.badge {{ display: inline-block; background: #eef6ff; border: 1px solid #cfe3ff; padding: 4px 8px; border-radius: 999px; margin-right: 8px; }}
.hidden {{ display: none; }}
.details-grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
button {{ border: 1px solid #bbb; background: #fff; border-radius: 6px; padding: 4px 10px; cursor: pointer; }}
button:hover {{ background: #f5f5f5; }}
ul {{ margin-top: 8px; }}
</style>
<script>
function toggleDetails(id) {{
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('hidden');
}}
</script>
</head>
<body>
<h1>Text-to-SPARQL Leaderboard</h1>
<p class="muted">Automatisch erzeugte Auswertung aller Submissions gegen den Hidden Goldstandard.</p>

<section class="card">
<h2>Gewinner</h2>
<p>Es gibt {len(winners)} Gewinner-Team(s) nach der definierten Ranking-Logik.</p>
<ul>{winner_items}</ul>
</section>

<section class="card">
<h2>Leaderboard</h2>
<table>
<thead>
<tr>
<th>Rank</th>
<th>Submission</th>
<th>Macro F1</th>
<th>Exec Rate</th>
<th>EM Rate</th>
<th>Macro P</th>
<th>Macro R</th>
<th>F1 Superhero</th>
<th>F1 Recipes</th>
<th>F1 Hard</th>
</tr>
</thead>
<tbody>
{''.join(leaderboard_rows)}
</tbody>
</table>
</section>

<h2>Deep Dive pro Submission</h2>
{''.join(deep_dives)}

</body>
</html>"""


def main() -> None:
    gold = json.loads(Path(GOLD_FILE).read_text(encoding="utf-8"))

    submissions_dir = Path(SUBMISSIONS_DIR)
    if not submissions_dir.exists():
        raise FileNotFoundError(f"Ordner nicht gefunden: {submissions_dir.resolve()}")

    submission_files = sorted(submissions_dir.glob("*.json"))
    if not submission_files:
        raise FileNotFoundError(f"Keine JSON-Dateien in {submissions_dir.resolve()} gefunden.")

    reports = []
    for sub_file in submission_files:
        submission = json.loads(sub_file.read_text(encoding="utf-8"))
        report = evaluate_submission(gold, submission, sub_file.name)
        reports.append(report)

    reports.sort(key=sort_key, reverse=True)

    reports_dir = Path(REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)

    leaderboard = []
    current_rank = 1
    previous_key = None

    for index, report in enumerate(reports):
        summary = report["summary"]
        row = {
            "rank": current_rank,
            "submission_name": summary["submission_name"],
            "macro_f1": summary["macro_f1"],
            "execution_rate": summary["execution_rate"],
            "exact_match_rate": summary["exact_match_rate"],
            "macro_precision": summary["macro_precision"],
            "macro_recall": summary["macro_recall"],
            "f1_by_graph": summary["f1_by_graph"],
            "f1_by_difficulty": summary["f1_by_difficulty"],
        }

        key = winner_key(row)
        if previous_key is None:
            current_rank = 1
            row["rank"] = current_rank
        elif key == previous_key:
            row["rank"] = current_rank
        else:
            current_rank = index + 1
            row["rank"] = current_rank

        previous_key = key
        leaderboard.append(row)

        report_path = reports_dir / f"{Path(summary['submission_name']).stem}_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    top_key = winner_key(leaderboard[0])
    winners = [row for row in leaderboard if winner_key(row) == top_key]

    out = {
        "winners": winners,
        "leaderboard": leaderboard,
        "detailed_reports": reports,
    }

    (reports_dir / LEADERBOARD_JSON).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(leaderboard, reports_dir / LEADERBOARD_CSV)
    (reports_dir / LEADERBOARD_HTML).write_text(build_html(out), encoding="utf-8")

    print(f"Created {(reports_dir / LEADERBOARD_JSON).resolve()}")
    print(f"Created {(reports_dir / LEADERBOARD_CSV).resolve()}")
    print(f"Created {(reports_dir / LEADERBOARD_HTML).resolve()}")
    print(f"Created detail reports in {reports_dir.resolve()}")
    print()
    print("Leaderboard:")
    for row in leaderboard:
        print(
            f"{row['rank']}. {row['submission_name']}  "
            f"macro_f1={row['macro_f1']:.4f}  "
            f"execution_rate={row['execution_rate']:.4f}  "
            f"exact_match_rate={row['exact_match_rate']:.4f}  "
            f"f1_hard={row['f1_by_difficulty'].get('hard', 0.0):.4f}"
        )
        print(
            f"   macro_precision={row['macro_precision']:.4f}  "
            f"macro_recall={row['macro_recall']:.4f}  "
            f"f1_superhero={row['f1_by_graph'].get('superhero_universe', 0.0):.4f}  "
            f"f1_recipes={row['f1_by_graph'].get('recipes_100', 0.0):.4f}"
        )
    print()
    if len(winners) == 1:
        print(f"Beste Gruppe / beste Submission: {winners[0]['submission_name']}")
    else:
        print("Gleichstand zwischen folgenden Gewinner-Teams / Gewinner-Submissions:")
        for winner in winners:
            print(f"- {winner['submission_name']}")


if __name__ == "__main__":
    main()
