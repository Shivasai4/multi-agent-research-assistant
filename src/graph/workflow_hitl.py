from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import GraphState
from src.agents.planner import planner_node
from src.agents.researcher import research_node
from src.agents.retriever import retriever_node
from src.agents.analyst import analyst_node
from src.agents.writer import writer_node

memory = MemorySaver()

def human_approval_node(state: GraphState):
    """Placeholder node; approval happens externally via update_state."""
    return state

def should_continue_after_approval(state: GraphState):
    if state.get("plan_approved") is True:
        return "retriever"
    else:
        # If not approved or still pending, stop
        return END

def build_research_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("writer", writer_node)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "human_approval")
    workflow.add_conditional_edges("human_approval", should_continue_after_approval, {
        "retriever": "retriever",
        END: END
    })
    workflow.add_edge("retriever", "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "writer")
    workflow.add_edge("writer", END)
    
    return workflow.compile(checkpointer=memory)

research_app = build_research_graph()