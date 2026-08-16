from typing import List, Dict, Any

class EvaluatorMetrics:
    @staticmethod
    def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
        total_q = len(results)
        if total_q == 0:
            return {}

        retrieved_correct_5 = 0
        retrieved_correct_10 = 0
        total_answerable = 0
        
        correct_citations = 0
        correct_refusals = 0
        total_unanswerable = 0
        
        grounded_count = 0
        unsupported_count = 0

        for item in results:
            is_answerable = item["is_answerable"]
            top_retrieved_specs = item.get("retrieved_specs", [])
            top_retrieved_sections = item.get("retrieved_sections", [])
            exp_spec = item.get("expected_spec")
            exp_sec = item.get("expected_section")

            if is_answerable:
                total_answerable += 1
                # Check Recall@5 and Recall@10
                if exp_spec in top_retrieved_specs[:5] or any(exp_sec in sec for sec in top_retrieved_sections[:5] if exp_sec):
                    retrieved_correct_5 += 1
                if exp_spec in top_retrieved_specs[:10] or any(exp_sec in sec for sec in top_retrieved_sections[:10] if exp_sec):
                    retrieved_correct_10 += 1
                    
                # Citation accuracy
                cited_specs = item.get("cited_specs", [])
                if exp_spec and exp_spec in cited_specs:
                    correct_citations += 1

                # Groundedness
                if item.get("grounded", False):
                    grounded_count += 1
                else:
                    unsupported_count += 1
            else:
                total_unanswerable += 1
                # Refusal check
                if not item.get("grounded", True) or "could not find sufficient evidence" in item.get("answer", ""):
                    correct_refusals += 1
                else:
                    unsupported_count += 1

        recall_5 = (retrieved_correct_5 / total_answerable) if total_answerable > 0 else 0.0
        recall_10 = (retrieved_correct_10 / total_answerable) if total_answerable > 0 else 0.0
        citation_acc = (correct_citations / total_answerable) if total_answerable > 0 else 0.0
        refusal_acc = (correct_refusals / total_unanswerable) if total_unanswerable > 0 else 0.0
        groundedness = (grounded_count / total_answerable) if total_answerable > 0 else 0.0
        hallucination_rate = (unsupported_count / total_q)

        return {
            "total_questions": total_q,
            "answerable_questions": total_answerable,
            "unanswerable_questions": total_unanswerable,
            "recall_at_5": round(recall_5 * 100, 2),
            "recall_at_10": round(recall_10 * 100, 2),
            "citation_accuracy": round(citation_acc * 100, 2),
            "refusal_accuracy": round(refusal_acc * 100, 2),
            "groundedness_rate": round(groundedness * 100, 2),
            "hallucination_rate": round(hallucination_rate * 100, 2)
        }
