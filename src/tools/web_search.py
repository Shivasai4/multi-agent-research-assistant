from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

ddg_search = DuckDuckGoSearchRun()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, Exception)),
    reraise=False
)
def safe_search(query: str) -> str:
    """Perform web search with retry."""
    return ddg_search.invoke(query)

@tool
def web_search(query: str) -> List[Dict]:
    """Search the web for recent information. Returns list of results."""
    if not query or len(query.strip()) < 3:
        return [{"content": "Query too short", "metadata": {"error": True}}]
    
    try:
        raw = safe_search(query)
        return [{"content": raw, "metadata": {"query": query, "source": "duckduckgo"}}]
    except Exception as e:
        # Fallback: return a friendly error message
        return [{"content": f"Web search failed: {str(e)}", "metadata": {"error": True, "query": query}}]