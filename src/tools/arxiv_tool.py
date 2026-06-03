from langchain_core.tools import tool
import arxiv
from typing import List, Dict
from loguru import logger

@tool
def arxiv_search(query: str, max_results: int = 2) -> List[Dict]:
    """Search academic papers on ArXiv. Returns title, authors, summary, and PDF link."""
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        results = []
        for paper in client.results(search):
            results.append({
                "content": f"Title: {paper.title}\nAuthors: {', '.join(a.name for a in paper.authors)}\nSummary: {paper.summary[:800]}",
                "metadata": {"source": "arxiv", "title": paper.title, "pdf_url": paper.pdf_url, "published": paper.published}
            })
        return results
    except Exception as e:
        logger.error(f"ArXiv search failed: {e}")
        return [{"content": f"ArXiv search error: {e}", "metadata": {"error": True}}]