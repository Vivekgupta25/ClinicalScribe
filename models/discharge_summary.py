from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .medication import Medication


class DischargeSummary(BaseModel):
    # Demographics
    patient_name: str = "MISSING ⚠️"
    age: str = "MISSING ⚠️"
    gender: str = "MISSING ⚠️"
    ip_number: str = "MISSING ⚠️"
    admission_date: str = "MISSING ⚠️"
    discharge_date: str = "MISSING ⚠️"
    department: str = "MISSING ⚠️"

    # Clinical
    principal_diagnosis: str = "MISSING ⚠️"
    secondary_diagnoses: List[str] = Field(default_factory=list)
    hospital_course: str = "MISSING ⚠️"
    procedures: List[str] = Field(default_factory=list)

    # Medications
    admission_meds: List[Medication] = Field(default_factory=list)
    discharge_meds: List[Medication] = Field(default_factory=list)
    med_changes: List[str] = Field(default_factory=list)

    # Safety
    allergies: str = "NOT KNOWN"
    pending_results: List[str] = Field(default_factory=list)
    discharge_condition: str = "MISSING ⚠️"
    followup_instructions: str = "MISSING ⚠️"

    # Flags
    conflicts: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    clinician_flags: List[str] = Field(default_factory=list)

    # Meta
    generated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    total_documents_processed: int = 0
    agent_steps_taken: int = 0
