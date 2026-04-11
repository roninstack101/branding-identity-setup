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
    """Strip markdown code fences and return raw JSON string."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


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
        return _extract_json(raw)
    except Exception as exc:
        print(f"[Gemini] Warning: {type(exc).__name__}: {str(exc)[:220]}")
        return "{}"
