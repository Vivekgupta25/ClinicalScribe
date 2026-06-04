from pydantic import BaseModel, Field
from typing import List, Literal


class TraceStep(BaseModel):
    step_number: int
    reasoning: str
    action: str
    inputs: dict
    result: str
    next_decision: str
    status: Literal["success", "warning", "conflict", "error"]


class ExtractedDoc(BaseModel):
    filename: str
    doc_type: str
    base64_images: List[str] = Field(default_factory=list)
    page_count: int = 0


class AgentState(BaseModel):
    patient_id: str
    documents: List[ExtractedDoc] = Field(default_factory=list)
    findings: dict = Field(default_factory=dict)
    conflicts: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    clinician_flags: List[str] = Field(default_factory=list)
    steps_taken: int = 0
    max_steps: int = 20
    trace: List[TraceStep] = Field(default_factory=list)
    is_complete: bool = False
    current_action: str = ""
