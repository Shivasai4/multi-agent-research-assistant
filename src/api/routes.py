from fastapi import APIRouter, BackgroundTasks, HTTPException
from src.api.schemas import ResearchRequest, ResearchResponse, ResearchResult
from src.graph.workflow import research_app
from src.graph.state import GraphState
from src.observability.langfuse_setup import get_langfuse_handler
from src.cache.redis_cache import get_cached_result, set_cached_result
import uuid
from typing import Dict
from loguru import logger

router = APIRouter(prefix="/research", tags=["research"])
tasks: Dict[str, dict] = {}

def run_research_task(task_id: str, request: ResearchRequest):
    """Background task that always updates tasks[task_id] with a result or error."""
    handler = get_langfuse_handler()
    
    # --- CHECK CACHE FIRST ---
    cached = get_cached_result(request.query, request.max_revisions)
    if cached:
        tasks[task_id] = {
            "status": "completed",
            "result": ResearchResult(**cached)
        }
        logger.info(f"Task {task_id} returned from cache")
        return
    # --- END CACHE CHECK ---
    
    try:
        initial_state: GraphState = {
            "user_query": request.query,
            "plan": None,
            "current_step": 0,
            "raw_documents": [],
            "search_results": [],
            "vector_results": [],
            "analysis": None,
            "review": None,
            "revision_count": 0,
            "max_revisions": request.max_revisions,
            "final_report": None,
            "errors": [],
            "agent_traces": []
        }
        
        # Pass the callback handler to LangGraph – it will automatically create traces
        config = {"callbacks": [handler]} if handler else {}
        
        # Invoke the LangGraph workflow
        final_state = research_app.invoke(initial_state, config=config)
        
        # Prepare result data for caching
        result_data = {
            "task_id": task_id,
            "final_report": final_state.get("final_report", "No report generated."),
            "agent_traces": final_state.get("agent_traces", []),
            "review_score": final_state.get("review", {}).get("score") if final_state.get("review") else None
        }
        
        # --- STORE IN CACHE ---
        set_cached_result(request.query, request.max_revisions, result_data)
        # --- END CACHE STORE ---
        
        # Store successful result
        tasks[task_id] = {
            "status": "completed",
            "result": ResearchResult(**result_data)
        }
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Task {task_id} failed with error: {e}")
        
        # Graceful failure – return a fallback report
        tasks[task_id] = {
            "status": "completed",
            "result": ResearchResult(
                task_id=task_id,
                final_report=f"# Research Failed\n\nSorry, the research assistant encountered an error:\n\n```\n{str(e)}\n```\n\nPlease try again with a different query or check that Ollama is running.",
                agent_traces=[{"agent": "system", "error": str(e)}],
                review_score=None
            )
        }

@router.post("/", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(run_research_task, task_id, request)
    return ResearchResponse(task_id=task_id, status="pending")

@router.get("/{task_id}", response_model=ResearchResult)
async def get_result(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks[task_id]
    
    if task["status"] == "pending":
        raise HTTPException(status_code=202, detail="Task still processing")
    
    if task["status"] == "completed":
        return task["result"]
    
    raise HTTPException(status_code=500, detail="Unexpected task status")