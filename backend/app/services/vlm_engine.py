"""VLM engine — semantic field extraction.

Primary: Groq API with llama-3.2-90b-vision-preview (or Qwen2-VL endpoint).
Fallback: Together AI. When no API key is configured, returns {} so the
compliance engine relies on OCR fields (still functional for demos).
"""
import base64
import json
import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.services.datatypes import ExtractedFields

logger = logging.getLogger(__name__)
settings = get_settings()

EXTRACTION_PROMPT = """\
You are a compliance checker for Indian packaged commodities under the Legal\
 Metrology (Packaged Commodities) Rules, 2011.
Extract the following fields from this product label image.
Return ONLY a valid JSON object with these exact keys.
If a field is not present, use null.

- manufacturer_name: string
- manufacturer_address: string
- product_name: string
- net_quantity: string (include unit, e.g., "150g", "500ml")
- mrp: string (full declaration as seen)
- manufacture_date: string (as printed)
- expiry_date: string (as printed, null if not required)
- consumer_care: string (contact phone/email/website)
- country_of_origin: string (null if not imported)
- fssai_license: string (for food products)
- batch_number: string
"""


class VLMEngine:
    async def extract_fields(self, image_bytes: bytes) -> dict:
        """Extract structured fields from a label image."""
        if settings.GROQ_API_KEY:
            data = await self._call_groq(image_bytes)
        elif settings.TOGETHER_API_KEY:
            data = await self._call_together(image_bytes)
        else:
            data = {}
        return self._parse_json_response(data)

    async def _call_groq(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{b64}"
                                    },
                                },
                                {"type": "text", "text": EXTRACTION_PROMPT},
                            ],
                        }
                    ],
                    "temperature": 0,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def _call_together(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": (
                        "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo"
                    ),
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": (
                                        f"data:image/jpeg;base64,{b64}"
                                    )},
                                },
                                {"type": "text", "text": EXTRACTION_PROMPT},
                            ],
                        }
                    ],
                    "temperature": 0,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json_response(response: str) -> dict:
        if not response:
            return {}
        text = response.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # find first { ... } block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
        logger.warning("Failed to parse VLM JSON response")
        return {}
