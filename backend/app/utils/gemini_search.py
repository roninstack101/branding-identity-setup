"""
Gemini utility – uses Google Gemini with Search Grounding.
Used by market_research and competitor_analysis agents for real-time web data.
"""
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))


def _extract_json(text: str) -> str:
    """
    Extract the first valid top-level JSON object from Gemini's response.
    Handles: markdown fences, leading/trailing prose, search grounding citations.
    """
    text = text.strip()

    # 1. Explicit markdown fence (```json ... ``` or ``` ... ```)
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence:
        candidate = fence.group(1).strip()
        try:
            import json; json.loads(candidate)
            return candidate
        except Exception:
            pass

    # 2. Find the outermost { ... } by tracking brace depth
    start = text.find("{")
    if start == -1:
        return "{}"
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return "{}"


async def call_gemini_with_search(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
) -> str:
    """
    Call Gemini with Google Search grounding enabled.
    Returns a raw string (JSON or text) from the model.
    Falls back to '{}' if the API key is missing or the call fails.
    """
    if not os.getenv("GEMINI_API_KEY", "").strip():
        print("[Gemini] Warning: GEMINI_API_KEY not set, returning empty fallback.")
        return "{}"

    try:
        client = _get_client()
        response = await client.aio.models.generate_content(
            model=_GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=temperature,
            ),
        )
        raw = response.text or "{}"
        extracted = _extract_json(raw)
        # Validate — if extraction failed, log first 500 chars of raw response
        try:
            import json as _json; _json.loads(extracted)
        except Exception:
            print(f"[Gemini] JSON parse failed. Raw response (first 500 chars):\n{raw[:500]}")
            return "{}"
        return extracted
    except Exception as exc:
        print(f"[Gemini] Warning: {type(exc).__name__}: {str(exc)[:220]}")
        return "{}"
