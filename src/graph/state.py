from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

class ResearchPlan(TypedDict):
    main_question: str
    sub_questions: List[str]
    search_queries: List[str]
    expected_sources: List[str]
    success_criteria: str

class Source(TypedDict):
    content: str
    metadata: Dict[str, Any]

class Finding(TypedDict):
    claim: str
    supporting_sources: List[Source]
    confidence: float
    contradictions: List[str]

class Analysis(TypedDict):
    summary: str
    key_findings: List[Finding]
    open_questions: List[str]
    source_quality: Dict[str, float]

class Review(TypedDict):
    passed: bool
    score: float
    missing_info: List[str]
    hallucinations: List[str]
    revision_suggestions: str

class GraphState(TypedDict):
    user_query: str
    plan: Optional[ResearchPlan]
    current_step: int
    raw_documents: Annotated[List[Source], operator.add]
    search_results: Annotated[List[Source], operator.add]
    vector_results: Annotated[List[Source], operator.add]
    analysis: Optional[Analysis]
    review: Optional[Review]
    revision_count: int
    max_revisions: int
    final_report: Optional[str]
    errors: Annotated[List[str], operator.add]
    agent_traces: Annotated[List[Dict], operator.add]
    plan_approved: Optional[bool]
    rejection_reason: Optional[str]