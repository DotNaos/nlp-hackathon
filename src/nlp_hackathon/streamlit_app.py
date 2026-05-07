from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from nlp_hackathon.evaluation import DEFAULT_GOLD, evaluate_submission, load_json
from nlp_hackathon.llm_pipeline import (
    LmStudioClient,
    build_prompt,
    extract_sparql,
    prepare_sparql_for_local_graph,
    response_message,
)
from nlp_hackathon.query_generation import generate_sparql
from nlp_hackathon.submission import DEFAULT_INPUT, build_submission, load_graph, run_query


PUBLIC_SET = DEFAULT_INPUT
DEV_SET = DEFAULT_GOLD


@st.cache_data
def load_questions(path: str) -> list[dict[str, Any]]:
    return load_json(Path(path))


@st.cache_data
def dev_metrics() -> dict[str, Any]:
    return evaluate_submission(load_json(DEV_SET), build_submission(DEV_SET))


def solve(question_de: str, graph_name: str, mode: str, base_url: str, model: str) -> dict[str, Any]:
    question = {
        "id": "interactive",
        "graph": graph_name,
        "question_de": question_de,
        "difficulty": "interactive",
    }
    prompt = ""
    raw_sparql = ""

    if mode == "Gemma 4 via LM Studio":
        prompt = build_prompt(question)
        client = LmStudioClient(
            base_url=base_url,
            model=model,
            temperature=0.0,
            max_tokens=1536,
            timeout_seconds=240,
        )
        completion = client.complete(prompt)
        message = response_message(completion)
        raw_sparql = extract_sparql(str(message.get("content") or message.get("reasoning_content") or ""))
        sparql = prepare_sparql_for_local_graph(raw_sparql)
    else:
        sparql = generate_sparql(question)

    result = {
        "generated_sparql": sparql,
        "raw_sparql": raw_sparql,
        "prompt": prompt,
        "execution_success": False,
        "predicted_result": [],
        "error": "",
    }
    if not sparql:
        result["error"] = "No SPARQL was generated."
        return result

    try:
        result["predicted_result"] = run_query(load_graph(graph_name), sparql)
        result["execution_success"] = True
    except Exception as exc:  # noqa: BLE001 - show interactive errors.
        result["error"] = str(exc)
    return result


st.set_page_config(page_title="Text-to-SPARQL Lab", layout="wide")
st.title("Text-to-SPARQL Lab")
st.caption("Running on the DGX Spark through your local localhost tunnel.")

metrics = dev_metrics()["summary"]
cols = st.columns(4)
cols[0].metric("Accuracy", f"{metrics['exact_match_accuracy']:.1%}")
cols[1].metric("Precision", f"{metrics['micro_precision']:.1%}")
cols[2].metric("Recall", f"{metrics['micro_recall']:.1%}")
cols[3].metric("F1", f"{metrics['micro_f1']:.1%}")
st.caption("Metrics are computed on the dev set, because the public test-set gold answers are hidden.")

left, right = st.columns([0.42, 0.58], gap="large")

with left:
    st.subheader("Question")
    dataset = st.segmented_control("Question set", ["Dev set", "Public test set"], default="Dev set")
    question_path = DEV_SET if dataset == "Dev set" else PUBLIC_SET
    questions = load_questions(str(question_path))
    labels = [f"{q['id']} - {q['question_de']}" for q in questions]
    selected_label = st.selectbox("Sample question", labels)
    selected = questions[labels.index(selected_label)]

    question_de = st.text_area("German question", value=selected["question_de"], height=110)
    graph_name = st.selectbox(
        "RDF graph",
        ["superhero_universe", "recipes_100"],
        index=["superhero_universe", "recipes_100"].index(selected["graph"]),
    )
    mode = st.radio("Solver", ["Rule solver", "Gemma 4 via LM Studio"], horizontal=True)
    base_url = st.text_input("LM Studio URL on Spark", "http://127.0.0.1:1234")
    model = st.text_input("Model", "gemma-4-31b")
    run = st.button("Run", type="primary")

with right:
    st.subheader("Output")
    if run:
        with st.spinner("Running query..."):
            result = solve(question_de, graph_name, mode, base_url, model)
        if result["execution_success"]:
            st.success(f"Query executed successfully with {len(result['predicted_result'])} result rows.")
        else:
            st.error(result["error"] or "Execution failed.")

        st.markdown("**Generated SPARQL**")
        st.code(result["generated_sparql"], language="sparql")

        if result["raw_sparql"] and result["raw_sparql"] != result["generated_sparql"]:
            with st.expander("Raw Gemma SPARQL before local-graph cleanup"):
                st.code(result["raw_sparql"], language="sparql")

        st.markdown("**Predicted rows**")
        st.dataframe(result["predicted_result"], use_container_width=True)

        if result["prompt"]:
            with st.expander("Prompt sent to Gemma 4"):
                st.text(result["prompt"])
    else:
        st.info("Choose a question and press Run.")

with st.expander("Dev metrics JSON"):
    st.json(metrics)
