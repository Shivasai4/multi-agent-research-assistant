from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_llm
import json

def check_hallucinations(report: str, source_documents: list) -> dict:
    llm = get_llm(temperature=0.0)
    sources_text = "\n".join([f"Source: {s.get('metadata', {})}\n{s.get('content', '')[:500]}" for s in source_documents[:5]])
    prompt = f"""Verify if the following report is fully supported by the provided sources.
Report: {report}
Sources: {sources_text}
Output JSON: {{"hallucinations": ["list of unsupported claims"], "faithfulness_score": 0.0-1.0}}"""
    response = llm.invoke([SystemMessage(content="You are a fact-checker."), HumanMessage(content=prompt)])
    try:
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content)
    except Exception:
        result = {"hallucinations": ["Parse error"], "faithfulness_score": 0.0}
    return result