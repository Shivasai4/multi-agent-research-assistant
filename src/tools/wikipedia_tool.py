from langchain_core.tools import tool
import wikipedia
from typing import List, Dict
from loguru import logger

@tool
def wikipedia_search(query: str, top_k: int = 2) -> List[Dict]:
    """Search Wikipedia for a given query. Returns summary and page metadata."""
    try:
        # Search for pages matching query
        search_results = wikipedia.search(query, results=top_k)
        results = []
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                results.append({
                    "content": f"Title: {page.title}\nSummary: {page.summary[:1000]}",
                    "metadata": {"source": "wikipedia", "title": page.title, "url": page.url}
                })
            except Exception as e:
                logger.warning(f"Failed to fetch Wikipedia page '{title}': {e}")
        return results
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return [{"content": f"Wikipedia search error: {e}", "metadata": {"error": True}}]