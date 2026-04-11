"""
Web search utility using DuckDuckGo (no API key required).
Uses the duckduckgo-search library.
"""
import asyncio
import os

import httpx
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


SERPER_URL = "https://google.serper.dev/search"


async def _serper_search(query: str, num_results: int) -> list[dict]:
    """Search using Serper when SERPER_API_KEY is configured."""
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SERPER_API_KEY is not configured")

    payload = {"q": query, "num": max(1, min(num_results, 20))}
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(SERPER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    organic = data.get("organic", [])
    return [
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in organic[:num_results]
    ]


async def _duckduckgo_search(query: str, num_results: int) -> list[dict]:
    """Fallback search implementation using DuckDuckGo."""
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: DDGS().text(query, max_results=num_results),
    )

    return [
        {
            "title": r.get("title", ""),
            "link": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in (results or [])[:num_results]
    ]


async def web_search(query: str, num_results: int = 8) -> list[dict]:
    """
    Return a list of search result dicts with keys: title, link, snippet.
    Uses DuckDuckGo – no API key needed.
    """
    try:
        # Prefer Serper when API key exists.
        if os.getenv("SERPER_API_KEY", "").strip():
            return await _serper_search(query, num_results)

        return await _duckduckgo_search(query, num_results)
    except Exception:
        try:
            # If Serper fails at runtime, gracefully fall back.
            return await _duckduckgo_search(query, num_results)
        except Exception as e:
            return [
                {
                    "title": f"[Search unavailable] for '{query}'",
                    "link": "",
                    "snippet": f"Search temporarily unavailable: {str(e)[:120]}",
                }
            ]
