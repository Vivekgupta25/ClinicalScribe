import json
import logging
from typing import List, Tuple

from models.agent_state import AgentState, ExtractedDoc, TraceStep
from models.discharge_summary import DischargeSummary
from models.medication import Medication
from prompts.extract_prompts import (
    CONFLICT_CHECK_PROMPT,
    DEMOGRAPHICS_PROMPT,
    DIAGNOSIS_PROMPT,
    HOSPITAL_COURSE_PROMPT,
    LAB_PROMPT,
    MEDICATION_PROMPT,
    PROCEDURES_PROMPT,
)

from .gemini_client import GeminiClient
from .pdf_reader import PDFReader
from .tools import Tools

logger = logging.getLogger(__name__)

REASONING_MAP = {
    "load_documents": "No documents loaded yet — must load PDFs before any extraction.",
    "extract_demographics": "Documents loaded — starting with patient demographics extraction.",
    "extract_diagnoses": "Demographics done — extracting diagnoses from all documents.",
    "check_diagnosis_conflicts": "Diagnoses extracted — checking for conflicts across documents.",
    "extract_labs": "Diagnosis conflicts checked — extracting laboratory results.",
    "extract_medications": "Labs done — extracting medications from drug charts and summaries.",
    "reconcile_medications": "Medications extracted — reconciling admission vs discharge medications.",
    "check_drug_interactions": "Medications reconciled — checking for drug interactions.",
    "extract_procedures": "Drug interactions checked — extracting procedures performed.",
    "extract_hospital_course": "Procedures done — summarizing hospital course from nursing and consultation notes.",
    "check_pending_results": "Hospital course done — checking for any pending investigation results.",
    "flag_missing_fields": "Pending results checked — flagging all missing required fields.",
    "generate_summary": "All extractions complete — generating final discharge summary.",
    "complete": "Summary generated — marking agent as complete.",
}


