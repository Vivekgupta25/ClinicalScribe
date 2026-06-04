import json
import logging
import os
import re
import time
from typing import List, Union

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a clinical data extraction AI for a hospital discharge summary system.

Rules you must follow strictly:
- Extract ONLY information that is explicitly written in the document. Never invent, guess, or hallucinate.
- If a field is not present in the document, return "NOT_FOUND" for that field.
- Always return valid JSON only — no markdown, no code fences (```), no explanations, no extra text.
- Be conservative: if you are unsure about a value, return "NOT_FOUND" rather than guessing.
- Preserve exact values as written (e.g., dates, drug names, dosages) without reformatting."""


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_INSTRUCTION,
        )

    def call_gemini(self, prompt: str, base64_images: List[str] = None) -> str:
        try:
            parts = [{"text": prompt}]
            if base64_images:
                for b64 in base64_images:
                    parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
            response = self.model.generate_content(parts)
            text = response.text.strip()
            logger.debug(f"Gemini raw response (first 300 chars): {text[:300]}")
            return text
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return ""

    def call_with_retry(self, prompt: str, base64_images: List[str] = None, max_retries: int = 3) -> str:
        for attempt in range(1, max_retries + 1):
            result = self.call_gemini(prompt, base64_images)
            if result:
                return result
            logger.warning(f"Gemini retry {attempt}/{max_retries}")
            time.sleep(2)
        logger.error("All Gemini retries exhausted")
        return "EXTRACTION_FAILED"

    def extract_json_from_response(self, response: str) -> Union[dict, list]:
        if not response or response == "EXTRACTION_FAILED":
            logger.warning("Empty or failed response — returning empty dict")
            return {}

        # Try 1: strip markdown code fences and parse
        try:
            cleaned = re.sub(r"```(?:json)?\s*", "", response).replace("```", "").strip()
            return json.loads(cleaned)
        except Exception:
            pass

        # Try 2: parse raw response directly
        try:
            return json.loads(response)
        except Exception:
            pass

        # Try 3: find JSON object {...} anywhere in the text
        try:
            match = re.search(r"\{[\s\S]*\}", response)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        # Try 4: find JSON array [...] anywhere in the text
        try:
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        logger.warning(f"JSON extraction failed. Response snippet: {response[:200]}")
        return {}
