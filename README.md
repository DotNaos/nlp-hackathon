# NLP Hackathon

Final Moodle submission file: [`submission.json`](submission.json).

## Task

Build a prototype that translates German natural-language questions into SPARQL,
runs the queries against the provided RDF graphs, and writes the predicted
results as JSON.

Moodle assignment note: upload the result file by 12:00.

## Data

- `data/knowledge-graphs/superhero_universe.ttl`
- `data/knowledge-graphs/recipes_100.ttl`
- `data/dev-test-set/dev_set.json`
- `data/dev-test-set/test_set_public.json`

Course-provided templates and notes are kept in `course-materials/`.

## Pipeline

The verified submission pipeline is intentionally small and reproducible:

```text
NLP Hackathon Pipeline

+----------------------+
| test_set_public.json |
| question_de + graph  |
+----------+-----------+
           |
           v
+------------------------------+
| Select RDF graph             |
| superhero_universe or recipes|
+----------+-------------------+
           |
           v
+------------------------------+
| Generate SPARQL              |
| query_generation.generate_*  |
+----------+-------------------+
           |
           v
+------------------------------+
| Execute query with RDFLib    |
| against selected .ttl graph  |
+----------+-------------------+
           |
           v
+------------------------------+
| Write submission.json entry  |
| SPARQL + success + results   |
+------------------------------+

Optional experiment path:

+------------------------------+
| LM Studio / Gemma            |
| prompt -> SPARQL -> cleanup  |
+------------------------------+
           |
           v
+------------------------------+
| Same local RDFLib execution  |
| same submission format       |
+------------------------------+
```

For each question, the pipeline uses the `graph` field to choose the matching
RDF file:

- `superhero_universe` -> `data/knowledge-graphs/superhero_universe.ttl`
- `recipes_100` -> `data/knowledge-graphs/recipes_100.ttl`

The final submission path uses a deterministic rule solver. It maps the German
question to the known classes, properties, entities, filters, grouping queries,
and ordering patterns in the two provided graphs. Every generated query is then
executed locally. If a query fails, the submission entry records
`execution_success = false` and an empty `predicted_result`.

The output format matches the course template and contains the question
metadata, generated SPARQL, execution status, and predicted result rows.

There is also an optional LM Studio/Gemma pipeline for experimentation. In that
mode, the app builds a prompt with the selected graph schema and question, sends
it to the local LM Studio chat endpoint, extracts the SPARQL, and still executes
the query locally against the same RDF graphs. The verified final submission
pipeline is the deterministic path above, because it is reproducible and passes
the local dev-set checks.

## Evaluation

The dev set includes reference answers, so local metrics can be calculated
there. The public test set does not include gold answers, so local verification
checks that every public question produces an executable query and a sensible
result shape. The official hidden-test performance is computed by the course
evaluator after submission.

## Setup

```bash
uv sync
```

## Run

Create a submission for the public test set:

```bash
uv run python -m nlp_hackathon.submission
```

This writes `submission.json`.

Run against the dev set with reference queries to verify the graph/query plumbing:

```bash
uv run python -m nlp_hackathon.submission \
  --input data/dev-test-set/dev_set.json \
  --output dev_submission.json \
  --use-reference
```

The `--use-reference` flag is only for local dev-set verification. It should not
be used for the final test set.

## Tests

```bash
uv run pytest
```

The tests parse both RDF graphs, verify all course reference queries against the
dev gold results, verify the generated solver against all dev gold results, and
check that every public test question produces an executable query with the
expected result shape.
