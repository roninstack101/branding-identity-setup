"""
LLM utility – multi-provider support.
  - call_llm      → Groq (Llama 3.3 70B)   – fast, free, structured JSON
  - call_openai   → OpenAI (GPT-4o mini)    – creative writing, reasoning, feedback
"""
import os
from dotenv import load_dotenv
from groq import AsyncGroq
from openai import AsyncOpenAI

load_dotenv()

_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
_STRICT_ERRORS = os.getenv("LLM_STRICT_ERRORS", "0").strip().lower() in {"1", "true", "yes", "on"}

_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict | None = None,
) -> str:
    """Send a chat completion request to Groq and return the assistant message text."""
    # When no key is present (or intentionally disabled), return a safe fallback response
    # so the workflow can continue with heuristic/default logic in agents.
    if not os.getenv("GROQ_API_KEY", "").strip():
        if response_format and response_format.get("type") == "json_object":
            return "{}"
        return "LLM unavailable."

    kwargs: dict = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    try:
        response = await _client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    except Exception as exc:
        if _STRICT_ERRORS:
            raise

        # Graceful degradation for transient/API limit failures.
        print(f"[LLM] Warning: {type(exc).__name__}: {str(exc)[:220]}")

        if response_format and response_format.get("type") == "json_object":
            return "{}"
        return "LLM temporarily unavailable."


async def call_openai(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    model: str = "gpt-4o-mini",
) -> str:
    """Send a chat completion request to OpenAI and return the assistant message text."""
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("[OpenAI] Warning: OPENAI_API_KEY not set, returning empty fallback.")
        return "{}"

    try:
        response = await _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"
    except Exception as exc:
        if _STRICT_ERRORS:
            raise

        print(f"[OpenAI] Warning: {type(exc).__name__}: {str(exc)[:220]}")
        return "{}"
