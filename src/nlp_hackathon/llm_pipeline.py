from __future__ import annotations

import argparse
import json
import re
import time
import http.client
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from nlp_hackathon.submission import DEFAULT_INPUT, load_graph, run_query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "gemma4-public"
DEFAULT_BASE_URL = "http://127.0.0.1:1234"
DEFAULT_MODEL = "gemma-4-31b"

SYSTEM_MESSAGE = (
    "You are a Text-to-SPARQL generator. Return only one executable SPARQL "
    "query. Do not use Markdown. Do not explain the query."
)

SCHEMA_CONTEXT = """Use only this RDF schema.

Prefixes:
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

Superhero graph: superhero_universe
Classes: ex:Superhero, ex:Antihero, ex:Villain, ex:Civilian
Useful properties:
- schema:name
- ex:memberOf, ex:publishedBy, ex:hasPower, ex:operatesIn, ex:species
- ex:enemyOf, ex:allyOf, ex:usesArtifact, ex:firstAppearanceYear
Known superhero entities:
- Teams: ex:Avengers, ex:JusticeLeague, ex:XMen
- Publishers: ex:Marvel, ex:DCComics
- Powers: ex:Flight, ex:SuperStrength
- Cities: ex:GothamCity, ex:NewYorkCity
- Species: ex:Mutant, ex:Kryptonian
- People: ex:Batman, ex:SpiderMan

Recipe graph: recipes_100
Class: schema:Recipe
Useful properties:
- schema:name
- ex:hasIngredient, ex:diet, ex:mealType, ex:cuisineType, ex:difficulty
- ex:totalTimeMinutes, ex:calories, ex:spiceLevel, ex:servings
Known recipe entities:
- Diets: ex:Vegan, ex:Vegetarian
- Ingredients: ex:Tofu, ex:Chickpeas, ex:SoySauce, ex:Rice
- Meal types: ex:Breakfast, ex:Dinner
- Cuisines: ex:Italian, ex:Japanese
- Difficulties: ex:Easy

Expected output:
- Include all needed PREFIX declarations.
- Use SELECT queries only.
- Keep variable names descriptive.
- Add ORDER BY when the question asks for a list or ranked result.
- Output exactly one SPARQL query and nothing else."""


def build_prompt(question: dict[str, Any]) -> str:
    return f"""{SCHEMA_CONTEXT}

Question id: {question["id"]}
Target graph: {question["graph"]}
Difficulty: {question.get("difficulty", "")}
German question: {question["question_de"]}

Write the SPARQL query for this question."""


def extract_sparql(response_text: str) -> str:
    text = response_text.strip()
    if not text:
        return ""

    fenced = re.search(r"```(?:sparql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    prefix_start = re.search(r"\bPREFIX\b", text, flags=re.IGNORECASE)
    select_start = re.search(r"\bSELECT\b", text, flags=re.IGNORECASE)
    start_match = prefix_start or select_start
    if not start_match:
        return text

    query = text[start_match.start() :].strip()
    end_match = re.search(r"\n\s*(?:Explanation|Hinweis|Note|```)\b", query, flags=re.IGNORECASE)
    if end_match:
        query = query[: end_match.start()].strip()
    return query.strip()


class LmStudioClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "reasoning_effort": "none",
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LM Studio HTTP {exc.code}: {body}") from exc


def response_message(completion: dict[str, Any]) -> dict[str, Any]:
    return completion.get("choices", [{}])[0].get("message", {})


def solve_question_with_llm(question: dict[str, Any], client: LmStudioClient) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = build_prompt(question)
    started = time.time()
    completion: dict[str, Any] = {}
    request_error = ""
    for attempt in range(1, 4):
        try:
            completion = client.complete(prompt)
            break
        except (RuntimeError, TimeoutError, urllib.error.URLError, http.client.HTTPException) as exc:
            request_error = f"attempt {attempt}: {exc}"
            time.sleep(attempt)

    duration_seconds = time.time() - started
    message = response_message(completion)
    response_text = str(message.get("content") or message.get("reasoning_content") or "")
    sparql = extract_sparql(response_text)

    execution_success = False
    predicted_result: list[dict[str, Any]] = []
    error = ""
    if request_error and not completion:
        error = request_error
    elif sparql:
        try:
            graph = load_graph(question["graph"])
            predicted_result = run_query(graph, sparql)
            execution_success = True
        except Exception as exc:  # noqa: BLE001 - pipeline report should keep failures.
            error = str(exc)

    result = {
        "id": question["id"],
        "question_id": question["id"],
        "graph": question["graph"],
        "difficulty": question.get("difficulty", ""),
        "question_de": question["question_de"],
        "generated_sparql": sparql,
        "execution_success": execution_success,
        "predicted_result": predicted_result,
    }
    trace = {
        "id": question["id"],
        "graph": question["graph"],
        "question_de": question["question_de"],
        "prompt": prompt,
        "raw_content": response_text,
        "reasoning_content": message.get("reasoning_content", ""),
        "completion_model": completion.get("model", ""),
        "usage": completion.get("usage", {}),
        "duration_seconds": round(duration_seconds, 3),
        "generated_sparql": sparql,
        "execution_success": execution_success,
        "execution_error": error,
        "result_count": len(predicted_result),
    }
    return result, trace


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    client: LmStudioClient,
    *,
    limit: int | None,
) -> dict[str, Any]:
    questions = json.loads(input_path.read_text(encoding="utf-8"))
    if limit is not None:
        questions = questions[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for index, question in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] {question['id']} -> Gemma 4", flush=True)
        result, trace = solve_question_with_llm(question, client)
        results.append(result)
        traces.append(trace)
        print(
            f"    success={trace['execution_success']} "
            f"rows={trace['result_count']} seconds={trace['duration_seconds']}",
            flush=True,
        )

    (output_dir / "submission.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_jsonl(output_dir / "prompts.jsonl", [{"id": row["id"], "prompt": row["prompt"]} for row in traces])
    write_jsonl(output_dir / "responses.jsonl", traces)

    summary = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "model": client.model,
        "total_questions": len(results),
        "execution_successes": sum(1 for row in results if row["execution_success"]),
        "execution_failures": sum(1 for row in results if not row["execution_success"]),
        "total_result_rows": sum(len(row["predicted_result"]) for row in results),
        "failed_question_ids": [row["id"] for row in results if not row["execution_success"]],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1536)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = LmStudioClient(
        base_url=args.base_url,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
    )
    summary = run_pipeline(args.input, args.output_dir, client, limit=args.limit)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
