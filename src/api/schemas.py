from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ResearchRequest(BaseModel):
    query: str
    max_revisions: int = 2

class ResearchResponse(BaseModel):
    task_id: str
    status: str

class ResearchResult(BaseModel):
    task_id: str
    final_report: str
    agent_traces: List[Dict[str, Any]]
    review_score: Optional[float] = None