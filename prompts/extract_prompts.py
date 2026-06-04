DEMOGRAPHICS_PROMPT = """Extract patient demographics from this medical document image.

Extract ONLY what is explicitly written. Use "NOT_FOUND" for any missing field. Never guess.

Return ONLY raw JSON (no markdown, no code fences, no explanation):
{
  "patient_name": "",
  "age": "",
  "gender": "",
  "ip_number": "",
  "admission_date": "",
  "discharge_date": "",
  "department": "",
  "weight": ""
}"""


DIAGNOSIS_PROMPT = """Extract ALL diagnoses mentioned in this medical document image.

Rules:
- Extract ONLY what is explicitly written. Include principal and secondary diagnoses.
- NEVER invent diagnoses.

Return ONLY raw JSON (no markdown, no code fences, no explanation):
{
  "diagnoses_found": ["diagnosis1", "diagnosis2"],
  "doc_type": "document type",
  "is_provisional": true,
  "is_final": false,
  "raw_text_found": "exact text where diagnosis was found"
}"""


MEDICATION_PROMPT = """Extract ALL medications from this medical document image.

Rules:
- Extract ONLY explicitly documented medications.
- Use "NOT_DOCUMENTED" for any missing field.
- Note if each medication is an admission or discharge medication.

Return ONLY raw JSON array (no markdown, no code fences, no explanation):
[
  {
    "name": "",
    "dose": "",
    "route": "",
    "frequency": "",
    "duration": "",
    "indication": "",
    "is_discharge_med": true,
    "is_admission_med": false
  }
]"""


LAB_PROMPT = """Extract ALL laboratory results from this medical document image.

Rules:
- Extract ONLY what is explicitly written.
- Mark pending/awaited results clearly.

Return ONLY raw JSON array (no markdown, no code fences, no explanation):
[
  {
    "test_name": "",
    "value": "",
    "unit": "",
    "reference_range": "",
    "status": "normal/abnormal/pending/critical",
    "date": ""
  }
]"""


PROCEDURES_PROMPT = """Extract ALL procedures performed on the patient from this medical document image.

Return ONLY raw JSON array (no markdown, no code fences, no explanation):
[
  {
    "procedure_name": "",
    "date": "",
    "details": ""
  }
]"""


CONFLICT_CHECK_PROMPT = """You are a medical analyst. I will give you multiple diagnoses extracted from different documents for the same patient.

Analyze these diagnoses and identify:
1. Any conflicts or contradictions
2. Diagnoses that appear in some documents but not others
3. Provisional vs final diagnosis differences

Input diagnoses by document:
{diagnoses_by_doc}

Return ONLY a JSON object:
{{
  "conflicts_found": true,
  "conflict_details": ["conflict1", "conflict2"],
  "consistent_diagnoses": ["diagnosis1"],
  "recommended_action": "description for clinician"
}}"""


HOSPITAL_COURSE_PROMPT = """You are a medical summarizer. Based on these nursing notes and consultation notes, write a brief hospital course summary.

Rules:
- Use ONLY information from the provided documents
- Do NOT invent any clinical details
- Keep it factual and chronological
- Flag any gaps or missing information

Documents content:
{documents_content}

Return ONLY a JSON object:
{{
  "hospital_course": "summary paragraph",
  "key_events": ["event1", "event2"],
  "missing_info": ["what is missing"]
}}"""
