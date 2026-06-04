import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Root paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
PATIENTS_DIR = ROOT / "patients"
PATIENTS_DIR.mkdir(exist_ok=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClinicalScribe",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Global reset ───────────────────────────────── */
[data-testid="stToolbar"],[data-testid="stDecoration"],
#MainMenu, header, footer { display:none !important; }
html, body, .stApp { background:#f1f5f9 !important; font-family:'Inter','Segoe UI',sans-serif; }
.main .block-container { padding-top:1.5rem; padding-bottom:2rem; }

/* ── Sidebar background ─────────────────────────── */
section[data-testid="stSidebar"] > div:first-child {
    background: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
    padding: 0 0 2rem !important;
}

/* ── Sidebar labels ─────────────────────────────── */
section[data-testid="stSidebar"] label {
    color: #374151 !important;
    font-size: 0.79rem !important;
    font-weight: 600 !important;
}

/* ── Text + date inputs ─────────────────────────── */
section[data-testid="stSidebar"] input[type="text"],
section[data-testid="stSidebar"] input[type="number"],
section[data-testid="stSidebar"] input[type="date"] {
    background: #ffffff !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #111827 !important;
    font-size: 0.84rem !important;
    padding: 7px 11px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
section[data-testid="stSidebar"] input[type="text"]:focus,
section[data-testid="stSidebar"] input[type="number"]:focus,
section[data-testid="stSidebar"] input[type="date"]:focus {
    border-color: #2E86AB !important;
    box-shadow: 0 0 0 3px rgba(46,134,171,0.15) !important;
    outline: none !important;
}
section[data-testid="stSidebar"] input::placeholder { color:#9ca3af !important; }

/* Hide "Press Enter to apply" tooltip */
section[data-testid="stSidebar"] [data-testid="InputInstructions"],
section[data-testid="stSidebar"] .st-emotion-cache-16idsys p { display:none !important; }

/* Date input wrapper — match text input look */
section[data-testid="stSidebar"] [data-baseweb="input"] {
    background: #ffffff !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] [data-baseweb="input"]:focus-within {
    border-color: #2E86AB !important;
    box-shadow: 0 0 0 3px rgba(46,134,171,0.15) !important;
}
/* Remove inner borders Streamlit adds */
section[data-testid="stSidebar"] [data-baseweb="input"] > div {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
/* Calendar icon color */
section[data-testid="stSidebar"] [data-baseweb="input"] svg {
    fill: #6b7280 !important;
}

/* ── Selectbox ──────────────────────────────────── */
section[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background: #ffffff !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-baseweb="select"] span:not([aria-hidden]) {
    color: #111827 !important;
    font-size: 0.84rem !important;
}

/* ── Slider ─────────────────────────────────────── */
section[data-testid="stSidebar"] .stSlider label { color:#374151 !important; }

/* ── File uploader ──────────────────────────────── */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 2px dashed #93c5fd !important;
    border-radius: 10px !important;
    transition: border-color 0.2s, background 0.2s !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
    border-color: #2E86AB !important;
    background: #eff6ff !important;
}

/* ── Run button ─────────────────────────────────── */
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg,#1d6fa4 0%,#2E86AB 60%,#38a3c9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(46,134,171,0.4) !important;
    transition: all 0.18s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 7px 20px rgba(46,134,171,0.45) !important;
}
section[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── History download buttons ───────────────────── */
section[data-testid="stSidebar"] .stDownloadButton > button {
    background: #fff !important;
    color: #374151 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 7px !important;
    font-size: 0.77rem !important;
    font-weight: 600 !important;
    padding: 5px 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
section[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: #f3f4f6 !important;
    border-color: #9ca3af !important;
}

/* ── Sidebar expanders ──────────────────────────── */
section[data-testid="stSidebar"] .stExpander {
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
section[data-testid="stSidebar"] hr { border-color: #e5e7eb !important; margin: 0.7rem 0 !important; }

/* ── Brand header (scoped class) ────────────────── */
.cs-brand {
    background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 100%);
    padding: 20px 18px 16px; margin: 0 0 14px;
    border-bottom: 3px solid #2E86AB;
}
.cs-brand-row { display:flex; align-items:center; gap:11px; }
.cs-icon {
    width:44px; height:44px; background:#2E86AB; border-radius:12px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.35rem; flex-shrink:0;
    box-shadow: 0 4px 12px rgba(46,134,171,0.4);
}
.cs-title { color:#f8fafc; font-size:1.18rem; font-weight:800; letter-spacing:0.2px; display:block; line-height:1.25; }
.cs-sub { color:#7dd3fc; font-size:0.68rem; font-weight:600; letter-spacing:1.4px; display:block; margin-top:3px; }

/* ── Section mini-header ────────────────────────── */
.cs-section {
    font-size:0.69rem; font-weight:700; color:#6b7280;
    letter-spacing:1.2px; padding: 0 0 5px; margin-bottom:6px;
    border-bottom: 1px solid #e5e7eb;
}

/* ── Validation error chips ─────────────────────── */
.cs-err {
    background:#fef2f2; border:1px solid #fecaca;
    border-radius:7px; padding:7px 11px;
    color:#dc2626; font-size:0.8rem; font-weight:500; margin:3px 0;
}

/* ── Main content styles ────────────────────────── */
.draft-banner {
    background:linear-gradient(135deg,#dc2626,#ef4444);
    color:#fff; text-align:center; padding:11px 16px;
    font-weight:700; font-size:0.88rem; border-radius:10px;
    margin-bottom:1.2rem; box-shadow:0 3px 10px rgba(220,38,38,0.25);
}
.alert-critical { background:#fef2f2; border-left:4px solid #dc2626; padding:11px 15px; border-radius:7px; margin:5px 0; color:#991b1b; font-size:0.87rem; }
.alert-warning  { background:#fffbeb; border-left:4px solid #f59e0b; padding:11px 15px; border-radius:7px; margin:5px 0; color:#92400e; font-size:0.87rem; }
.alert-success  { background:#f0fdf4; border-left:4px solid #22c55e; padding:11px 15px; border-radius:7px; margin:5px 0; color:#166534; font-size:0.87rem; }
.section-header { color:#0f172a; font-size:1rem; font-weight:700; margin:1.1rem 0 0.5rem; padding-bottom:6px; border-bottom:2px solid #e2e8f0; }
.storage-box { background:#f0f9ff; border:1px solid #bae6fd; padding:10px 14px; border-radius:8px; margin:8px 0; font-size:0.81rem; color:#0369a1; line-height:1.7; }
[data-testid="stTabs"] [data-baseweb="tab"] { font-weight:600; font-size:0.87rem; }
</style>
""", unsafe_allow_html=True)


# ── Storage helpers ───────────────────────────────────────────────────────────
def slugify(name: str, max_len: int = 25) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", name.strip())[:max_len]


def make_patient_id(patient_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(patient_name) if patient_name else "patient"
    return f"{slug}_{ts}"


def save_uploads(uploaded_files, patient_id: str) -> str:
    d = PATIENTS_DIR / patient_id
    d.mkdir(parents=True, exist_ok=True)
    for f in uploaded_files:
        (d / f.name).write_bytes(f.read())
    return str(d)


def save_pending_uploads(pending_files: list, patient_id: str) -> str:
    d = PATIENTS_DIR / patient_id
    d.mkdir(parents=True, exist_ok=True)
    for fname, fbytes in pending_files:
        (d / fname).write_bytes(fbytes)
    return str(d)


def save_reports(summary, trace, patient_id: str) -> Path:
    import importlib, sys
    # Force reload so Streamlit's sys.modules cache never serves a stale version
    # of the module (e.g. one loaded before generate_pdf was added to the file).
    if "core.summary_generator" in sys.modules:
        importlib.reload(sys.modules["core.summary_generator"])
    from core.summary_generator import SummaryGenerator
    out = PATIENTS_DIR / patient_id
    out.mkdir(parents=True, exist_ok=True)
    gen = SummaryGenerator()
    (out / "summary.pdf").write_bytes(gen.generate_pdf(summary, patient_id))
    (out / "trace.txt").write_text(gen.generate_trace_log(trace, patient_id), encoding="utf-8")
    return out


def list_history() -> list:
    records = []
    for d in sorted(PATIENTS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        pdf = d / "summary.pdf"
        if pdf.exists():
            records.append({
                "id":   d.name,
                "pdf":  pdf,
                "time": datetime.fromtimestamp(d.stat().st_mtime).strftime("%d %b %Y, %H:%M"),
            })
    return records


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar():
    generating = st.session_state.get("generating", False)

    with st.sidebar:
        # ── Brand header ──────────────────────────────────────────────
        st.markdown("""
        <div class="cs-brand">
          <div class="cs-brand-row">
            <div class="cs-icon">🏥</div>
            <div>
              <span class="cs-title">ClinicalScribe</span>
              <span class="cs-sub">AI DISCHARGE SUMMARY</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Upload section ────────────────────────────────────────────
        st.markdown('<p class="cs-section">📄 &nbsp;UPLOAD DOCUMENTS</p>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            label="",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload patient PDFs — admission, labs, drug chart, nursing notes",
            label_visibility="collapsed",
            disabled=generating,
        )

        st.divider()

        # ── Patient Information ───────────────────────────────────────
        st.markdown('<p class="cs-section">👤 &nbsp;PATIENT INFORMATION</p>', unsafe_allow_html=True)

        manual_name = st.text_input("Patient Name *", placeholder="e.g. Ramesh Kumar", disabled=generating)

        c1, c2 = st.columns(2)
        with c1:
            manual_age = st.text_input("Age *", placeholder="e.g. 54", disabled=generating)
        with c2:
            manual_gender = st.selectbox("Gender *", ["", "Male", "Female", "Other"], disabled=generating)

        c3, c4 = st.columns(2)
        with c3:
            manual_admission = st.date_input("Admission Date", value=None, format="DD/MM/YYYY", disabled=generating)
        with c4:
            manual_discharge = st.date_input("Discharge Date *", value=None, format="DD/MM/YYYY", disabled=generating)

        manual_ward = st.text_input("Ward / Bed No.", placeholder="e.g. Ward 3 / Bed 12", disabled=generating)

        st.divider()

        # ── Settings ──────────────────────────────────────────────────
        max_steps = st.slider("Max Agent Steps", min_value=5, max_value=30, value=20, disabled=generating)

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        # ── Run button ────────────────────────────────────────────────
        btn_label = "⏳  Generating Report..." if generating else "▶   Generate Summary"
        run_clicked = st.button(btn_label, type="primary", use_container_width=True, disabled=generating)

        # Validation
        validation_errors = []
        if run_clicked:
            if not manual_name.strip():
                validation_errors.append("Please fill in Patient Name.")
            if not manual_age.strip():
                validation_errors.append("Please fill in Age.")
            if not manual_gender:
                validation_errors.append("Please select Gender.")
            if not manual_discharge:
                validation_errors.append("Please select Discharge Date.")
            for err in validation_errors:
                st.markdown(f'<div class="cs-err">⚠ &nbsp;{err}</div>', unsafe_allow_html=True)

        st.divider()

        # ── Previous Reports ──────────────────────────────────────────
        st.markdown('<p class="cs-section">📁 &nbsp;PREVIOUS REPORTS</p>', unsafe_allow_html=True)
        history = list_history()
        if history:
            for rec in history[:6]:
                name_part = rec["id"].rsplit("_", 2)[0].replace("_", " ").title()
                with st.expander(f"🗂  {name_part[:24]}", expanded=False):
                    st.caption(f"🕐 {rec['time']}")
                    st.download_button("⬇ Download PDF", rec["pdf"].read_bytes(),
                        file_name=f"{rec['id']}_summary.pdf", mime="application/pdf",
                        key=f"h_pdf_{rec['id']}", use_container_width=True)
        else:
            st.caption("No previous reports found.")

    manual_info = {
        "patient_name":   manual_name.strip(),
        "age":            manual_age.strip(),
        "gender":         manual_gender,
        "admission_date": manual_admission.strftime("%d %b %Y") if manual_admission else "",
        "discharge_date": manual_discharge.strftime("%d %b %Y") if manual_discharge else "",
        "ward_bed":       manual_ward.strip(),
    }
    return uploaded_files, max_steps, run_clicked, manual_info, validation_errors


# ── Helpers ───────────────────────────────────────────────────────────────────
def check_api_key() -> bool:
    key = os.getenv("GEMINI_API_KEY", "")
    return bool(key and key != "your_gemini_api_key_here")


def apply_manual_overrides(summary, info: dict):
    MISSING = ("MISSING ⚠️", "", None)
    if info.get("patient_name") and summary.patient_name in MISSING:
        summary.patient_name = info["patient_name"]
    if info.get("age") and summary.age in MISSING:
        summary.age = info["age"]
    if info.get("gender") and summary.gender in MISSING:
        summary.gender = info["gender"]
    if info.get("admission_date") and summary.admission_date in MISSING:
        summary.admission_date = info["admission_date"]
    if info.get("discharge_date") and summary.discharge_date in MISSING:
        summary.discharge_date = info["discharge_date"]
    if info.get("ward_bed") and summary.department in MISSING:
        summary.department = info["ward_bed"]

    filled = {
        "patient name":   bool(info.get("patient_name")),
        "age":            bool(info.get("age")),
        "gender":         bool(info.get("gender")),
        "admission date": bool(info.get("admission_date")),
        "discharge date": bool(info.get("discharge_date")),
    }
    summary.missing_fields = [
        mf for mf in summary.missing_fields
        if not any(k in mf.lower() and v for k, v in filled.items())
    ]
    return summary


def pdf_filename(patient_name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9 ]", "", patient_name).strip().replace(" ", "_")
    return f"{safe}_Discharge_Summary.pdf" if safe else "Discharge_Summary.pdf"


def run_agent(patient_id: str, patient_folder: str, max_steps: int):
    from core.agent import DischargeAgent
    agent = DischargeAgent()
    with st.spinner("Agent is analysing documents..."):
        summary, trace = agent.run(patient_id=patient_id, patient_folder=patient_folder, max_steps=max_steps)
    return summary, trace


# ── Tab renderers ─────────────────────────────────────────────────────────────
def render_summary_tab(summary, patient_id: str, out_dir: Path):
    import pandas as pd

    st.markdown('<div class="draft-banner">⚠️ AI-GENERATED DRAFT — NOT FOR CLINICAL USE WITHOUT CLINICIAN REVIEW</div>', unsafe_allow_html=True)

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Documents Processed", summary.total_documents_processed)
    with c2:
        st.metric("Agent Steps", summary.agent_steps_taken)
    with c3:
        st.metric("Conflicts Found", len(summary.conflicts))
    with c4:
        st.metric("Missing Fields", len(summary.missing_fields))

    # Storage info
    st.markdown(f"""
    <div class="storage-box">
        📂 <b>Files saved automatically</b><br>
        &nbsp;&nbsp;• PDFs &amp; Discharge Summary → <code>patients/{patient_id}/</code>
    </div>
    """, unsafe_allow_html=True)

    # Critical Alerts
    if summary.clinician_flags or summary.conflicts:
        st.markdown('<div class="section-header">🚨 Critical Alerts</div>', unsafe_allow_html=True)
        for flag in summary.clinician_flags:
            st.markdown(f'<div class="alert-critical">🚨 <b>CRITICAL:</b> {flag}</div>', unsafe_allow_html=True)
        for conflict in summary.conflicts:
            st.markdown(f'<div class="alert-critical">⚠️ <b>CONFLICT:</b> {conflict}</div>', unsafe_allow_html=True)

    if summary.missing_fields:
        st.markdown('<div class="section-header">⚠️ Missing Information</div>', unsafe_allow_html=True)
        for mf in summary.missing_fields:
            st.markdown(f'<div class="alert-warning">⚠️ {mf}</div>', unsafe_allow_html=True)

    st.divider()

    # Demographics
    st.markdown('<div class="section-header">👤 Patient Demographics</div>', unsafe_allow_html=True)
    demo_df = pd.DataFrame({
        "Field": ["Patient Name", "Age", "Gender", "Admission Date", "Discharge Date", "Department / Ward"],
        "Value": [summary.patient_name, summary.age, summary.gender,
                  summary.admission_date, summary.discharge_date, summary.department],
    })
    st.dataframe(demo_df, use_container_width=True, hide_index=True)

    st.divider()

    # Diagnoses
    st.markdown('<div class="section-header">📋 Diagnoses</div>', unsafe_allow_html=True)
    if summary.conflicts:
        st.markdown('<div class="alert-critical">⚠️ Diagnosis conflict detected across documents — Clinician must confirm before finalisation.</div>', unsafe_allow_html=True)
    st.markdown(f"**Principal Diagnosis:** {summary.principal_diagnosis}")
    if summary.secondary_diagnoses:
        st.markdown("**Secondary Diagnoses:**")
        for dx in summary.secondary_diagnoses:
            st.markdown(f"&nbsp;&nbsp;• {dx}")

    st.divider()

    # Hospital Course
    st.markdown('<div class="section-header">🏨 Hospital Course</div>', unsafe_allow_html=True)
    st.write(summary.hospital_course)

    st.divider()

    # Discharge Medications
    st.markdown('<div class="section-header">💊 Discharge Medications</div>', unsafe_allow_html=True)
    if summary.discharge_meds:
        med_rows = [{"#": i, "Medication": m.name, "Dose": m.dose, "Route": m.route,
                     "Frequency": m.frequency, "Duration": m.duration, "Status": m.status}
                    for i, m in enumerate(summary.discharge_meds, 1)]
        st.dataframe(pd.DataFrame(med_rows), use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="alert-warning">No discharge medications documented.</div>', unsafe_allow_html=True)

    if summary.med_changes:
        st.markdown("**Medication Changes from Admission:**")
        for change in summary.med_changes:
            st.markdown(f'<div class="alert-warning">⚠️ {change}</div>', unsafe_allow_html=True)

    st.divider()

    # Pending Results
    st.markdown('<div class="section-header">🧪 Pending Results</div>', unsafe_allow_html=True)
    if summary.pending_results:
        for pr in summary.pending_results:
            st.markdown(f'<div class="alert-warning">⏳ {pr}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ No pending results identified.</div>', unsafe_allow_html=True)

    # Procedures
    if summary.procedures:
        st.divider()
        st.markdown('<div class="section-header">⚕️ Procedures Performed</div>', unsafe_allow_html=True)
        for proc in summary.procedures:
            st.markdown(f"• {proc}")

    st.divider()

    # Follow-up & Discharge Condition
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">📅 Follow-Up Instructions</div>', unsafe_allow_html=True)
        st.write(summary.followup_instructions)
    with c2:
        st.markdown('<div class="section-header">⚕️ Discharge Condition</div>', unsafe_allow_html=True)
        st.write(summary.discharge_condition)

    st.divider()
    st.markdown(f"<span style='color:#6b7c93; font-size:0.8rem;'>Generated: {summary.generated_at}</span>", unsafe_allow_html=True)

    # Download button
    st.markdown("---")
    st.markdown("**Download Report**")
    pdf_file = out_dir / "summary.pdf"
    if pdf_file.exists():
        fname = pdf_filename(summary.patient_name)
        dl1, _ = st.columns([1, 3])
        with dl1:
            st.download_button("⬇️ Download PDF", pdf_file.read_bytes(),
                file_name=fname, mime="application/pdf", use_container_width=True)


def render_trace_tab(trace):
    ICONS = {"success": "✅", "warning": "⚠️", "conflict": "🔴", "error": "❌"}
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Steps", len(trace))
    with c2: st.metric("Warnings / Conflicts", sum(1 for s in trace if s.status in ("warning", "conflict")))
    with c3: st.metric("Errors", sum(1 for s in trace if s.status == "error"))
    st.divider()
    for step in trace:
        icon = ICONS.get(step.status, "•")
        with st.expander(f"{icon}  Step {step.step_number} — {step.action.replace('_', ' ').title()}  [{step.status.upper()}]"):
            st.markdown(f"**Reasoning:** {step.reasoning}")
            st.markdown(f"**Action:** `{step.action}`")
            st.markdown(f"**Result:** {step.result}")
            st.markdown(f"**Next:** {step.next_decision}")


def render_documents_tab(documents):
    TYPE_ICONS = {"admission": "🟦", "labs": "🟩", "nursing": "🟨", "drug_chart": "🟪",
                  "consultation": "🟫", "radiology": "⬜", "er_chart": "🟥",
                  "icu_chart": "🟧", "discharge": "🟦", "unknown": "⬛"}
    if not documents:
        st.info("No documents available.")
        return
    st.markdown(f"**{len(documents)} document(s) processed**")
    for doc in documents:
        icon = TYPE_ICONS.get(doc.doc_type, "⬛")
        with st.expander(f"{icon}  {doc.filename}  —  {doc.doc_type.replace('_', ' ').upper()}  ({doc.page_count} pages)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Document Type", doc.doc_type.replace("_", " ").title())
            c2.metric("Pages", doc.page_count)
            c3.metric("Images", len(doc.base64_images))


def welcome_screen():
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem;'>
        <div style='font-size:3.5rem;'>🏥</div>
        <h1 style='color:#1a2d4a; font-size:2rem; margin:0.3rem 0 0.2rem;'>ClinicalScribe</h1>
        <p style='color:#6b7c93; font-size:1rem; margin:0;'>AI-Powered Discharge Summary Generator</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style='background:white; border-radius:10px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,0.07); height:180px;'>
        <div style='font-size:1.8rem;'>📄</div>
        <div style='font-weight:700; color:#1a2d4a; margin:8px 0 4px;'>Upload Documents</div>
        <div style='color:#6b7c93; font-size:0.85rem;'>Upload patient PDFs — admission records, lab reports, drug charts, nursing notes</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style='background:white; border-radius:10px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,0.07); height:180px;'>
        <div style='font-size:1.8rem;'>🤖</div>
        <div style='font-weight:700; color:#1a2d4a; margin:8px 0 4px;'>AI Extraction</div>
        <div style='color:#6b7c93; font-size:0.85rem;'>Extracts demographics, diagnoses, medications, labs and procedures automatically</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style='background:white; border-radius:10px; padding:20px; box-shadow:0 1px 6px rgba(0,0,0,0.07); height:180px;'>
        <div style='font-size:1.8rem;'>📋</div>
        <div style='font-weight:700; color:#1a2d4a; margin:8px 0 4px;'>Structured Summary</div>
        <div style='color:#6b7c93; font-size:0.85rem;'>Generates a structured discharge summary PDF — ready for clinician review</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div class="alert-warning" style='text-align:center; font-size:0.88rem;'>
    ⚠️ All AI-generated output is a <b>draft only</b>. It must be reviewed and verified by a qualified clinician before clinical use.
    </div>
    """, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    from dotenv import load_dotenv
    load_dotenv()

    uploaded_files, max_steps, run_clicked, manual_info, validation_errors = sidebar()

    if not check_api_key():
        st.error("🔑 **GEMINI_API_KEY not configured.** Add it to your `.env` file:")
        st.code("GEMINI_API_KEY=your_key_here", language="bash")
        return

    if "summary" not in st.session_state:
        st.session_state.update(
            summary=None, trace=[], documents=[], patient_id=None, out_dir=None,
            generating=False, pending_files=None, pending_info=None, pending_steps=None,
        )

    # Step 1: Button clicked — save everything to session state, set generating=True, rerun
    # On the rerun the sidebar will render with all inputs disabled.
    if run_clicked and not validation_errors:
        if not uploaded_files:
            st.warning("⚠️ Please upload at least one PDF document before running the agent.")
        else:
            st.session_state.pending_files = [(f.name, f.read()) for f in uploaded_files]
            st.session_state.pending_info  = manual_info
            st.session_state.pending_steps = max_steps
            st.session_state.generating    = True
            st.rerun()

    # Step 2: After rerun with disabled UI, actually run the agent
    if st.session_state.get("generating") and st.session_state.get("pending_files"):
        st.markdown("""
        <div style='text-align:center; padding:3rem 1rem;'>
            <div style='font-size:2.8rem; margin-bottom:1rem;'>⏳</div>
            <div style='font-size:1.15rem; font-weight:700; color:#1a2d4a;'>Generating Discharge Summary…</div>
            <div style='color:#6b7c93; font-size:0.88rem; margin-top:0.5rem;'>
                Please wait — do not refresh or close this page.
            </div>
        </div>
        """, unsafe_allow_html=True)

        patient_id     = make_patient_id(st.session_state.pending_info["patient_name"])
        patient_folder = save_pending_uploads(st.session_state.pending_files, patient_id)
        try:
            summary, trace = run_agent(patient_id, patient_folder, st.session_state.pending_steps)
            summary        = apply_manual_overrides(summary, st.session_state.pending_info)
            out_dir        = save_reports(summary, trace, patient_id)

            from core.pdf_reader import PDFReader
            docs = PDFReader().load_patient_pdfs(patient_folder)

            st.session_state.update(
                summary=summary, trace=trace, documents=docs,
                patient_id=patient_id, out_dir=out_dir,
                generating=False, pending_files=None, pending_info=None, pending_steps=None,
            )
            st.success(f"✅ Summary generated in {summary.agent_steps_taken} steps and saved to `outputs/{patient_id}/`")
            st.rerun()
        except Exception as e:
            st.session_state.update(
                generating=False, pending_files=None, pending_info=None, pending_steps=None,
            )
            st.error(f"❌ Agent failed: {e}")
            st.exception(e)
        return  # Don't render tabs while generating

    if st.session_state.summary:
        tab1, tab2, tab3 = st.tabs(["📋  Discharge Summary", "🔍  Agent Trace", "📄  Documents"])
        with tab1:
            render_summary_tab(st.session_state.summary, st.session_state.patient_id, st.session_state.out_dir)
        with tab2:
            render_trace_tab(st.session_state.trace)
        with tab3:
            render_documents_tab(st.session_state.documents)
    else:
        welcome_screen()


if __name__ == "__main__":
    main()
