from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from nlp_hackathon.evaluation import DEFAULT_GOLD, evaluate_submission, load_json
from nlp_hackathon.llm_pipeline import LmStudioClient, build_prompt, extract_sparql, response_message
from nlp_hackathon.query_generation import generate_sparql
from nlp_hackathon.submission import DEFAULT_INPUT, build_submission, load_graph, run_query


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SET = DEFAULT_INPUT
DEV_SET = DEFAULT_GOLD

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Text-to-SPARQL Lab</title>
  <style>
    :root { color-scheme: light; --bg:#f7f4ee; --ink:#17212f; --muted:#657080; --line:#d8d3c8; --teal:#087f83; --blue:#2d65b8; --ok:#16794c; --bad:#b13b3b; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--ink); }
    main { max-width:1180px; margin:0 auto; padding:30px 22px 44px; }
    header { display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:24px; }
    h1 { font-size:42px; line-height:1; margin:0; letter-spacing:0; }
    h2 { font-size:22px; margin:0 0 12px; }
    p { color:var(--muted); margin:8px 0 0; }
    section { border-top:1px solid var(--line); padding:22px 0; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:22px; align-items:start; }
    label { display:block; font-size:13px; font-weight:700; color:#3b4654; margin:14px 0 6px; }
    textarea, select, input { width:100%; border:1px solid var(--line); background:#fffdf9; border-radius:8px; padding:11px 12px; color:var(--ink); font:inherit; }
    textarea { min-height:96px; resize:vertical; }
    button { border:0; border-radius:8px; padding:11px 15px; font:inherit; font-weight:800; background:var(--teal); color:white; cursor:pointer; }
    button.secondary { background:#263241; }
    button:disabled { opacity:.5; cursor:wait; }
    .row { display:flex; gap:10px; align-items:end; }
    .row > * { flex:1; }
    .metrics { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:10px; }
    .metric { border:1px solid var(--line); border-radius:8px; padding:14px; background:#fffdf9; }
    .metric strong { display:block; font-size:26px; color:var(--blue); }
    pre { white-space:pre-wrap; overflow:auto; max-height:360px; border:1px solid var(--line); border-radius:8px; background:#fffdf9; padding:14px; font-size:13px; line-height:1.45; }
    table { width:100%; border-collapse:collapse; background:#fffdf9; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    th, td { padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; font-size:13px; vertical-align:top; }
    th { color:#3b4654; }
    .ok { color:var(--ok); font-weight:800; }
    .bad { color:var(--bad); font-weight:800; }
    @media (max-width: 850px) { .grid, header { grid-template-columns:1fr; display:block; } .metrics { grid-template-columns:1fr 1fr; } h1 { font-size:34px; } }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Text-to-SPARQL Lab</h1>
      <p>Run questions through the rule solver or a local LM Studio model, execute the SPARQL, and inspect metrics.</p>
    </div>
    <button id="refreshMetrics" class="secondary">Refresh metrics</button>
  </header>

  <section>
    <h2>Dev-set metrics</h2>
    <div id="metrics" class="metrics"></div>
    <p id="metricsNote"></p>
  </section>

  <section class="grid">
    <div>
      <h2>Interactive query test</h2>
      <div class="row">
        <div>
          <label for="dataset">Question set</label>
          <select id="dataset"><option value="dev">Dev set</option><option value="public">Public test set</option></select>
        </div>
        <div>
          <label for="sample">Sample question</label>
          <select id="sample"></select>
        </div>
      </div>
      <label for="question">German question</label>
      <textarea id="question"></textarea>
      <div class="row">
        <div>
          <label for="graph">Graph</label>
          <select id="graph"><option value="superhero_universe">superhero_universe</option><option value="recipes_100">recipes_100</option></select>
        </div>
        <div>
          <label for="mode">Solver</label>
          <select id="mode"><option value="rules">Fast rule solver</option><option value="gemma">Gemma via LM Studio</option></select>
        </div>
      </div>
      <div class="row">
        <div>
          <label for="baseUrl">LM Studio base URL</label>
          <input id="baseUrl" value="http://127.0.0.1:1234" />
        </div>
        <div>
          <label for="model">Model</label>
          <input id="model" value="gemma-4-31b" />
        </div>
      </div>
      <label>&nbsp;</label>
      <button id="run">Run question</button>
    </div>

    <div>
      <h2>Result</h2>
      <p id="status">No run yet.</p>
      <label>Generated SPARQL</label>
      <pre id="sparql"></pre>
      <label>Rows</label>
      <pre id="rows"></pre>
      <label>Prompt sent to Gemma</label>
      <pre id="prompt"></pre>
    </div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
let questions = [];

function fmt(value) { return `${(value * 100).toFixed(1)}%`; }

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

async function loadMetrics() {
  const data = await api("/api/metrics");
  const s = data.summary;
  $("metrics").innerHTML = [
    ["Accuracy", fmt(s.exact_match_accuracy)],
    ["Precision", fmt(s.micro_precision)],
    ["Recall", fmt(s.micro_recall)],
    ["F1", fmt(s.micro_f1)],
  ].map(([k,v]) => `<div class="metric"><span>${k}</span><strong>${v}</strong></div>`).join("");
  $("metricsNote").textContent = `Evaluated ${s.evaluated_questions} dev questions with gold answers. Public test-set metrics need the hidden gold file.`;
}

async function loadQuestions() {
  questions = await api(`/api/questions?dataset=${$("dataset").value}`);
  $("sample").innerHTML = questions.map((q, i) => `<option value="${i}">${q.id} - ${q.question_de}</option>`).join("");
  applySample();
}

function applySample() {
  const q = questions[Number($("sample").value)] || questions[0];
  if (!q) return;
  $("question").value = q.question_de;
  $("graph").value = q.graph;
}

async function runQuestion() {
  $("run").disabled = true;
  $("status").textContent = "Running...";
  try {
    const data = await api("/api/solve", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question_de: $("question").value,
        graph: $("graph").value,
        mode: $("mode").value,
        base_url: $("baseUrl").value,
        model: $("model").value
      })
    });
    $("status").innerHTML = data.execution_success ? `<span class="ok">Success</span> - ${data.predicted_result.length} rows` : `<span class="bad">Failed</span> - ${data.error || "No details"}`;
    $("sparql").textContent = data.generated_sparql || "";
    $("rows").textContent = JSON.stringify(data.predicted_result, null, 2);
    $("prompt").textContent = data.prompt || "";
  } catch (error) {
    $("status").innerHTML = `<span class="bad">${error.message}</span>`;
  } finally {
    $("run").disabled = false;
  }
}

$("refreshMetrics").addEventListener("click", loadMetrics);
$("dataset").addEventListener("change", loadQuestions);
$("sample").addEventListener("change", applySample);
$("run").addEventListener("click", runQuestion);
loadMetrics();
loadQuestions();
</script>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(HTML, "text/html; charset=utf-8")
        elif parsed.path == "/api/questions":
            query = parse_qs(parsed.query)
            dataset = query.get("dataset", ["dev"])[0]
            self.send_json(load_questions(dataset))
        elif parsed.path == "/api/metrics":
            report = evaluate_submission(load_json(DEV_SET), build_submission(DEV_SET))
            self.send_json(report)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/solve":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = self.read_json_body()
        try:
            self.send_json(solve(body))
        except Exception as exc:  # noqa: BLE001 - return frontend-friendly errors.
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_text(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json", status)

    def send_text(
        self,
        payload: str | bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def load_questions(dataset: str) -> list[dict[str, Any]]:
    path = PUBLIC_SET if dataset == "public" else DEV_SET
    return [
        {
            "id": question["id"],
            "graph": question["graph"],
            "difficulty": question.get("difficulty", ""),
            "question_de": question["question_de"],
            "has_gold": "gold_result" in question,
        }
        for question in load_json(path)
    ]


def solve(payload: dict[str, Any]) -> dict[str, Any]:
    question = {
        "id": "interactive",
        "graph": payload["graph"],
        "question_de": payload["question_de"],
        "difficulty": "interactive",
    }
    prompt = ""
    if payload.get("mode") == "gemma":
        prompt = build_prompt(question)
        client = LmStudioClient(
            base_url=payload.get("base_url") or "http://127.0.0.1:1234",
            model=payload.get("model") or "gemma-4-31b",
            temperature=0.0,
            max_tokens=1536,
            timeout_seconds=240,
        )
        completion = client.complete(prompt)
        message = response_message(completion)
        sparql = extract_sparql(str(message.get("content") or message.get("reasoning_content") or ""))
    else:
        sparql = generate_sparql(question)

    result: dict[str, Any] = {
        "generated_sparql": sparql,
        "execution_success": False,
        "predicted_result": [],
        "prompt": prompt,
    }
    if not sparql:
        result["error"] = "No SPARQL was generated."
        return result

    graph = load_graph(question["graph"])
    result["predicted_result"] = run_query(graph, sparql)
    result["execution_success"] = True
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Serving Text-to-SPARQL Lab at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
