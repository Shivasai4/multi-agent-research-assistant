from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_llm, invoke_llm_with_retry
from src.graph.state import GraphState
from loguru import logger

WRITER_SYSTEM = """You are a technical report writer. Produce a final markdown report with:
- Executive Summary
- Key Findings (with citations to sources)
- Limitations & Open Questions
- Conclusion
Use the analysis and reviewer feedback to improve."""

def writer_node(state: GraphState) -> dict:
    logger.info(">>> WRITER: Started")
    
    analysis = state.get("analysis")
    review = state.get("review")
    revision_suggestions = review.get("revision_suggestions", "") if review else ""
    sources = state.get("raw_documents", [])[:5]
    sources_text = "\n".join([f"- {s['content'][:500]}..." for s in sources])
    
    # Prepare fallback report in case LLM fails
    fallback_report = f"""# Research Report

**User question:** {state['user_query']}

## Executive Summary
Unable to generate a complete report due to a technical issue. Below is the raw information gathered.

## Raw Information
{sources_text if sources_text else "No sources were retrieved."}

## Next Steps
Please try rephrasing your question or check that Ollama is running properly.
"""
    
    # If no analysis or empty findings, use fallback quickly
    if not analysis or not analysis.get("key_findings"):
        logger.warning("WRITER: No analysis found, using fallback report from raw documents.")
        return {
            "final_report": fallback_report,
            "agent_traces": [{"agent": "writer", "fallback": "no_analysis"}]
        }
    
    try:
        llm = get_llm(temperature=0.4)
        messages = [
            SystemMessage(content=WRITER_SYSTEM),
            HumanMessage(content=f"""
User question: {state['user_query']}

Analysis summary: {analysis.get('summary', 'N/A')}

Key findings:
{chr(10).join([f"- {f['claim']} (confidence {f.get('confidence', 0.5):.2f})" for f in analysis.get('key_findings', [])])}

Reviewer feedback: {revision_suggestions if revision_suggestions else 'No revisions needed'}

Sources:
{sources_text}

Generate final report in markdown.
""")
        ]
        
        # Use retry wrapper for LLM call
        response = invoke_llm_with_retry(llm, messages)
        
        # Check if response is valid
        if not response.content or len(response.content.strip()) < 50:
            logger.warning("WRITER: LLM returned short/empty content, using fallback.")
            return {
                "final_report": fallback_report,
                "agent_traces": [{"agent": "writer", "fallback": "empty_llm_response"}]
            }
        
        logger.info(">>> WRITER: Completed")
        return {
            "final_report": response.content,
            "agent_traces": [{"agent": "writer", "report_length": len(response.content)}]
        }
        
    except Exception as e:
        logger.error(f"WRITER: LLM invocation failed: {e}, using fallback report.")
        return {
            "final_report": fallback_report,
            "agent_traces": [{"agent": "writer", "error": str(e), "fallback": True}]
        }