class DischargeAgent:
    def __init__(self):
        self.gemini = GeminiClient()
        self.tools = Tools()
        self.state: AgentState = None
        self.patient_folder: str = ""

    def run(self, patient_id: str, patient_folder: str, max_steps: int = 20) -> Tuple[DischargeSummary, List[TraceStep]]:
        self.patient_folder = patient_folder
        self.state = AgentState(patient_id=patient_id, max_steps=max_steps)
        logger.info(f"Agent starting for patient: {patient_id}")
        self._agent_loop()
        summary = self.state.findings.get("summary", DischargeSummary())
        return summary, self.state.trace

    def _agent_loop(self) -> None:
        while not self.state.is_complete and self.state.steps_taken < self.state.max_steps:
            action = self._decide_next_action()
            reasoning = REASONING_MAP.get(action, f"Proceeding with {action}.")
            self.state.current_action = action
            logger.info(f"[Step {self.state.steps_taken + 1}] Action: {action}")

            result = self._execute_action(action)
            self._log_trace_step(action, reasoning, result)
            self._update_state(action, result)
            self.state.steps_taken += 1

    def _decide_next_action(self) -> str:
        f = self.state.findings
        if not self.state.documents:
            return "load_documents"
        if "demographics" not in f:
            return "extract_demographics"
        if "diagnoses_by_doc" not in f:
            return "extract_diagnoses"
        if "conflict_analysis" not in f:
            return "check_diagnosis_conflicts"
        if "labs" not in f:
            return "extract_labs"
        if "medications" not in f:
            return "extract_medications"
        if "med_changes" not in f:
            return "reconcile_medications"
        if "drug_interactions" not in f:
            return "check_drug_interactions"
        if "procedures" not in f:
            return "extract_procedures"
        if "hospital_course" not in f:
            return "extract_hospital_course"
        if "pending_results" not in f:
            return "check_pending_results"
        if "missing_fields_checked" not in f:
            return "flag_missing_fields"
        if "summary" not in f:
            return "generate_summary"
        return "complete"

    def _execute_action(self, action: str) -> dict:
        try:
            dispatch = {
                "load_documents": self._do_load_documents,
                "extract_demographics": self._do_extract_demographics,
                "extract_diagnoses": self._do_extract_diagnoses,
                "check_diagnosis_conflicts": self._do_check_diagnosis_conflicts,
                "extract_labs": self._do_extract_labs,
                "extract_medications": self._do_extract_medications,
                "reconcile_medications": self._do_reconcile_medications,
                "check_drug_interactions": self._do_check_drug_interactions,
                "extract_procedures": self._do_extract_procedures,
                "extract_hospital_course": self._do_extract_hospital_course,
                "check_pending_results": self._do_check_pending_results,
                "flag_missing_fields": self._do_flag_missing_fields,
                "generate_summary": self._do_generate_summary,
                "complete": self._do_complete,
            }
            handler = dispatch.get(action)
            if not handler:
                return {"success": False, "error": f"Unknown action: {action}"}
            return handler()
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {"success": False, "error": str(e), "message": f"Action {action} encountered an error."}

    def _get_images_for_doc_types(self, *doc_types) -> List[str]:
        images = []
        for doc in self.state.documents:
            if doc.doc_type in doc_types:
                images.extend(doc.base64_images)
        return images

    def _do_load_documents(self) -> dict:
        reader = PDFReader()
        docs = reader.load_patient_pdfs(self.patient_folder)
        self.state.documents = docs
        return {
            "success": True,
            "data": {"count": len(docs)},
            "message": f"Loaded {len(docs)} documents.",
        }

    def _do_extract_demographics(self) -> dict:
        merged = {}
        for doc in self.state.documents:
            if not doc.base64_images:
                continue
            response = self.gemini.call_with_retry(DEMOGRAPHICS_PROMPT, doc.base64_images[:3])
            parsed = self.gemini.extract_json_from_response(response)
            if not isinstance(parsed, dict):
                continue
            for k, v in parsed.items():
                if k not in merged or merged.get(k) in ("NOT_FOUND", "", None):
                    if v and v != "NOT_FOUND":
                        merged[k] = v
        self.state.findings["demographics"] = merged
        return {"success": True, "data": merged, "message": f"Extracted {len(merged)} demographic fields."}

    def _do_extract_diagnoses(self) -> dict:
        diagnoses_by_doc = {}
        for doc in self.state.documents:
            if not doc.base64_images:
                continue
            response = self.gemini.call_with_retry(DIAGNOSIS_PROMPT, doc.base64_images[:3])
            parsed = self.gemini.extract_json_from_response(response)
            if parsed and parsed.get("diagnoses_found"):
                diagnoses_by_doc[doc.filename] = parsed
        self.state.findings["diagnoses_by_doc"] = diagnoses_by_doc
        total = sum(len(v.get("diagnoses_found", [])) for v in diagnoses_by_doc.values())
        return {"success": True, "data": diagnoses_by_doc, "message": f"Found diagnoses in {len(diagnoses_by_doc)} documents ({total} total)."}

    def _do_check_diagnosis_conflicts(self) -> dict:
        diagnoses_by_doc = self.state.findings.get("diagnoses_by_doc", {})
        if not diagnoses_by_doc:
            self.state.findings["conflict_analysis"] = {}
            return {"success": True, "data": {}, "message": "No diagnoses to check conflicts for."}

        summary_text = json.dumps(
            {k: v.get("diagnoses_found", []) for k, v in diagnoses_by_doc.items()},
            indent=2,
        )
        prompt = CONFLICT_CHECK_PROMPT.format(diagnoses_by_doc=summary_text)
        response = self.gemini.call_with_retry(prompt)
        analysis = self.gemini.extract_json_from_response(response)

        self.state.findings["conflict_analysis"] = analysis

        if analysis.get("conflicts_found"):
            for conflict in analysis.get("conflict_details", []):
                self.state.conflicts.append(conflict)
            flag = self.tools.flag_for_clinician("Diagnosis conflict detected across documents", "critical")
            self.state.clinician_flags.append(flag["reason"])

        return {
            "success": True,
            "data": analysis,
            "message": f"Conflict check done. Conflicts found: {analysis.get('conflicts_found', False)}",
        }

    def _do_extract_labs(self) -> dict:
        images = self._get_images_for_doc_types("labs")
        if not images:
            for doc in self.state.documents:
                images.extend(doc.base64_images[:2])
                if len(images) >= 10:
                    break

        all_labs = []
        if images:
            response = self.gemini.call_with_retry(LAB_PROMPT, images[:8])
            parsed = self.gemini.extract_json_from_response(response)
            if isinstance(parsed, list):
                all_labs = parsed

        self.state.findings["labs"] = all_labs
        return {"success": True, "data": all_labs, "message": f"Extracted {len(all_labs)} lab results."}

    def _do_extract_medications(self) -> dict:
        images = self._get_images_for_doc_types("drug_chart", "discharge", "admission")
        if not images:
            images = self._get_images_for_doc_types(*[d.doc_type for d in self.state.documents])

        all_meds = []
        if images:
            response = self.gemini.call_with_retry(MEDICATION_PROMPT, images[:8])
            parsed = self.gemini.extract_json_from_response(response)
            if isinstance(parsed, list):
                all_meds = parsed

        self.state.findings["medications"] = all_meds
        return {"success": True, "data": all_meds, "message": f"Extracted {len(all_meds)} medications."}

    def _do_reconcile_medications(self) -> dict:
        meds = self.state.findings.get("medications", [])
        admission_meds = [m for m in meds if m.get("is_admission_med")]
        discharge_meds = [m for m in meds if m.get("is_discharge_med")]
        changes = []

        admission_names = {m.get("name", "").lower() for m in admission_meds}
        discharge_names = {m.get("name", "").lower() for m in discharge_meds}

        for name in discharge_names - admission_names:
            changes.append(f"NEW medication on discharge: {name} — reason NOT documented ⚠️")
            self.tools.flag_for_clinician(f"New medication {name} added without documented reason", "warning")

        for name in admission_names - discharge_names:
            changes.append(f"STOPPED on discharge: {name} — reason NOT documented ⚠️")
            self.tools.flag_for_clinician(f"Medication {name} stopped without documented reason", "warning")

        for med in meds:
            validation = self.tools.validate_medication_documented(med)
            if not validation["valid"]:
                self.state.clinician_flags.append(validation["flag"])

        self.state.findings["med_changes"] = changes
        self.state.findings["admission_meds"] = admission_meds
        self.state.findings["discharge_meds"] = discharge_meds
        return {"success": True, "data": changes, "message": f"{len(changes)} medication changes identified."}

    def _do_check_drug_interactions(self) -> dict:
        discharge_meds = self.state.findings.get("discharge_meds", [])
        interactions = []
        names = [m.get("name", "") for m in discharge_meds if m.get("name")]

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                result = self.tools.drug_interaction_checker(names[i], names[j])
                if result["interaction_found"] and result["severity"] in ("moderate", "severe"):
                    interactions.append(result)
                    flag = self.tools.flag_for_clinician(
                        f"Drug interaction: {names[i]} + {names[j]} — {result['message']}",
                        "critical" if result["severity"] == "severe" else "warning",
                    )
                    self.state.clinician_flags.append(flag["reason"])

        self.state.findings["drug_interactions"] = interactions
        return {"success": True, "data": interactions, "message": f"{len(interactions)} drug interactions found."}

    def _do_extract_procedures(self) -> dict:
        images = self._get_images_for_doc_types("nursing", "consultation", "admission")
        all_procs = []
        if images:
            response = self.gemini.call_with_retry(PROCEDURES_PROMPT, images[:8])
            parsed = self.gemini.extract_json_from_response(response)
            if isinstance(parsed, list):
                all_procs = parsed

        self.state.findings["procedures"] = all_procs
        return {"success": True, "data": all_procs, "message": f"Extracted {len(all_procs)} procedures."}

    def _do_extract_hospital_course(self) -> dict:
        relevant_docs = [d for d in self.state.documents if d.doc_type in ("nursing", "consultation")]
        if not relevant_docs:
            relevant_docs = self.state.documents[:3]

        content_parts = []
        for doc in relevant_docs[:4]:
            content_parts.append(f"Document: {doc.filename} ({doc.doc_type})")

        documents_content = "\n".join(content_parts) if content_parts else "No nursing or consultation notes available."
        prompt = HOSPITAL_COURSE_PROMPT.format(documents_content=documents_content)

        images = []
        for doc in relevant_docs[:4]:
            images.extend(doc.base64_images[:2])

        response = self.gemini.call_with_retry(prompt, images[:8] if images else None)
        parsed = self.gemini.extract_json_from_response(response)

        self.state.findings["hospital_course"] = parsed
        return {
            "success": True,
            "data": parsed,
            "message": f"Hospital course extracted from {len(relevant_docs)} documents.",
        }

    def _do_check_pending_results(self) -> dict:
        labs = self.state.findings.get("labs", [])
        pending = []
        for lab in labs:
            check = self.tools.check_pending_results(
                lab.get("test_name", "Unknown"),
                lab.get("value", "") + " " + lab.get("status", ""),
            )
            if check["status"] == "pending":
                pending.append(check["message"])

        self.state.findings["pending_results"] = pending
        return {"success": True, "data": pending, "message": f"{len(pending)} pending results identified."}

    def _do_flag_missing_fields(self) -> dict:
        demo = self.state.findings.get("demographics", {})
        required_demo = ["patient_name", "age", "gender", "ip_number", "admission_date", "discharge_date"]
        missing = []

        for field in required_demo:
            val = demo.get(field, "")
            if not val or val in ("NOT_FOUND", "MISSING", ""):
                missing.append(f"Patient {field.replace('_', ' ')} not found in any document")

        if not self.state.findings.get("diagnoses_by_doc"):
            missing.append("Principal diagnosis not found")

        meds = self.state.findings.get("medications", [])
        if not any(m.get("is_discharge_med") for m in meds):
            missing.append("Discharge medications not documented")

        if not any(m.get("is_admission_med") for m in meds):
            missing.append("Admission medications not documented")

        hospital_course = self.state.findings.get("hospital_course", {})
        if not hospital_course or not hospital_course.get("hospital_course"):
            missing.append("Hospital course summary unavailable")

        self.state.missing_fields.extend(missing)
        self.state.findings["missing_fields_checked"] = True
        return {"success": True, "data": missing, "message": f"{len(missing)} missing fields identified."}

    def _do_generate_summary(self) -> dict:
        demo = self.state.findings.get("demographics", {})
        meds = self.state.findings.get("medications", [])
        labs = self.state.findings.get("labs", [])
        procs = self.state.findings.get("procedures", [])
        hospital_course_data = self.state.findings.get("hospital_course", {})
        conflict_analysis = self.state.findings.get("conflict_analysis", {})
        med_changes = self.state.findings.get("med_changes", [])

        all_diagnoses = []
        for doc_data in self.state.findings.get("diagnoses_by_doc", {}).values():
            all_diagnoses.extend(doc_data.get("diagnoses_found", []))
        unique_diagnoses = list(dict.fromkeys(all_diagnoses))

        def build_med(m: dict) -> Medication:
            return Medication(
                name=m.get("name", "Unknown"),
                dose=m.get("dose", "NOT_DOCUMENTED"),
                route=m.get("route", "NOT_DOCUMENTED"),
                frequency=m.get("frequency", "NOT_DOCUMENTED"),
                duration=m.get("duration", "NOT_DOCUMENTED"),
                status="unknown",
            )

        admission_meds = [build_med(m) for m in meds if m.get("is_admission_med")]
        discharge_meds = [build_med(m) for m in meds if m.get("is_discharge_med")]
        if not discharge_meds:
            discharge_meds = [build_med(m) for m in meds]

        pending_results = self.state.findings.get("pending_results", [])

        summary = DischargeSummary(
            patient_name=demo.get("patient_name", "MISSING ⚠️") or "MISSING ⚠️",
            age=demo.get("age", "MISSING ⚠️") or "MISSING ⚠️",
            gender=demo.get("gender", "MISSING ⚠️") or "MISSING ⚠️",
            ip_number=demo.get("ip_number", "MISSING ⚠️") or "MISSING ⚠️",
            admission_date=demo.get("admission_date", "MISSING ⚠️") or "MISSING ⚠️",
            discharge_date=demo.get("discharge_date", "MISSING ⚠️") or "MISSING ⚠️",
            department=demo.get("department", "MISSING ⚠️") or "MISSING ⚠️",
            principal_diagnosis=unique_diagnoses[0] if unique_diagnoses else "MISSING ⚠️",
            secondary_diagnoses=unique_diagnoses[1:] if len(unique_diagnoses) > 1 else [],
            hospital_course=hospital_course_data.get("hospital_course", "MISSING ⚠️") if hospital_course_data else "MISSING ⚠️",
            procedures=[p.get("procedure_name", "") for p in procs if p.get("procedure_name")],
            admission_meds=admission_meds,
            discharge_meds=discharge_meds,
            med_changes=med_changes,
            pending_results=pending_results,
            conflicts=list(self.state.conflicts),
            missing_fields=list(self.state.missing_fields),
            clinician_flags=list(self.state.clinician_flags),
            total_documents_processed=len(self.state.documents),
            agent_steps_taken=self.state.steps_taken + 1,
        )

        self.state.findings["summary"] = summary
        return {"success": True, "data": "Summary generated", "message": "Discharge summary built successfully."}

    def _do_complete(self) -> dict:
        self.state.is_complete = True
        return {"success": True, "data": {}, "message": "Agent completed all steps."}

    def _log_trace_step(self, action: str, reasoning: str, result: dict) -> None:
        if result.get("success"):
            if self.state.conflicts:
                status = "conflict"
            elif self.state.missing_fields:
                status = "warning"
            else:
                status = "success"
        else:
            status = "error"

        next_action = self._decide_next_action() if not self.state.is_complete else "complete"

        step = TraceStep(
            step_number=self.state.steps_taken + 1,
            reasoning=reasoning,
            action=action,
            inputs={"patient_id": self.state.patient_id, "docs_loaded": len(self.state.documents)},
            result=result.get("message", str(result)),
            next_decision=f"Next: {next_action}",
            status=status,
        )
        self.state.trace.append(step)

    def _update_state(self, action: str, result: dict) -> None:
        if action == "complete":
            self.state.is_complete = True
