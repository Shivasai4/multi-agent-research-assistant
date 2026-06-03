from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_llm
from src.graph.state import GraphState
from loguru import logger

ANALYST_SYSTEM = """You are an expert analyst. Given a research question and relevant documents, extract a direct answer and key supporting facts.

Output format (strictly follow these headings):
ANSWER: (one clear sentence answering the question)
KEY FINDINGS:
- finding 1
- finding 2
OPEN QUESTIONS: (if any, else "None")

Do not add any extra commentary or markdown."""

def analyst_node(state: GraphState) -> dict:
    logger.info(">>> ANALYST: Started")
    all_docs = state.get("raw_documents", []) + state.get("vector_results", []) + state.get("search_results", [])
    if not all_docs:
        logger.warning("No documents found.")
        return {
            "analysis": {
                "summary": "No information could be retrieved.",
                "key_findings": [],
                "open_questions": [state["user_query"]],
                "source_quality": {}
            },
            "agent_traces": [{"agent": "analyst", "fallback": "no_docs"}]
        }

    # Combine documents (limit to ~5 for token efficiency)
    docs_text = "\n\n---\n\n".join([f"[Source]\n{d['content'][:800]}" for d in all_docs[:5]])
    llm = get_llm(temperature=0.2)
    messages = [
        SystemMessage(content=ANALYST_SYSTEM),
        HumanMessage(content=f"Question: {state['user_query']}\n\nDocuments:\n{docs_text}\n\nNow answer using the required format:")
    ]
    response = llm.invoke(messages)
    content = response.content

    # Parse the response
    answer = ""
    findings = []
    open_questions = []
    current = None
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith("ANSWER:"):
            answer = line.replace("ANSWER:", "").strip()
            current = "answer"
        elif line.startswith("KEY FINDINGS:"):
            current = "findings"
        elif line.startswith("OPEN QUESTIONS:"):
            current = "open"
        elif current == "findings" and line.startswith("-"):
            findings.append(line[1:].strip())
        elif current == "open" and line and line != "None":
            open_questions.append(line)

    if not answer:
        # Fallback: try to extract from first sentence of the response
        answer = content.split('\n')[0][:200]

    # Convert findings to required internal format (list of dicts)
    structured_findings = []
    for f in findings:
        structured_findings.append({
            "claim": f,
            "supporting_sources": [],
            "confidence": 0.8,
            "contradictions": []
        })

    analysis = {
        "summary": answer,
        "key_findings": structured_findings,
        "open_questions": open_questions if open_questions else [],
        "source_quality": {}
    }
    logger.info(f"ANALYST: Extracted {len(structured_findings)} findings")
    logger.info(">>> ANALYST: Completed")
    return {
        "analysis": analysis,
        "agent_traces": [{"agent": "analyst", "num_findings": len(structured_findings)}]
    }