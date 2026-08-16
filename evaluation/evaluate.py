import os
import json
import logging
from typing import List, Dict, Any
from app.config.settings import settings
from app.query.query_parser import QueryParser
from app.retrieval.hybrid import HybridRetriever
from app.generation.generator import GroundedGenerator
from evaluation.baseline import BaselineRAG
from evaluation.metrics import EvaluatorMetrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_evaluation():
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dataset.json"))
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
    os.makedirs(results_dir, exist_ok=True)
    logger.info(f"Results directory: {results_dir}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    logger.info(f"Loaded {len(questions)} evaluation questions.")

    # Initialize components
    retriever = HybridRetriever()
    generator = GroundedGenerator()
    baseline = BaselineRAG()

    proposed_eval_records = []
    baseline_eval_records = []

    for q in questions:
        q_id = q["id"]
        q_text = q["question"]
        is_ans = q["is_answerable"]

        # --- 1. Evaluate Proposed System ---
        query_info = QueryParser.parse_query(q_text)
        chunks = retriever.retrieve(
            query=q_text,
            spec_filter=query_info.get("specification"),
            release_filter=query_info.get("release")
        )
        resp = generator.generate_answer(q_text, chunks)

        retrieved_specs = [c.spec_number for c, _ in chunks]
        retrieved_sections = [c.section for c, _ in chunks]
        cited_specs = [s.spec_number for s in resp.sources]

        proposed_eval_records.append({
            "id": q_id,
            "question": q_text,
            "category": q["category"],
            "is_answerable": is_ans,
            "expected_spec": q.get("expected_spec"),
            "expected_section": q.get("expected_section"),
            "answer": resp.answer,
            "grounded": resp.grounded,
            "confidence": resp.confidence,
            "retrieved_specs": retrieved_specs,
            "retrieved_sections": retrieved_sections,
            "cited_specs": cited_specs
        })

        # --- 2. Evaluate Baseline System ---
        base_resp = baseline.run_query(q_text)
        baseline_eval_records.append({
            "id": q_id,
            "question": q_text,
            "category": q["category"],
            "is_answerable": is_ans,
            "expected_spec": q.get("expected_spec"),
            "expected_section": q.get("expected_section"),
            "answer": base_resp["answer"],
            "grounded": base_resp["grounded"],
            "retrieved_specs": base_resp["retrieved_specs"],
            "retrieved_sections": base_resp["retrieved_sections"],
            "cited_specs": base_resp["cited_specs"]
        })

    # Compute Metrics
    proposed_metrics = EvaluatorMetrics.calculate_metrics(proposed_eval_records)
    baseline_metrics = EvaluatorMetrics.calculate_metrics(baseline_eval_records)

    # Save output JSON files
    with open(os.path.join(results_dir, "proposed_results.json"), "w", encoding="utf-8") as f:
        json.dump({"metrics": proposed_metrics, "details": proposed_eval_records}, f, indent=2)

    with open(os.path.join(results_dir, "baseline_results.json"), "w", encoding="utf-8") as f:
        json.dump({"metrics": baseline_metrics, "details": baseline_eval_records}, f, indent=2)

    summary = {
        "baseline_architecture": baseline_metrics,
        "proposed_architecture": proposed_metrics
    }

    with open(os.path.join(results_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print("      3GPP RAG EVALUATION REPORT: BASELINE vs PROPOSED")
    print("=" * 65)
    print(f"{'Metric':<28} | {'Baseline':<12} | {'Proposed RAG':<12}")
    print("-" * 65)
    print(f"{'Recall@5 (%)':<28} | {baseline_metrics.get('recall_at_5', 0):<12} | {proposed_metrics.get('recall_at_5', 0):<12}")
    print(f"{'Recall@10 (%)':<28} | {baseline_metrics.get('recall_at_10', 0):<12} | {proposed_metrics.get('recall_at_10', 0):<12}")
    print(f"{'Citation Accuracy (%)':<28} | {baseline_metrics.get('citation_accuracy', 0):<12} | {proposed_metrics.get('citation_accuracy', 0):<12}")
    print(f"{'Groundedness Rate (%)':<28} | {baseline_metrics.get('groundedness_rate', 0):<12} | {proposed_metrics.get('groundedness_rate', 0):<12}")
    print(f"{'Refusal Accuracy (%)':<28} | {baseline_metrics.get('refusal_accuracy', 0):<12} | {proposed_metrics.get('refusal_accuracy', 0):<12}")
    print(f"{'Hallucination Rate (%)':<28} | {baseline_metrics.get('hallucination_rate', 0):<12} | {proposed_metrics.get('hallucination_rate', 0):<12}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_evaluation()
