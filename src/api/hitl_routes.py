from fastapi import APIRouter, HTTPException
from src.graph.workflow_hitl import research_app
from src.graph.state import GraphState
import uuid
import os
from typing import Dict
from loguru import logger

router = APIRouter(prefix="/research/hitl", tags=["human-in-the-loop"])
active_tasks: Dict[str, str] = {}  # task_id -> thread_id

@router.post("/start")
async def start_research(query: str, max_revisions: int = 2):
    task_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state: GraphState = {
        "user_query": query,
        "plan": None,
        "plan_approved": None,
        "rejection_reason": None,
        "current_step": 0,
        "raw_documents": [],
        "search_results": [],
        "vector_results": [],
        "analysis": None,
        "review": None,
        "revision_count": 0,
        "max_revisions": max_revisions,
        "final_report": None,
        "errors": [],
        "agent_traces": []
    }
    
    # Run graph until human_approval node
    try:
        for event in research_app.stream(initial_state, config):
            if "human_approval" in event:
                current_state = research_app.get_state(config)
                active_tasks[task_id] = thread_id
                return {
                    "task_id": task_id,
                    "status": "awaiting_approval",
                    "plan": current_state.values.get("plan"),
                    "message": "Plan ready. Approve with POST /research/hitl/approve/{task_id}?approved=true"
                }
    except Exception as e:
        logger.error(f"Start error: {e}")
        raise HTTPException(500, str(e))
    
    raise HTTPException(500, "Graph ended without requiring approval")

@router.post("/approve/{task_id}")
async def approve_plan(task_id: str, approved: bool, notes: str = None):
    if task_id not in active_tasks:
        raise HTTPException(404, "Task not found or already approved")
    
    thread_id = active_tasks[task_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get current state
    current_state = research_app.get_state(config)
    if not current_state:
        del active_tasks[task_id]
        raise HTTPException(404, "Graph state not found")
    
    # Update state with approval decision
    current_state.values["plan_approved"] = approved
    current_state.values["rejection_reason"] = notes if not approved else None
    research_app.update_state(config, current_state.values)
    
    if not approved:
        del active_tasks[task_id]
        return {"status": "rejected", "message": f"Plan rejected: {notes}"}
    
    # Resume execution (graph will continue from human_approval)
    try:
        for event in research_app.stream(None, config):
            # Wait for completion
            pass
        final_state = research_app.get_state(config)
        del active_tasks[task_id]
        
        final_report = final_state.values.get("final_report")
        review_score = final_state.values.get("review", {}).get("score") if final_state.values.get("review") else None
        
        # Save report to file
        report_file = None
        if final_report:
            os.makedirs("reports", exist_ok=True)
            report_file = f"reports/report_{task_id}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(final_report)
            logger.info(f"Report saved to {report_file}")
        
        return {
            "status": "completed",
            "final_report": final_report,
            "review_score": review_score,
            "saved_file": report_file
        }
    except Exception as e:
        logger.error(f"Resume error: {e}")
        raise HTTPException(500, str(e))

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(404, "Task not found")
    thread_id = active_tasks[task_id]
    config = {"configurable": {"thread_id": thread_id}}
    state = research_app.get_state(config)
    return {
        "task_id": task_id,
        "status": "awaiting_approval",
        "plan": state.values.get("plan") if state else None
    }