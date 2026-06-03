from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.base import get_llm
from src.graph.state import GraphState, Source
from src.tools.web_search import web_search
from src.tools.wikipedia_tool import wikipedia_search
from src.tools.arxiv_tool import arxiv_search
from src.tools.calculator_tool import calculate
from loguru import logger
import json
import concurrent.futures

RESEARCH_SYSTEM = """You are a research assistant. You have access to web search, Wikipedia, ArXiv, and a calculator.
For each sub-question, gather information from relevant sources.
After gathering, summarize findings as a list of sources with key quotes."""

def research_node(state: GraphState) -> dict:
    logger.info(">>> RESEARCHER: Started")
    user_query = state["user_query"]
    plan = state.get("plan", {})
    sub_questions = plan.get("sub_questions", [])
    
    # Collect all queries to search: user_query + sub_questions
    all_queries = [user_query] + sub_questions[:2]  # limit to avoid overload
    
    tool_results = []
    
    # Define a worker to run all tools for a given query
    def fetch_for_query(query):
        results = []
        # Web search
        try:
            results.extend(web_search.invoke(query))
        except Exception as e:
            logger.error(f"Web search failed for '{query}': {e}")
        # Wikipedia
        try:
            results.extend(wikipedia_search.invoke(query))
        except Exception as e:
            logger.error(f"Wikipedia failed for '{query}': {e}")
        # ArXiv (skip very short queries)
        if len(query) > 5:
            try:
                results.extend(arxiv_search.invoke(query, max_results=1))
            except Exception as e:
                logger.error(f"ArXiv failed for '{query}': {e}")
        return results
    
    # Parallel execution across queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_for_query, q) for q in all_queries]
        for future in concurrent.futures.as_completed(futures):
            tool_results.extend(future.result())
    
    # If the query looks like a calculation, also run calculator
    calc_keywords = ["calculate", "compute", "sum", "average", "math", "+", "-", "*", "/"]
    if any(kw in user_query.lower() for kw in calc_keywords):
        calc_result = calculate.invoke(user_query)
        tool_results.append({
            "content": calc_result,
            "metadata": {"source": "calculator", "query": user_query}
        })
    
    sources = [{"content": r["content"], "metadata": r["metadata"]} for r in tool_results]
    logger.info(f"RESEARCHER: Completed with {len(sources)} sources")
    return {
        "search_results": sources,
        "raw_documents": sources,
        "agent_traces": [{"agent": "researcher", "num_sources": len(sources)}]
    }