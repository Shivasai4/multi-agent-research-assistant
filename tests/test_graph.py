# test_graph.py
from src.graph.workflow import research_app
from src.graph.state import GraphState

initial_state: GraphState = {
    "user_query": "What are the latest advances in LLM agents?",
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

# Run the graph
final_state = research_app.invoke(initial_state)
print(final_state["final_report"])