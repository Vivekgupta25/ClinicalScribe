import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import argparse
from core.agent import DischargeAgent
from core.summary_generator import SummaryGenerator


def main():
    parser = argparse.ArgumentParser(description="ClinicalScribe — AI Discharge Summary Generator")
    parser.add_argument("--patient", required=True, help="Path to patient folder containing PDFs")
    parser.add_argument("--max-steps", default=20, type=int, help="Maximum agent steps (default: 20)")
    args = parser.parse_args()

    patient_folder = Path(args.patient)
    patient_id = patient_folder.name

    print(f"\nClinicalScribe Starting...")
    print(f"Patient folder: {args.patient}")
    print("-" * 40)

    agent = DischargeAgent()
    summary, trace = agent.run(
        patient_id=patient_id,
        patient_folder=str(patient_folder),
        max_steps=args.max_steps,
    )

    gen = SummaryGenerator()
    (patient_folder / "summary.pdf").write_bytes(gen.generate_pdf(summary, patient_id))
    (patient_folder / "trace.txt").write_text(gen.generate_trace_log(trace, patient_id), encoding="utf-8")

    print(f"\nDone!")
    print(f"Summary PDF: {patient_folder}/summary.pdf")
    print(f"Trace:       {patient_folder}/trace.txt")
    print(f"\nSteps taken:     {summary.agent_steps_taken}")
    print(f"Documents:       {summary.total_documents_processed}")
    print(f"Conflicts:       {len(summary.conflicts)}")
    print(f"Missing fields:  {len(summary.missing_fields)}")


if __name__ == "__main__":
    main()
