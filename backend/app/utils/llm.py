"""
LLM utility – multi-provider support.
  - call_llm            → Groq (Llama 3.3 70B)   – fast, free, structured JSON
  - call_openai         → OpenAI (GPT-4o mini)    – creative writing, reasoning, feedback
  - generate_logo_image → OpenAI image generation – logo concept grid (gpt-image-1 → dall-e-3)
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
    json_mode: bool = True,
) -> str:
    """Send a chat completion request to OpenAI and return the assistant message text.
    Set json_mode=False to get raw text output (e.g. for SVG generation)."""
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("[OpenAI] Warning: OPENAI_API_KEY not set, returning empty fallback.")
        return "" if not json_mode else "{}"

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await _openai_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ("" if not json_mode else "{}")
    except Exception as exc:
        if _STRICT_ERRORS:
            raise

        print(f"[OpenAI] Warning: {type(exc).__name__}: {str(exc)[:220]}")
        return "" if not json_mode else "{}"


async def generate_logo_from_reference(
    brand_prompt: str,
    reference_url: str | None = None,
) -> dict:
    """
    Generate a logo image using a brand prompt, optionally guided by a reference image URL.
    - If reference_url is given: downloads the image and uses gpt-image-1 edit endpoint.
    - Falls back to gpt-image-1 / dall-e-3 generation-only if edit fails or no reference.
    Returns {"b64_json": ..., "model": ..., "error": ...}
    """
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return {"error": "OPENAI_API_KEY not set"}

    # ── Attempt 1: gpt-image-1 edit with reference image ──────────────────────
    if reference_url:
        try:
            import httpx, io
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                r = await client.get(reference_url)
                r.raise_for_status()
                image_bytes = r.content
                ct = r.headers.get("content-type", "image/png")

            ext = "jpg" if ("jpeg" in ct or "jpg" in ct) else ("webp" if "webp" in ct else "png")
            buf = io.BytesIO(image_bytes)
            buf.name = f"reference.{ext}"

            response = await _openai_client.images.edit(
                model="gpt-image-1",
                image=buf,
                prompt=brand_prompt,
                n=1,
                size="1024x1024",
            )
            b64 = getattr(response.data[0], "b64_json", None)
            if b64:
                print("[LogoGen] Generated with gpt-image-1 edit + reference")
                return {"b64_json": b64, "model": "gpt-image-1-edit"}
        except Exception as exc:
            print(f"[LogoGen] gpt-image-1 edit failed: {type(exc).__name__}: {str(exc)[:200]}")

    # ── Attempt 2: gpt-image-1 generation (no reference) ─────────────────────
    try:
        response = await _openai_client.images.generate(
            model="gpt-image-1",
            prompt=brand_prompt,
            n=1,
            size="1024x1024",
        )
        b64 = getattr(response.data[0], "b64_json", None)
        if b64:
            print("[LogoGen] Generated with gpt-image-1 (no reference)")
            return {"b64_json": b64, "model": "gpt-image-1"}
    except Exception as exc:
        print(f"[LogoGen] gpt-image-1 generate failed: {type(exc).__name__}: {str(exc)[:200]}")

    # ── Attempt 3: dall-e-3 fallback ──────────────────────────────────────────
    try:
        response = await _openai_client.images.generate(
            model="dall-e-3",
            prompt=brand_prompt[:4000],
            n=1,
            size="1024x1024",
            quality="hd",
            response_format="b64_json",
        )
        b64 = getattr(response.data[0], "b64_json", None)
        if b64:
            print("[LogoGen] Generated with dall-e-3")
            return {"b64_json": b64, "model": "dall-e-3"}
    except Exception as exc:
        print(f"[LogoGen] dall-e-3 failed: {type(exc).__name__}: {str(exc)[:200]}")

    return {"error": "Logo generation failed — check API key tier and logs"}


async def generate_logo_image(prompt: str) -> dict:
    """
    Generate a logo concepts grid image.
    Tries gpt-image-1 first (best logo quality), falls back to dall-e-3.
    Returns {"b64_json": ..., "model": ..., "error": ...}
    """
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("[Image] ERROR: OPENAI_API_KEY not set")
        return {"error": "OPENAI_API_KEY not set"}

    # Attempt 1: gpt-image-1 (ChatGPT-quality logo generation)
    try:
        response = await _openai_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1536x1024",
        )
        item = response.data[0]
        b64 = getattr(item, "b64_json", None)
        if b64:
            print("[Image] Generated with gpt-image-1")
            return {"b64_json": b64, "model": "gpt-image-1"}
    except Exception as exc:
        print(f"[Image] gpt-image-1 failed: {type(exc).__name__}: {str(exc)[:200]}")

    # Attempt 2: dall-e-3 (widely available fallback — max 4000 chars)
    try:
        response = await _openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000],
            n=1,
            size="1792x1024",
            quality="hd",
            response_format="b64_json",
        )
        item = response.data[0]
        b64 = getattr(item, "b64_json", None)
        if b64:
            print("[Image] Generated with dall-e-3")
            return {"b64_json": b64, "model": "dall-e-3"}
    except Exception as exc:
        print(f"[Image] dall-e-3 failed: {type(exc).__name__}: {str(exc)[:200]}")

    return {"error": "Image generation failed — check API key tier and logs"}
