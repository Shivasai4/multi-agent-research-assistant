from typing import List, Dict, Any
from loguru import logger
from src.graph.workflow import research_app
from src.graph.state import GraphState
from src.evaluation.faithfulness import check_hallucinations
from src.evaluation.coverage import answer_coverage

def evaluate_on_test_set(test_queries: List[str]) -> Dict[str, Any]:
    results = []
    for query in test_queries:
        logger.info(f"Evaluating: {query}")
        initial_state: GraphState = {
            "user_query": query,
            "plan": None,
            "current_step": 0,
            "raw_documents": [],
            "search_results": [],
            "vector_results": [],
            "analysis": None,
            "review": None,
            "revision_count": 0,
            "max_revisions": 2,
            "final_report": None,
            "errors": [],
            "agent_traces": []
        }
        try:
            final_state = research_app.invoke(initial_state)
            final_report = final_state.get("final_report", "")
            plan = final_state.get("plan")
            sub_questions = plan.get("sub_questions", []) if plan else []
            raw_documents = final_state.get("raw_documents", [])
            coverage = answer_coverage(query, final_report, sub_questions)
            faithfulness_result = check_hallucinations(final_report, raw_documents)
            results.append({
                "query": query,
                "coverage": coverage,
                "faithfulness": faithfulness_result["faithfulness_score"],
                "hallucinations_count": len(faithfulness_result["hallucinations"]),
                "hallucinations": faithfulness_result["hallucinations"],
                "success": final_state.get("review", {}).get("passed", False),
                "review_score": final_state.get("review", {}).get("score", 0),
            })
        except Exception as e:
            logger.error(f"Failed: {e}")
            results.append({"query": query, "error": str(e), "coverage": 0, "faithfulness": 0, "hallucinations_count": 0})
    
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"error": "No successful evaluations", "results": results}
    return {
        "total_queries": len(test_queries),
        "successful_evaluations": len(valid),
        "avg_coverage": sum(r["coverage"] for r in valid)/len(valid),
        "avg_faithfulness": sum(r["faithfulness"] for r in valid)/len(valid),
        "avg_review_score": sum(r["review_score"] for r in valid)/len(valid),
        "success_rate": sum(1 for r in valid if r.get("success"))/len(valid),
        "per_query_results": results
    }