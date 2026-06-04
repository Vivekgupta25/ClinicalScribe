import base64
import logging
import os
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from models.agent_state import ExtractedDoc

logger = logging.getLogger(__name__)


class PDFReader:
    def pdf_to_base64_images(self, pdf_path: str) -> List[str]:
        try:
            doc = fitz.open(pdf_path)
            images = []
            for page in doc:
                mat = fitz.Matrix(2, 2)  # 2x zoom
                pix = page.get_pixmap(matrix=mat)
                png_bytes = pix.tobytes("png")
                b64 = base64.b64encode(png_bytes).decode("utf-8")
                images.append(b64)
            doc.close()
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF {pdf_path} to images: {e}")
            return []

    def classify_document(self, filename: str) -> str:
        name = filename.lower()
        if any(k in name for k in ["admission", "case_record", "case record"]):
            return "admission"
        if any(k in name for k in ["lab", "investigation", "pathology", "biochemistry", "haematology"]):
            return "labs"
        if any(k in name for k in ["nursing", "nurse", "nsg"]):
            return "nursing"
        if any(k in name for k in ["drug", "medication", "chart"]):
            return "drug_chart"
        if any(k in name for k in ["consultation", "consult"]):
            return "consultation"
        if any(k in name for k in ["usg", "ct", "xray", "echo", "radiology"]):
            return "radiology"
        if any(k in name for k in ["er", "emergency", "casualty"]):
            return "er_chart"
        if any(k in name for k in ["icu", "hdu", "icu_chart"]):
            return "icu_chart"
        if any(k in name for k in ["discharge", "summary"]):
            return "discharge"
        return "unknown"

    def load_patient_pdfs(self, patient_folder: str) -> List[ExtractedDoc]:
        folder = Path(patient_folder)
        if not folder.exists():
            logger.error(f"Patient folder not found: {patient_folder}")
            return []

        docs = []
        pdf_files = sorted(folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {patient_folder}")
            return []

        for pdf_path in pdf_files:
            try:
                images = self.pdf_to_base64_images(str(pdf_path))
                doc_type = self.classify_document(pdf_path.name)
                extracted = ExtractedDoc(
                    filename=pdf_path.name,
                    doc_type=doc_type,
                    base64_images=images,
                    page_count=len(images),
                )
                docs.append(extracted)
                logger.info(f"Loaded {pdf_path.name} ({doc_type}, {len(images)} pages)")
            except Exception as e:
                logger.error(f"Failed to load {pdf_path.name}: {e}")

        return docs
