import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.agent_state import TraceStep
from models.discharge_summary import DischargeSummary

STATUS_ICONS = {
    "success": "✅",
    "warning": "⚠️",
    "conflict": "🔴",
    "error": "❌",
}

# Color palette
_RED = colors.HexColor("#E84855")
_BLUE = colors.HexColor("#2E86AB")
_LIGHT_RED = colors.HexColor("#fde8ea")
_LIGHT_ORANGE = colors.HexColor("#fff3e0")
_GREY = colors.HexColor("#555555")
_TABLE_HEADER = colors.HexColor("#2E86AB")
_TABLE_ROW_ALT = colors.HexColor("#f0f7fb")


class SummaryGenerator:
    def generate_trace_log(self, trace: List[TraceStep], patient_id: str) -> str:
        lines = []
        lines.append(f"AGENT TRACE LOG — Patient: {patient_id}")
        lines.append("=" * 48)
        lines.append("")

        for step in trace:
            icon = STATUS_ICONS.get(step.status, "•")
            lines.append(f"Step {step.step_number} [{step.status.upper()}] {icon}")
            lines.append(f"Reasoning: {step.reasoning}")
            lines.append(f"Action: {step.action}")
            lines.append(f"Inputs: {step.inputs}")
            lines.append(f"Result: {step.result}")
            lines.append(f"Next Decision: {step.next_decision}")
            lines.append("-" * 48)
            lines.append("")

        return "\n".join(lines)

    def generate_pdf(self, summary: DischargeSummary, patient_id: str) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=_BLUE, fontSize=16, spaceAfter=4)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=_BLUE, fontSize=12, spaceBefore=10, spaceAfter=4)
        normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=9, leading=13)
        bold = ParagraphStyle("bold", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold")

        def hr():
            return HRFlowable(width="100%", thickness=0.5, color=_GREY, spaceAfter=6, spaceBefore=6)

        def section_table(data, col_widths, header=True):
            t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
            style = [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, _TABLE_ROW_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            if header:
                style += [
                    ("BACKGROUND", (0, 0), (-1, 0), _TABLE_HEADER),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            t.setStyle(TableStyle(style))
            return t

        def alert_row(text, bg, text_color=colors.black):
            t = Table([[Paragraph(text, ParagraphStyle("a", parent=normal, textColor=text_color, fontSize=8))]], colWidths=[175 * mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, _GREY),
            ]))
            return t

        def _m(val: str) -> str:
            if not val or "MISSING" in str(val):
                return ""
            return val

        elems = []

        # Draft banner
        banner_data = [[Paragraph(
            "<b>THIS IS AN AI-GENERATED DRAFT — NOT FOR CLINICAL USE WITHOUT CLINICIAN REVIEW</b>",
            ParagraphStyle("banner", parent=normal, textColor=colors.white, alignment=TA_CENTER, fontSize=9),
        )]]
        banner = Table(banner_data, colWidths=[175 * mm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _RED),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elems.append(banner)
        elems.append(Spacer(1, 6))

        # Title
        elems.append(Paragraph("DISCHARGE SUMMARY", h1))
        elems.append(hr())

        # Alerts
        has_alerts = summary.clinician_flags or summary.conflicts or summary.missing_fields
        if has_alerts:
            elems.append(Paragraph("ALERTS &amp; FLAGS", h2))
            for flag in summary.clinician_flags:
                elems.append(alert_row(f"CRITICAL: {flag}", _LIGHT_RED, colors.HexColor("#c0392b")))
                elems.append(Spacer(1, 3))
            for conflict in summary.conflicts:
                elems.append(alert_row(f"CONFLICT: {conflict}", _LIGHT_RED, colors.HexColor("#c0392b")))
                elems.append(Spacer(1, 3))
            for mf in summary.missing_fields:
                elems.append(alert_row(f"MISSING: {mf}", _LIGHT_ORANGE, colors.HexColor("#d35400")))
                elems.append(Spacer(1, 3))
            elems.append(hr())

        # Demographics
        elems.append(Paragraph("PATIENT DEMOGRAPHICS", h2))
        demo_data = [
            ["Field", "Value", "Field", "Value"],
            ["Patient Name", _m(summary.patient_name), "IP Number", _m(summary.ip_number)],
            ["Age", _m(summary.age), "Admission Date", _m(summary.admission_date)],
            ["Gender", _m(summary.gender), "Discharge Date", _m(summary.discharge_date)],
            ["Department", _m(summary.department), "", ""],
        ]
        elems.append(section_table(demo_data, [38 * mm, 50 * mm, 38 * mm, 50 * mm]))
        elems.append(hr())

        # Diagnoses
        elems.append(Paragraph("DIAGNOSES", h2))
        if summary.conflicts:
            elems.append(alert_row("CONFLICT DETECTED — Multiple diagnoses found across documents. Clinician must confirm.", _LIGHT_RED, colors.HexColor("#c0392b")))
            elems.append(Spacer(1, 4))
        elems.append(Paragraph(f"<b>Principal Diagnosis:</b> {_m(summary.principal_diagnosis)}", normal))
        if summary.secondary_diagnoses:
            elems.append(Spacer(1, 3))
            elems.append(Paragraph("<b>Secondary Diagnoses:</b>", bold))
            for dx in summary.secondary_diagnoses:
                elems.append(Paragraph(f"&nbsp;&nbsp;&bull; {dx}", normal))
        elems.append(hr())

        # Hospital Course
        elems.append(Paragraph("HOSPITAL COURSE", h2))
        elems.append(Paragraph(_m(summary.hospital_course).replace("\n", "<br/>"), normal))
        elems.append(hr())

        # Procedures
        if summary.procedures:
            elems.append(Paragraph("PROCEDURES PERFORMED", h2))
            for proc in summary.procedures:
                elems.append(Paragraph(f"&bull; {proc}", normal))
            elems.append(hr())

        # Discharge Medications
        elems.append(Paragraph("DISCHARGE MEDICATIONS", h2))
        if summary.discharge_meds:
            med_data = [["#", "Medication", "Dose", "Route", "Frequency", "Duration", "Status"]]
            for i, med in enumerate(summary.discharge_meds, 1):
                med_data.append([str(i), med.name, med.dose, med.route, med.frequency, med.duration, med.status])
            elems.append(section_table(med_data, [8 * mm, 38 * mm, 25 * mm, 20 * mm, 25 * mm, 25 * mm, 20 * mm]))
        else:
            elems.append(Paragraph("No discharge medications documented.", normal))

        if summary.med_changes:
            elems.append(Spacer(1, 5))
            elems.append(Paragraph("<b>Medication Changes from Admission:</b>", bold))
            for change in summary.med_changes:
                elems.append(alert_row(change, _LIGHT_ORANGE, colors.HexColor("#d35400")))
                elems.append(Spacer(1, 2))
        elems.append(hr())

        # Pending Results
        elems.append(Paragraph("PENDING RESULTS", h2))
        if summary.pending_results:
            for pr in summary.pending_results:
                elems.append(alert_row(f"PENDING: {pr}", _LIGHT_ORANGE, colors.HexColor("#d35400")))
                elems.append(Spacer(1, 2))
        else:
            elems.append(Paragraph("No pending results identified.", normal))
        elems.append(hr())

        # Allergies & Follow-up
        elems.append(Paragraph("ALLERGIES", h2))
        elems.append(Paragraph(summary.allergies, normal))
        elems.append(Spacer(1, 4))
        elems.append(Paragraph("FOLLOW-UP INSTRUCTIONS", h2))
        elems.append(Paragraph(_m(summary.followup_instructions), normal))
        elems.append(Spacer(1, 4))
        elems.append(Paragraph("DISCHARGE CONDITION", h2))
        elems.append(Paragraph(_m(summary.discharge_condition), normal))
        elems.append(hr())

        doc.build(elems)
        return buffer.getvalue()

