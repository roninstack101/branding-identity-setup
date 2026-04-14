"""
Serper utility – real Google search results via Serper.dev API.
Used by market_competitor_agent for up-to-date market and competitor data.
"""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()


async def serper_search(query: str, num_results: int = 10) -> list[dict]:
    """
    Run a Google search via Serper.dev and return a list of result dicts.
    Each dict has: title, link, snippet.
    Returns [] if the API key is missing or the call fails.
    """
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key or api_key == "your_serper_api_key_here":
        print("[Serper] Warning: SERPER_API_KEY not set.")
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num_results},
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title":   item.get("title", ""),
                "link":    item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return results

    except Exception as exc:
        print(f"[Serper] Warning: {type(exc).__name__}: {str(exc)[:200]}")
        return []


async def serper_multi_search(queries: list[str], num_per_query: int = 8) -> list[dict]:
    """Run multiple searches and return combined deduplicated results."""
    import asyncio
    tasks = [serper_search(q, num_per_query) for q in queries]
    all_results = await asyncio.gather(*tasks)

    seen_links: set[str] = set()
    combined: list[dict] = []
    for results in all_results:
        for r in results:
            if r["link"] not in seen_links:
                seen_links.add(r["link"])
                combined.append(r)
    return combined
