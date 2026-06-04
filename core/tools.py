import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

INTERACTIONS_DB = {
    ("meropenem", "valproate"): {
        "severity": "severe",
        "message": "Meropenem significantly reduces valproate levels, risking seizure breakthrough.",
        "action_required": True,
    },
    ("metformin", "contrast"): {
        "severity": "moderate",
        "message": "Contrast media can cause acute kidney injury, increasing metformin-associated lactic acidosis risk.",
        "action_required": True,
    },
    ("warfarin", "aspirin"): {
        "severity": "moderate",
        "message": "Concomitant use increases bleeding risk significantly.",
        "action_required": True,
    },
}


class Tools:
    def drug_interaction_checker(self, med1: str, med2: str) -> Dict:
        logger.info(f"[TOOL] drug_interaction_checker: {med1} + {med2}")
        key1 = (med1.lower(), med2.lower())
        key2 = (med2.lower(), med1.lower())
        hit = INTERACTIONS_DB.get(key1) or INTERACTIONS_DB.get(key2)
        if hit:
            return {
                "interaction_found": True,
                "severity": hit["severity"],
                "message": hit["message"],
                "action_required": hit["action_required"],
            }
        return {
            "interaction_found": False,
            "severity": "none",
            "message": f"No known interaction between {med1} and {med2}.",
            "action_required": False,
        }

    def flag_for_clinician(self, reason: str, severity: str = "warning") -> Dict:
        logger.info(f"[TOOL] flag_for_clinician [{severity}]: {reason}")
        return {
            "flagged": True,
            "reason": reason,
            "severity": severity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "REQUIRES CLINICIAN REVIEW BEFORE FINALIZATION",
        }

    def check_pending_results(self, lab_name: str, result_text: str) -> Dict:
        logger.info(f"[TOOL] check_pending_results: {lab_name}")
        pending_keywords = ["awaited", "pending", "due", "sent to lab"]
        is_pending = any(kw in result_text.lower() for kw in pending_keywords)
        return {
            "lab_name": lab_name,
            "status": "pending" if is_pending else "resulted",
            "message": f"{lab_name} is {'still pending' if is_pending else 'resulted'}.",
        }

    def validate_medication_documented(self, med: Dict) -> Dict:
        logger.info(f"[TOOL] validate_medication_documented: {med.get('name', 'unknown')}")
        required = ["dose", "route", "frequency"]
        missing = [f for f in required if not med.get(f) or med.get(f) == "NOT_DOCUMENTED"]
        return {
            "valid": len(missing) == 0,
            "missing_fields": missing,
            "flag": f"Incomplete medication documentation — missing: {', '.join(missing)}" if missing else "",
        }
