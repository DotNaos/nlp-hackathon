# NLP Hackathon

Private project for the FS26 Natural Language Processing hackathon.

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
