# ClinicalScribe 🏥

An agentic AI system that reads patient medical PDF documents and generates structured discharge summaries with conflict detection, missing field flagging, and medication reconciliation.

> ⚠️ **All output is an AI-generated draft. Requires clinician review before clinical use.**

---

## Features

- **Multi-document PDF ingestion** — converts PDF pages to images for vision-based extraction
- **Agentic loop** — autonomous step-by-step decision engine (not a fixed pipeline)
- **Diagnosis conflict detection** — flags contradictions across ER charts, admission records, and consultation notes
- **Medication reconciliation** — compares admission vs discharge medications, flags undocumented changes
- **Drug interaction checker** — detects clinically significant interactions
- **Missing field flagging** — identifies incomplete required fields
- **Pending results tracker** — catches awaited labs and follow-up investigations
- **Full agent trace log** — every decision step logged for auditability
- **Streamlit UI** — professional medical interface with download support

---

## Installation

```bash
git clone <repo-url>
cd ClinicalScribe
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

## Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key into your `.env` file:

```bash
GEMINI_API_KEY=your_key_here
```

---

## Run via Command Line

```bash
python main.py --patient patients/patient_1
python main.py --patient patients/patient_2 --max-steps 25
```

Output files are saved to `outputs/`:
- `outputs/patient_1_summary.md` — structured discharge summary
- `outputs/patient_1_trace.txt` — full agent trace log

---

## Run via Streamlit UI

```bash
streamlit run ui/app.py
```

Then open `http://localhost:8501` in your browser.

1. Enter a Patient ID
2. Upload PDF documents
3. Click **▶ Run Agent**
4. Review tabs: Summary · Agent Trace · Raw Documents
5. Download the summary as markdown

---

## Project Structure

```
ClinicalScribe/
├── main.py                    # CLI entry point
├── requirements.txt
├── .env                       # GEMINI_API_KEY
├── core/
│   ├── pdf_reader.py          # PDF → base64 images, document classification
│   ├── gemini_client.py       # Gemini API wrapper with retry logic
│   ├── agent.py               # Main agentic loop
│   ├── tools.py               # Drug interaction checker, flagging tools
│   └── summary_generator.py  # Markdown + trace log generation
├── models/
│   ├── medication.py          # Medication Pydantic model
│   ├── agent_state.py         # AgentState, TraceStep, ExtractedDoc models
│   └── discharge_summary.py  # DischargeSummary Pydantic model
├── prompts/
│   ├── extract_prompts.py     # Gemini extraction prompt templates
│   └── agent_prompts.py      # Agent decision prompt template
├── ui/
│   └── app.py                 # Streamlit web interface
├── patients/
│   ├── patient_1/             # Place patient PDFs here
│   └── patient_2/
└── outputs/                   # Generated summaries and trace logs
```

---

## How the Agent Works

The agent follows a deterministic priority queue of actions, deciding at each step what to do based on what has been completed:

```
1. load_documents          → Load and classify all PDFs
2. extract_demographics    → Patient name, age, gender, dates
3. extract_diagnoses       → All diagnoses from all documents
4. check_diagnosis_conflicts → Cross-document conflict detection
5. extract_labs            → Lab results and statuses
6. extract_medications     → Admission and discharge medications
7. reconcile_medications   → Compare and flag undocumented changes
8. check_drug_interactions → Detect significant drug pairs
9. extract_procedures      → Procedures performed
10. extract_hospital_course → Chronological course summary
11. check_pending_results  → Identify awaited investigations
12. flag_missing_fields    → Required fields not found
13. generate_summary       → Build DischargeSummary object
14. complete               → Mark agent done
```

Every step is logged in the trace with reasoning, inputs, result, and next decision.

---

## Supported Document Types

Documents are auto-classified by filename keywords:

| Type | Keywords |
|------|----------|
| admission | admission, case_record |
| labs | lab, investigation, pathology, biochemistry |
| nursing | nursing, nurse, nsg |
| drug_chart | drug, medication, chart |
| consultation | consultation, consult |
| radiology | usg, ct, xray, echo, radiology |
| er_chart | er, emergency, casualty |
| icu_chart | icu, hdu |
| discharge | discharge, summary |

---

## Limitations & Future Work

**Current limitations:**
- Drug interaction database is illustrative (3 pairs) — production use requires a full pharmacopeia DB
- Handwritten notes may reduce extraction accuracy
- Very long documents are truncated to first 8 pages per extraction call
- No FHIR/HL7 output format yet

**Planned improvements:**
- Integration with real drug interaction APIs (e.g. DrugBank, RxNorm)
- FHIR R4 structured output
- Multi-patient batch processing
- EHR system integration
- Confidence scores per extracted field
- Human-in-the-loop correction interface
