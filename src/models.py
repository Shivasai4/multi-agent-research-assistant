from pydantic import BaseModel, Field
from typing import List, Optional

class PlannerOutput(BaseModel):
    sub_questions: List[str] = Field(description="Breakdown into 2-5 sub-questions")
    search_queries: List[str] = Field(description="Search engine queries")
    expected_sources: List[str] = Field(description="Types of sources needed")
    success_criteria: str = Field(description="Measurable completion criteria")

class FindingModel(BaseModel):
    claim: str
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    contradictions: List[str] = Field(default_factory=list)

class AnalysisOutput(BaseModel):
    summary: str
    key_findings: List[FindingModel]
    open_questions: List[str]

class ReviewOutput(BaseModel):
    passed: bool
    score: float = Field(ge=0, le=10)
    missing_info: List[str]
    hallucinations: List[str]
    revision_suggestions: str