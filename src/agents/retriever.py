from src.graph.state import GraphState, Source
from src.tools.vector_store import vector_store
from loguru import logger


def retriever_node(state: GraphState) -> dict:
    logger.info(">>> RETRIEVER: Started")
    queries = []
    if state.get("plan") and state["plan"].get("search_queries"):
        queries = state["plan"]["search_queries"]
    else:
        queries = [state["user_query"]]
    
    all_results: list[Source] = []
    for q in queries[:3]:
        results = vector_store.search(q, top_k=3)
        for r in results:
            all_results.append({
                "content": r["content"],
                "metadata": {"source_type": "vector_db", "query": q, **r.get("metadata", {})}
            })
    logger.info(">>> RETRIEVER: Completed")
    return {
        "vector_results": all_results,
        "agent_traces": [{"agent": "retriever", "num_results": len(all_results)}]
    }