from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_llm
from src.graph.state import GraphState, Review
from src.models import ReviewOutput

REVIEWER_SYSTEM = """You are a strict quality reviewer. Check for:
1. Did we answer all parts of the question? (missing_info)
2. Are any claims not supported by sources? (hallucinations)
3. Overall quality score (0-10)
If score < 7 or passed=False, the report must be revised."""

def reviewer_node(state: GraphState) -> dict:
    analysis = state.get("analysis")
    if not analysis:
        return {"review": {"passed": False, "score": 0, "missing_info": ["No analysis"], "hallucinations": [], "revision_suggestions": "Analyst failed"}}
    
    sources = state.get("raw_documents", [])
    sources_text = "\n".join([f"- {s['content'][:300]}" for s in sources[:5]])
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ReviewOutput)
    messages = [
        SystemMessage(content=REVIEWER_SYSTEM),
        HumanMessage(content=f"Question: {state['user_query']}\n\nAnalysis summary: {analysis['summary']}\n\nKey findings: {[f['claim'] for f in analysis['key_findings']]}\n\nSources:\n{sources_text}\n\nReview and output.")
    ]
    review_out = structured_llm.invoke(messages)
    review: Review = {
        "passed": review_out.passed,
        "score": review_out.score,
        "missing_info": review_out.missing_info,
        "hallucinations": review_out.hallucinations,
        "revision_suggestions": review_out.revision_suggestions
    }
    return {
        "review": review,
        "revision_count": state.get("revision_count", 0) + 1,
        "agent_traces": [{"agent": "reviewer", "score": review_out.score, "passed": review_out.passed}]
    }