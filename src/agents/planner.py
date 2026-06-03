from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base import get_llm
from src.graph.state import GraphState, ResearchPlan
from src.models import PlannerOutput
from loguru import logger

SYSTEM_PROMPT = """You are an expert research planner. Given a user's query, create a structured research plan.
Rules:
- Sub-questions must be atomic and non-overlapping
- Search queries should be optimized for search engines (use the exact original term if it's a proper noun or product name)
- If the query contains a lowercase term that might be a product/tool (like "ollama", "langgraph", "fastapi"), treat it as the actual name, not an acronym
- Success criteria must be measurable
- Output ONLY valid JSON matching the schema"""

def planner_node(state: GraphState) -> dict:
    logger.info(">>> PLANNER: Started")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(PlannerOutput)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User query: {state['user_query']}\nGenerate research plan.")
    ]
    plan_output = structured_llm.invoke(messages)
    
    research_plan: ResearchPlan = {
        "main_question": state["user_query"],
        "sub_questions": plan_output.sub_questions,
        "search_queries": plan_output.search_queries,
        "expected_sources": plan_output.expected_sources,
        "success_criteria": plan_output.success_criteria,
    }
    logger.info(">>> PLANNER: Completed")
    return {
        "plan": research_plan,
        "current_step": 0,
        "agent_traces": [{"agent": "planner", "plan": research_plan}]
    }