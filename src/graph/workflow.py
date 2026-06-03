from langgraph.graph import StateGraph, END
from src.graph.state import GraphState
from src.agents.planner import planner_node
from src.agents.researcher import research_node
from src.agents.retriever import retriever_node
from src.agents.analyst import analyst_node
from src.agents.reviewer import reviewer_node
from src.agents.writer import writer_node

def should_continue_after_review(state: GraphState) -> str:
    review = state.get("review")
    if not review:
        return "writer"
    if not review["passed"] and state.get("revision_count", 0) < state.get("max_revisions", 2):
        return "research"
    return "writer"

def build_research_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("writer", writer_node)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "reviewer")
    workflow.add_conditional_edges(
        "reviewer",
        should_continue_after_review,
        {"research": "researcher", "writer": "writer"}
    )
    workflow.add_edge("writer", END)
    return workflow.compile()

research_app = build_research_graph()